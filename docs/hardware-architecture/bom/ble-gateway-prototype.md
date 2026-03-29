# BLE Gateway Prototype BOM

This draft BOM supports the recommended MVP: a `BLE` coin-cell button with a powered local gateway.

## Button Side

| Part | Role | Notes |
| --- | --- | --- |
| Nordic `nRF52832` or Silicon Labs `EFR32BG22` module | Button MCU and radio | Prioritize a small off-the-shelf module |
| `CR2032` holder | Battery power | Through-hole for quick prototype, lower profile later |
| `CR2032` battery | Primary battery | Prototype with fresh name-brand cells |
| Momentary pushbutton switch | User input | Prefer larger cap for bedside usability |
| Bulk capacitor | Peak current support | Place close to module supply |
| Optional low-current LED | Brief status feedback | Keep off by default |

## Gateway Side

| Part | Role | Notes |
| --- | --- | --- |
| `ESP32-C3` dev board or Raspberry Pi | Always-on gateway | USB powered |
| USB power supply | Gateway power | Bedside or nearby outlet |
| Local network connection | Cloud access | `Wi-Fi` or Ethernet depending on gateway |

## Software Notes

The gateway should:

- listen for the button event
- forward the event to a backend or webhook
- support retries and simple event logging
