# Wi-Fi Direct Prototype BOM

This draft BOM supports a direct `Wi-Fi` button that calls a cloud service without a local gateway.

## Device Side

| Part | Role | Notes |
| --- | --- | --- |
| `ESP32-C3` or similar board/module | MCU, `Wi-Fi`, and optional `BLE` for provisioning | Best suited for powered or larger-battery designs |
| Battery or USB power source | Primary power | `CR2032` is not the preferred target here |
| Larger momentary pushbutton switch | User input | Important for bedside usability |
| Optional status LED | Brief setup and alert feedback | Keep short to limit energy use |
| Optional enclosure parts | Mounting and battery access | Likely larger than the `BLE` coin-cell design |

## Preferred Power Note

For this path, favor one of:

- USB power
- a larger coin cell such as `CR2450`
- a rechargeable battery if charging is acceptable

## Software Notes

This path reduces local hardware count, but it increases:

- provisioning complexity
- network failure modes
- power design difficulty
