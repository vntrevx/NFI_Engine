from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from nfi_engine.config import load_runtime_settings
from nfi_engine.config.models import CircuitBreakerSettings, RuntimeSettings
from nfi_engine.exchange.live_canary import build_live_canary_preview
from nfi_engine.exchange.live_canary_models import LiveCanaryCheckCode

FIXTURE = Path("tests/fixtures/config/live-canary-preview.yaml")
NOW = datetime(2026, 6, 30, 0, 1, tzinfo=UTC)


def test_live_canary_preview_is_ready_only_when_explicit_gates_are_clear() -> None:
    # Given: an explicit owner-style live canary preview fixture.
    settings = load_runtime_settings(FIXTURE)

    # When: the preview is built.
    preview = build_live_canary_preview(settings=settings, config_path=FIXTURE, now=NOW)

    # Then: the command remains read-only while reporting the complete canary plan.
    assert preview.ready is True
    assert preview.production is True
    assert preview.testnet is False
    assert preview.exchange == "binance"
    assert preview.pair == "BTC/USDT:USDT"
    assert preview.trading_mode == "futures"
    assert preview.order_type == "market"
    assert preview.canary_notional_usdt == Decimal("7.50")
    assert preview.leverage == Decimal(2)
    assert preview.max_loss_estimate_usdt == Decimal("0.1500")
    assert preview.fee_estimate_usdt == Decimal("0.00750")
    assert preview.kill_switch_state == "armed"
    assert preview.reconciliation_age_seconds == 60
    assert preview.wallet_balance_age_seconds == 60
    assert preview.confirmation_phrase_matches is True
    assert preview.credentials_present is True
    assert preview.adapter_constructed is False
    assert preview.order_would_be_submitted is False
    assert preview.blockers == ()


def test_live_canary_preview_blocks_missing_confirmation_without_constructing_adapter() -> None:
    # Given: every field except the explicit confirmation phrase.
    settings = _settings_with_canary(confirmation_phrase=None)

    # When
    preview = build_live_canary_preview(settings=settings, config_path=FIXTURE, now=NOW)

    # Then
    assert preview.ready is False
    assert LiveCanaryCheckCode.REQUIRED_FIELDS.value in preview.blockers
    assert LiveCanaryCheckCode.CONFIRMATION.value in preview.blockers
    assert preview.confirmation_phrase_matches is False
    assert preview.adapter_constructed is False
    assert preview.order_would_be_submitted is False


def test_live_canary_preview_blocks_stale_reconciliation() -> None:
    # Given: reconciliation proof older than the configured freshness budget.
    stale = NOW - timedelta(seconds=1_000_000_000)
    settings = _settings_with_canary(reconciliation_captured_at=stale)

    # When
    preview = build_live_canary_preview(settings=settings, config_path=FIXTURE, now=NOW)

    # Then
    assert preview.ready is False
    assert LiveCanaryCheckCode.RECONCILIATION_FRESHNESS.value in preview.blockers
    assert preview.adapter_constructed is False
    assert preview.order_would_be_submitted is False


def test_live_canary_preview_blocks_active_manual_halt_file(tmp_path: Path) -> None:
    # Given: the configured kill-switch file already exists.
    halt_file = tmp_path / "manual-halt"
    halt_file.write_text("halt\n", encoding="utf-8")
    settings = load_runtime_settings(FIXTURE).model_copy(
        update={
            "circuit_breakers": CircuitBreakerSettings(
                manual_halt_file=str(halt_file),
                max_stale_seconds=999999999,
            ),
        },
    )

    # When
    preview = build_live_canary_preview(settings=settings, config_path=FIXTURE, now=NOW)

    # Then
    assert preview.ready is False
    assert preview.kill_switch_state == "blocked-halt-file"
    assert LiveCanaryCheckCode.MANUAL_HALT.value in preview.blockers


def test_live_canary_preview_redacts_secret_values_from_json() -> None:
    # Given
    settings = load_runtime_settings(FIXTURE)

    # When
    payload = build_live_canary_preview(
        settings=settings, config_path=FIXTURE, now=NOW
    ).model_dump_json()

    # Then
    assert "local-live-canary-key" not in payload
    assert "local-live-canary-secret" not in payload
    assert "credentials_present" in payload


def _settings_with_canary(**updates: object) -> RuntimeSettings:
    settings = load_runtime_settings(FIXTURE)
    return settings.model_copy(
        update={"live_canary": settings.live_canary.model_copy(update=updates)},
    )
