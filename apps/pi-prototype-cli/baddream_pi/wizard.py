from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from .config import AppConfig, resolve_config_path
from .runtime import print_config_summary, test_hardware
from .ui import divider, error, heading, info, success, warn


REQUIRED_PACKAGES = [
    "sense-hat",
    "python3-sense-hat",
    "bluez",
    "bluetooth",
    "pi-bluetooth",
    "git",
    "curl",
]


class SetupWizard:
    def __init__(self, config_path: Path | None = None):
        self.config_path = resolve_config_path(config_path)
        self.config = AppConfig.load(self.config_path)
        self.entrypoint = Path(__file__).resolve().parents[1] / "main.py"

    def run(self) -> int:
        print(heading("Bad Dream Button Pi Prototype Setup"))
        print(info("This wizard prepares the Raspberry Pi 3 + Sense HAT prototype."))
        print(info(f"Config path: {self.config_path}"))

        while True:
            print()
            print(divider())
            print("1. Review current configuration")
            print("2. Update package lists")
            print("3. Upgrade system packages")
            print("4. Install or upgrade required packages")
            print("5. Edit prototype configuration")
            print("6. Test Sense HAT hardware")
            print("7. Install systemd service")
            print("8. Start runtime now")
            print("9. Quit")
            print(divider())
            choice = input("Choose an option [1-9]: ").strip()

            if choice == "1":
                self.show_configuration()
            elif choice == "2":
                self.run_command(["sudo", "apt", "update"], "Updating apt package lists")
            elif choice == "3":
                self.run_command(["sudo", "apt", "full-upgrade", "-y"], "Upgrading system packages")
            elif choice == "4":
                self.install_packages()
            elif choice == "5":
                self.edit_configuration()
            elif choice == "6":
                test_hardware(self.config)
            elif choice == "7":
                self.install_service()
            elif choice == "8":
                return self.start_runtime_now()
            elif choice == "9":
                print("Exiting setup wizard.")
                return 0
            else:
                print(warn("Please choose a valid menu option."))

    def show_configuration(self) -> None:
        print_config_summary(self.config)
        if self.config.webhook_url:
            print(success("Webhook delivery is enabled."))
        else:
            print(warn("Webhook URL is empty. Runtime will operate in local log-only mode."))

    def install_packages(self) -> None:
        print(heading("Required Packages"))
        print(", ".join(REQUIRED_PACKAGES))
        self.run_command(["sudo", "apt", "update"], "Refreshing apt package lists")
        self.run_command(
            ["sudo", "apt", "install", "-y", *REQUIRED_PACKAGES],
            "Installing or upgrading required packages",
        )

    def edit_configuration(self) -> None:
        print(heading("Edit Prototype Configuration"))
        fields = [
            ("device_name", "Device name", self.config.device_name),
            ("message", "Alert message", self.config.message),
            ("webhook_url", "Webhook URL (leave blank for local-only mode)", self.config.webhook_url),
            ("alert_mode", "Alert mode", self.config.alert_mode),
            ("bridge_token", "Bridge token (optional)", self.config.bridge_token),
            ("reply_poll_url", "Reply poll URL (optional)", self.config.reply_poll_url),
            ("healthcheck_url", "Healthcheck URL (optional)", self.config.healthcheck_url),
        ]

        updates = {}
        for key, label, current in fields:
            value = input(f"{label} [{current}]: ").strip()
            updates[key] = current if value == "" else value

        led_brightness = self.prompt_float("LED brightness", self.config.led_brightness, 0.05, 1.0)
        cooldown = self.prompt_int("Cooldown seconds", self.config.cooldown_seconds, 0)
        timeout = self.prompt_int("Request timeout seconds", self.config.request_timeout_seconds, 1)
        reply_poll_seconds = self.prompt_int("Reply poll interval seconds", self.config.reply_poll_seconds, 1)

        self.config = AppConfig(
            device_name=updates["device_name"],
            message=updates["message"],
            webhook_url=updates["webhook_url"],
            alert_mode=updates["alert_mode"],
            bridge_token=updates["bridge_token"],
            reply_poll_url=updates["reply_poll_url"],
            reply_poll_seconds=reply_poll_seconds,
            healthcheck_url=updates["healthcheck_url"],
            led_brightness=led_brightness,
            cooldown_seconds=cooldown,
            request_timeout_seconds=timeout,
        )
        saved_path = self.config.save(self.config_path)
        print(success(f"Configuration saved to {saved_path}"))

    def install_service(self) -> None:
        print(heading("Install systemd Service"))
        service_name = "baddream-button.service"
        command = f"{shlex.quote(sys.executable)} {shlex.quote(str(self.entrypoint))} run"
        service_contents = "\n".join(
            [
                "[Unit]",
                "Description=Bad Dream Button Pi Prototype",
                "After=network-online.target",
                "",
                "[Service]",
                f"User={os.environ.get('USER', 'pi')}",
                f"WorkingDirectory={shlex.quote(str(self.entrypoint.parent))}",
                f"Environment=BAD_DREAM_CONFIG={self.config_path}",
                f"ExecStart={command}",
                "Restart=always",
                "RestartSec=3",
                "",
                "[Install]",
                "WantedBy=multi-user.target",
                "",
            ]
        )
        tmp_path = Path("/tmp") / service_name
        tmp_path.write_text(service_contents, encoding="utf-8")
        print(info(f"Prepared service file at {tmp_path}"))
        self.run_command(["sudo", "cp", str(tmp_path), f"/etc/systemd/system/{service_name}"], "Copying service file")
        self.run_command(["sudo", "systemctl", "daemon-reload"], "Reloading systemd")
        self.run_command(["sudo", "systemctl", "enable", service_name], "Enabling service")

        if self.confirm("Start the service now? [Y/n]: ", default=True):
            self.run_command(["sudo", "systemctl", "start", service_name], "Starting service")
            self.run_command(["sudo", "systemctl", "status", service_name, "--no-pager"], "Showing service status")

    def start_runtime_now(self) -> int:
        from .runtime import PrototypeRuntime

        print(info("Starting runtime in the foreground."))
        runtime = PrototypeRuntime(self.config)
        return runtime.run()

    def run_command(self, command: list[str], description: str) -> int:
        print(info(description))
        print(info("$ " + " ".join(shlex.quote(part) for part in command)))
        try:
            result = subprocess.run(command, check=False)
        except FileNotFoundError as exc:
            print(error(f"Command not found: {exc}"))
            return 1

        if result.returncode == 0:
            print(success("Command completed successfully."))
        else:
            print(error(f"Command failed with exit code {result.returncode}."))
        return result.returncode

    def confirm(self, prompt: str, default: bool) -> bool:
        raw = input(prompt).strip().lower()
        if not raw:
            return default
        return raw in {"y", "yes"}

    def prompt_int(self, label: str, current: int, minimum: int) -> int:
        while True:
            raw = input(f"{label} [{current}]: ").strip()
            if raw == "":
                return current
            try:
                value = int(raw)
            except ValueError:
                print(warn("Please enter a whole number."))
                continue
            if value < minimum:
                print(warn(f"Value must be at least {minimum}."))
                continue
            return value

    def prompt_float(self, label: str, current: float, minimum: float, maximum: float) -> float:
        while True:
            raw = input(f"{label} [{current}]: ").strip()
            if raw == "":
                return current
            try:
                value = float(raw)
            except ValueError:
                print(warn("Please enter a number."))
                continue
            if not (minimum <= value <= maximum):
                print(warn(f"Value must be between {minimum} and {maximum}."))
                continue
            return value
