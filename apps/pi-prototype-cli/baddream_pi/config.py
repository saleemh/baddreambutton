from __future__ import annotations

import json
import os
import socket
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "baddream-button" / "config.json"


@dataclass
class AppConfig:
    device_name: str
    message: str
    webhook_url: str
    alert_mode: str
    led_brightness: float
    cooldown_seconds: int
    request_timeout_seconds: int
    healthcheck_url: str

    @classmethod
    def default(cls) -> "AppConfig":
        return cls(
            device_name=f"{socket.gethostname()}",
            message="A bad dream occurred and help is requested.",
            webhook_url="",
            alert_mode="sms_only",
            led_brightness=0.4,
            cooldown_seconds=5,
            request_timeout_seconds=10,
            healthcheck_url="",
        )

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        config_path = resolve_config_path(path)
        if not config_path.exists():
            return cls.default()

        with config_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        defaults = asdict(cls.default())
        defaults.update(raw)
        return cls(**defaults)

    def save(self, path: Path | None = None) -> Path:
        config_path = resolve_config_path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=2, sort_keys=True)
            handle.write("\n")
        return config_path


def resolve_config_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    override = os.environ.get("BAD_DREAM_CONFIG")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_PATH
