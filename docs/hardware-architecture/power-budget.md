# Power Budget And Battery Constraints

This document explains the power constraints for the selected `BLE` button architecture.

## Primary Power Assumption

The button is mostly asleep and wakes only when:

- the user presses it
- the device enters a short configuration mode
- the firmware performs infrequent health or battery reporting, if that feature is added later

That usage pattern strongly favors a low-power `BLE` design.

## `CR2032` Reality Check

`CR2032` is realistic when all of the following are true:

- the button uses `BLE`
- the device spends nearly all of its time in deep sleep
- radio activity is short and infrequent
- the power path is designed to tolerate short transmit bursts

`CR2032` becomes a poor fit when:

- the design tries to do too much work on each press
- the design needs high peak current repeatedly
- LEDs, buzzers, or periodic reporting are active too often

## Why The Relay Should Handle Network Delivery

The bedside button should stay focused on:

- waking on press
- sending a short `BLE` event
- returning to sleep quickly

The powered relay can handle:

- event receipt
- timestamp normalization
- cloud delivery
- retries
- SMS and optional voice workflows

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

If the product later needs more complex button-side behavior, stronger local feedback, or a larger enclosure, consider moving away from `CR2032`.

Better alternatives:

- `CR2450` for more capacity and somewhat better headroom in a still-compact form factor
- small rechargeable `LiPo` if periodic charging is acceptable
- USB or mains power for the relay hardware

## Recommended Power Direction

For the first prototype, design around:

- `CR2032` only for the `BLE` button path
- powered gateway hardware for network and telephony integration

That keeps the bedside device small and low-maintenance while avoiding the hardest power problem too early.
