# OpenClaw WhatsApp Bridge Setup

This guide sets up the two-way prototype flow:

`Sense HAT button -> Pi app -> Linux bridge -> OpenClaw -> WhatsApp`

and back:

`WhatsApp reply -> OpenClaw transcript -> Linux bridge -> Pi app -> Sense HAT LEDs`

## What This Adds

- pressing the button sends a WhatsApp message through your existing OpenClaw setup
- replying on WhatsApp causes the reply text to be shown on the `Sense HAT`

## Repo Components

- `services/openclaw-bridge/`: Linux-side bridge service
- `apps/pi-prototype-cli/`: Pi-side prototype app
- `always-on-services.md`: how to make the bridge, tunnel, and runtime start automatically

## Assumptions

- OpenClaw is already running on the Linux machine
- WhatsApp is already configured in OpenClaw
- the Pi can reach the Linux machine over the network
- the repo starts on your laptop and is copied to each machine

## Step 1: Copy The Repo To The Linux Machine

From the laptop:

```bash
scp -r baddreambutton saleem@saleem.net:~/
```

Then SSH into the Linux machine:

```bash
ssh saleem@saleem.net
cd ~/baddreambutton
```

## Step 2: Create The Bridge Config

The bridge config lives at:

```text
~/.config/baddream-button/openclaw-bridge.json
```

Create the config directory:

```bash
mkdir -p ~/.config/baddream-button
```

Find the OpenClaw main session transcript path:

```bash
find ~/.openclaw/agents -path '*/sessions/main.jsonl'
```

Use the matching path in this config file:

```json
{
  "bind_host": "0.0.0.0",
  "bind_port": 8787,
  "bridge_token": "choose-a-long-random-token",
  "whatsapp_target": "+16177107422",
  "openclaw_command": "openclaw",
  "transcript_path": "/home/saleem/.openclaw/agents/default/sessions/main.jsonl",
  "active_device_ttl_minutes": 1440,
  "state_path": "/home/saleem/.local/state/baddream-button/openclaw-bridge-state.json"
}
```

Notes:

- `bridge_token` is shared with the Pi and protects the bridge API
- `whatsapp_target` should be the phone number you want OpenClaw to message
- `transcript_path` must point at the active `main.jsonl` used by your OpenClaw WhatsApp session

## Step 3: Test The Bridge Manually On Linux

Start the bridge in the foreground:

```bash
cd ~/baddreambutton
python3 services/openclaw-bridge/main.py
```

You should see output like:

```text
Bad Dream Button OpenClaw bridge listening on http://0.0.0.0:8787
```

In another terminal on the Linux machine, test health:

```bash
curl http://127.0.0.1:8787/health
```

If `bridge_token` is set, include it:

```bash
curl http://127.0.0.1:8787/health \
  -H 'Authorization: Bearer choose-a-long-random-token'
```

## Step 4: Test Outbound WhatsApp Before Using The Pi

Send a test alert through the bridge:

```bash
curl -X POST http://127.0.0.1:8787/alerts \
  -H 'Authorization: Bearer choose-a-long-random-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "device_name": "BadDreamButton-Prototype-01",
    "message": "A bad dream occurred and help is requested.",
    "timestamp": "2026-03-30T00:00:00Z",
    "alert_mode": "sms_only",
    "hostname": "baddreambutton-v1"
  }'
```

Expected result:

- OpenClaw sends a WhatsApp message
- the bridge returns `200`

## Step 5: Verify Inbound Replies

After the WhatsApp message arrives, reply to it from the allowed WhatsApp number.

Then ask the bridge for unread replies:

```bash
curl 'http://127.0.0.1:8787/replies?device_name=BadDreamButton-Prototype-01' \
  -H 'Authorization: Bearer choose-a-long-random-token'
```

Expected result:

- a JSON response containing the unread reply text

If this works, the Linux side is ready.

## Step 6: Install The Bridge As A Service On Linux

Create a user systemd unit:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/baddream-openclaw-bridge.service <<'EOF'
[Unit]
Description=Bad Dream Button OpenClaw Bridge
After=network-online.target

[Service]
WorkingDirectory=/home/saleem/baddreambutton
Environment=BAD_DREAM_BRIDGE_CONFIG=/home/saleem/.config/baddream-button/openclaw-bridge.json
ExecStart=/usr/bin/python3 /home/saleem/baddreambutton/services/openclaw-bridge/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF
```

Then enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable baddream-openclaw-bridge.service
systemctl --user start baddream-openclaw-bridge.service
systemctl --user status baddream-openclaw-bridge.service --no-pager
```

## Step 7: Configure The Pi App

On the Pi, run the prototype wizard:

```bash
cd ~/baddreambutton
python3 apps/pi-prototype-cli/main.py
```

Set these values:

- `device_name`: for example `BadDreamButton-Prototype-01`
- `message`: the alert text you want sent
- `webhook_url`: `http://saleem.net:8787/alerts`
- `bridge_token`: the same token used in the Linux bridge config
- `reply_poll_url`: `http://saleem.net:8787/replies`
- `reply_poll_seconds`: `5`
- `healthcheck_url`: `http://saleem.net:8787/health`

Then:

- install dependencies
- test the `Sense HAT`
- start the runtime

## Step 8: End-To-End Test

1. Start the bridge on Linux.
2. Start the Pi runtime.
3. Press the center joystick on the `Sense HAT`.
4. Confirm that a WhatsApp message arrives.
5. Reply to the WhatsApp message.
6. Wait a few seconds.
7. Confirm the reply scrolls across the `Sense HAT` LEDs.

## Runtime Behavior

When a reply arrives:

- the Pi polls the bridge
- the `Sense HAT` flashes a reply color
- the reply text scrolls once across the LEDs
- the Pi acknowledges the reply so it is not shown again

## Troubleshooting

### WhatsApp alert does not send

Check on Linux:

```bash
systemctl --user status openclaw-gateway --no-pager
systemctl --user status baddream-openclaw-bridge.service --no-pager
```

### Bridge says transcript file is missing

Re-run:

```bash
find ~/.openclaw/agents -path '*/sessions/main.jsonl'
```

Update `transcript_path` to the correct file.

### Reply does not show on the Pi

Check:

- the Pi can reach `http://saleem.net:8787/health`
- `bridge_token` matches on both sides
- `device_name` on the Pi matches the device name used for alerts
- the Linux bridge returns replies from:

```bash
curl 'http://127.0.0.1:8787/replies?device_name=BadDreamButton-Prototype-01' \
  -H 'Authorization: Bearer choose-a-long-random-token'
```

## Current Prototype Limitation

For this first implementation, inbound WhatsApp replies are routed to the most recently active device. That is good enough for a single-button prototype, but a future multi-device version should use explicit per-device conversation routing.
