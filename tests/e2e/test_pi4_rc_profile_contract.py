from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
PROFILE_SCRIPT: Final = PROJECT_ROOT / "scripts/pi4_rc_profile.sh"
SOAK_SCRIPT: Final = PROJECT_ROOT / "scripts/pi4_soak.sh"
FORBIDDEN_HOST_MUTATION_SNIPPETS: Final = (
    "systemctl ",
    "sysctl -w",
    "rfkill ",
    "raspi-config",
    "cpufreq-set",
    "modprobe ",
    "dtoverlay=",
    "pinctrl set",
    "gpio -g",
    "sed -i",
    "tee /boot",
    "tee /etc/sysctl",
    "tee /etc/systemd/journald.conf",
    "tee /etc/docker/daemon.json",
    "tee /sys/devices/system/cpu",
    "tee /sys/class/gpio",
    "> /boot",
    "> /etc/sysctl",
    "> /etc/systemd",
    "> /etc/docker/daemon.json",
    "> /sys/devices/system/cpu",
    "> /sys/class/gpio",
)


def test_pi4_rc_profile_does_not_ship_host_mutation_commands() -> None:
    # Given: the Pi4 RC profile shipped as the deployment-readiness gate.
    script = PROFILE_SCRIPT.read_text(encoding="utf-8")

    # When/Then: it may inspect host state, but it must not mutate host tuning.
    for forbidden in FORBIDDEN_HOST_MUTATION_SNIPPETS:
        assert forbidden not in script
    assert "host_tuning=not_applied" in script
    assert "rollback_safe_uninstall" in script
    assert "rollback_purge_preview" in script


def test_pi4_soak_does_not_ship_host_mutation_commands() -> None:
    # Given: the bounded Pi4 soak evidence loop shipped as the deployment-readiness gate.
    script = SOAK_SCRIPT.read_text(encoding="utf-8")

    # When/Then: it may inspect host/runtime state, but it must not mutate host tuning.
    for forbidden in FORBIDDEN_HOST_MUTATION_SNIPPETS:
        assert forbidden not in script
    assert "runtime-health" in script
    assert "testnet-pilot" in script
    assert "--allow-blockers" in script


def test_pi4_soak_help_documents_bounded_evidence() -> None:
    # Given
    command: Final = ["bash", str(SOAK_SCRIPT), "--help"]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "--iterations" in result.stdout
    assert "--config" in result.stdout
    assert "--pi-host" in result.stdout
    assert "runtime-health" in result.stdout
    assert "testnet-pilot" in result.stdout


def test_pi4_soak_bounded_dry_run_records_resource_health_and_pilot_outputs(
    tmp_path: Path,
) -> None:
    # Given: a local simulator config and an output directory outside the repo.
    config_path = tmp_path / "runtime-health.yaml"
    db_path = tmp_path / "health.sqlite3"
    output_dir = tmp_path / "soak"
    config_path.write_text(
        f"""database:
  url: sqlite+aiosqlite:///{db_path}
exchange:
  name: simulator
  trading_mode: spot
  testnet: true
""",
        encoding="utf-8",
    )
    command: Final = [
        "bash",
        str(SOAK_SCRIPT),
        "--iterations",
        "1",
        "--interval-seconds",
        "1",
        "--output-dir",
        str(output_dir),
        "--config",
        str(config_path),
        "--allow-blockers",
    ]

    # When: blockers are allowed so missing Pi hardware or Docker is recorded, not hidden.
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    # Then: the dry-run exits cleanly and leaves bounded evidence files.
    assert result.returncode == 0, result.stderr
    summary = (output_dir / "summary.txt").read_text(encoding="utf-8")
    resources = (output_dir / "resources-0001.txt").read_text(encoding="utf-8")
    runtime_health = (output_dir / "runtime-health-0001.json").read_text(encoding="utf-8")
    testnet_pilot = (output_dir / "testnet-pilot-0001.json").read_text(encoding="utf-8")

    assert "iterations_completed=1" in summary
    assert "profile_output=" in summary
    assert "resources_output=" in summary
    assert "runtime_health_output=" in summary
    assert "testnet_pilot_output=" in summary
    assert "mem_available_kb=" in resources
    assert "load_1m=" in resources
    assert '"checks"' in runtime_health
    assert '"live_money_orders_enabled": false' in testnet_pilot
    assert "local-test-secret" not in summary + resources + runtime_health + testnet_pilot


def test_pi4_rc_profile_rejects_invalid_port_before_output_file(tmp_path: Path) -> None:
    # Given: a malformed host port and a requested evidence output file.
    output_path = tmp_path / "pi4-profile.txt"
    command: Final = [
        "bash",
        str(PROFILE_SCRIPT),
        "--host-port",
        "not-a-port",
        "--output",
        str(output_path),
    ]

    # When: the profile parses operator input.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: it fails before writing profile output or touching runtime state.
    assert result.returncode != 0
    assert "PI4_INVALID_HOST_PORT" in result.stderr
    assert not output_path.exists()
