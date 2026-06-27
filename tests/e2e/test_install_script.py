from __future__ import annotations

import stat
import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_install_script_dry_run_generates_runtime_config_and_redacted_output(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    command: Final = [
        "bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--testnet",
        "--runtime-dir",
        str(runtime_dir),
        "--host-port",
        "18113",
        "--project-name",
        "nfi-engine-test",
        "--dry-run",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    config = runtime_dir / "config" / "futures-paper.yaml"
    env_file = runtime_dir / "docker.env"
    marker = runtime_dir / ".nfi-engine-runtime"
    validation_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        str(config),
    ]
    validation = subprocess.run(
        validation_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert "install_plan=dry-run" in result.stdout
    assert "url=http://127.0.0.1:18113" in result.stdout
    assert "host_port=18113" in result.stdout
    assert "compose_project=nfi-engine-test" in result.stdout
    assert "intent=testnet" in result.stdout
    assert f"login_token_file={env_file}" in result.stdout
    assert (
        f"uninstall=bash scripts/uninstall.sh --yes --runtime-dir {runtime_dir} "
        "--project-name nfi-engine-test"
    ) in result.stdout
    assert config.exists()
    assert env_file.exists()
    assert marker.read_text(encoding="utf-8") == "nfi-engine-runtime=1\n"
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert not tuple(runtime_dir.glob("setup-credentials.*"))


def test_install_script_is_docker_first_and_uses_safe_runtime_files() -> None:
    script = (PROJECT_ROOT / "scripts/install.sh").read_text(encoding="utf-8")

    assert 'docker compose --project-name "$project_name" up --build -d api' in script
    assert (
        'docker compose --project-name "$project_name" run --rm cli nfi-engine config validate'
        in script
    )
    assert "NFI_ENGINE_HOST_PORT" in script
    assert "NFI_ENGINE_RUNTIME_CONFIG_DIR" in script
    assert "NFI_ENGINE_RUNTIME_ENV_FILE" in script
    assert "chmod 600" in script
    assert ".runtime" in script
    assert "curl | bash" not in script
    assert 'setup_args+=(--api-secret "$api_secret")' not in script
    assert 'setup_args+=(--passphrase "$passphrase")' not in script


def test_install_script_refuses_invalid_host_port(tmp_path: Path) -> None:
    # Given: an invalid host port for an isolated RC deployment.
    runtime_dir = tmp_path / "runtime"
    command: Final = [
        "bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--testnet",
        "--runtime-dir",
        str(runtime_dir),
        "--host-port",
        "not-a-port",
        "--dry-run",
    ]

    # When: the installer parses the request.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: it refuses before generating runtime files.
    assert result.returncode != 0
    assert "INSTALL_INVALID_HOST_PORT" in result.stderr
    assert not runtime_dir.exists()


def test_compose_publishes_api_on_configurable_loopback_port() -> None:
    # Given: the Compose stack used by the one-line installer.
    compose_text = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")

    # When/Then: host exposure stays loopback-only and the host port is overridable.
    assert '"127.0.0.1:${NFI_ENGINE_HOST_PORT:-18080}:18080"' in compose_text
    assert "${NFI_ENGINE_RUNTIME_ENV_FILE:-.runtime/docker.env}" in compose_text
    assert "${NFI_ENGINE_RUNTIME_CONFIG_DIR:-./.runtime/config}:/config:ro" in compose_text
    assert "0.0.0.0:18080:18080" not in compose_text


def test_pi4_rc_profile_script_has_reversible_deployment_contract() -> None:
    # Given: the Pi4 RC profile script shipped for hardware deployment checks.
    script = (PROJECT_ROOT / "scripts/pi4_rc_profile.sh").read_text(encoding="utf-8")

    # When/Then: it checks the non-destructive gates and prints rollback receipts.
    assert "PI4_CPU_MAX_REDUCED" in script
    assert "PI4_THROTTLED" in script
    assert "PI4_COMPOSE_PUBLIC_BIND" in script
    assert "PI4_DOCKER_LOG_UNBOUNDED" in script
    assert "rollback_safe_uninstall" in script
    assert "systemctl" not in script
    assert "/boot/firmware/config.txt" not in script


def test_uninstall_script_safe_dry_run_preserves_runtime_and_data(
    tmp_path: Path,
) -> None:
    # Given: generated operator runtime files that must survive safe uninstall.
    runtime_dir = tmp_path / "runtime"
    config_dir = runtime_dir / "config"
    config_dir.mkdir(parents=True)
    marker = config_dir / "operator-marker.txt"
    marker.write_text("keep", encoding="utf-8")

    # When: the operator requests a safe uninstall dry run.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
        "--project-name",
        "nfi-engine-test",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: output names the preserved paths and the marker remains untouched.
    assert result.returncode == 0, result.stderr
    assert "mode=safe" in result.stdout
    assert "compose_project=nfi-engine-test" in result.stdout
    assert f"preserve_runtime={runtime_dir}" in result.stdout
    assert "preserve_volumes=nfi-data,nfi-logs" in result.stdout
    assert "remove_runtime=" not in result.stdout
    assert marker.read_text(encoding="utf-8") == "keep"


def test_uninstall_script_refuses_purge_without_explicit_confirmation() -> None:
    # Given: a destructive purge request without the required confirmation.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--dry-run",
    ]

    # When: the command is executed.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: purge is refused before any Docker or filesystem action can run.
    assert result.returncode != 0
    assert "UNINSTALL_PURGE_CONFIRMATION_REQUIRED" in result.stderr


def test_uninstall_script_purge_dry_run_prints_known_removal_scope(
    tmp_path: Path,
) -> None:
    # Given: a generated runtime directory that would be removed by purge.
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    marker = runtime_dir / "docker.env"
    marker.write_text("NFI_ENGINE_API_TOKEN=redacted", encoding="utf-8")
    (runtime_dir / ".nfi-engine-runtime").write_text("nfi-engine-runtime=1\n", encoding="utf-8")

    # When: purge is requested with explicit confirmation in dry-run mode.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
        "--remove-image",
        "--project-name",
        "nfi-engine-test",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: only known generated resources are listed and dry-run keeps files intact.
    assert result.returncode == 0, result.stderr
    assert "mode=purge" in result.stdout
    assert "compose_project=nfi-engine-test" in result.stdout
    assert f"remove_runtime={runtime_dir}" in result.stdout
    assert "remove_volumes=nfi-data,nfi-logs" in result.stdout
    assert "remove_image=nfi-engine:local" in result.stdout
    assert marker.read_text(encoding="utf-8") == "NFI_ENGINE_API_TOKEN=redacted"


def test_uninstall_script_refuses_unmarked_purge_runtime(tmp_path: Path) -> None:
    # Given: an arbitrary directory that is not marked as generated runtime.
    runtime_dir = tmp_path / "operator-files"
    runtime_dir.mkdir()

    # When: destructive purge is requested for that path.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the script refuses before printing a removal plan.
    assert result.returncode != 0
    assert "UNINSTALL_RUNTIME_MARKER_MISSING" in result.stderr
    assert "remove_runtime=" not in result.stdout


def test_uninstall_script_refuses_home_directory_purge() -> None:
    # Given: the user home directory, which must never be purge-scoped.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--yes",
        "--runtime-dir",
        str(Path.home()),
        "--dry-run",
    ]

    # When: destructive purge is requested.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the path is rejected even before marker checks.
    assert result.returncode != 0
    assert "UNINSTALL_UNSAFE_RUNTIME_DIR" in result.stderr


