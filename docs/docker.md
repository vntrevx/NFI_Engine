# Docker Runtime

The M2 container stack is for local paper trading, simulation, and testnet-style
operator checks. It is not a live-money deployment recipe.

## One-Command Install

```bash
bash scripts/install.sh --yes --paper --testnet
npm run nfi:install
bun run nfi:install
```

The installer creates `.runtime/config/futures-paper.yaml`,
`.runtime/.nfi-engine-runtime`, and `.runtime/docker.env`, starts the API
service, waits for `/api/v1/ping`, and validates the generated config inside the
CLI container. The generated env file is written with `0600` permissions and
command output never prints exchange keys, API secrets, or the generated
operator password. The output prints the runtime env-file path so the operator
knows where to read the local browser password.

The npm and Bun commands are thin wrappers around the same shell installer and
do not add runtime dependencies. Use the dry-run path to verify the generated
receipt before starting Docker:

```bash
bash scripts/install.sh --yes --paper --testnet --dry-run
npm run nfi:install:dry-run
bun run nfi:install:dry-run
```

Host requirements are explicit. Dry-run setup needs `uv` and Python 3.12+
available as `python3`; the full Docker path also needs Docker with Compose v2.
If a tool is missing, the installer exits with `INSTALL_MISSING_COMMAND` and an
`install_hint` line instead of printing a partial or misleading success message.

For isolated release-candidate checks on a host that may already run another
NFI Engine stack, give the Docker project and loopback host port explicitly:

```bash
bash scripts/install.sh --yes --paper --testnet --project-name nfi-engine-pi4-rc --host-port 18113
```

The API still binds to loopback only:
`http://127.0.0.1:18113/`. The option exists to avoid port and volume conflicts
during Pi4 verification, not to expose the service publicly.

## First Run

After install, open `http://127.0.0.1:18080/` and log in as `admin` with the
operator password from `.runtime/docker.env`. The Home screen shows Setup Doctor,
Safety Explainer, chart status, recent errors, pairlist state, and the next
maintenance action. Settings keeps the normal first-run form short: exchange,
spot/futures, paper/testnet intent, risk preset, and optional exchange
credentials.

Exchange credential entry is write-only in the operator flow. Standard
`api_key` / `api_secret` fields and exchange-specific fields such as
`passphrase`, `memo`, `operator_id`, `account_address`, and `api_wallet_signer`
are redacted from command output, support reports, and docs evidence. Use paper
or testnet credentials for local trials.

The installer rejects secret-bearing command arguments. Pass setup credentials
through owner-only environment variables or an owner-only credentials file:

```bash
cat > .runtime/setup-credentials.env <<'EOF'
api_key=...
api_secret=...
passphrase=...
EOF
chmod 600 .runtime/setup-credentials.env
bash scripts/install.sh --yes --testnet --exchange bitget \
  --credentials-file .runtime/setup-credentials.env
```

The file accepts `api_key`, `api_secret`, `passphrase`, `memo`, `operator_id`,
`account_address`, and `api_wallet_signer`. Matching `NFI_ENGINE_SETUP_*`
environment variables are also accepted and are converted to a temporary
owner-only file before the setup CLI is invoked.

For priority testnet exchange checks, create owner-only per-exchange templates
and fill only testnet/sandbox keys:

```bash
bash scripts/testnet_credential_probe.sh --init-template
$EDITOR .runtime/secrets/testnet-binance.env
$EDITOR .runtime/secrets/testnet-bybit.env
$EDITOR .runtime/secrets/testnet-okx.env
$EDITOR .runtime/secrets/testnet-bitget.env
bash scripts/testnet_credential_probe.sh
```

For the current owner-primary pilot lane, run only the Binance check:

```bash
bash scripts/testnet_credential_probe.sh --exchange binance
```

`--exchange bybit`, `--exchange okx`, and `--exchange bitget` are accepted for
redacted user issue reports. They are not owner-primary validation lanes.

The probe reads `.runtime/secrets/testnet-<exchange>.env` first and falls back
to `.runtime/secrets/exchange-wallet.env` for older local setups. Empty
templates stay `blocked-no-key`; the script never prints credential values.

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

The API publishes `127.0.0.1:${NFI_ENGINE_HOST_PORT:-18080}:18080`. Keep that
loopback binding unless a later deployment task adds a reverse proxy, TLS, and
explicit operator auth.
The API container uses `restart: unless-stopped`, Docker init, and bounded
json-file logs (`10m` x 3) so Raspberry Pi and low-resource paper/testnet
installs can survive service restarts without unbounded log growth. This is an
operator reliability setting, not a live-money deployment guarantee.

## Raspberry Pi 4 RC Profile

Pi4 release-candidate checks are explicit and reversible. The profile script
does not change CPU, fan, sysctl, journald, Docker daemon, Bluetooth, GPIO, or
boot settings:

```bash
bash scripts/pi4_rc_profile.sh --project-name nfi-engine-pi4-rc --host-port 18113 --output .omo/evidence/pi4-rc-profile.txt
npm run nfi:pi4:rc-check -- --project-name nfi-engine-pi4-rc --host-port 18113
bun run nfi:pi4:rc-check -- --project-name nfi-engine-pi4-rc --host-port 18113
```

The script blocks deployment on reduced CPU max frequency, active throttling,
high temperature, missing Docker/Compose/uv/Python, public port binding,
unbounded Docker logs, or low disk space. It prints rollback receipts:

```bash
bash scripts/uninstall.sh --yes --project-name nfi-engine-pi4-rc
bash scripts/uninstall.sh --purge --yes --dry-run --project-name nfi-engine-pi4-rc
```

## Volumes

Compose creates:

- `nfi-data`: SQLite and runtime data.
- `nfi-logs`: operator logs and notification dry-run files.

The generated `.runtime/config` directory is mounted read-only into `/config`.
The repository `examples/` directory is mounted read-only into `/app/examples`.

## Secrets

Do not commit exchange keys, operator passwords, or real API tokens.
`examples/docker.env.example`
contains only local defaults. Override secrets from your shell or an untracked
env file:

```bash
NFI_ENGINE_OPERATOR_PASSWORD="$(openssl rand -hex 32)" docker compose up -d api
```

Weak operator credentials are rejected outside local/dev/test environments.

## CLI In Container

```bash
docker compose run --rm cli nfi-engine --help
docker compose run --rm cli nfi-engine config validate --config /config/futures-paper.yaml
docker compose run --rm cli nfi-engine strategy inspect --config /app/examples/x7-futures-paper.yaml --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy --json
```

The X7 inspect command verifies the native semantic strategy surface available
to the local dry-run/paper/testnet runtime. It is a runtime-shape check, not a
trade-result claim.

## Safe Uninstall

```bash
bash scripts/uninstall.sh --yes
npm run nfi:uninstall
bun run nfi:uninstall
```

Safe uninstall stops and removes Compose containers while preserving generated
runtime files and named data volumes. Use this when you want to stop the local
stack but keep config, logs, and SQLite data for the next run.

## Destructive Purge

```bash
bash scripts/uninstall.sh --purge --yes
npm run nfi:uninstall:purge:dry-run
bun run nfi:uninstall:purge:dry-run
```

Destructive Purge removes Compose volumes and the generated `.runtime`
directory. The npm and Bun commands above are dry-run previews only. Add
`--remove-image` only when you also want to remove the local `nfi-engine:local`
image. Add `--backup-dir .runtime-backups/manual` before purge when you want a
copy of the generated runtime directory first.

The script prints the exact removal scope before it acts. It does not scan the
filesystem outside the configured runtime directory and known Compose resources.
