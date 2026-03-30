# OpenClaw WhatsApp Bridge

This service bridges the powered Bad Dream Button prototype to `OpenClaw` running on a Linux machine.

It provides two-way behavior:

- outbound: button press on the Pi sends a WhatsApp message via OpenClaw
- inbound: WhatsApp replies are picked up from the OpenClaw session transcript and exposed back to the Pi

## What It Does

- accepts alert webhooks from the Pi
- formats and sends a WhatsApp message with `openclaw agent`
- tracks the currently active device
- watches an OpenClaw session transcript for inbound user replies
- exposes unread replies to the Pi over HTTP
- accepts acknowledgements from the Pi after a reply is shown on the `Sense HAT`

## Files

- `main.py`: service entry point
- `openclaw_bridge/config.py`: bridge config loading and defaults
- `openclaw_bridge/service.py`: HTTP server, OpenClaw send logic, and transcript polling

## Default Config Path

```text
~/.config/baddream-button/openclaw-bridge.json
```

## Start The Bridge

```bash
python3 services/openclaw-bridge/main.py
```

## Endpoints

- `GET /health`
- `POST /alerts`
- `GET /replies?device_name=...`
- `POST /replies/ack`

## Auth

If `bridge_token` is set in the config, callers must include:

```text
Authorization: Bearer <token>
```

## Notes

- This service is intentionally lightweight and uses only the Python standard library.
- It assumes a prototype-friendly OpenClaw setup where direct WhatsApp messages use the `main` session transcript.
- For a single-device prototype, inbound WhatsApp replies are routed to the most recently active device.
