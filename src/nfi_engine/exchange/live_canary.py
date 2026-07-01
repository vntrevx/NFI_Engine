from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from nfi_engine.config import RuntimeSettings
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.live_canary_checks import (
    LIVE_CANARY_CONFIRMATION_PHRASE,
    kill_switch_state,
    normalized_pair,
    static_preview_checks,
)
from nfi_engine.exchange.live_canary_freshness import age_seconds, freshness_check
from nfi_engine.exchange.live_canary_hash import live_canary_preview_hash
from nfi_engine.exchange.live_canary_models import (
    LiveCanaryCheck,
    LiveCanaryCheckCode,
    LiveCanaryCheckState,
    LiveCanaryPreview,
)
from nfi_engine.wallet import WalletPermissionAuditSnapshot


def build_live_canary_preview(
    *,
    settings: RuntimeSettings,
    config_path: Path | None = None,
    now: datetime | None = None,
) -> LiveCanaryPreview:
    generated_at = now if now is not None else datetime.now(UTC)
    canary = settings.live_canary
    checks = _preview_checks(settings=settings, now=generated_at)
    blockers = tuple(
        check.code.value for check in checks if check.state is LiveCanaryCheckState.BLOCK
    )
    notional = canary.canary_notional_usdt
    return LiveCanaryPreview(
        ready=blockers == (),
        preview_hash=live_canary_preview_hash(settings),
        exchange=settings.exchange.name,
        testnet=settings.exchange.testnet,
        production=not settings.exchange.testnet,
        trading_mode=canary.trading_mode.value if canary.trading_mode is not None else None,
        pair=normalized_pair(settings),
        order_type=canary.order_type.value if canary.order_type is not None else None,
        canary_notional_usdt=notional,
        leverage=canary.leverage,
        max_loss_estimate_usdt=_loss_estimate(settings, notional),
        fee_estimate_usdt=_fee_estimate(settings, notional),
        kill_switch_state=kill_switch_state(settings),
        reconciliation_captured_at=canary.reconciliation_captured_at,
        reconciliation_age_seconds=age_seconds(canary.reconciliation_captured_at, generated_at),
        wallet_balance_captured_at=canary.wallet_balance_captured_at,
        wallet_balance_age_seconds=age_seconds(canary.wallet_balance_captured_at, generated_at),
        rollback_command=_rollback_command(settings=settings, config_path=config_path),
        required_confirmation_phrase=LIVE_CANARY_CONFIRMATION_PHRASE,
        confirmation_phrase_matches=canary.confirmation_phrase == LIVE_CANARY_CONFIRMATION_PHRASE,
        credentials_present=missing_runtime_credential_fields(settings) == (),
        permission_summary=WalletPermissionAuditSnapshot.from_settings(settings).summary,
        adapter_constructed=False,
        order_would_be_submitted=False,
        checks=checks,
        blockers=blockers,
    )


def _preview_checks(*, settings: RuntimeSettings, now: datetime) -> tuple[LiveCanaryCheck, ...]:
    canary = settings.live_canary
    return (
        *static_preview_checks(settings),
        freshness_check(
            code=LiveCanaryCheckCode.RECONCILIATION_FRESHNESS,
            label="reconciliation",
            captured_at=canary.reconciliation_captured_at,
            max_stale_seconds=settings.circuit_breakers.max_stale_seconds,
            now=now,
        ),
        freshness_check(
            code=LiveCanaryCheckCode.WALLET_FRESHNESS,
            label="wallet_balance",
            captured_at=canary.wallet_balance_captured_at,
            max_stale_seconds=settings.circuit_breakers.max_stale_seconds,
            now=now,
        ),
    )


def _loss_estimate(settings: RuntimeSettings, notional: Decimal | None) -> Decimal | None:
    if notional is None or notional <= 0:
        return None
    return notional * settings.risk.stoploss_pct


def _fee_estimate(settings: RuntimeSettings, notional: Decimal | None) -> Decimal | None:
    if notional is None or notional <= 0 or settings.backtest.fee_rate < 0:
        return None
    return notional * settings.backtest.fee_rate


def _rollback_command(*, settings: RuntimeSettings, config_path: Path | None) -> str:
    halt_path = settings.circuit_breakers.manual_halt_file
    if halt_path is None or halt_path.strip() == "":
        return "set circuit_breakers.manual_halt=true before retrying live canary"
    config = str(config_path) if config_path is not None else "<config>"
    return (
        f"touch {halt_path} && uv run nfi-engine runtime-health check "
        f"--config {config} --format json"
    )
