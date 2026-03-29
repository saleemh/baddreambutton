# Raspberry Pi 3 + Sense HAT Prototype Guide

This is the shortest path to a working Bad Dream Button prototype using:

- `Raspberry Pi 3 Model B v1.2`
- `Sense HAT v1.0`
- wall power

The `Sense HAT` center joystick press acts as the button press, and the LED matrix shows device status.

## Quickstart

From the laptop:

```bash
scp -r baddreambutton saleem@baddream-prototype.local:~/
ssh saleem@baddream-prototype.local
cd ~/baddreambutton
python3 apps/pi-prototype-cli/main.py
```

Then in the wizard:

1. update package lists
2. upgrade outdated system packages
3. install required dependencies
4. save the prototype config
5. test the `Sense HAT`
6. start the runtime

## What This Prototype Does

The prototype flow is:

`Sense HAT center press -> Pi app -> webhook/backend -> later SMS/call workflow`

The app already handles the setup and runtime work, so this guide focuses on:

- getting the repo onto the Pi
- running the on-device wizard
- starting the runtime

## App Location

The prototype app lives here:

- `apps/pi-prototype-cli/`

Main entry point:

```bash
python3 apps/pi-prototype-cli/main.py
```

## Install On The Pi

This assumes:

- the repo is on a laptop
- the Pi is already reachable over `SSH`
- the Pi username is something like `saleem`
- the Pi hostname is something like `baddream-prototype.local`

### 1. Copy The Repo To The Pi

From the laptop, run:

```bash
scp -r baddreambutton saleem@baddream-prototype.local:~/
```

Or use the Pi IP directly:

```bash
scp -r baddreambutton saleem@192.168.1.42:~/
```

### 2. Connect To The Pi

```bash
ssh saleem@baddream-prototype.local
```

Then go into the repo:

```bash
cd ~/baddreambutton
```

## Run The Wizard

Start the app:

```bash
python3 apps/pi-prototype-cli/main.py
```

The wizard can:

- update package lists
- upgrade outdated system packages
- install required dependencies
- save the prototype config
- test the `Sense HAT`
- install a `systemd` service
- start the runtime

## Useful Direct Commands

Run the prototype runtime directly:

```bash
python3 apps/pi-prototype-cli/main.py run
```

Show the current config:

```bash
python3 apps/pi-prototype-cli/main.py show-config
```

Test only the `Sense HAT` joystick and LEDs:

```bash
python3 apps/pi-prototype-cli/main.py test-hardware
```

## What The Runtime Does

When the app is running:

- the center joystick press triggers a bad dream alert event
- the LED matrix shows current device state
- the event is logged locally
- if a webhook is configured, the event is posted there

## LED States

The runtime uses the `Sense HAT` LEDs to show status:

- `booting`: startup
- `ready_not_connected`: app is running but backend or network is unavailable
- `ready_connected`: app is healthy and backend is reachable
- `sending`: alert is in progress
- `send_success`: alert was accepted
- `send_failed`: alert failed

## Config Location

By default, config is stored on the Pi here:

```text
~/.config/baddream-button/config.json
```

Local event logs are stored under the Pi user's home directory.

## Recommended First Run

1. Copy the repo to the Pi with `scp`.
2. `ssh` into the Pi.
3. `cd ~/baddreambutton`
4. run `python3 apps/pi-prototype-cli/main.py`
5. use the wizard to install packages, save config, test the hardware, and start the runtime

## What This Prototype Proves

This powered prototype proves:

- the interaction model
- the alert state machine
- the payload format
- backend integration shape
- on-device success and failure feedback

It does not yet prove:

- final product enclosure
- battery operation
- low-power BLE button hardware
- dedicated embedded firmware

## Next Step

Once this works end-to-end, the next hardware step is to replace the `Sense HAT` center press with a real low-power `BLE` button while keeping the event contract and backend behavior as similar as possible.
