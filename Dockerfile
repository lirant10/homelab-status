# Image for the Telegram bot (bot.py). The web page uses the same image:
#   docker run ... homelab-status python -m uvicorn app:app --host 0.0.0.0 --port 8000
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"

# dependencies first, so code changes don't re-download them
COPY pyproject.toml uv.lock .python-version README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY *.py ./
COPY templates ./templates

# never run as root
RUN useradd --system --uid 10001 app
USER 10001

CMD ["python", "bot.py"]
