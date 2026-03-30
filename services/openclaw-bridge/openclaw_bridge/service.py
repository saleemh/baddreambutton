from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import BridgeConfig, resolve_config_path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReplyMessage:
    reply_id: str
    text: str
    created_at: str
    sender: str = "whatsapp"


@dataclass
class DeviceState:
    last_alert_at: str | None = None
    unread_replies: list[ReplyMessage] = field(default_factory=list)


@dataclass
class BridgeState:
    current_device_name: str = ""
    transcript_offset: int = 0
    seen_reply_ids: list[str] = field(default_factory=list)
    devices: dict[str, DeviceState] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "BridgeState":
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        devices = {
            key: DeviceState(
                last_alert_at=value.get("last_alert_at"),
                unread_replies=[ReplyMessage(**msg) for msg in value.get("unread_replies", [])],
            )
            for key, value in raw.get("devices", {}).items()
        }
        return cls(
            current_device_name=raw.get("current_device_name", ""),
            transcript_offset=raw.get("transcript_offset", 0),
            seen_reply_ids=raw.get("seen_reply_ids", []),
            devices=devices,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "current_device_name": self.current_device_name,
            "transcript_offset": self.transcript_offset,
            "seen_reply_ids": self.seen_reply_ids[-500:],
            "devices": {
                key: {
                    "last_alert_at": value.last_alert_at,
                    "unread_replies": [asdict(msg) for msg in value.unread_replies],
                }
                for key, value in self.devices.items()
            },
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OpenClawBridge:
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.state_path = Path(config.state_path).expanduser()
        self.transcript_path = Path(config.transcript_path).expanduser()
        self.state = BridgeState.load(self.state_path)
        self.lock = threading.RLock()
        if not self.state_path.exists() and self.transcript_path.exists():
            self.state.transcript_offset = self.transcript_path.stat().st_size
            self.persist()

    def health(self) -> dict[str, Any]:
        with self.lock:
            return {
                "ok": True,
                "bind": f"{self.config.bind_host}:{self.config.bind_port}",
                "transcript_exists": self.transcript_path.exists(),
                "current_device_name": self.state.current_device_name,
                "devices": list(self.state.devices.keys()),
            }

    def handle_alert(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        device_name = str(payload.get("device_name", "")).strip()
        message = str(payload.get("message", "")).strip()
        timestamp = str(payload.get("timestamp", "")).strip()
        alert_mode = str(payload.get("alert_mode", "sms_only")).strip()
        hostname = str(payload.get("hostname", "")).strip()

        if not device_name or not message:
            return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "device_name and message are required"}

        rendered = self.render_outbound_message(
            device_name=device_name,
            message=message,
            timestamp=timestamp or utc_now_iso(),
            alert_mode=alert_mode,
            hostname=hostname,
        )

        ok, detail = self.send_via_openclaw(rendered)
        if not ok:
            return HTTPStatus.BAD_GATEWAY, {"ok": False, "error": detail}

        with self.lock:
            state = self.state.devices.setdefault(device_name, DeviceState())
            state.last_alert_at = utc_now_iso()
            self.state.current_device_name = device_name
            self.reset_transcript_cursor_to_end()
            self.persist()

        return HTTPStatus.OK, {"ok": True, "detail": detail, "device_name": device_name}

    def list_replies(self, device_name: str) -> tuple[int, dict[str, Any]]:
        if not device_name:
            return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "device_name is required"}

        self.poll_transcript_for_new_replies()
        with self.lock:
            device_state = self.state.devices.setdefault(device_name, DeviceState())
            return HTTPStatus.OK, {
                "ok": True,
                "device_name": device_name,
                "replies": [asdict(reply) for reply in device_state.unread_replies],
            }

    def acknowledge_reply(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        device_name = str(payload.get("device_name", "")).strip()
        reply_id = str(payload.get("reply_id", "")).strip()
        if not device_name or not reply_id:
            return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "device_name and reply_id are required"}

        with self.lock:
            device_state = self.state.devices.setdefault(device_name, DeviceState())
            before = len(device_state.unread_replies)
            device_state.unread_replies = [reply for reply in device_state.unread_replies if reply.reply_id != reply_id]
            removed = before - len(device_state.unread_replies)
            self.persist()
        return HTTPStatus.OK, {"ok": True, "removed": removed}

    def render_outbound_message(
        self,
        *,
        device_name: str,
        message: str,
        timestamp: str,
        alert_mode: str,
        hostname: str,
    ) -> str:
        lines = [
            "Bad Dream Button alert.",
            f"Device: {device_name}",
            f"Time: {timestamp}",
            f"Mode: {alert_mode}",
            f"Message: {message}",
        ]
        if hostname:
            lines.append(f"Host: {hostname}")
        lines.append("Reply here and the response will be shown on the button display.")
        return "\n".join(lines)

    def send_via_openclaw(self, message: str) -> tuple[bool, str]:
        command = [
            self.config.openclaw_command,
            "agent",
            "--to",
            self.config.whatsapp_target,
            "--message",
            message,
            "--deliver",
            "--reply-channel",
            "whatsapp",
            "--reply-to",
            self.config.whatsapp_target,
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except FileNotFoundError:
            return False, f"OpenClaw command not found: {self.config.openclaw_command}"
        except subprocess.TimeoutExpired:
            return False, "OpenClaw agent timed out"

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            return False, stderr or stdout or f"OpenClaw exited with code {completed.returncode}"

        return True, "OpenClaw accepted the alert request"

    def poll_transcript_for_new_replies(self) -> None:
        with self.lock:
            if not self.transcript_path.exists():
                return

            if self.state.current_device_name:
                self.expire_old_device_mapping()

            with self.transcript_path.open("rb") as handle:
                handle.seek(self.state.transcript_offset)
                for raw_line in handle:
                    self.state.transcript_offset = handle.tell()
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    reply = self.extract_reply(entry)
                    if reply is None:
                        continue
                    if reply.reply_id in self.state.seen_reply_ids:
                        continue
                    self.state.seen_reply_ids.append(reply.reply_id)
                    if not self.state.current_device_name:
                        continue
                    device_state = self.state.devices.setdefault(self.state.current_device_name, DeviceState())
                    device_state.unread_replies.append(reply)
            self.persist()

    def extract_reply(self, entry: dict[str, Any]) -> ReplyMessage | None:
        role = self.extract_role(entry)
        if role != "user":
            return None

        text = self.extract_text(entry)
        if not text:
            return None

        reply_id = str(self.extract_field(entry, ["id", "message.id", "messageId", "event.id"]))
        if not reply_id:
            reply_id = hashlib.sha256(json.dumps(entry, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        created_at = str(self.extract_field(entry, ["createdAt", "timestamp", "message.timestamp", "ts"])) or utc_now_iso()
        sender = str(self.extract_field(entry, ["from", "sender", "peer", "message.from"])) or "whatsapp"
        return ReplyMessage(reply_id=reply_id, text=text, created_at=created_at, sender=sender)

    def extract_role(self, entry: dict[str, Any]) -> str:
        for path in ["role", "message.role", "payload.role", "entry.role"]:
            value = self.extract_field(entry, [path])
            if isinstance(value, str) and value:
                return value
        return ""

    def extract_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts = []
            for item in value:
                text = self.extract_text(item)
                if text:
                    parts.append(text)
            return " ".join(parts).strip()
        if isinstance(value, dict):
            for key in ["text", "message", "content", "body", "value"]:
                if key in value:
                    text = self.extract_text(value[key])
                    if text:
                        return text
            if value.get("type") == "text" and "text" in value:
                return self.extract_text(value["text"])
        return ""

    def extract_field(self, entry: dict[str, Any], paths: list[str]) -> Any:
        for path in paths:
            cursor: Any = entry
            ok = True
            for part in path.split("."):
                if isinstance(cursor, dict) and part in cursor:
                    cursor = cursor[part]
                else:
                    ok = False
                    break
            if ok:
                return cursor
        return None

    def expire_old_device_mapping(self) -> None:
        current = self.state.current_device_name
        if not current:
            return
        device_state = self.state.devices.get(current)
        if not device_state or not device_state.last_alert_at:
            return
        try:
            last = datetime.fromisoformat(device_state.last_alert_at)
        except ValueError:
            return
        ttl = timedelta(minutes=self.config.active_device_ttl_minutes)
        if datetime.now(timezone.utc) - last > ttl:
            self.state.current_device_name = ""

    def reset_transcript_cursor_to_end(self) -> None:
        if self.transcript_path.exists():
            self.state.transcript_offset = self.transcript_path.stat().st_size

    def persist(self) -> None:
        self.state.save(self.state_path)


class BridgeRequestHandler(BaseHTTPRequestHandler):
    bridge: OpenClawBridge

    def do_GET(self) -> None:  # noqa: N802
        if not self.authorized():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(HTTPStatus.OK, self.bridge.health())
            return
        if parsed.path == "/replies":
            params = parse_qs(parsed.query)
            device_name = params.get("device_name", [""])[0]
            status, payload = self.bridge.list_replies(device_name)
            self.respond(status, payload)
            return
        self.respond(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self.authorized():
            return
        parsed = urlparse(self.path)
        body = self.read_json()
        if body is None:
            self.respond(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Invalid JSON body"})
            return

        if parsed.path == "/alerts":
            status, payload = self.bridge.handle_alert(body)
            self.respond(status, payload)
            return
        if parsed.path == "/replies/ack":
            status, payload = self.bridge.acknowledge_reply(body)
            self.respond(status, payload)
            return
        self.respond(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def authorized(self) -> bool:
        token = self.bridge.config.bridge_token
        if not token:
            return True
        header = self.headers.get("Authorization", "")
        expected = f"Bearer {token}"
        if header == expected:
            return True
        self.respond(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "Unauthorized"})
        return False

    def read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def respond(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bad Dream Button OpenClaw bridge")
    parser.add_argument("--config", type=Path, help="Path to the bridge config file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = resolve_config_path(args.config)
    config = BridgeConfig.load(config_path)
    bridge = OpenClawBridge(config)

    server = ThreadingHTTPServer((config.bind_host, config.bind_port), BridgeRequestHandler)
    BridgeRequestHandler.bridge = bridge

    print(f"Bad Dream Button OpenClaw bridge listening on http://{config.bind_host}:{config.bind_port}")
    print(f"Config: {config_path}")
    print(f"Transcript: {config.transcript_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
