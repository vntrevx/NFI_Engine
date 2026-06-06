from __future__ import annotations

import sys
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.domain import (
    DomainError,
    OrderIntentDraft,
    OrderType,
    PositionSide,
    TradingMode,
    TradingPair,
    create_order_intent,
)

domain_app: Final[typer.Typer] = typer.Typer(help="Inspect and validate domain values.")


@domain_app.command("inspect-pair")
def inspect_pair(
    raw_pair: Annotated[str, typer.Argument(metavar="PAIR")],
    mode: Annotated[TradingMode, typer.Option("--mode")] = TradingMode.SPOT,
) -> None:
    try:
        pair = TradingPair.parse(raw_pair, mode)
    except DomainError as exc:
        _exit_with_domain_error(exc)
    sys.stdout.write(
        "\n".join(
            (
                f"base={pair.base}",
                f"quote={pair.quote}",
                f"settle={pair.settle}",
                f"trading_mode={mode.value}",
                f"normalized={pair.normalized}",
            ),
        ),
    )
    sys.stdout.write("\n")


@domain_app.command("validate-order")
def validate_order(
    pair: Annotated[str, typer.Option("--pair")],
    mode: Annotated[TradingMode, typer.Option("--mode")],
    side: Annotated[PositionSide, typer.Option("--side")],
    order_type: Annotated[OrderType, typer.Option("--type")],
) -> None:
    try:
        parsed_pair = TradingPair.parse(pair, mode)
        create_order_intent(
            OrderIntentDraft(
                pair=parsed_pair,
                trading_mode=mode,
                side=side,
                order_type=order_type,
            ),
        )
    except DomainError as exc:
        _exit_with_domain_error(exc)
    sys.stdout.write("valid\n")


def _exit_with_domain_error(exc: DomainError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
