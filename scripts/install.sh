#!/usr/bin/env bash
set -euo pipefail

runtime_dir=".runtime"
project_name="${COMPOSE_PROJECT_NAME:-nfi-engine}"
host_port="${NFI_ENGINE_HOST_PORT:-18080}"
exchange="bybit"
trading_mode="futures"
risk_preset="balanced"
api_key="${NFI_ENGINE_SETUP_API_KEY:-}"
api_secret="${NFI_ENGINE_SETUP_API_SECRET:-}"
yes=0
paper=0
testnet=0
live=0
confirm_live=0
dry_run=0

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

need_command() {
  if command -v "$1" >/dev/null 2>&1; then
    return
  fi
  printf 'INSTALL_MISSING_COMMAND: %s\n' "$1" >&2
  case "$1" in
    uv)
      printf 'install_hint=Install uv from https://docs.astral.sh/uv/ and Python 3.12+ with python3 on PATH; then re-run this command.\n' >&2
      ;;
    python3)
      printf 'install_hint=Install Python 3.12+ and ensure python3 is on PATH; then re-run this command.\n' >&2
      ;;
    docker)
      printf 'install_hint=Install Docker with Compose v2 and verify `docker compose version`; then re-run this command.\n' >&2
      ;;
    *)
      printf 'install_hint=Install the missing command and re-run this command.\n' >&2
      ;;
  esac
  exit 1
}

require_docker_compose() {
  need_command docker
  local compose_output
  if ! compose_output="$(docker compose version 2>&1)"; then
    printf 'INSTALL_DOCKER_UNAVAILABLE\n' >&2
    if [ -n "$compose_output" ]; then
      printf '%s\n' "$compose_output" >&2
    fi
    printf 'install_hint=Install Docker with Compose v2 and verify `docker compose version`; then re-run this command.\n' >&2
    exit 1
  fi
}

validate_host_port() {
  case "$host_port" in
    "" | *[!0-9]*)
      die "INSTALL_INVALID_HOST_PORT: $host_port"
      ;;
  esac
  if [ "$host_port" -lt 1 ] || [ "$host_port" -gt 65535 ]; then
    die "INSTALL_INVALID_HOST_PORT: $host_port"
  fi
}

random_token() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
    return
  fi
  python3 -c 'import secrets; print(secrets.token_hex(32))'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --yes)
      yes=1
      shift
      ;;
    --paper)
      paper=1
      shift
      ;;
    --testnet)
      testnet=1
      shift
      ;;
    --live)
      live=1
      shift
      ;;
    --confirm-live)
      confirm_live=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --runtime-dir)
      runtime_dir="${2:?INSTALL_MISSING_VALUE: --runtime-dir}"
      shift 2
      ;;
    --project-name)
      project_name="${2:?INSTALL_MISSING_VALUE: --project-name}"
      shift 2
      ;;
    --host-port)
      host_port="${2:?INSTALL_MISSING_VALUE: --host-port}"
      shift 2
      ;;
    --exchange)
      exchange="${2:?INSTALL_MISSING_VALUE: --exchange}"
      shift 2
      ;;
    --trading-mode)
      trading_mode="${2:?INSTALL_MISSING_VALUE: --trading-mode}"
      shift 2
      ;;
    --risk-preset)
      risk_preset="${2:?INSTALL_MISSING_VALUE: --risk-preset}"
      shift 2
      ;;
    --api-key)
      api_key="${2:?INSTALL_MISSING_VALUE: --api-key}"
      shift 2
      ;;
    --api-secret)
      api_secret="${2:?INSTALL_MISSING_VALUE: --api-secret}"
      shift 2
      ;;
    *)
      die "INSTALL_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

[ "$yes" -eq 1 ] || die "INSTALL_CONFIRMATION_REQUIRED: pass --yes"
if [ "$live" -eq 1 ] && { [ "$paper" -eq 1 ] || [ "$testnet" -eq 1 ]; }; then
  die "INSTALL_INTENT_CONFLICT: --live cannot be combined with --paper or --testnet"
fi
validate_host_port

need_command uv
need_command python3

started_at="$(date +%s)"
config_dir="${runtime_dir%/}/config"
config_path="$config_dir/futures-paper.yaml"
env_file="${runtime_dir%/}/docker.env"
mkdir -p "$config_dir"
printf 'nfi-engine-runtime=1\n' > "${runtime_dir%/}/.nfi-engine-runtime"

token="$(random_token)"
umask 077
{
  printf 'NFI_ENGINE_API_TOKEN=%s\n' "$token"
  printf 'NFI_ENGINE__ENGINE__ENVIRONMENT=local\n'
  printf 'NFI_ENGINE__LOGGING__LEVEL=INFO\n'
} > "$env_file"
chmod 600 "$env_file"

intent_flag="--paper"
intent_name="paper"
if [ "$testnet" -eq 1 ]; then
  intent_flag="--testnet"
  intent_name="testnet"
fi
if [ "$live" -eq 1 ]; then
  intent_flag="--live"
  intent_name="live"
fi

setup_args=(
  nfi-engine setup init
  --config "$config_path"
  --exchange "$exchange"
  --trading-mode "$trading_mode"
  "$intent_flag"
  --risk-preset "$risk_preset"
  --non-interactive
  --force
)
if [ -n "$api_key" ]; then
  setup_args+=(--api-key "$api_key")
fi
if [ -n "$api_secret" ]; then
  setup_args+=(--api-secret "$api_secret")
fi
if [ "$confirm_live" -eq 1 ]; then
  setup_args+=(--confirm-live)
fi
uv run "${setup_args[@]}" >/dev/null

if [ "$dry_run" -eq 1 ]; then
  printf 'install_plan=dry-run\n'
else
  require_docker_compose
  export NFI_ENGINE_HOST_PORT="$host_port"
  export NFI_ENGINE_RUNTIME_CONFIG_DIR="$config_dir"
  export NFI_ENGINE_RUNTIME_ENV_FILE="$env_file"
  export COMPOSE_PROJECT_NAME="$project_name"
  docker compose --project-name "$project_name" up --build -d api
  for _ in $(seq 1 120); do
    if curl -fsS "http://127.0.0.1:${host_port}/api/v1/ping" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  curl -fsS "http://127.0.0.1:${host_port}/api/v1/ping" >/dev/null
  docker compose --project-name "$project_name" run --rm cli nfi-engine config validate --config /config/futures-paper.yaml >/dev/null
  printf 'install=ok\n'
fi

duration_seconds="$(( $(date +%s) - started_at ))"
printf 'url=http://127.0.0.1:%s\n' "$host_port"
printf 'host_port=%s\n' "$host_port"
printf 'compose_project=%s\n' "$project_name"
printf 'intent=%s\n' "$intent_name"
printf 'config=%s\n' "$config_path"
printf 'env_file=%s\n' "$env_file"
printf 'login_token_file=%s\n' "$env_file"
printf 'logs=NFI_ENGINE_HOST_PORT=%s docker compose --project-name %s logs -f api\n' "$host_port" "$project_name"
printf 'uninstall=bash scripts/uninstall.sh --yes --runtime-dir %s --project-name %s\n' "$runtime_dir" "$project_name"
printf 'secrets=redacted\n'
printf 'install_duration_seconds=%s\n' "$duration_seconds"
