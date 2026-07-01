#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
duration_seconds="${NFI_ENGINE_PI4_SOAK_SECONDS:-900}"
interval_seconds="${NFI_ENGINE_PI4_SOAK_INTERVAL_SECONDS:-60}"
iterations=""
output_dir=""
project_name="${COMPOSE_PROJECT_NAME:-nfi-engine-pi4-rc}"
host_port="${NFI_ENGINE_HOST_PORT:-18080}"
config_path="${NFI_ENGINE_CONFIG:-examples/futures-paper.yaml}"
allow_blockers="false"
pi_host="${NFI_ENGINE_PI4_SOAK_PI_HOST:-}"
ssh_timeout_seconds="${NFI_ENGINE_PI4_SOAK_SSH_TIMEOUT_SECONDS:-5}"

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

print_help() {
  cat <<'HELP'
Usage: bash scripts/pi4_soak.sh [OPTIONS]

Runs repeated non-mutating Raspberry Pi 4 RC profile probes. The script records
bounded per-iteration evidence for CPU profile, memory/load, temperature,
throttle flags, runtime-health, and testnet-pilot readiness. It does not change
CPU, fan, Docker daemon, boot, sysctl, or trading settings.

Options:
  --duration-seconds N    Wall-clock loop duration when --iterations is omitted.
  --interval-seconds N    Delay between iterations.
  --iterations N          Exact iteration count for bounded local dry-runs.
  --output-dir PATH       Evidence directory.
  --config PATH           Runtime config for runtime-health/testnet-pilot.
  --project-name NAME     Docker Compose project name passed to profile checks.
  --host-port PORT        Host port expected to bind to 127.0.0.1.
  --pi-host USER@HOST     Optional SSH reachability check for a target Pi.
  --ssh-timeout-seconds N SSH connection timeout for --pi-host.
  --allow-blockers        Exit 0 after recording environmental blockers.
  --help, -h              Show this help.

The default mode is strict: any recorded blocker exits non-zero. Use
--allow-blockers for CI/local dry-runs where missing Pi hardware, Docker, or
owner-only credentials should be captured as evidence instead of failing the
script runner.
HELP
}

number_arg() {
  local value="$1"
  local name="$2"
  case "$value" in
    "" | *[!0-9]*)
      die "PI4_SOAK_INVALID_NUMBER: $name=$value"
      ;;
  esac
  if [ "$value" -lt 1 ]; then
    die "PI4_SOAK_INVALID_NUMBER: $name=$value"
  fi
}

