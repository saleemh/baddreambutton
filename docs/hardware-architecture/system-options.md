# System Options

This document compares the main architecture patterns for the Bad Dream Button.

## Evaluation Criteria

Each option is compared across:

- button battery life
- setup friction for non-technical users
- alert reliability during sleep hours
- implementation complexity
- privacy and security surface
- press-to-alert latency

## Option 1: BLE Button To Smartphone App

Flow:

`Button -> BLE -> mobile app -> cloud API -> SMS / voice`

Strengths:

- lowest power on the button
- no always-on gateway hardware required
- quick path for demos if a phone is always nearby

Weaknesses:

- mobile background behavior is unreliable, especially on `iOS`
- app installation, pairing, permissions, and battery optimization settings add friction
- depends on the phone being present, charged, and connected

## Option 2: BLE Button To Powered Gateway

Flow:

`Button -> BLE -> gateway -> cloud API -> SMS / voice`

Strengths:

- best match for a small battery-powered bedside button
- avoids phone background restrictions
- keeps network and telephony work on powered hardware

Weaknesses:

- requires a second device in the home
- gateway setup adds some installation overhead
- alert path depends on local power and network availability

## Option 3: Wi-Fi Button Direct To Cloud

Flow:

`Button -> Wi-Fi -> cloud API -> SMS / voice`

Strengths:

- no phone or gateway needed once configured
- straightforward cloud event model
- easiest architecture to explain to users

Weaknesses:

- much worse power profile than `BLE`
- hard fit for `CR2032` because of connection and transmit current spikes
- Wi-Fi provisioning and password changes create support burden

## Option 4: Hybrid Provisioning Or Hybrid Delivery

Examples:

- `BLE` for initial provisioning, `Wi-Fi` for live alerts
- `BLE` primary to gateway, with another fallback path later

Strengths:

- can improve user experience by simplifying setup
- allows a long-term architecture that supports more than one deployment style

Weaknesses:

- highest implementation complexity
- larger security surface and more edge cases
- easy to overbuild before the basic product is proven

## Comparison Matrix

| Option | Battery Fit | Reliability | Setup Friction | Complexity | Privacy / Security | Latency |
| --- | --- | --- | --- | --- | --- | --- |
| `BLE -> phone` | Excellent | Fair | High | High | Medium | Variable |
| `BLE -> gateway` | Excellent | Good | Medium | Medium | Good | Low to medium |
| `Wi-Fi -> cloud` | Fair | Good | Medium | Medium | Good | Medium |
| `Hybrid` | Mixed | Good to very good | High | High | Mixed | Tunable |

## Recommendation

The preferred MVP architecture is `BLE -> powered gateway`.

Reasoning:

- it is the best fit for a `CR2032`-class device
- it minimizes power on the bedside hardware
- it avoids the weakest part of the phone-based path
- it is easier to prototype from off-the-shelf parts than a true low-power `Wi-Fi` coin-cell button

## Recommendation Matrix

| Product Priority | Best Choice | Why |
| --- | --- | --- |
| Maximize battery life | `BLE -> gateway` | Keeps the button mostly asleep and avoids Wi-Fi bursts |
| Lowest hardware count | `Wi-Fi -> cloud` | One device path, but with worse power tradeoffs |
| Fastest demo using existing devices | `BLE -> phone` | Can work without adding a dedicated hub |
| Best long-term flexibility | `BLE -> gateway`, then optional hybrid | Simple MVP with room to add provisioning or other transports later |

## Notes For The Software Stack

Whichever path is chosen, the software system should eventually define a shared event contract for a button press, such as:

- device identifier
- human-readable button name
- event timestamp
- alert policy, for example `sms_only` or `sms_and_call`
- optional metadata such as battery level or signal strength

That contract can later be shared across `firmware/`, `services/`, `sdk/`, and optional `apps/`.
