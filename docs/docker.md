# Docker Runtime

The M1 container stack is for local paper trading, simulation, and testnet-style
operator checks. It is not a live-money deployment recipe.

## Build

```bash
docker build -t nfi-engine:local .
```

The runtime image installs the package with `uv`, runs as the non-root `nfi`
user, and exposes port `18080` inside the container.

## Compose Services

```bash
docker compose config
docker compose --profile paper up --build -d api
curl -i http://127.0.0.1:18080/api/v1/ping
```

Services:

- `api`: FastAPI REST/UI server using `/app/examples/futures-paper.yaml`.
- `cli`: one-shot CLI container for maintenance and smoke commands.
- `paper`: profile-gated paper runner using fixture ticks.

The API publishes `127.0.0.1:18080:18080`. Keep that loopback binding unless a
later deployment task adds a reverse proxy, TLS, and explicit operator auth.

## Volumes

Compose creates:

- `nfi-data`: SQLite and runtime data.
- `nfi-logs`: operator logs and notification dry-run files.
- `nfi-config`: mutable local config volume.

The repository `examples/` directory is mounted read-only into `/app/examples`.

## Secrets

Do not commit exchange keys or real API tokens. `examples/docker.env.example`
contains only local defaults. Override secrets from your shell or an untracked
env file:

```bash
NFI_ENGINE_API_TOKEN="$(openssl rand -hex 32)" docker compose up -d api
```

Weak tokens are rejected outside local/dev/test environments.

## CLI In Container

```bash
docker compose run --rm cli nfi-engine --help
docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml
```

## Teardown

```bash
docker compose down -v
```

This removes containers and named volumes. Back up anything important first.
