# Bad Dream Button Pi Prototype CLI

This app provides an on-device terminal workflow for the first powered Bad Dream Button prototype using:

- `Raspberry Pi 3 Model B`
- `Sense HAT`
- wall power

It is designed to run over a normal terminal session, including `ssh` or `Raspberry Connect` remote shell.

## What It Does

- checks and installs required system packages
- walks through prototype configuration
- verifies the `Sense HAT`
- optionally installs a `systemd` service
- runs the prototype runtime
- listens for the `Sense HAT` center joystick press
- shows status on the LED matrix
- logs and sends alert events to a webhook

## App Structure

- `main.py`: entry point
- `baddream_pi/wizard.py`: interactive setup wizard
- `baddream_pi/runtime.py`: runtime loop and alert handling
- `baddream_pi/hardware.py`: `Sense HAT` LED and joystick helpers
- `baddream_pi/config.py`: config loading and saving

## Run It On The Pi

From the repo root:

```bash
python3 apps/pi-prototype-cli/main.py
```

That starts the interactive wizard.

To run the prototype service directly:

```bash
python3 apps/pi-prototype-cli/main.py run
```

To only verify the hardware:

```bash
python3 apps/pi-prototype-cli/main.py test-hardware
```

## Config Location

By default, the app stores config here:

```text
~/.config/baddream-button/config.json
```

You can override that path with:

```bash
BAD_DREAM_CONFIG=/path/to/config.json python3 apps/pi-prototype-cli/main.py
```
