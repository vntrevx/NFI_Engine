from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from nfi_engine.config import RuntimeSettings

PASS_STATUSES: Final = frozenset({"pass", "passed"})
RECONCILIATION_PASS_STATUSES: Final = frozenset(
    {"clear", "cleared", "pass", "passed", "reconciled"}
)
ZERO: Final = Decimal(0)


class CanaryPassMarkerPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    live_canary_status: str
    generated_at: datetime
    config_hash: str
    preview_hash: str
    pair: str
    canary_notional_usdt: Decimal
    entry_order_id: str
    exit_order_id: str
    owner_approval_ref: str
    reduce_only_exit: bool
    wallet_before_after: bool
    rollback_receipt: bool
    final_reconciliation_status: str


def canary_pass_marker_blocker(
    *,
    settings: RuntimeSettings,
    now: datetime,
    pairs: tuple[str, ...],
) -> str | None:
    path_text = settings.restricted_live_pilot.canary_pass_marker_path
    if _blank(path_text):
        return "canary pass marker path is missing"
    path = Path(path_text or "")
    if not path.exists():
        return "canary pass marker is missing"
    try:
        marker_payload = CanaryPassMarkerPayload.model_validate_json(
            path.read_text(encoding="utf-8"),
        )
    except OSError:
        return "canary pass marker is unreadable"
    except ValidationError:
        return "canary pass marker is not sanitized"
    sanitization_blocker = _marker_sanitization_blocker(marker_payload, settings, pairs)
    if sanitization_blocker is not None:
        return sanitization_blocker
    return _marker_freshness_blocker(marker_payload, settings, now)


def _marker_sanitization_blocker(
    marker_payload: CanaryPassMarkerPayload,
    settings: RuntimeSettings,
    pairs: tuple[str, ...],
) -> str | None:
    blockers = (
        _marker_required_text_blocker(marker_payload),
        _marker_status_blocker(marker_payload),
        _marker_scope_blocker(marker_payload, settings, pairs),
        _marker_proof_blocker(marker_payload),
    )
    return next((blocker for blocker in blockers if blocker is not None), None)


def _marker_required_text_blocker(marker_payload: CanaryPassMarkerPayload) -> str | None:
    required_text = (
        marker_payload.config_hash,
        marker_payload.preview_hash,
        marker_payload.pair,
        marker_payload.entry_order_id,
        marker_payload.exit_order_id,
        marker_payload.owner_approval_ref,
    )
    if any(_blank(value) for value in required_text):
        return "canary pass marker is not sanitized"
    return None


def _marker_status_blocker(marker_payload: CanaryPassMarkerPayload) -> str | None:
    if marker_payload.live_canary_status.casefold() not in PASS_STATUSES:
        return "canary pass marker does not record pass status"
    if marker_payload.final_reconciliation_status.casefold() not in RECONCILIATION_PASS_STATUSES:
        return "canary pass marker does not record final reconciliation pass"
    return None


def _marker_scope_blocker(
    marker_payload: CanaryPassMarkerPayload,
    settings: RuntimeSettings,
    pairs: tuple[str, ...],
) -> str | None:
    if marker_payload.pair not in pairs:
        return "canary pass marker pair is outside restricted allowlist"
    if marker_payload.canary_notional_usdt <= ZERO:
        return "canary pass marker notional is invalid"
    pilot_stake = settings.restricted_live_pilot.stake_usdt
    if pilot_stake is not None and marker_payload.canary_notional_usdt > pilot_stake:
        return "canary pass marker notional exceeds restricted stake"
    return None


def _marker_proof_blocker(marker_payload: CanaryPassMarkerPayload) -> str | None:
    if (
        not marker_payload.reduce_only_exit
        or not marker_payload.wallet_before_after
        or not marker_payload.rollback_receipt
    ):
        return "canary pass marker is missing exit, wallet, or rollback proof"
    return None


def _marker_freshness_blocker(
    marker_payload: CanaryPassMarkerPayload,
    settings: RuntimeSettings,
    now: datetime,
) -> str | None:
    if (
        marker_payload.generated_at.tzinfo is None
        or marker_payload.generated_at.utcoffset() is None
    ):
        return "canary pass marker timestamp is not timezone-aware"
    if marker_payload.generated_at > now:
        return "canary pass marker timestamp is in the future"
    marker_age = _age_seconds(marker_payload.generated_at, now)
    max_age = settings.restricted_live_pilot.reconciliation_interval_seconds
    if max_age is not None and marker_age is not None and marker_age > max_age:
        return f"canary_marker_age_seconds={marker_age}"
    return None


def _age_seconds(value: datetime | None, now: datetime) -> int | None:
    if value is None:
        return None
    return max(0, int((now - value).total_seconds()))


def _blank(value: str | None) -> bool:
    return value is None or value.strip() == ""
