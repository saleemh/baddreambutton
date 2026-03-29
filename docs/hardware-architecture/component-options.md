# Component Options

This document lists practical off-the-shelf component families for hand-built prototypes of the Bad Dream Button.

## MCU And Radio Candidates

### Nordic `nRF52832`

Best for:

- low-power `BLE` button designs
- small hand-solderable modules
- simple button-plus-alert firmware

Why it fits:

- strong low-power reputation
- broad module availability
- realistic path for `CR2032` with careful firmware and buffering

Tradeoffs:

- no native `Wi-Fi`
- requires a phone or gateway for SMS and voice workflows

### Nordic `nRF52840`

Best for:

- `BLE` prototypes that may need more headroom
- development setups that want mature tooling and broad board support

Why it fits:

- large ecosystem
- easy to prototype with off-the-shelf dev boards

Tradeoffs:

- often larger and more power-hungry than strictly necessary for a one-button device
- many dev boards include extra parts that are not representative of final battery performance

### Silicon Labs `EFR32BG22`

Best for:

- very low-power `BLE` designs
- teams that want an alternative to Nordic with strong energy characteristics

Why it fits:

- good fit for a coin-cell product concept
- strong profile for small event-driven devices

Tradeoffs:

- smaller hobby ecosystem than Nordic
- tooling is less familiar to many makers

### `STM32WB`

Best for:

- teams already comfortable with `STM32`
- `BLE` designs where shared tooling matters more than the smallest path to prototype

Why it fits:

- integrated `BLE`
- familiar MCU environment for many embedded developers

Tradeoffs:

- not the simplest first path for a small battery button
- power tuning may take more effort than the leading `BLE` options

### Raspberry Pi Or Linux SBC Relay

Best for:

- powered `BLE` relay hardware
- fast proof of concept with logging and retry logic

Why it fits:

- easy to prototype with off-the-shelf parts
- can host `BLE` receive logic and relay services together
- avoids putting `Wi-Fi` requirements on the bedside button spec

Tradeoffs:

- physically larger than an eventual appliance-style relay
- higher cost than a minimal embedded receiver

## Module And Board Strategy

For early hardware work, use:

- dev boards for firmware bring-up and proof of concept
- small certified modules for closer-to-product electrical prototypes

Recommended practical split:

- button prototype: small `BLE` module on a simple carrier or breakout
- relay prototype: Raspberry Pi or another powered `BLE` receiver

## Supporting Electrical Parts

### Button Switch

Look for:

- soft-touch or low-travel tact switch for prototyping
- larger cap or dome-style actuator for bedside usability
- clear mechanical feel without requiring fine motor accuracy

### Battery Holder

For `CR2032`, evaluate:

- through-hole holders for quick prototypes
- low-profile surface-mount holders for more compact revisions

### Energy Buffering

Useful support parts:

- bulk capacitor near the radio supply path
- careful brownout behavior to survive short transmit bursts

This is especially important for coin-cell `BLE` designs.

### LED And Feedback

Possible user feedback:

- single low-current status LED
- short blink on successful press acknowledgment
- no always-on indicator

Power note:

- LEDs can dominate idle power decisions if used carelessly
- any visual or audio feedback should be very brief

### Pairing Or Reset Control

Helpful for support and setup:

- hidden reset pinhole
- long-press button behavior for configuration mode
- dedicated secondary setup pad if needed during early prototypes

## Relay Candidates

### Raspberry Pi Relay

Good for:

- fast iteration
- easy integration with local services, logs, and retry logic

Tradeoff:

- much larger and less appliance-like than an eventual product gateway

### Dedicated BLE Receiver

Good for:

- a later, smaller relay appliance
- a more product-like always-on receiver

Tradeoff:

- requires more embedded work than a Raspberry Pi proof of concept

## Mechanical And Enclosure Support

Early enclosure support should consider:

- adhesive mounting near a bed frame or nightstand
- optional screw or keyhole mount
- printable front cap that makes a small switch easier to press in the dark
- battery access without opening the full case

## Initial Shortlist

For the first prototype cycle, the highest-value shortlist is:

- button MCU: Nordic `nRF52832` or Silicon Labs `EFR32BG22`
- relay hardware: Raspberry Pi or similar powered `BLE` receiver
- battery: `CR2032` for `BLE` button only
- enclosure: simple 3D-printed bedside puck with adhesive backing
