from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def _write_unusable_docker_stub(docker_stub: Path, message: str) -> None:
    docker_stub.write_text(
        f"""#!/usr/bin/env bash
if [[ "$1" == "compose" && "$2" == "version" ]]; then
  printf '%s\\n' "{message}"
  exit 1
fi
printf 'unexpected docker invocation: %s\\n' "$*" >&2
exit 99
""",
        encoding="utf-8",
    )
    docker_stub.chmod(docker_stub.stat().st_mode | stat.S_IXUSR)


def test_install_script_reports_unusable_docker_compose(tmp_path: Path) -> None:
    # Given: a Docker executable exists but Compose is unavailable in the shell.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker_stub = fake_bin / "docker"
    _write_unusable_docker_stub(
        docker_stub,
        "The command 'docker' could not be found in this WSL 2 distro.",
    )
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    command: Final = [
        "bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--testnet",
        "--runtime-dir",
        str(runtime_dir),
    ]

    # When: the real installer reaches its Docker Compose readiness gate.
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: the operator gets a stable error code and the captured Docker hint.
    assert result.returncode != 0
    assert "INSTALL_DOCKER_UNAVAILABLE" in result.stderr
    assert "The command 'docker' could not be found in this WSL 2 distro." in result.stderr
    assert "install_hint=Install Docker with Compose v2" in result.stderr


def test_uninstall_script_reports_unusable_docker_compose(tmp_path: Path) -> None:
    # Given: uninstall cleanup can find Docker, but Compose itself cannot run.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker_stub = fake_bin / "docker"
    _write_unusable_docker_stub(docker_stub, "Docker Desktop WSL integration is disabled.")
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--yes",
        "--runtime-dir",
        str(tmp_path / "runtime"),
    ]

    # When: uninstall reaches Docker Compose readiness.
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: it emits an actionable stable code instead of failing silently.
    assert result.returncode != 0
    assert "UNINSTALL_DOCKER_UNAVAILABLE" in result.stderr
    assert "Docker Desktop WSL integration is disabled." in result.stderr
    assert "install_hint=Install Docker with Compose v2" in result.stderr


def test_final_smoke_uses_isolated_runtime_for_real_docker_install() -> None:
    # Given: the final smoke is allowed to run a real Docker install.
    script = (PROJECT_ROOT / "scripts/final_smoke.sh").read_text(encoding="utf-8")

    # When/Then: it must isolate that install from the operator's default runtime.
    assert '--runtime-dir "${real_runtime_dir}/runtime"' in script
    assert '--project-name "${real_project_name}"' in script
    assert '--host-port "${real_host_port}"' in script
    assert ".runtime/docker.env" not in script
    assert "test -e .runtime" not in script
    assert "test ! -e .runtime" not in script
