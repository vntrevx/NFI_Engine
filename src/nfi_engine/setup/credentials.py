from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from nfi_engine.config.models import ExchangeSettings, RuntimeSettings
from nfi_engine.domain import MarginMode
from nfi_engine.setup.models import SetupIntent, SetupRequest

EXTRA_EXCHANGE_CREDENTIAL_FIELDS: Final = (
    "passphrase",
    "memo",
    "operator_id",
    "account_address",
    "api_wallet_signer",
)


def exchange_settings_from_request(
    request: SetupRequest,
    *,
    margin_mode: MarginMode | None,
) -> ExchangeSettings:
    return ExchangeSettings(
        name=request.exchange,
        trading_mode=request.trading_mode,
        margin_mode=margin_mode,
        testnet=request.intent is not SetupIntent.LIVE,
        api_key=request.api_key or None,
        api_secret=request.api_secret or None,
        passphrase=request.passphrase or None,
        memo=request.memo or None,
        operator_id=request.operator_id or None,
        account_address=request.account_address or None,
        api_wallet_signer=request.api_wallet_signer or None,
        permission_read=request.permission_read,
        permission_trade=request.permission_trade,
        permission_futures=request.permission_futures,
        permission_withdrawal=request.permission_withdrawal,
        permission_ip_allowlist=request.permission_ip_allowlist,
    )


def extra_exchange_config_lines(settings: RuntimeSettings) -> tuple[tuple[str, str], ...]:
    return tuple(
        (field, value)
        for field in EXTRA_EXCHANGE_CREDENTIAL_FIELDS
        if (value := _exchange_value(settings.exchange, field)) is not None
    )


def setup_credential_values(request: SetupRequest) -> tuple[str, ...]:
    return tuple(value for value in _request_credential_values(request) if value)


def _request_credential_values(request: SetupRequest) -> Iterable[str]:
    yield request.api_key
    yield request.api_secret
    yield request.passphrase
    yield request.memo
    yield request.operator_id
    yield request.account_address
    yield request.api_wallet_signer


def _exchange_value(exchange: ExchangeSettings, field: str) -> str | None:
    match field:
        case "passphrase":
            return exchange.passphrase
        case "memo":
            return exchange.memo
        case "operator_id":
            return exchange.operator_id
        case "account_address":
            return exchange.account_address
        case "api_wallet_signer":
            return exchange.api_wallet_signer
        case _:
            return None
