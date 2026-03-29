# BLE Gateway Prototype BOM

This draft BOM supports the recommended MVP: a `BLE` coin-cell button with a powered local relay.

## Button Side

| Part | Role | Notes |
| --- | --- | --- |
| Nordic `nRF52832` or Silicon Labs `EFR32BG22` module | Button MCU and radio | Prioritize a small off-the-shelf module |
| `CR2032` holder | Battery power | Through-hole for quick prototype, lower profile later |
| `CR2032` battery | Primary battery | Prototype with fresh name-brand cells |
| Momentary pushbutton switch | User input | Prefer larger cap for bedside usability |
| Bulk capacitor | Peak current support | Place close to module supply |
| Optional low-current LED | Brief status feedback | Keep off by default |

## Relay Side

| Part | Role | Notes |
| --- | --- | --- |
| Raspberry Pi or similar powered `BLE` receiver | Always-on relay | USB powered |
| USB power supply | Relay power | Bedside or nearby outlet |
| Local network connection | Cloud access | Ethernet or other powered host connectivity |

## Software Notes

The relay should:

- listen for the button event
- forward the event to a backend or webhook
- support retries and simple event logging
