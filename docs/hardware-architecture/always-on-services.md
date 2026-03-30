# Always-On Service Setup

This guide makes the prototype run without starting pieces manually from a laptop.

The final always-on setup is:

- Linux machine: `baddream-openclaw-bridge.service`
- Raspberry Pi: `baddream-bridge-tunnel.service`
- Raspberry Pi: `baddream-button.service`

## Why Three Services

The Linux machine hosts the OpenClaw bridge and talks to WhatsApp through your existing OpenClaw setup.

The Pi needs:

- an SSH tunnel to the Linux bridge, because the bridge is not exposed publicly
- the actual Bad Dream Button runtime

## Service Files In The Repo

- `services/openclaw-bridge/systemd/baddream-openclaw-bridge.service.example`
- `apps/pi-prototype-cli/systemd/baddream-bridge-tunnel.service.example`
- `apps/pi-prototype-cli/systemd/baddream-button.service.example`

## Part 1: Linux Bridge Service

On the Linux machine:

```bash
mkdir -p ~/.config/systemd/user
cp ~/baddreambutton/services/openclaw-bridge/systemd/baddream-openclaw-bridge.service.example \
  ~/.config/systemd/user/baddream-openclaw-bridge.service
```

Then enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable baddream-openclaw-bridge.service
systemctl --user restart baddream-openclaw-bridge.service
systemctl --user status baddream-openclaw-bridge.service --no-pager
```

## Part 2: Pi SSH Key For The Tunnel

The tunnel service cannot type a password at boot. It needs SSH key-based login from the Pi to `saleem.net`.

### 1. Generate an SSH key on the Pi

On the Pi:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

### 2. Install that key on the Linux machine

From the Pi:

```bash
ssh-copy-id saleem@saleem.net
```

If `ssh-copy-id` is unavailable:

```bash
cat ~/.ssh/id_ed25519.pub
```

Then append the printed key to:

```text
/home/saleem/.ssh/authorized_keys
```

on the Linux machine.

### 3. Verify passwordless SSH from the Pi

On the Pi:

```bash
ssh -o BatchMode=yes saleem@saleem.net 'echo tunnel-ok'
```

Expected output:

```text
tunnel-ok
```

If this fails, do not continue to the tunnel service yet.

## Part 3: Pi Tunnel Service

On the Pi:

```bash
sudo cp ~/baddreambutton/apps/pi-prototype-cli/systemd/baddream-bridge-tunnel.service.example \
  /etc/systemd/system/baddream-bridge-tunnel.service
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable baddream-bridge-tunnel.service
sudo systemctl restart baddream-bridge-tunnel.service
sudo systemctl status baddream-bridge-tunnel.service --no-pager
```

### Verify the tunnel

Still on the Pi:

```bash
curl http://127.0.0.1:8787/health \
  -H 'Authorization: Bearer choose-a-long-random-token'
```

If that works, the tunnel is good.

## Part 4: Pi Runtime Service

Make sure the Pi config already points to the tunnel-local URLs:

- `webhook_url = http://127.0.0.1:8787/alerts`
- `reply_poll_url = http://127.0.0.1:8787/replies`
- `healthcheck_url = http://127.0.0.1:8787/health`

Then install the runtime service:

```bash
sudo cp ~/baddreambutton/apps/pi-prototype-cli/systemd/baddream-button.service.example \
  /etc/systemd/system/baddream-button.service
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable baddream-button.service
sudo systemctl restart baddream-button.service
sudo systemctl status baddream-button.service --no-pager
```

## Part 5: Reboot Test

Once all services are enabled, reboot both machines and verify:

### Linux machine

```bash
systemctl --user status baddream-openclaw-bridge.service --no-pager
```

### Pi

```bash
sudo systemctl status baddream-bridge-tunnel.service --no-pager
sudo systemctl status baddream-button.service --no-pager
```

## Useful Commands

### Linux machine

```bash
systemctl --user restart baddream-openclaw-bridge.service
systemctl --user status baddream-openclaw-bridge.service --no-pager
journalctl --user -u baddream-openclaw-bridge.service -n 50 --no-pager
```

### Pi

```bash
sudo systemctl restart baddream-bridge-tunnel.service
sudo systemctl restart baddream-button.service
sudo systemctl status baddream-bridge-tunnel.service --no-pager
sudo systemctl status baddream-button.service --no-pager
journalctl -u baddream-bridge-tunnel.service -n 50 --no-pager
journalctl -u baddream-button.service -n 50 --no-pager
```

## Current Limitation

The tunnel service depends on the Pi having a working SSH key for `saleem.net`. That is the only part that cannot work unattended with password-only SSH.
