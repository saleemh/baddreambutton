# BLE Phone Prototype BOM

This draft BOM supports a quick demo path where the button talks to a nearby smartphone.

## Button Side

| Part | Role | Notes |
| --- | --- | --- |
| Nordic `nRF52832`, `nRF52840`, or Silicon Labs `EFR32BG22` board or module | Button MCU and radio | Choose the easiest board for firmware bring-up |
| `CR2032` holder | Battery power | Coin-cell target remains realistic here |
| `CR2032` battery | Primary battery | Fine for a demo path |
| Momentary pushbutton switch | User input | Can be on-board for early testing |
| Optional capacitor | Improve stability | Helpful during radio bursts |

## Phone Side

| Part | Role | Notes |
| --- | --- | --- |
| `iPhone` or Android device | Event receiver | Must remain nearby and configured |
| Mobile app | Cloud relay | Needs permissions and reliable background behavior |

## Software Notes

This path is mainly valuable for:

- UX exploration
- fast internal prototyping
- validating event formats before a gateway exists
