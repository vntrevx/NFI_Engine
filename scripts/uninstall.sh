#!/usr/bin/env bash
set -euo pipefail

runtime_dir=".runtime"
project_name="${COMPOSE_PROJECT_NAME:-nfi-engine}"
yes=0
purge=0
dry_run=0
remove_image=0
backup_dir=""

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "UNINSTALL_MISSING_COMMAND: $1"
}

require_docker_compose() {
  need_command docker
  local compose_output
  if ! compose_output="$(docker compose version 2>&1)"; then
    printf 'UNINSTALL_DOCKER_UNAVAILABLE\n' >&2
    if [ -n "$compose_output" ]; then
      printf '%s\n' "$compose_output" >&2
    fi
    printf 'install_hint=Install Docker with Compose v2 and verify `docker compose version`; then re-run this command.\n' >&2
    exit 1
  fi
}

guard_runtime_dir() {
  case "$runtime_dir" in
    "" | "/" | "." | "./")
      die "UNINSTALL_UNSAFE_RUNTIME_DIR: $runtime_dir"
      ;;
  esac
  if [ "$purge" -eq 0 ]; then
    return
  fi
  command -v realpath >/dev/null 2>&1 || die "UNINSTALL_MISSING_COMMAND: realpath"
  runtime_abs="$(realpath -m -- "$runtime_dir")"
  cwd_abs="$(pwd -P)"
  home_abs="${HOME:-}"
  if [ "$runtime_abs" = "$cwd_abs" ]; then
    die "UNINSTALL_UNSAFE_RUNTIME_DIR: $runtime_dir"
  fi
  if [ -n "$home_abs" ] && [ "$runtime_abs" = "$home_abs" ]; then
    die "UNINSTALL_UNSAFE_RUNTIME_DIR: $runtime_dir"
  fi
  if [ -e "$runtime_abs" ] && [ ! -f "$runtime_abs/.nfi-engine-runtime" ]; then
    die "UNINSTALL_RUNTIME_MARKER_MISSING: $runtime_dir"
  fi
}

print_plan() {
  printf 'compose_project=%s\n' "$project_name"
  if [ "$purge" -eq 1 ]; then
    printf 'mode=purge\n'
    printf 'compose_action=docker compose --project-name %s down --volumes --remove-orphans\n' "$project_name"
    printf 'remove_runtime=%s\n' "$runtime_dir"
    printf 'remove_volumes=nfi-data,nfi-logs\n'
    if [ "$remove_image" -eq 1 ]; then
      printf 'remove_image=nfi-engine:local\n'
    else
      printf 'remove_image=preserved\n'
    fi
    if [ -n "$backup_dir" ]; then
      printf 'backup_runtime=%s\n' "$backup_dir"
    else
      printf 'backup_runtime=not_requested\n'
    fi
    return
  fi
  printf 'mode=safe\n'
  printf 'compose_action=docker compose --project-name %s down --remove-orphans\n' "$project_name"
  printf 'preserve_runtime=%s\n' "$runtime_dir"
  printf 'preserve_volumes=nfi-data,nfi-logs\n'
}

backup_runtime() {
  if [ -z "$backup_dir" ] || [ ! -e "$runtime_dir" ]; then
    return
  fi
  mkdir -p "$backup_dir"
  cp -a "$runtime_dir" "$backup_dir/runtime"
}

remove_known_volumes() {
  docker volume rm "${project_name}_nfi-data" "${project_name}_nfi-logs" >/dev/null 2>&1 || true
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --yes)
      yes=1
      shift
      ;;
    --purge)
      purge=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --remove-image)
      remove_image=1
      shift
      ;;
    --backup-dir)
      backup_dir="${2:?UNINSTALL_MISSING_VALUE: --backup-dir}"
      shift 2
      ;;
    --runtime-dir)
      runtime_dir="${2:?UNINSTALL_MISSING_VALUE: --runtime-dir}"
      shift 2
      ;;
    --project-name)
      project_name="${2:?UNINSTALL_MISSING_VALUE: --project-name}"
      shift 2
      ;;
    *)
      die "UNINSTALL_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

if [ "$purge" -eq 1 ] && [ "$yes" -ne 1 ]; then
  die "UNINSTALL_PURGE_CONFIRMATION_REQUIRED: pass --purge --yes"
fi
[ "$yes" -eq 1 ] || die "UNINSTALL_CONFIRMATION_REQUIRED: pass --yes"

guard_runtime_dir
print_plan

if [ "$dry_run" -eq 1 ]; then
  printf 'uninstall_plan=dry-run\n'
  exit 0
fi

export COMPOSE_PROJECT_NAME="$project_name"
require_docker_compose

if [ "$purge" -eq 1 ]; then
  backup_runtime
  if [ "$remove_image" -eq 1 ]; then
    docker compose --project-name "$project_name" down --volumes --remove-orphans --rmi local
  else
    docker compose --project-name "$project_name" down --volumes --remove-orphans
  fi
  remove_known_volumes
  rm -rf -- "$runtime_dir"
  printf 'uninstall=purged\n'
  exit 0
fi

docker compose --project-name "$project_name" down --remove-orphans
printf 'uninstall=stopped\n'
