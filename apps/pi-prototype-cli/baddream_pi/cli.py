from __future__ import annotations

import argparse
from pathlib import Path

from .config import AppConfig
from .runtime import PrototypeRuntime, print_config_summary, test_hardware
from .wizard import SetupWizard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bad Dream Button Pi prototype CLI")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to the config file. Defaults to ~/.config/baddream-button/config.json",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("wizard", help="Run the interactive setup wizard")
    subparsers.add_parser("run", help="Run the prototype runtime")
    subparsers.add_parser("show-config", help="Print the current configuration")
    subparsers.add_parser("test-hardware", help="Run a Sense HAT hardware test")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {None, "wizard"}:
        return SetupWizard(args.config).run()

    config = AppConfig.load(args.config)

    if args.command == "run":
        return PrototypeRuntime(config).run()
    if args.command == "show-config":
        print_config_summary(config)
        return 0
    if args.command == "test-hardware":
        return test_hardware(config)

    parser.error(f"Unknown command: {args.command}")
    return 2
