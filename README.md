# homelab-status

A small Python project that reports homelab status from Prometheus:
VMware ESXi hosts (CPU, memory), datastores (% used), VMs (on/off, per host)
and Podman containers (running/stopped).
It has a Telegram bot that answers `/status`, and a local AI agent
(Ollama) that answers free-text questions about the lab.

## Files

- `homelab.py` - queries Prometheus: `get_hosts()`, `get_datastores()`, `get_vms()`,
  `get_containers()`, `get_down_targets()`. Works with any number of ESXi hosts and with vCenter;
  results are de-duplicated, so a host scraped both directly and through vCenter shows up once.
- `app.py` + `templates/index.html` - web page and `/api/status` JSON
- `agent.py` - AI agent: a local model (Ollama) that uses the functions above as tools
- `bot.py` - Telegram bot (long polling): `/status`, and any other text goes to the agent
- `deploy/homelab-bot.service` - systemd user service for the bot
- `main.py` - first version, prints VMs in the terminal

## Requirements

- Python + [uv](https://docs.astral.sh/uv/)
- Prometheus with vmware_exporter and prometheus-podman-exporter metrics
- A Telegram bot token from @BotFather
- For the agent: [Ollama](https://ollama.com) with a model that supports tools (default `qwen3:8b`)

## Setup

~~~bash
uv sync
cp .env.example .env && chmod 600 .env
# edit .env: add your bot token, chat id and Prometheus URL
~~~

`OLLAMA_URL` and `OLLAMA_MODEL` are optional (defaults: `http://localhost:11434`, `qwen3:8b`).

## Run

<img width="400" alt="Bot /status reply" src="https://github.com/user-attachments/assets/7b34bd7f-3f57-4e10-a13b-8d0791c943b8" />

~~~bash
uv run --env-file .env python bot.py
~~~

Send `/status` to the bot, or ask a question like "What is off in the lab?".
It only answers the chat id from `.env`.

## AI agent

Ask from the terminal:

~~~bash
uv run --env-file .env python agent.py "What is off in the lab?"
~~~

The model decides which tools to call (`get_hosts`, `get_datastores`, `get_vms`,
`get_containers`, `get_down_targets`). The code runs them and sends the results back to the
model. The model never runs code itself.

Ollama can run on another machine (for example a PC with a GPU) and stay
bound to `127.0.0.1` there. Instead of opening a port, reach it with an
SSH reverse tunnel from the Ollama machine:

~~~bash
ssh -R 11434:127.0.0.1:11434 user@bot-host
~~~

While the tunnel is closed, the bot replies that the AI is not available,
and `/status` still works.

## Run as a service

~~~bash
mkdir -p ~/.config/systemd/user
cp deploy/homelab-bot.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now homelab-bot
sudo loginctl enable-linger $USER
~~~

Logs: `journalctl --user -u homelab-bot -f`

## Container image

Every push to `master` builds `ghcr.io/lirant10/homelab-status` (`:latest` and `:sha-<commit>`),
see `.github/workflows/image.yml`. PRs build it and check that the code imports.

~~~bash
docker run --rm --env-file .env ghcr.io/lirant10/homelab-status:latest          # the bot
docker run --rm --env-file .env -p 8000:8000 ghcr.io/lirant10/homelab-status:latest \
  python -m uvicorn app:app --host 0.0.0.0 --port 8000                           # the web page
~~~

It runs on my k3s cluster through Argo CD (manifests in the `homelab-k8s` repo).
Run **only one bot at a time**: Telegram long polling allows a single consumer per token, so stop the
systemd service before the bot starts in Kubernetes (`systemctl --user disable --now homelab-bot`).

## Roadmap

See GitHub Issues.
