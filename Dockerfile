# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.11.19-python3.12-trixie-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md .python-version ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-trixie AS runtime

LABEL org.opencontainers.image.title="nfi-engine"
LABEL org.opencontainers.image.description="Local-safe NFI Engine paper trading runtime"
LABEL org.opencontainers.image.source="https://local/nfi-engine"

ENV NFI_ENGINE_CONFIG=/config/futures-paper.yaml
ENV NFI_ENGINE_API_TOKEN=change-me-local-only
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /usr/sbin/nologin nfi \
    && mkdir -p /app /config /data /logs \
    && chown -R nfi:nfi /app /config /data /logs

WORKDIR /app
COPY --from=builder --chown=nfi:nfi /app/.venv /app/.venv
COPY --chown=nfi:nfi examples ./examples

USER nfi
EXPOSE 18080
VOLUME ["/config", "/data", "/logs"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:18080/api/v1/ping', timeout=2).read()" || exit 1

CMD ["nfi-engine", "serve", "--config", "/config/futures-paper.yaml"]
