from __future__ import annotations

from nfi_engine.exchange.permissions import (
    ExchangeApiPermissionState,
    audit_exchange_api_permissions,
)


def test_permission_audit_blocks_live_when_withdrawal_is_enabled() -> None:
    # Given: an exchange key whose withdrawal permission is still enabled.
    audit = audit_exchange_api_permissions(
        read=ExchangeApiPermissionState.ENABLED,
        trade=ExchangeApiPermissionState.ENABLED,
        futures=ExchangeApiPermissionState.ENABLED,
        withdrawal=ExchangeApiPermissionState.ENABLED,
        ip_allowlist=ExchangeApiPermissionState.UNKNOWN,
    )

    # When: the live safety state is evaluated.
    live_blocking_codes = audit.live_blocking_codes

    # Then: live operation is blocked without leaking any credential values.
    assert audit.live_safe is False
    assert live_blocking_codes == ("EXCHANGE_WITHDRAWAL_PERMISSION_ENABLED",)
    assert "withdrawal=enabled" in audit.summary
    assert "secret" not in audit.summary.lower()


def test_permission_audit_allows_dry_run_inspection_when_withdrawal_unknown() -> None:
    # Given: a dry-run setup where the exchange does not expose every permission flag.
    audit = audit_exchange_api_permissions(
        read=ExchangeApiPermissionState.ENABLED,
        trade=ExchangeApiPermissionState.ENABLED,
        futures=ExchangeApiPermissionState.NOT_APPLICABLE,
        withdrawal=ExchangeApiPermissionState.UNKNOWN,
        ip_allowlist=ExchangeApiPermissionState.UNKNOWN,
    )

    # When: the audit is rendered for operator diagnostics.
    diagnostics = audit.diagnostic_codes

    # Then: the operator can inspect the unknown state without a live block.
    assert audit.live_safe is True
    assert diagnostics == ("EXCHANGE_PERMISSION_WITHDRAWAL_UNKNOWN",)
    assert audit.summary == (
        "read=enabled trade=enabled futures=not_applicable withdrawal=unknown ip_allowlist=unknown"
    )
