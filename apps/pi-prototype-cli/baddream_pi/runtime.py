from __future__ import annotations

import json
import socket
import time
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .config import AppConfig
from .hardware import BLUE, GREEN, RED, SenseHatDisplay
from .ui import error, heading, info, success, warn


LOG_PATH = Path.home() / ".local" / "state" / "baddream-button" / "events.log"
DISPLAY_MAX_CHARS = 96
DISPLAY_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?:;'-()/")


class PrototypeRuntime:
    def __init__(self, config: AppConfig):
        self.config = config
        self.display = SenseHatDisplay(brightness=config.led_brightness)
        self.last_connectivity_ok = False
        self.last_press_time = 0.0
        self.last_connectivity_check_at = 0.0
        self.last_reply_poll_at = 0.0

    def run(self) -> int:
        hardware = self.display.status()
        print(heading("Bad Dream Button Runtime"))
        print(info(f"Device name: {self.config.device_name}"))
        print(info(f"Alert mode: {self.config.alert_mode}"))
        if self.config.webhook_url:
            print(info(f"Webhook: {self.config.webhook_url}"))
        else:
            print(warn("Webhook not configured. Runtime will log locally and simulate success."))

        if not hardware.available:
            print(error(hardware.detail))
            return 1

        print(success(hardware.detail))
        self.display.set_state("booting")
        time.sleep(0.25)
        self.last_connectivity_ok = self.check_connectivity()
        self.refresh_ready_state()
        print(info("Waiting for Sense HAT center press. Press Ctrl+C to stop."))

        try:
            while True:
                now = time.time()
                if now - self.last_connectivity_check_at >= 10:
                    latest = self.check_connectivity()
                    self.last_connectivity_check_at = now
                    if latest != self.last_connectivity_ok:
                        self.last_connectivity_ok = latest
                        self.refresh_ready_state()
                        print(info(f"Connectivity changed: {'online' if latest else 'offline'}"))

                if now - self.last_reply_poll_at >= self.config.reply_poll_seconds:
                    self.last_reply_poll_at = now
                    self.poll_for_replies()

                for event in self.display.joystick_events():
                    if self.display.is_middle_press(event):
                        self.handle_button_press()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.display.set_state("off")
            print("\nStopped.")
            return 0

    def handle_button_press(self) -> None:
        now = time.time()
        if now - self.last_press_time < self.config.cooldown_seconds:
            print(warn("Ignoring press because cooldown is still active."))
            return

        self.last_press_time = now
        payload = self.build_payload()
        self.display.pulse_sending()
        print(info("Sending alert payload..."))
        self.log_event(payload)

        if self.config.webhook_url:
            ok, message = self.send_webhook(payload)
        else:
            ok, message = True, "No webhook configured; logged locally only."

        if ok:
            self.display.flash_success()
            print(success(message))
        else:
            self.display.flash_failure()
            print(error(message))

        self.last_connectivity_ok = self.check_connectivity()
        self.refresh_ready_state()

    def build_payload(self) -> dict[str, Any]:
        return {
            "event_type": "bad_dream_button_pressed",
            "device_name": self.config.device_name,
            "message": self.config.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_mode": self.config.alert_mode,
            "hostname": socket.gethostname(),
        }

    def log_event(self, payload: dict[str, Any]) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def send_webhook(self, payload: dict[str, Any]) -> tuple[bool, str]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.config.webhook_url,
            data=body,
            headers=self.build_headers({"Content-Type": "application/json"}),
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                status = getattr(response, "status", None) or response.getcode()
                if 200 <= status < 300:
                    return True, f"Alert sent successfully with HTTP {status}."
                return False, f"Webhook returned unexpected status {status}."
        except HTTPError as exc:
            return False, f"Webhook failed with HTTP {exc.code}."
        except URLError as exc:
            return False, f"Webhook connection failed: {exc.reason}."
        except Exception as exc:  # pragma: no cover - safety net
            return False, f"Unexpected send error: {exc}."

    def check_connectivity(self) -> bool:
        target_url = self.config.healthcheck_url or self.config.webhook_url or self.config.reply_poll_url
        if not target_url:
            return True

        parsed = urlparse(target_url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not hostname:
            return False

        try:
            with socket.create_connection((hostname, port), timeout=3):
                return True
        except OSError:
            return False

    def refresh_ready_state(self) -> None:
        state = "ready_connected" if self.last_connectivity_ok else "ready_not_connected"
        self.display.set_state(state)

    def poll_for_replies(self) -> None:
        reply_url = self.resolve_reply_poll_url()
        if not reply_url:
            return
        ok, replies_or_error = self.fetch_replies(reply_url)
        if not ok:
            print(warn(f"Reply poll failed: {replies_or_error}"))
            return

        replies = replies_or_error
        if not replies:
            return

        for reply in replies:
            reply_text = str(reply.get("text", "")).strip()
            reply_id = str(reply.get("reply_id", "")).strip()
            if not reply_text or not reply_id:
                continue
            display_text = self.sanitize_for_display(reply_text)
            if not display_text:
                continue
            self.display.flash_reply()
            print(info(f"New WhatsApp reply: {display_text}"))
            self.display.show_text(display_text, BLUE)
            self.acknowledge_reply(reply_id)
            self.refresh_ready_state()

    def resolve_reply_poll_url(self) -> str:
        if self.config.reply_poll_url:
            return self.config.reply_poll_url
        if not self.config.webhook_url:
            return ""
        parsed = urlparse(self.config.webhook_url)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}/replies"

    def fetch_replies(self, reply_url: str) -> tuple[bool, list[dict[str, Any]] | str]:
        query = urlencode({"device_name": self.config.device_name})
        connector = "&" if "?" in reply_url else "?"
        url = f"{reply_url}{connector}{query}"
        request = Request(url, headers=self.build_headers())
        try:
            with urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                replies = payload.get("replies", [])
                if not isinstance(replies, list):
                    return False, "Reply payload is not a list"
                return True, replies
        except HTTPError as exc:
            return False, f"HTTP {exc.code}"
        except URLError as exc:
            return False, f"connection failed: {exc.reason}"
        except Exception as exc:  # pragma: no cover - safety net
            return False, f"unexpected error: {exc}"

    def acknowledge_reply(self, reply_id: str) -> None:
        reply_url = self.resolve_reply_poll_url()
        if not reply_url:
            return
        ack_url = reply_url.rstrip("/") + "/ack"
        payload = {
            "device_name": self.config.device_name,
            "reply_id": reply_id,
        }
        request = Request(
            ack_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self.build_headers({"Content-Type": "application/json"}),
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.request_timeout_seconds):
                return
        except Exception:
            return

    def build_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.config.bridge_token:
            headers["Authorization"] = f"Bearer {self.config.bridge_token}"
        if extra:
            headers.update(extra)
        return headers

    def sanitize_for_display(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        upper = ascii_text.upper()
        cleaned = "".join(ch if ch in DISPLAY_ALLOWED else " " for ch in upper)
        cleaned = " ".join(cleaned.split()).strip()
        if not cleaned:
            return ""
        if len(cleaned) > DISPLAY_MAX_CHARS:
            cleaned = cleaned[: DISPLAY_MAX_CHARS - 3].rstrip() + "..."
        return cleaned


def print_config_summary(config: AppConfig) -> None:
    print(heading("Current Configuration"))
    for key, value in asdict(config).items():
        print(f"- {key}: {value}")


def test_hardware(config: AppConfig) -> int:
    display = SenseHatDisplay(brightness=config.led_brightness)
    status = display.status()
    print(heading("Sense HAT Hardware Test"))
    if not status.available:
        print(error(status.detail))
        return 1

    print(success(status.detail))
    display.set_state("booting")
    time.sleep(0.4)
    display.set_state("ready_not_connected")
    time.sleep(0.4)
    display.set_state("ready_connected")
    time.sleep(0.4)
    display.pulse_sending()
    display.flash_success()
    display.flash_failure()
    display.show_text("OK", GREEN)
    display.set_state("ready_connected")
    print(success("LED state sequence completed."))
    print(info("Now press the center joystick once."))

    deadline = time.time() + 15
    while time.time() < deadline:
        for event in display.joystick_events():
            if display.is_middle_press(event):
                display.show_text("BTN", BLUE)
                display.set_state("ready_connected")
                print(success("Center press detected."))
                return 0
        time.sleep(0.1)

    print(warn("Center press was not detected within 15 seconds."))
    return 1