resolve_repo_path() {
  local path="$1"
  case "$path" in
    /*)
      printf '%s' "$path"
      ;;
    *)
      printf '%s/%s' "$repo_root" "$path"
      ;;
  esac
}

append_summary() {
  local key="$1"
  local value="$2"
  printf '%s=%s\n' "$key" "$value" | tee -a "$summary_path"
}

write_resource_snapshot() {
  local path="$1"
  local mem_total_kb="unknown"
  local mem_available_kb="unknown"
  local swap_total_kb="unknown"
  local swap_free_kb="unknown"
  local load_1m="unknown"
  local load_5m="unknown"
  local load_15m="unknown"
  local cpu_count="unknown"

  if [ -r /proc/meminfo ]; then
    while IFS=': ' read -r key value unit; do
      case "$key" in
        MemTotal)
          mem_total_kb="$value"
          ;;
        MemAvailable)
          mem_available_kb="$value"
          ;;
        SwapTotal)
          swap_total_kb="$value"
          ;;
        SwapFree)
          swap_free_kb="$value"
          ;;
      esac
      [ -n "${unit:-}" ] || true
    done < /proc/meminfo
  fi

  if [ -r /proc/loadavg ]; then
    read -r load_1m load_5m load_15m _ < /proc/loadavg
  fi
  if command -v getconf >/dev/null 2>&1; then
    cpu_count="$(getconf _NPROCESSORS_ONLN)"
  fi

  {
    printf 'mem_total_kb=%s\n' "$mem_total_kb"
    printf 'mem_available_kb=%s\n' "$mem_available_kb"
    printf 'swap_total_kb=%s\n' "$swap_total_kb"
    printf 'swap_free_kb=%s\n' "$swap_free_kb"
    printf 'load_1m=%s\n' "$load_1m"
    printf 'load_5m=%s\n' "$load_5m"
    printf 'load_15m=%s\n' "$load_15m"
    printf 'cpu_count=%s\n' "$cpu_count"
  } > "$path"
}

run_runtime_health() {
  local output_path="$1"
  local stderr_path="$2"
  if uv run nfi-engine runtime-health check --config "$config_abs" --format json \
    > "$output_path" 2> "$stderr_path"; then
    printf 'pass'
    return
  fi
  printf 'block'
}

run_testnet_pilot() {
  local output_path="$1"
  local stderr_path="$2"
  if uv run nfi-engine exchange testnet-pilot --config "$config_abs" --json \
    > "$output_path" 2> "$stderr_path"; then
    printf 'pass'
    return
  fi
  printf 'block'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help | -h)
      print_help
      exit 0
      ;;
    --duration-seconds)
      duration_seconds="${2:?PI4_SOAK_MISSING_VALUE: --duration-seconds}"
      shift 2
      ;;
    --interval-seconds)
      interval_seconds="${2:?PI4_SOAK_MISSING_VALUE: --interval-seconds}"
      shift 2
      ;;
    --iterations)
      iterations="${2:?PI4_SOAK_MISSING_VALUE: --iterations}"
      shift 2
      ;;
    --output-dir)
      output_dir="${2:?PI4_SOAK_MISSING_VALUE: --output-dir}"
      shift 2
      ;;
    --config)
      config_path="${2:?PI4_SOAK_MISSING_VALUE: --config}"
      shift 2
      ;;
    --project-name)
      project_name="${2:?PI4_SOAK_MISSING_VALUE: --project-name}"
      shift 2
      ;;
    --host-port)
      host_port="${2:?PI4_SOAK_MISSING_VALUE: --host-port}"
      shift 2
      ;;
    --pi-host)
      pi_host="${2:?PI4_SOAK_MISSING_VALUE: --pi-host}"
      shift 2
      ;;
    --ssh-timeout-seconds)
      ssh_timeout_seconds="${2:?PI4_SOAK_MISSING_VALUE: --ssh-timeout-seconds}"
      shift 2
      ;;
    --allow-blockers)
      allow_blockers="true"
      shift
      ;;
    *)
      die "PI4_SOAK_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

number_arg "$duration_seconds" duration_seconds
number_arg "$interval_seconds" interval_seconds
number_arg "$ssh_timeout_seconds" ssh_timeout_seconds
if [ -n "$iterations" ]; then
  number_arg "$iterations" iterations
fi
case "$host_port" in
  "" | *[!0-9]*)
    die "PI4_SOAK_INVALID_NUMBER: host_port=$host_port"
    ;;
esac
if [ "$host_port" -lt 1 ] || [ "$host_port" -gt 65535 ]; then
  die "PI4_SOAK_INVALID_NUMBER: host_port=$host_port"
fi

config_abs="$(resolve_repo_path "$config_path")"
if [ ! -f "$config_abs" ]; then
  die "PI4_SOAK_CONFIG_MISSING: $config_path"
fi

if [ -z "$output_dir" ]; then
  output_dir=".omo/evidence/pi4-soak-$(date -u +%Y%m%dT%H%M%SZ)"
fi

mkdir -p "$output_dir"
summary_path="$output_dir/summary.txt"
: > "$summary_path"
start_epoch="$(date +%s)"
end_epoch=$((start_epoch + duration_seconds))
iteration=0
pass_count=0
block_count=0
environment_block_count=0

append_summary soak pi4
append_summary duration_seconds "$duration_seconds"
append_summary interval_seconds "$interval_seconds"
append_summary iterations "${iterations:-duration}"
append_summary project_name "$project_name"
append_summary host_port "$host_port"
append_summary config_path "$config_path"
append_summary allow_blockers "$allow_blockers"

if [ -n "$pi_host" ]; then
  pi_ssh_path="$output_dir/pi-ssh.txt"
  if ssh -o BatchMode=yes -o ConnectTimeout="$ssh_timeout_seconds" \
    "$pi_host" "printf 'pi_ssh=ok\n'" > "$pi_ssh_path" 2>&1; then
    append_summary pi_status reachable
  else
    append_summary pi_status blocked-no-pi
    append_summary pi_ssh_output "$pi_ssh_path"
    environment_block_count=$((environment_block_count + 1))
  fi
else
  append_summary pi_status local-only
fi

while :; do
  if [ -n "$iterations" ]; then
    [ "$iteration" -lt "$iterations" ] || break
  else
    [ "$(date +%s)" -lt "$end_epoch" ] || break
  fi

  iteration=$((iteration + 1))
  suffix="$(printf '%04d' "$iteration")"
  profile_path="$output_dir/profile-$suffix.txt"
  resources_path="$output_dir/resources-$suffix.txt"
  runtime_health_path="$output_dir/runtime-health-$suffix.json"
  runtime_health_stderr_path="$output_dir/runtime-health-$suffix.stderr.txt"
  testnet_pilot_path="$output_dir/testnet-pilot-$suffix.json"
  testnet_pilot_stderr_path="$output_dir/testnet-pilot-$suffix.stderr.txt"

  profile_status="pass"
  if ! COMPOSE_PROJECT_NAME="$project_name" NFI_ENGINE_HOST_PORT="$host_port" \
    bash "$repo_root/scripts/pi4_rc_profile.sh" --output "$profile_path"; then
    profile_status="block"
  fi

  write_resource_snapshot "$resources_path"
  runtime_health_status="$(run_runtime_health "$runtime_health_path" "$runtime_health_stderr_path")"
  testnet_pilot_status="$(run_testnet_pilot "$testnet_pilot_path" "$testnet_pilot_stderr_path")"

  status="pass"
  if [ "$profile_status" = "block" ] \
    || [ "$runtime_health_status" = "block" ] \
    || [ "$testnet_pilot_status" = "block" ]; then
    status="block"
  fi

  if [ "$status" = "pass" ]; then
    pass_count=$((pass_count + 1))
  else
    block_count=$((block_count + 1))
  fi

  printf \
    'iteration=%s status=%s profile_status=%s resources_status=pass runtime_health_status=%s testnet_pilot_status=%s profile_output=%s resources_output=%s runtime_health_output=%s testnet_pilot_output=%s\n' \
    "$iteration" "$status" "$profile_status" "$runtime_health_status" "$testnet_pilot_status" \
    "$profile_path" "$resources_path" "$runtime_health_path" "$testnet_pilot_path" \
    | tee -a "$summary_path"

  if [ -n "$iterations" ] && [ "$iteration" -ge "$iterations" ]; then
    break
  fi
  if [ -z "$iterations" ] && [ "$(date +%s)" -ge "$end_epoch" ]; then
    break
  fi
  sleep "$interval_seconds"
done

append_summary iterations_completed "$iteration"
append_summary pass_count "$pass_count"
append_summary block_count "$block_count"
append_summary environment_block_count "$environment_block_count"
total_block_count=$((block_count + environment_block_count))
append_summary total_block_count "$total_block_count"

if [ "$total_block_count" -gt 0 ] && [ "$allow_blockers" != "true" ]; then
  exit 1
fi
