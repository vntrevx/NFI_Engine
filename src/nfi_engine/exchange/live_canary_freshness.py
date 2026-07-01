from __future__ import annotations

from datetime import UTC, datetime

from nfi_engine.exchange.live_canary_models import (
    LiveCanaryCheck,
    LiveCanaryCheckCode,
    LiveCanaryCheckState,
)


def freshness_check(
    *,
    code: LiveCanaryCheckCode,
    label: str,
    captured_at: datetime | None,
    max_stale_seconds: int,
    now: datetime,
) -> LiveCanaryCheck:
    if captured_at is None:
        return _block(code, f"{label}_captured_at=missing", f"Capture fresh {label} proof.")
    normalized = aware(captured_at)
    age = int((now - normalized).total_seconds())
    if age < 0:
        return _block(code, f"{label}_captured_at=future", "Fix system clock skew.")
    if age > max_stale_seconds:
        return _block(
            code,
            f"{label}_age_seconds={age}",
            f"Refresh {label} proof before live canary preview.",
        )
    return _clear(code, f"{label}_age_seconds={age}", f"No {label} freshness action required.")


def age_seconds(captured_at: datetime | None, now: datetime) -> int | None:
    if captured_at is None:
        return None
    return int((now - aware(captured_at)).total_seconds())


def aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _clear(code: LiveCanaryCheckCode, message: str, next_action: str) -> LiveCanaryCheck:
    return LiveCanaryCheck(
        code=code,
        state=LiveCanaryCheckState.CLEAR,
        message=message,
        next_action=next_action,
    )


def _block(code: LiveCanaryCheckCode, message: str, next_action: str) -> LiveCanaryCheck:
    return LiveCanaryCheck(
        code=code,
        state=LiveCanaryCheckState.BLOCK,
        message=message,
        next_action=next_action,
    )
