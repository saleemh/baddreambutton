# Prototype Paths

This document turns the architecture options into concrete prototype directions.

## Prototype A: BLE Button Plus Powered Gateway

Status:

- recommended MVP

System flow:

`Button -> BLE -> local gateway -> cloud service -> SMS / optional voice`

Why this path leads:

- strongest fit for `CR2032`
- avoids mobile background reliability issues
- keeps the bedside button simple
- easiest to evolve into a durable product architecture

Suggested hardware:

- button: Nordic `nRF52832` or Silicon Labs `EFR32BG22`
- gateway: `ESP32-C3` dev board or Raspberry Pi
- battery: `CR2032`

Recommended first build:

1. Build a button prototype that wakes on press and emits a compact `BLE` event.
2. Build a powered gateway that receives the event and forwards it to a simple backend or webhook.
3. Have the backend trigger SMS first, then optionally voice escalation.

## Prototype B: BLE Button Plus Smartphone App

Status:

- useful for quick validation, but not recommended as the primary product path

System flow:

`Button -> BLE -> phone app -> cloud service -> SMS / optional voice`

Why it may still be useful:

- lowest initial hardware count
- can validate user experience and message formats quickly
- useful as a backup concept if a gateway is deferred

Main risk:

- reliability depends too heavily on phone state and OS behavior

Suggested use:

- short-term concept demo
- internal development aid, not the only shipping path

## Prototype C: Wi-Fi Button Direct To Cloud

Status:

- viable if power constraints are relaxed

System flow:

`Button -> Wi-Fi -> cloud service -> SMS / optional voice`

Why it is attractive:

- single-device story
- simple mental model for users
- no local receiver required

Main risk:

- not a good first fit for `CR2032`
- likely pushes the design toward a bigger battery or bedside power

Suggested use:

- later evaluation path
- acceptable if a wall-powered puck is allowed

## Prototype Selection Matrix

| Prototype | Best For | Key Risk | Recommended Timing |
| --- | --- | --- | --- |
| `A: BLE + gateway` | Realistic low-power MVP | Requires extra powered device | First |
| `B: BLE + phone` | Fast demo and UX validation | Phone reliability | Secondary |
| `C: Wi-Fi direct` | Simplest user story | Coin-cell power mismatch | Later |

## MVP Recommendation

Start with Prototype A.

Reasoning:

- it fits the battery goal
- it minimizes the hard radio and power problems on the bedside device
- it still supports the default software behavior of SMS plus optional voice escalation
- it separates concerns cleanly across future `firmware/` and `services/`

## Suggested Phase Order

1. Validate the button press to `BLE` event path.
2. Validate a local gateway receiving the event reliably in a bedroom-like environment.
3. Validate SMS delivery and optional phone call through a backend service.
4. Revisit whether a phone-relay or direct `Wi-Fi` path is worth supporting later.
