# Docker Runtime

The M2 container stack is for local paper trading, simulation, and testnet-style
operator checks. It is not a live-money deployment recipe.

## One-Command Install

```bash
bash scripts/install.sh --yes --paper --testnet
```

The installer creates `.runtime/config/futures-paper.yaml`,
`.runtime/.nfi-engine-runtime`, and `.runtime/docker.env`, starts the API
service, waits for `/api/v1/ping`, and validates the generated config inside the
CLI container. The generated env file is written with `0600` permissions and
command output never prints exchange keys, API secrets, or the generated API
token. The output prints `login_token_file=.runtime/docker.env` so the operator
knows where to read the local browser login token.

## First Run

After install, open `http://127.0.0.1:18080/` and paste the operator token from
`.runtime/docker.env` into the login screen. The Home screen shows Setup Doctor,
Safety Explainer, chart status, recent errors, pairlist state, and the next
maintenance action. Settings keeps the normal first-run form short: exchange,
spot/futures, paper/testnet intent, risk preset, and optional exchange
credentials.

Exchange key and secret entry is write-only in the operator flow. Values are
redacted from command output, support reports, and docs evidence. Use paper or
testnet credentials for local trials.

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

- `api`: FastAPI REST/UI server using `/config/futures-paper.yaml`.
- `cli`: one-shot CLI container for maintenance and smoke commands.
- `paper`: profile-gated paper runner using fixture ticks.

The API publishes `127.0.0.1:18080:18080`. Keep that loopback binding unless a
later deployment task adds a reverse proxy, TLS, and explicit operator auth.

## Volumes

Compose creates:

- `nfi-data`: SQLite and runtime data.
- `nfi-logs`: operator logs and notification dry-run files.

The generated `.runtime/config` directory is mounted read-only into `/config`.
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
docker compose run --rm cli nfi-engine config validate --config /config/futures-paper.yaml
```

## Safe Uninstall

```bash
bash scripts/uninstall.sh --yes
```

Safe uninstall stops and removes Compose containers while preserving generated
runtime files and named data volumes. Use this when you want to stop the local
stack but keep config, logs, and SQLite data for the next run.

## Destructive Purge

```bash
bash scripts/uninstall.sh --purge --yes
```

Destructive Purge removes Compose volumes and the generated `.runtime`
directory. Add `--remove-image` only when you also want to remove the local
`nfi-engine:local` image. Add `--backup-dir .runtime-backups/manual` before
purge when you want a copy of the generated runtime directory first.

The script prints the exact removal scope before it acts. It does not scan the
filesystem outside the configured runtime directory and known Compose resources.
