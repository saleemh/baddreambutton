from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "baddream-button" / "openclaw-bridge.json"
DEFAULT_STATE_PATH = Path.home() / ".local" / "state" / "baddream-button" / "openclaw-bridge-state.json"


@dataclass
class BridgeConfig:
    bind_host: str
    bind_port: int
    bridge_token: str
    whatsapp_target: str
    openclaw_command: str
    transcript_path: str
    active_device_ttl_minutes: int
    state_path: str

    @classmethod
    def default(cls) -> "BridgeConfig":
        return cls(
            bind_host="0.0.0.0",
            bind_port=8787,
            bridge_token="",
            whatsapp_target="+16177107422",
            openclaw_command="openclaw",
            transcript_path=str(Path.home() / ".openclaw" / "agents" / "default" / "sessions" / "main.jsonl"),
            active_device_ttl_minutes=1440,
            state_path=str(DEFAULT_STATE_PATH),
        )

    @classmethod
    def load(cls, path: Path | None = None) -> "BridgeConfig":
        config_path = resolve_config_path(path)
        if not config_path.exists():
            config = cls.default()
            config.save(config_path)
            return config

        raw = json.loads(config_path.read_text(encoding="utf-8"))
        defaults = asdict(cls.default())
        defaults.update(raw)
        return cls(**defaults)

    def save(self, path: Path | None = None) -> Path:
        config_path = resolve_config_path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return config_path


def resolve_config_path(path: Path | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    override = os.environ.get("BAD_DREAM_BRIDGE_CONFIG")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_PATH
