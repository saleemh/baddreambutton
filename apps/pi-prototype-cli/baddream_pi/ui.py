from __future__ import annotations

import shutil


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def supports_color() -> bool:
    return shutil.get_terminal_size((80, 24)).columns > 0


def colorize(text: str, color: str) -> str:
    if not supports_color():
        return text
    return f"{color}{text}{RESET}"


def heading(text: str) -> str:
    return colorize(f"{BOLD}{text}", CYAN)


def success(text: str) -> str:
    return colorize(text, GREEN)


def warn(text: str) -> str:
    return colorize(text, YELLOW)


def error(text: str) -> str:
    return colorize(text, RED)


def info(text: str) -> str:
    return colorize(text, BLUE)


def divider() -> str:
    width = shutil.get_terminal_size((80, 24)).columns
    return colorize("-" * min(max(width, 40), 100), DIM)
