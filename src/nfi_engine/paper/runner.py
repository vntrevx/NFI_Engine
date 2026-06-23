from __future__ import annotations

from dataclasses import replace
from typing import assert_never

from nfi_engine.domain import AccountSnapshot, StakeAmount
from nfi_engine.exchange import Tick, get_exchange_profile
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.paper.errors import PaperError, PaperErrorCode
from nfi_engine.paper.execution import execute_paper_events, first_breaker, trading_halted
from nfi_engine.paper.lifecycle import apply_bot_command
from nfi_engine.paper.models import (
    BotCommand,
    BotState,
    PaperRunRequest,
    PaperRunResult,
    PaperTick,
)
from nfi_engine.persistence import create_persistence_database
from nfi_engine.preflight import PreflightReport, PreflightStatus
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name
from nfi_engine.safety import enforce_milestone_live_trading_scope
from nfi_engine.wallet import WalletBalanceSnapshot, WalletBalanceStatus, fetch_wallet_balance


async def run_paper(request: PaperRunRequest) -> PaperRunResult:
    enforce_milestone_live_trading_scope(request.settings)
    _validate_paper_exchange(request)
    gated_request = await _startup_checked_request(request)
    state = apply_bot_command(BotState.STOPPED, BotCommand.START)
    database = create_persistence_database(gated_request.database_url)
    await database.initialize()
    simulator = DeterministicExchangeSimulator(ticks=_exchange_ticks(gated_request.ticks))
    try:
        execution = await execute_paper_events(
            database=database,
            simulator=simulator,
            request=gated_request,
            state=state,
        )
        state = apply_bot_command(state, BotCommand.STOP)
        state = apply_bot_command(state, BotCommand.STOP)
        return PaperRunResult(
            processed_events=execution.processed_events,
            created_trades=execution.created_trades,
            live_orders=False,
            final_state=state,
            trading_halted=trading_halted(execution.latest_decision),
            halted_breaker=first_breaker(execution.latest_decision),
            new_orders_blocked=execution.blocked_orders > 0,
            timeline=execution.timeline,
        )
    finally:
        await database.dispose()


def _validate_paper_exchange(request: PaperRunRequest) -> None:
    profile = get_exchange_profile(request.settings.exchange.name)
    if profile is None or (
        profile.exchange_id != "simulator" and not request.settings.exchange.testnet
    ):
        raise PaperError(
            code=PaperErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE,
            message="paper-run requires testnet or simulator exchange in milestone 1",
        )


async def _startup_checked_request(request: PaperRunRequest) -> PaperRunRequest:
    if request.strategy_adapter is None:
        return request
    report = run_preflight(
        settings=request.settings,
        profile_name=default_profile_name(request.settings),
    )
    if report.blocked:
        raise PaperError(
            code=PaperErrorCode.PREFLIGHT_BLOCKED,
            message=_preflight_block_message(report),
        )
    if request.account_snapshot is not None:
        return request
    wallet = await fetch_wallet_balance(settings=request.settings)
    return replace(request, account_snapshot=_wallet_account_snapshot(wallet))


def _preflight_block_message(report: PreflightReport) -> str:
    blocked = tuple(check for check in report.checks if check.status is PreflightStatus.BLOCK)
    details = "; ".join(f"{check.code.value}: {check.message}" for check in blocked)
    return f"{report.profile}: {details}"


def _wallet_account_snapshot(wallet: WalletBalanceSnapshot) -> AccountSnapshot:
    match wallet.status:
        case WalletBalanceStatus.FETCHED:
            pass
        case (
            WalletBalanceStatus.BLOCKED
            | WalletBalanceStatus.UNAVAILABLE
            | WalletBalanceStatus.ERROR
        ):
            raise PaperError(
                code=PaperErrorCode.WALLET_BALANCE_UNAVAILABLE,
                message=f"{wallet.code.value}: {wallet.message}",
            )
        case unreachable:
            assert_never(unreachable)
    if wallet.captured_at is None or wallet.equity is None or wallet.available is None:
        raise PaperError(
            code=PaperErrorCode.WALLET_BALANCE_UNAVAILABLE,
            message=f"{wallet.code.value}: wallet balance payload is incomplete",
        )
    return AccountSnapshot(
        captured_at=wallet.captured_at,
        equity=StakeAmount(wallet.equity),
        available=StakeAmount(wallet.available),
        positions=(),
    )


def _exchange_ticks(ticks: tuple[PaperTick, ...]) -> tuple[Tick, ...]:
    return tuple(Tick(pair=tick.pair, price=tick.price, at=tick.at) for tick in ticks)
