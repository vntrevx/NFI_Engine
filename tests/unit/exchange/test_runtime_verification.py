from __future__ import annotations

from nfi_engine.config.models import EngineSettings, ExchangeSettings, RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capabilities import list_exchange_profiles
from nfi_engine.exchange.credential_requirements import required_runtime_credential_fields
from nfi_engine.exchange.mode_runtime_proofs import (
    MODE_RUNTIME_PROOFS,
    RuntimeProofChannel,
    RuntimeProofKind,
    runtime_proof_evidence,
)
from nfi_engine.exchange.official_requirements import get_official_requirement
from nfi_engine.exchange.profile_constants import BATCH_RUNTIME_EVIDENCE
from nfi_engine.exchange.runtime_verification import (
    ExchangeRuntimeCheck,
    ExchangeRuntimeCheckStatus,
    build_exchange_runtime_report,
    build_exchange_runtime_reports,
)
from nfi_engine.exchange.runtime_verification_evidence import (
    BATCH_RUNTIME_MODES,
    DRY_RUN_ENVIRONMENT_EVIDENCE,
    ORDER_LANE_EVIDENCE,
    READ_ONLY_BALANCE_EVIDENCE,
)


def test_bitvavo_runtime_report_blocks_until_operator_id_and_order_lane_exist() -> None:
    # Given
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="bitvavo",
            trading_mode=TradingMode.SPOT,
            api_key="key",
            api_secret="secret",  # noqa: S106 - test-only placeholder.
        ),
    )

    # When
    report = build_exchange_runtime_report(settings=settings)

    # Then
    checks = {check.stage: check for check in report.checks}
    assert report.exchange_id == "bitvavo"
    assert report.runtime_verified is True
    assert report.promotion_ready is False
    assert checks["official_requirements"].status is ExchangeRuntimeCheckStatus.PASS
    assert checks["credentials"].status is ExchangeRuntimeCheckStatus.BLOCK
    assert checks["credentials"].code == "RUNTIME_CREDENTIALS_MISSING"
    assert "operator_id" in checks["credentials"].next_action
    assert checks["order_lane"].status is ExchangeRuntimeCheckStatus.PASS


def test_all_registered_exchange_modes_are_promotion_ready_with_runtime_config() -> None:
    # Given
    report_targets = build_exchange_runtime_reports()

    # When
    reports = tuple(
        build_exchange_runtime_report(
            settings=_settings_for_runtime_report(report.exchange_id, report.trading_mode)
        )
        for report in report_targets
    )

    # Then
    assert len(reports) == len(report_targets)
    assert all(report.runtime_verified for report in reports)
    assert all(report.promotion_ready for report in reports)
    assert all(report.blockers == () for report in reports)
    assert all(_closed_statuses(report.checks) for report in reports)


def test_batch_runtime_evidence_covers_registered_modes_exactly() -> None:
    # Given
    registered_modes = {
        f"{profile.exchange_id}:{trading_mode.value}"
        for profile in list_exchange_profiles()
        for trading_mode in (TradingMode.SPOT, TradingMode.FUTURES)
        if profile.supports_trading_mode(trading_mode)
    }

    # When
    evidence_modes = set(BATCH_RUNTIME_MODES)

    # Then
    assert evidence_modes == registered_modes
    assert "generic-ccxt:spot" not in evidence_modes
    assert "generic-ccxt:futures" not in evidence_modes


def test_mode_runtime_proofs_are_mode_scoped_fixtures() -> None:
    # Given / When
    proofs = tuple(MODE_RUNTIME_PROOFS.values())

    # Then
    assert {proof.key for proof in proofs} == set(BATCH_RUNTIME_MODES)
    assert any(proof.kind is RuntimeProofKind.TEST_ORDER for proof in proofs)
    assert any(proof.kind is RuntimeProofKind.TESTNET_ADAPTER for proof in proofs)
    assert any(proof.kind is RuntimeProofKind.DETERMINISTIC_FIXTURE for proof in proofs)
    for proof in proofs:
        assert proof.key == f"{proof.exchange_id}:{proof.trading_mode.value}"
        assert proof.balance.asset.strip()
        assert proof.balance.wallet_surface.strip()
        assert proof.balance.permission.strip()
        assert proof.order.symbol.strip()
        assert proof.order.order_type == "limit"
        assert proof.order.safety.strip()
        if proof.exchange_id != "simulator":
            assert get_official_requirement(proof.exchange_id) is not None


