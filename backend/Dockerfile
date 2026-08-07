# Builder stage 
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
	UV_LINK_MODE=copy \
	UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-dev --extra rag --no-install-project

# Runtime stage
FROM python:3.13-slim-bookworm AS runner

RUN groupadd --system --gid 1001 app \
	&& useradd --system --uid 1001 --gid 1001 app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app ./app

ENV PATH="/app/.venv/bin:$PATH" \
	PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
