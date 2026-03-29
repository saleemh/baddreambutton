# Raspberry Pi 3 + Sense HAT Prototype Guide

This guide defines the first Bad Dream Button prototype using hardware already on hand:

- `Raspberry Pi 3 Model B v1.2`
- `Sense HAT v1.0`
- wall power

This prototype treats the `Sense HAT` joystick center press as the button press and uses the `Sense HAT` LED matrix as the status display.

## Prototype Goal

Build a powered prototype that can:

- boot reliably on a `Raspberry Pi 3`
- detect a button press using the `Sense HAT`
- show device status on the LED matrix
- send an event to a backend or webhook
- later trigger SMS and optional phone call workflows through the software stack

This is a prototype of the product behavior, not the final low-power BLE hardware.

## What This Prototype Represents

For now, the prototype is:

`Sense HAT center press -> Pi 3 application -> webhook/backend -> SMS/call workflow`

This lets the project validate:

- the button interaction flow
- device state handling
- alert payload structure
- backend integration shape
- success and failure feedback behavior

## Hardware Required

- `Raspberry Pi 3 Model B v1.2`
- `Sense HAT v1.0`
- `microSD` card, recommended `16 GB` or larger
- `5V / 2.5A` micro-USB power supply for the Pi 3
- Mac with an SD card reader or adapter

Optional:

- monitor and HDMI cable
- USB keyboard
- Ethernet cable

## Prototype State Model

The `Sense HAT` LED matrix should show the current device state.

Suggested states:

- `off`: no power, LEDs off
- `booting`: Pi is starting, application not yet ready
- `ready_not_connected`: application is running but network or backend is unavailable
- `ready_connected`: application is healthy and backend is reachable
- `sending`: button was pressed and an alert is in progress
- `send_success`: alert was accepted successfully
- `send_failed`: alert failed or timed out

Suggested color semantics:

- `booting`: white or dim blue pulse
- `ready_not_connected`: yellow or orange
- `ready_connected`: green
- `sending`: blue animation
- `send_success`: green flash
- `send_failed`: red flash

After `send_success`, return to `ready_connected`.

After `send_failed`, return to `ready_not_connected` or `ready_connected` depending on the result of the latest connectivity check.

## Step 1: Flash Raspberry Pi OS From macOS

Use official Raspberry Pi tools:

- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- [Getting started documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html)

Recommended OS:

- `Raspberry Pi OS Lite`

Why:

- lighter and closer to the eventual appliance-like runtime
- enough for Python, networking, and hardware input handling

### Flashing Steps

1. Install `Raspberry Pi Imager` on the Mac.
2. Insert the `microSD` card into the Mac.
3. Open `Raspberry Pi Imager`.
4. Select `Raspberry Pi 3` as the device.
5. Select `Raspberry Pi OS Lite` as the operating system.
6. Select the `microSD` card as the storage device.
7. Open the advanced settings using the gear icon.
8. Configure:
   - hostname, for example `baddream-prototype`
   - username, for example `saleem`
   - password
   - `Wi-Fi` SSID and password if using wireless
   - wireless country
   - locale and timezone
   - `SSH` enabled
9. Write the image to the card.
10. Eject the card safely from macOS.

## Step 2: Assemble The Hardware

1. Ensure the Pi is powered off.
2. Align the `Sense HAT` with the Pi `40-pin GPIO` header.
3. Press the HAT down evenly until seated.
4. Insert the flashed `microSD` card into the Pi.
5. Connect power to the Pi.

Important:

- do not attach or remove the `Sense HAT` while the Pi is powered
- use standoffs if available to reduce strain on the GPIO header

## Step 3: Connect To The Pi

If `SSH` and networking were configured in Imager, connect from the Mac:

```bash
ssh saleem@baddream-prototype.local
```

Replace the username and hostname with the values chosen during imaging.

If `.local` does not resolve:

- check the device list in the router
- use the Pi IP address directly
- use Ethernet temporarily for simpler first setup

## Step 4: Update The Pi

After logging in:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Reconnect after reboot.

## Step 5: Install Prototype Dependencies

Install system packages for:

- `Sense HAT`
- Python runtime
- HTTP requests
- Bluetooth tooling for future BLE work

```bash
sudo apt update
sudo apt install -y sense-hat python3-sense-hat python3-requests bluez bluetooth pi-bluetooth git curl
```

Official accessory documentation:

