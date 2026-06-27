from __future__ import annotations

from decimal import Decimal
from html import escape

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import Locale, LogLevel, RuntimeSettings
from nfi_engine.dashboard import DashboardAction
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.discovery import build_exchange_capability_report
from nfi_engine.exchange.errors import ExchangeError
from nfi_engine.exchange.permissions import audit_exchange_api_permissions
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.home_context import HomeRuntimeContext
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.wallet import WalletBalanceStatus


def render_home_cockpit(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    actions: tuple[DashboardAction, ...],
    locale: Locale,
    runtime: HomeRuntimeContext | None = None,
) -> str:
    resolved_runtime = runtime or HomeRuntimeContext()
    items = "\n".join(
        _cockpit_items(
            settings,
            logs,
            actions,
            locale=locale,
            runtime=resolved_runtime,
        ),
    )
    return f"""
    <section data-testid="operator-cockpit" class="cockpit">
      <h2>{localize(locale, MessageKey.HOME_COCKPIT_TITLE)}</h2>
      <div class="cockpit-grid">
        {items}
      </div>
    </section>
"""


def _cockpit_items(
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    actions: tuple[DashboardAction, ...],
    *,
    locale: Locale,
    runtime: HomeRuntimeContext,
) -> tuple[str, ...]:
    return (
        _item(
            "cockpit-configured",
            localize(locale, MessageKey.HOME_COCKPIT_CONFIGURED),
            _configured(settings, locale=locale),
        ),
        _item(
            "cockpit-safety",
            localize(locale, MessageKey.HOME_COCKPIT_SAFETY),
            _safety(settings, runtime.readiness, locale=locale),
        ),
        _item(
            "cockpit-capability-level",
            localize(locale, MessageKey.HOME_COCKPIT_CAPABILITY_LEVEL),
            _capability_level(settings),
        ),
        _item(
            "cockpit-active-mode",
            localize(locale, MessageKey.HOME_COCKPIT_ACTIVE_MODE),
            _active_mode(settings, locale=locale),
        ),
        _item(
            "cockpit-runtime-health",
            localize(locale, MessageKey.HOME_COCKPIT_RUNTIME_HEALTH),
            _runtime_health(runtime, locale=locale),
        ),
        _item(
            "cockpit-wallet-balance",
            localize(locale, MessageKey.HOME_COCKPIT_WALLET_BALANCE),
            _wallet_balance(runtime, locale=locale),
        ),
        _item(
            "cockpit-allocated-amount",
            localize(locale, MessageKey.HOME_COCKPIT_ALLOCATED_AMOUNT),
            f"{_decimal(settings.risk.stake_usdt)} USDT",
        ),
        _item(
            "cockpit-leverage",
            localize(locale, MessageKey.HOME_COCKPIT_LEVERAGE),
            f"{_decimal(settings.risk.leverage)}x",
        ),
        _item(
            "cockpit-risk-profile",
            localize(locale, MessageKey.HOME_COCKPIT_RISK_PROFILE),
            settings.risk.risk_profile.value,
        ),
        _item(
            "cockpit-permission-audit",
            localize(locale, MessageKey.HOME_COCKPIT_PERMISSION_AUDIT),
            _permission_audit(settings),
        ),
        _item(
            "cockpit-latest-error",
            localize(locale, MessageKey.HOME_COCKPIT_LATEST_ERROR),
            _latest_error(logs, locale=locale),
        ),
        _item(
            "cockpit-next-action",
            localize(locale, MessageKey.HOME_COCKPIT_NEXT_ACTION),
            _next_action(actions, locale=locale),
        ),
        _item(
            "cockpit-where-next",
            localize(locale, MessageKey.HOME_COCKPIT_WHERE_NEXT),
            localize(locale, MessageKey.HOME_COCKPIT_GO_SETTINGS),
        ),
    )


def _item(test_id: str, label: str, value: str) -> str:
    return (
        f'<div class="cockpit-item" data-testid="{escape(test_id)}">'
        f"<span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
    )


def _configured(settings: RuntimeSettings, *, locale: Locale) -> str:
    if not missing_runtime_credential_fields(settings):
        return localize(locale, MessageKey.HOME_COCKPIT_CREDENTIALS_READY)
    return localize(locale, MessageKey.HOME_COCKPIT_CREDENTIALS_MISSING)


def _safety(
    settings: RuntimeSettings,
    readiness: PreflightReport | None,
    *,
    locale: Locale,
) -> str:
    blocked = settings.engine.live_trading or (
        readiness.blocked if readiness is not None else False
    )
    if blocked:
        return localize(locale, MessageKey.HOME_COCKPIT_BLOCKED)
    return localize(locale, MessageKey.HOME_COCKPIT_SAFE)


def _capability_level(settings: RuntimeSettings) -> str:
    try:
        report = build_exchange_capability_report(
            exchange_id=settings.exchange.name,
            trading_mode=settings.exchange.trading_mode,
        )
    except ExchangeError:
        return "generic-unverified"
    return report.profile.support_level.value


def _permission_audit(settings: RuntimeSettings) -> str:
    audit = audit_exchange_api_permissions(
        read=settings.exchange.permission_read,
        trade=settings.exchange.permission_trade,
        futures=settings.exchange.permission_futures,
        withdrawal=settings.exchange.permission_withdrawal,
        ip_allowlist=settings.exchange.permission_ip_allowlist,
    )
    if audit.live_safe:
        return audit.summary
    return f"blocked: {audit.summary}"


def _latest_error(logs: tuple[LogEntryResponse, ...], *, locale: Locale) -> str:
    errors = tuple(log for log in logs if log.level is LogLevel.ERROR)
    if not errors:
        return localize(locale, MessageKey.COMMON_NONE)
    return errors[0].code


def _next_action(actions: tuple[DashboardAction, ...], *, locale: Locale) -> str:
    if not actions:
        return localize(locale, MessageKey.HOME_ACTION_EMPTY)
    return actions[0].title


def _wallet_balance(runtime: HomeRuntimeContext, *, locale: Locale) -> str:
    snapshot = runtime.wallet_balance
    if snapshot is None:
        return localize(locale, MessageKey.HOME_COCKPIT_WALLET_NOT_FETCHED)
    if (
        snapshot.status is WalletBalanceStatus.FETCHED
        and snapshot.available is not None
        and snapshot.equity is not None
    ):
        return (
            f"{_decimal(snapshot.available)} / {_decimal(snapshot.equity)} {snapshot.quote_asset}"
        )
    return f"{snapshot.code.value}: {snapshot.next_action}"


def _runtime_health(runtime: HomeRuntimeContext, *, locale: Locale) -> str:
    snapshot = runtime.runtime_health
    if snapshot is None:
        return localize(locale, MessageKey.HOME_COCKPIT_RUNTIME_UNKNOWN)
    return f"{snapshot.state.value}: {snapshot.next_action}"


def _active_mode(settings: RuntimeSettings, *, locale: Locale) -> str:
    venue = (
        localize(locale, MessageKey.HOME_VALUE_TESTNET)
        if settings.exchange.testnet
        else localize(locale, MessageKey.HOME_VALUE_LIVE_VENUE)
    )
    return f"{settings.exchange.trading_mode.value} / {venue}"


def _decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered
