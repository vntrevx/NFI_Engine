from __future__ import annotations

import sys
from typing import Final

import typer

from nfi_engine.profiles import list_operator_profiles

profile_app: Final[typer.Typer] = typer.Typer(help="Inspect operator profiles.")


@profile_app.command("list")
def list_profiles() -> None:
    for profile in list_operator_profiles():
        modes = ",".join(mode.value for mode in profile.trading_modes)
        columns = (
            profile.name,
            f"modes={modes}",
            f"testnet={str(profile.requires_testnet).lower()}",
            f"readonly={str(profile.read_only).lower()}",
            profile.description,
        )
        line = "\t".join(columns) + "\n"
        sys.stdout.write(line)
