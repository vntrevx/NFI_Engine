from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated, Final, NoReturn, assert_never

import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.domain import (
    AccountSnapshot,
    DomainError,
    PositionSide,
    StakeAmount,
    TradingPair,
)
from nfi_engine.risk import (
    AcceptedOrderQuote,
    RejectedOrderQuote,
    RiskRequest,
    pair_locks_from_runtime,
    policy_from_runtime,
    quote_order,
)

risk_app: Final[typer.Typer] = typer.Typer(help="Inspect risk and order safety decisions.")
DEFAULT_AVAILABLE: Final = Decimal(1000)


@risk_app.command("quote")
def quote_risk(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    pair: Annotated[str, typer.Option("--pair")],
    side: Annotated[str, typer.Option("--side")],
    stake: Annotated[str, typer.Option("--stake")],
    leverage: Annotated[str, typer.Option("--leverage")] = "1",
) -> None:
    try:
        settings = load_runtime_settings(config)
        current_time = datetime.now(tz=UTC)
        request = RiskRequest(
            pair=TradingPair.parse(pair, settings.exchange.trading_mode),
            side=_parse_side(side),
            stake=StakeAmount(_parse_decimal(stake, "stake")),
            requested_leverage=_parse_decimal(leverage, "leverage"),
            account=AccountSnapshot(
                captured_at=current_time,
                equity=StakeAmount(DEFAULT_AVAILABLE),
                available=StakeAmount(DEFAULT_AVAILABLE),
                positions=(),
            ),
            policy=policy_from_runtime(settings),
            pair_locks=pair_locks_from_runtime(settings=settings, current_time=current_time),
            cooldown_until=_cooldown_until(settings.risk.cooldown_seconds, current_time),
            current_time=current_time,
        )
        quote = quote_order(request)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except DomainError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except InvalidOperation as exc:
        _exit_with_error("RISK_DECIMAL_INVALID", str(exc))
    match quote:
        case AcceptedOrderQuote():
            _write_accepted_quote(quote)
        case RejectedOrderQuote():
            _exit_with_rejection(quote)
        case unreachable:
            assert_never(unreachable)


def _parse_side(raw: str) -> PositionSide:
    try:
        return PositionSide(raw.lower())
    except ValueError as exc:
        code = "RISK_SIDE_INVALID"
        message = f"invalid side: {raw}"
        raise _exit_with_error(code, message) from exc


def _parse_decimal(raw: str, field_name: str) -> Decimal:
    value = Decimal(raw)
    if not value.is_finite():
        _exit_with_error("RISK_DECIMAL_INVALID", f"{field_name} must be finite")
    return value


def _cooldown_until(cooldown_seconds: int, current_time: datetime) -> datetime | None:
    if cooldown_seconds <= 0:
        return None
    return current_time + timedelta(seconds=cooldown_seconds)


def _write_accepted_quote(quote: AcceptedOrderQuote) -> None:
    sys.stdout.write("accepted=true\n")
    sys.stdout.write(f"pair={quote.pair.normalized}\n")
    sys.stdout.write(f"side={quote.side.value}\n")
    sys.stdout.write(f"stake={quote.stake}\n")
    sys.stdout.write(f"leverage={quote.leverage.value}\n")
    sys.stdout.write(f"adjusted={str(quote.adjusted).lower()}\n")
    if quote.reason is not None:
        sys.stdout.write(f"reason={quote.reason}\n")


def _exit_with_rejection(quote: RejectedOrderQuote) -> NoReturn:
    sys.stdout.write("accepted=false\n")
    sys.stdout.write(f"code={quote.code.value}\n")
    sys.stdout.write(f"message={quote.message}\n")
    raise typer.Exit(code=1)


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
