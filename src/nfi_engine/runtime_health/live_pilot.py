from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nfi_engine.config import RuntimeSettings
from nfi_engine.runtime_health.live_pilot_marker import canary_pass_marker_blocker
from nfi_engine.runtime_health.live_pilot_models import (
    RestrictedLivePilotCode,
    RestrictedLivePilotStatus,
)
from nfi_engine.runtime_health.models import (
    RuntimeHealthCheck,
    RuntimeHealthCode,
    RuntimeHealthState,
)


def evaluate_restricted_live_pilot(
    *,
    settings: RuntimeSettings,
    now: datetime,
) -> RestrictedLivePilotStatus:
    pilot = settings.restricted_live_pilot
    pairs = _pairs(pilot.pair_allowlist)
    if not pilot.enabled:
        return _status(
            enabled=False,
            state=RuntimeHealthState.HEALTHY,
            code=RestrictedLivePilotCode.DISABLED,
            message="restricted live pilot is disabled",
            next_action="No restricted live pilot action required.",
            settings=settings,
            pairs=pairs,
        )
    marker_blocker = canary_pass_marker_blocker(settings=settings, now=now, pairs=pairs)
    if marker_blocker is not None:
        return _blocked(RestrictedLivePilotCode.CANARY_MARKER, marker_blocker, settings, pairs)
    field_blocker = _field_blocker(settings)
    if field_blocker is not None:
        return _blocked(RestrictedLivePilotCode.REQUIRED_FIELDS, field_blocker, settings, pairs)
    freshness_blocker = _freshness_blocker(settings, now)
    if freshness_blocker is not None:
        return _blocked(RestrictedLivePilotCode.FRESHNESS, freshness_blocker, settings, pairs)
    breaker_blocker = _breaker_blocker(settings)
    if breaker_blocker is not None:
        return _blocked(RestrictedLivePilotCode.BREAKER, breaker_blocker, settings, pairs)
    return _status(
        enabled=True,
        state=RuntimeHealthState.HEALTHY,
        code=RestrictedLivePilotCode.READY,
        message="restricted live pilot dry-run harness is gated and ready",
        next_action="Run only after owner-approved live canary evidence is attached.",
        settings=settings,
        pairs=pairs,
    )


def live_pilot_health_check(status: RestrictedLivePilotStatus) -> RuntimeHealthCheck:
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.LIVE_PILOT,
        state=status.state,
        message=f"{status.code.value}: {status.message}",
        next_action=status.next_action,
    )


def _field_blocker(settings: RuntimeSettings) -> str | None:
    missing = _required_field_issues(settings)
    pilot = settings.restricted_live_pilot
    if pilot.max_open_trades is None or pilot.leverage is None:
        return "restricted live pilot numeric bounds are missing"
    if missing:
        return f"missing_or_invalid={','.join(missing)}"
    if pilot.max_open_trades > settings.risk.max_open_trades:
        return "max_open_trades exceeds risk.max_open_trades"
    if pilot.leverage is not None and pilot.leverage > settings.risk.max_leverage:
        return "leverage exceeds risk.max_leverage"
    return None


def _required_field_issues(settings: RuntimeSettings) -> tuple[str, ...]:
    pilot = settings.restricted_live_pilot
    return tuple(
        field
        for field, missing in (
            ("pair_allowlist", not _pairs(pilot.pair_allowlist)),
            ("stake_usdt", pilot.stake_usdt is None or pilot.stake_usdt <= 0),
            ("leverage", pilot.leverage is None or pilot.leverage <= 0),
            (
                "max_open_trades",
                pilot.max_open_trades is None or pilot.max_open_trades <= 0,
            ),
            (
                "max_daily_loss_usdt",
                pilot.max_daily_loss_usdt is None or pilot.max_daily_loss_usdt <= 0,
            ),
            ("manual_halt_file", _blank(pilot.manual_halt_file)),
            (
                "reconciliation_interval_seconds",
                pilot.reconciliation_interval_seconds is None
                or pilot.reconciliation_interval_seconds <= 0,
            ),
            (
                "wallet_sync_interval_seconds",
                pilot.wallet_sync_interval_seconds is None
                or pilot.wallet_sync_interval_seconds <= 0,
            ),
            (
                "runtime_duration_seconds",
                pilot.runtime_duration_seconds is None or pilot.runtime_duration_seconds <= 0,
            ),
        )
        if missing
    )


def _freshness_blocker(settings: RuntimeSettings, now: datetime) -> str | None:
    pilot = settings.restricted_live_pilot
    reconciliation_age = _age_seconds(pilot.reconciliation_captured_at, now)
    if reconciliation_age is None:
        return "reconciliation proof timestamp is missing"
    if (
        pilot.reconciliation_interval_seconds is not None
        and reconciliation_age > pilot.reconciliation_interval_seconds
    ):
        return f"reconciliation_age_seconds={reconciliation_age}"
    wallet_age = _age_seconds(pilot.wallet_balance_captured_at, now)
    if wallet_age is None:
        return "wallet proof timestamp is missing"
    if (
        pilot.wallet_sync_interval_seconds is not None
        and wallet_age > pilot.wallet_sync_interval_seconds
    ):
        return f"wallet_age_seconds={wallet_age}"
    return None


def _breaker_blocker(settings: RuntimeSettings) -> str | None:
    pilot = settings.restricted_live_pilot
    breakers = settings.circuit_breakers
    if not breakers.enabled:
        return "circuit breakers are disabled"
    if breakers.manual_halt:
        return "manual halt is enabled"
    halt_file = pilot.manual_halt_file
    if _blank(halt_file):
        return "manual halt file is missing"
    if Path(halt_file or "").exists():
        return "manual halt file is active"
    return None


def _blocked(
    code: RestrictedLivePilotCode,
    message: str,
    settings: RuntimeSettings,
    pairs: tuple[str, ...],
) -> RestrictedLivePilotStatus:
    return _status(
        enabled=settings.restricted_live_pilot.enabled,
        state=RuntimeHealthState.BLOCKED,
        code=code,
        message=message,
        next_action="Keep restricted live pilot stopped until this blocker clears.",
        settings=settings,
        pairs=pairs,
    )


def _status(  # noqa: PLR0913
    *,
    enabled: bool,
    state: RuntimeHealthState,
    code: RestrictedLivePilotCode,
    message: str,
    next_action: str,
    settings: RuntimeSettings,
    pairs: tuple[str, ...],
) -> RestrictedLivePilotStatus:
    return RestrictedLivePilotStatus(
        enabled=enabled,
        state=state,
        code=code,
        message=message,
        next_action=next_action,
        canary_pass_marker_path=settings.restricted_live_pilot.canary_pass_marker_path,
        pair_allowlist=pairs,
    )


def _pairs(raw: str) -> tuple[str, ...]:
    return tuple(pair.strip() for pair in raw.split(",") if pair.strip())


def _age_seconds(value: datetime | None, now: datetime) -> int | None:
    if value is None:
        return None
    return max(0, int((now - value).total_seconds()))


def _blank(value: str | None) -> bool:
    return value is None or value.strip() == ""
