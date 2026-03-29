from __future__ import annotations

import time
from dataclasses import dataclass


try:
    from sense_hat import ACTION_PRESSED, SenseHat
except ImportError:  # pragma: no cover - depends on target hardware
    ACTION_PRESSED = "pressed"
    SenseHat = None


Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
RED: Color = (255, 0, 0)
GREEN: Color = (0, 255, 0)
BLUE: Color = (0, 0, 255)
YELLOW: Color = (255, 180, 0)


@dataclass
class HardwareStatus:
    available: bool
    detail: str


class SenseHatDisplay:
    def __init__(self, brightness: float = 0.4):
        self._brightness = max(0.05, min(brightness, 1.0))
        self._sense = SenseHat() if SenseHat is not None else None
        if self._sense is not None:
            self._sense.low_light = self._brightness <= 0.5
        self._last_state = "off"

    def status(self) -> HardwareStatus:
        if self._sense is None:
            return HardwareStatus(False, "python3-sense-hat is not installed or hardware is unavailable.")
        return HardwareStatus(True, "Sense HAT detected.")

    def _fill(self, color: Color) -> None:
        if self._sense is None:
            return
        self._sense.clear(color)

    def _scale(self, color: Color) -> Color:
        return tuple(max(0, min(255, int(channel * self._brightness))) for channel in color)

    def set_state(self, state: str) -> None:
        self._last_state = state
        if state == "booting":
            self._fill(self._scale(WHITE))
        elif state == "ready_not_connected":
            self._fill(self._scale(YELLOW))
        elif state == "ready_connected":
            self._fill(self._scale(GREEN))
        elif state == "off":
            self._fill(BLACK)

    def pulse_sending(self) -> None:
        for _ in range(2):
            self._fill(self._scale(BLUE))
            time.sleep(0.15)
            self._fill(BLACK)
            time.sleep(0.08)
        self._fill(self._scale(BLUE))

    def flash_success(self) -> None:
        for _ in range(2):
            self._fill(self._scale(GREEN))
            time.sleep(0.15)
            self._fill(BLACK)
            time.sleep(0.08)

    def flash_failure(self) -> None:
        for _ in range(2):
            self._fill(self._scale(RED))
            time.sleep(0.2)
            self._fill(BLACK)
            time.sleep(0.1)

    def show_text(self, text: str, color: Color = WHITE) -> None:
        if self._sense is None:
            return
        self._sense.show_message(text, text_colour=self._scale(color))

    def joystick_events(self):
        if self._sense is None:
            return []
        return self._sense.stick.get_events()

    def is_middle_press(self, event) -> bool:
        return getattr(event, "direction", None) == "middle" and getattr(event, "action", None) == ACTION_PRESSED
