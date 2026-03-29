# Power Budget And Battery Constraints

This document explains where a `CR2032` is realistic for the Bad Dream Button and where it is not.

## Primary Power Assumption

The button is mostly asleep and wakes only when:

- the user presses it
- the device enters a short configuration mode
- the firmware performs infrequent health or battery reporting, if that feature is added later

That usage pattern strongly favors a low-power `BLE` design.

## `CR2032` Reality Check

`CR2032` is realistic when all of the following are true:

- the button uses `BLE` rather than direct `Wi-Fi`
- the device spends nearly all of its time in deep sleep
- radio activity is short and infrequent
- the power path is designed to tolerate short transmit bursts

`CR2032` becomes a poor fit when:

- the device must join `Wi-Fi` on demand
- the design needs high peak current repeatedly
- LEDs, buzzers, or periodic reporting are active too often

## Why `Wi-Fi` Is Hard On A Coin Cell

Direct `Wi-Fi` requires:

- scanning and associating with an access point
- performing network setup such as DHCP and TLS
- transmitting at current levels that can exceed what a coin cell handles comfortably

Even if the average energy per day looks low, the peak current behavior makes reliable `CR2032` operation difficult. A bench prototype may appear to work and still fail in real bedrooms as the battery ages, temperature drops, or the radio link gets weaker.

## Rough Design Guidance

### Good Fit

- `BLE` button
- deep sleep between presses
- very short radio exchange
- no always-on lights
- optional powered gateway nearby

### Risky Fit

- `BLE` button with frequent status broadcasts
- large bright LED confirmations
- more complex multi-step pairing behavior on every press

### Poor Fit

- direct `Wi-Fi` from `CR2032`
- direct cellular path from the button
- continuous beeping, lighting, or other active feedback

## Power-Sensitive Design Choices

### Sleep First

The button firmware should default to:

- deepest practical sleep mode
- interrupt-driven wake on physical press
- no periodic work unless a clear product need exists

### Keep The Alert Payload Small

For a `BLE`-based button:

- send the smallest useful event possible
- let the gateway enrich it with timestamp normalization, routing, and retries

### Avoid Expensive User Feedback

If feedback is needed, prefer:

- one short LED blink
- gateway-side confirmation in software, not long button-side activity

### Buffer The Supply

Coin cells benefit from:

- local capacitance near the radio supply
- careful brownout thresholds
- firmware that fails safely if voltage droops during transmission

## Battery Alternatives

If the product later needs direct `Wi-Fi`, higher confidence radio retries, or louder feedback, consider moving away from `CR2032`.

Better alternatives:

- `CR2450` for more capacity and somewhat better headroom in a still-compact form factor
- small rechargeable `LiPo` if periodic charging is acceptable
- USB or mains power for the gateway and possibly for a bedside `Wi-Fi` puck

## Recommended Power Direction

For the first prototype, design around:

- `CR2032` only for the `BLE` button path
- powered gateway hardware for network and telephony integration

That keeps the bedside device small and low-maintenance while avoiding the hardest power problem too early.
