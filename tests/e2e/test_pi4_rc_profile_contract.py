from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
PROFILE_SCRIPT: Final = PROJECT_ROOT / "scripts/pi4_rc_profile.sh"
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