- [Sense HAT documentation](https://www.raspberrypi.com/documentation/accessories/sense-hat.html)

## Step 6: Verify The Sense HAT

### LED Matrix Check

Run:

```bash
python3 - <<'PY'
from sense_hat import SenseHat
sense = SenseHat()
sense.show_message("OK")
print("Sense HAT ready")
PY
```

Expected result:

- the matrix scrolls `OK`
- the terminal prints `Sense HAT ready`

### Joystick Check

Run:

```bash
python3 - <<'PY'
from sense_hat import SenseHat
sense = SenseHat()
print("Press joystick directions. Ctrl+C to exit.")
while True:
    for event in sense.stick.get_events():
        print(event.direction, event.action)
PY
```

Press the joystick in all directions.

The most important event for this prototype is:

- center press, reported as `middle`

## Step 7: Define The Prototype Behavior

The center joystick press represents a bad dream alert request.

When the center press occurs:

1. capture the current timestamp
2. create an event payload
3. set LEDs to `sending`
4. send the payload to the configured backend or webhook
5. if successful, show `send_success`
6. if unsuccessful, show `send_failed`
7. return to the steady connection state

## Step 8: Use This Initial Event Payload

Start with a simple payload:

```json
{
  "event_type": "bad_dream_button_pressed",
  "device_name": "BadDreamButton-Prototype-01",
  "message": "A bad dream occurred and help is requested.",
  "timestamp": "2026-03-29T12:00:00Z"
}
```

Later fields can include:

- configured recipient
- escalation mode such as `sms_only` or `sms_and_call`
- software version
- connectivity state

## Step 9: Prototype Script Shape

The first application on the Pi should do four things:

1. initialize the `Sense HAT`
2. track current system state
3. listen for center joystick presses
4. send a JSON payload to a webhook or backend

Suggested environment variables:

- `BAD_DREAM_DEVICE_NAME`
- `BAD_DREAM_WEBHOOK_URL`
- `BAD_DREAM_ALERT_MODE`

Suggested local config values:

- device name
- recipient phone number or recipient identifier
- whether SMS is enabled
- whether voice call escalation is enabled

## Pi CLI App In This Repo

An on-device setup and runtime app now lives here:

- `apps/pi-prototype-cli/`

Run the setup wizard on the Pi with:

```bash
python3 apps/pi-prototype-cli/main.py
```

That wizard can:

- update package lists
- upgrade outdated system packages
- install required dependencies
- save the prototype config
- test the `Sense HAT`
- install a `systemd` service

Run the runtime directly with:

```bash
python3 apps/pi-prototype-cli/main.py run
```

## Install On The Pi

If the code is currently on a laptop and not yet on the Pi, copy the repository to the Pi first and then run the app there.

This section assumes:

- the repo exists on the laptop
- the Pi is already reachable over `SSH`
- the Pi username is something like `saleem`
- the Pi hostname is something like `baddream-prototype.local`

### Option A: Copy The Whole Repo From The Laptop

On the laptop, from the parent directory of the repo:

```bash
scp -r baddreambutton saleem@baddream-prototype.local:~/
```

That copies the full repo to:

```text
/home/saleem/baddreambutton
```

If you prefer using the Pi IP directly:

```bash
scp -r baddreambutton saleem@192.168.1.42:~/
```

### Option B: Copy Only The Current Version Again Later

If you already copied the repo once and want to overwrite it with the latest local version, use:

```bash
scp -r baddreambutton saleem@baddream-prototype.local:~/
```

This is simple, but it recopies the entire directory each time.

### Verify The Files On The Pi

After copying, connect to the Pi:

```bash
ssh saleem@baddream-prototype.local
```

Then check the repo:

```bash
cd ~/baddreambutton
ls
ls apps/pi-prototype-cli
```

You should see:

- `apps/`
- `docs/`
- `services/`
- `firmware/`
- `sdk/`

And inside the app folder:

- `main.py`
- `README.md`
- `baddream_pi/`

### Install Dependencies On The Pi

Once connected to the Pi and inside the repo:

```bash
cd ~/baddreambutton
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3 python3-sense-hat python3-requests sense-hat bluez bluetooth pi-bluetooth git curl
```

### Start The Setup Wizard

From the repo root on the Pi:

```bash
cd ~/baddreambutton
python3 apps/pi-prototype-cli/main.py
```

That opens the terminal wizard and lets you:

- update package lists
- upgrade outdated system packages
- install required dependencies
- configure the prototype
- test the `Sense HAT`
- install the `systemd` service

### Run The Prototype Directly

If you want to skip the wizard and run the prototype runtime:

```bash
cd ~/baddreambutton
python3 apps/pi-prototype-cli/main.py run
```

### Test The Hardware Only

To only test the `Sense HAT` joystick and LEDs:

```bash
cd ~/baddreambutton
python3 apps/pi-prototype-cli/main.py test-hardware
```

### Where The App Stores Config

By default, the app saves its config on the Pi here:

```text
~/.config/baddream-button/config.json
```

The runtime also logs button events locally under the Pi user's home directory.

### If `scp` Fails

Common fixes:

- confirm the Pi hostname or IP address
- verify `SSH` still works
- make sure both devices are on the same network
- try using the IP address instead of `.local`
- if permission is denied, confirm the Pi username is correct

### Recommended First Run Sequence

1. Copy the repo from the laptop to the Pi with `scp`.
2. `SSH` into the Pi.
3. `cd ~/baddreambutton`
4. run `python3 apps/pi-prototype-cli/main.py`
5. use the wizard to install packages, save config, test hardware, and start the runtime

## Step 10: Recommended First Implementation Order

Build the prototype in small stages:

1. get the Pi booting reliably
2. verify the `Sense HAT` joystick and LEDs
3. write a script that changes LED state when the center button is pressed
4. add structured logging to a local file
5. add outbound webhook delivery
6. add success and failure LED transitions
7. only after that, connect the webhook to real SMS and optional phone call workflows

## Step 11: Connectivity Definition

For this prototype, `connected` should mean:

- the Pi has network access
- the application can reach the configured backend or webhook

It does not need to mean that a separate `BLE` connection is active. The current prototype is a powered software prototype that stands in for the future dedicated hardware.

## Step 12: Suggested File Layout Later

Once implementation begins, the code can live under the software stack areas already reserved in the repo:

- `services/` for backend intake and notification logic
- `apps/` only if a client or admin UI is needed later
- `firmware/` for future dedicated embedded button hardware

For this Pi-based prototype, a simple runtime structure could look like:

- `services/prototype-relay/` for the Pi application
- `services/alert-api/` for the backend webhook receiver

## Step 13: What This Prototype Proves

This prototype proves:

- the interaction model
- the alert state machine
- the payload format
- the backend integration pattern
- the usefulness of immediate device feedback

This prototype does not yet prove:

- final bedside industrial design
- battery life
- low-power BLE hardware
- dedicated embedded button firmware

## Next Step After This Prototype

After this powered prototype works end-to-end, replace the `Sense HAT` center press with a real low-power `BLE` button and keep the backend behavior and event contract as similar as possible.
