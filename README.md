# homelab-status

A small Python project that reports homelab status from Prometheus:
VMware VMs (on/off) and Podman containers (running/stopped).
The main part is a Telegram bot that answers `/status`.

## Files

- `homelab.py` - queries Prometheus: `get_vms()`, `get_containers()`
- `bot.py` - Telegram bot (long polling), answers `/status`
- `deploy/homelab-bot.service` - systemd user service for the bot
- `main.py` - first version, prints VMs in the terminal

## Requirements

- Python + [uv](https://docs.astral.sh/uv/)
- Prometheus with vmware_exporter and prometheus-podman-exporter metrics
- A Telegram bot token from @BotFather

## Setup

```bash
uv sync
cp .env.example .env && chmod 600 .env
# edit .env: add your bot token, chat id and Prometheus URL
```

## Run

<img width="400" alt="Bot /status reply" src="https://github.com/user-attachments/assets/7b34bd7f-3f57-4e10-a13b-8d0791c943b8" />

```bash
uv run --env-file .env python bot.py
```

Send `/status` to the bot. It only answers the chat id from `.env`.

## Run as a service

```bash
mkdir -p ~/.config/systemd/user
cp deploy/homelab-bot.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now homelab-bot
sudo loginctl enable-linger $USER
```

Logs: `journalctl --user -u homelab-bot -f`

## Roadmap

See GitHub Issues. Next: an AI agent that uses `get_vms()` and
`get_containers()` as tools.