def test_runtime_evidence_ledgers_are_closed_for_every_batch_mode() -> None:
    # Given
    expected_modes = set(BATCH_RUNTIME_MODES)

    # When
    balance_modes = set(READ_ONLY_BALANCE_EVIDENCE)
    order_modes = set(ORDER_LANE_EVIDENCE)
    environment_modes = set(DRY_RUN_ENVIRONMENT_EVIDENCE)

    # Then
    assert balance_modes == expected_modes
    assert order_modes == expected_modes
    assert environment_modes == expected_modes
    for mode in expected_modes:
        assert READ_ONLY_BALANCE_EVIDENCE[mode] == runtime_proof_evidence(
            mode,
            RuntimeProofChannel.READ_ONLY_BALANCE,
        )
        assert ORDER_LANE_EVIDENCE[mode] == runtime_proof_evidence(
            mode,
            RuntimeProofChannel.ORDER_LANE,
        )
        assert DRY_RUN_ENVIRONMENT_EVIDENCE[mode] == runtime_proof_evidence(
            mode,
            RuntimeProofChannel.TEST_ENVIRONMENT,
        )
        assert mode in READ_ONLY_BALANCE_EVIDENCE[mode]
        assert mode in ORDER_LANE_EVIDENCE[mode]
        assert mode in DRY_RUN_ENVIRONMENT_EVIDENCE[mode]
        assert "test_runtime_verification.py" not in READ_ONLY_BALANCE_EVIDENCE[mode]


def test_batch_profile_evidence_points_to_mode_runtime_proof_source() -> None:
    # Given
    batch_profiles = tuple(
        profile
        for profile in list_exchange_profiles()
        if profile.evidence == BATCH_RUNTIME_EVIDENCE
    )

    # Then
    assert batch_profiles
    assert BATCH_RUNTIME_EVIDENCE == "src/nfi_engine/exchange/mode_runtime_proofs.py"
    assert all(profile.support_level.value == "verified" for profile in batch_profiles)


def test_runtime_report_blocks_field_specific_required_credentials() -> None:
    # Given
    missing_field_cases = (
        ("bitvavo", TradingMode.SPOT, "operator_id"),
        ("bitget", TradingMode.SPOT, "passphrase"),
        ("hyperliquid", TradingMode.FUTURES, "api_wallet_signer"),
    )

    # When
    reports = tuple(
        build_exchange_runtime_report(
            settings=_settings_for_runtime_report(
                exchange_id=exchange_id,
                trading_mode=trading_mode,
                omitted_field=omitted_field,
            ),
        )
        for exchange_id, trading_mode, omitted_field in missing_field_cases
    )

    # Then
    for report, (_, _, omitted_field) in zip(reports, missing_field_cases, strict=True):
        checks = {check.stage: check for check in report.checks}
        assert report.runtime_verified is True
        assert report.promotion_ready is False
        assert checks["credentials"].status is ExchangeRuntimeCheckStatus.BLOCK
        assert checks["credentials"].code == "RUNTIME_CREDENTIALS_MISSING"
        assert omitted_field in checks["credentials"].next_action


def test_runtime_report_blocks_live_trading_as_promotion_proof() -> None:
    # Given
    settings = _settings_for_runtime_report("bitget", TradingMode.FUTURES).model_copy(
        update={"engine": EngineSettings(live_trading=True)},
    )

    # When
    report = build_exchange_runtime_report(settings=settings)

    # Then
    checks = {check.stage: check for check in report.checks}
    assert report.runtime_verified is True
    assert report.promotion_ready is False
    assert "LIVE_RUNTIME_DISABLED_FOR_PROMOTION" in report.blockers
    assert checks["test_environment"].status is ExchangeRuntimeCheckStatus.BLOCK


def test_binance_futures_runtime_report_is_promotion_ready_with_order_lane_evidence() -> None:
    # Given
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            testnet=True,
            api_key="key",
            api_secret="secret",  # noqa: S106 - test-only placeholder.
        ),
    )

    # When
    report = build_exchange_runtime_report(settings=settings)

    # Then
    checks = {check.stage: check for check in report.checks}
    assert report.exchange_id == "binance"
    assert report.runtime_verified is True
    assert report.promotion_ready is True
    assert report.blockers == ()
    assert checks["credentials"].status is ExchangeRuntimeCheckStatus.PASS
    assert checks["read_only_balance"].status is ExchangeRuntimeCheckStatus.PASS
    assert checks["order_lane"].status is ExchangeRuntimeCheckStatus.PASS


def test_all_runtime_reports_cover_each_supported_official_mode_without_generic() -> None:
    # Given / When
    reports = build_exchange_runtime_reports()

    # Then
    exchange_ids = {report.exchange_id for report in reports}
    assert "generic-ccxt" not in exchange_ids
    assert "simulator" in exchange_ids
    assert "bybit" in exchange_ids
    assert "bitvavo" in exchange_ids
    assert len(reports) == 21
    assert all(report.runtime_verified for report in reports)
    assert all(report.checks for report in reports)


def _settings_for_runtime_report(
    exchange_id: str,
    trading_mode: TradingMode,
    omitted_field: str | None = None,
) -> RuntimeSettings:
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name=exchange_id,
            trading_mode=trading_mode,
            testnet=True,
        ),
    )
    credentials = {
        field: f"{field}-fixture"
        for field in required_runtime_credential_fields(settings)
        if field != omitted_field
    }
    return settings.model_copy(
        update={
            "exchange": settings.exchange.model_copy(update=credentials),
        },
    )


def _closed_statuses(checks: tuple[ExchangeRuntimeCheck, ...]) -> bool:
    return all(
        check.status
        in (
            ExchangeRuntimeCheckStatus.PASS,
            ExchangeRuntimeCheckStatus.NOT_REQUIRED,
        )
        for check in checks
    )
