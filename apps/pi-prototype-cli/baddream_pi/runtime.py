from __future__ import annotations

import json
import socket
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import AppConfig
from .hardware import BLUE, GREEN, RED, SenseHatDisplay
from .ui import error, heading, info, success, warn


LOG_PATH = Path.home() / ".local" / "state" / "baddream-button" / "events.log"


class PrototypeRuntime:
    def __init__(self, config: AppConfig):
        self.config = config
        self.display = SenseHatDisplay(brightness=config.led_brightness)
        self.last_connectivity_ok = False
        self.last_press_time = 0.0
        self.last_connectivity_check_at = 0.0

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
            headers={"Content-Type": "application/json"},
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
        target_url = self.config.healthcheck_url or self.config.webhook_url
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