def test_uninstall_script_refuses_absolute_current_directory_purge(tmp_path: Path) -> None:
    # Given: a generated marker inside the process current directory.
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / ".nfi-engine-runtime").write_text("nfi-engine-runtime=1\n", encoding="utf-8")

    # When: purge dry-run targets the absolute current directory.
    command: Final = [
        "bash",
        str(PROJECT_ROOT / "scripts/uninstall.sh"),
        "--purge",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
    ]
    result = subprocess.run(command, cwd=runtime_dir, capture_output=True, text=True, check=False)

    # Then: current-directory deletion is refused even with a valid runtime marker.
    assert result.returncode != 0
    assert "UNINSTALL_UNSAFE_RUNTIME_DIR" in result.stderr
    assert "remove_runtime=" not in result.stdout


def test_uninstall_script_allows_absent_runtime_for_docker_cleanup(tmp_path: Path) -> None:
    # Given: a generated runtime directory path that has already been removed.
    runtime_dir = tmp_path / "runtime"

    # When: purge dry-run is used to inspect remaining Docker cleanup.
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: marker absence is allowed because no filesystem delete can happen there.
    assert result.returncode == 0, result.stderr
    assert f"remove_runtime={runtime_dir}" in result.stdout


def test_uninstall_script_uses_compose_down_without_broad_filesystem_scans() -> None:
    # Given: the uninstall script shipped to operators.
    script = (PROJECT_ROOT / "scripts/uninstall.sh").read_text(encoding="utf-8")

    # When/Then: safe and purge paths are scoped to Compose and known runtime paths.
    assert 'docker compose --project-name "$project_name" down --remove-orphans' in script
    assert 'docker compose --project-name "$project_name" down --volumes --remove-orphans' in script
    assert 'docker volume rm "${project_name}_nfi-data" "${project_name}_nfi-logs"' in script
    assert ".nfi-engine-runtime" in script
    assert 'rm -rf -- "$runtime_dir"' in script
    assert "find /" not in script
    assert "docker compose down -v" not in script
