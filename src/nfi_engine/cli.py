from __future__ import annotations

from typing import Final

import typer

from nfi_engine.cli_backtest import backtest
from nfi_engine.cli_backup import backup_app
from nfi_engine.cli_benchmark import benchmark_app
from nfi_engine.cli_circuit_breaker import circuit_breaker_app
from nfi_engine.cli_compat import compat_app
from nfi_engine.cli_config import config_app
from nfi_engine.cli_data import data_app
from nfi_engine.cli_db import db_app
from nfi_engine.cli_domain import domain_app
from nfi_engine.cli_exchange import exchange_app
from nfi_engine.cli_logs import logs_app
from nfi_engine.cli_notify import notify_app
from nfi_engine.cli_pairlist import pairlist_app
from nfi_engine.cli_paper import paper_run
from nfi_engine.cli_plugins import plugins_app
from nfi_engine.cli_preflight import preflight_app
from nfi_engine.cli_profile import profile_app
from nfi_engine.cli_risk import risk_app
from nfi_engine.cli_runtime_health import runtime_health_app
from nfi_engine.cli_sandbox import sandbox_app
from nfi_engine.cli_serve import serve
from nfi_engine.cli_setup import setup_app
from nfi_engine.cli_simulate import simulate_app
from nfi_engine.cli_strategy import strategy_app
from nfi_engine.cli_validation import validate_app

APP_NAME: Final = "nfi-engine"


def _root() -> None:
    return None


app: Final[typer.Typer] = typer.Typer(
    name=APP_NAME,
    callback=_root,
    help="Operator CLI for the NFI Engine.",
    no_args_is_help=True,
)
app.add_typer(backup_app, name="backup")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(config_app, name="config")
app.add_typer(circuit_breaker_app, name="circuit-breaker")
app.add_typer(compat_app, name="compat")
app.add_typer(data_app, name="data")
app.add_typer(db_app, name="db")
app.add_typer(domain_app, name="domain")
app.add_typer(exchange_app, name="exchange")
app.add_typer(logs_app, name="logs")
app.add_typer(notify_app, name="notify")
app.add_typer(pairlist_app, name="pairlist")
app.add_typer(preflight_app, name="preflight")
app.add_typer(profile_app, name="profile")
app.add_typer(plugins_app, name="plugins")
app.add_typer(risk_app, name="risk")
app.add_typer(sandbox_app, name="sandbox")
app.add_typer(runtime_health_app, name="runtime-health")
app.add_typer(setup_app, name="setup")
app.add_typer(simulate_app, name="simulate")
app.add_typer(strategy_app, name="strategy")
app.add_typer(validate_app, name="validate")
app.command(name="backtest")(backtest)
app.command(name="paper-run")(paper_run)
app.command(name="serve")(serve)


def main() -> None:
    app()
