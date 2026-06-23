from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from nfi_engine.api.state import ApiContext
from nfi_engine.api.wallet_models import WalletBalanceResponse
from nfi_engine.wallet import fetch_wallet_balance

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_wallet_routes(router: APIRouter, *, context: ApiContext) -> None:
    router.add_api_route("/wallet/balance", _wallet_balance(context), methods=["GET"])
    router.add_api_route("/wallet/balance/fetch", _wallet_balance(context), methods=["POST"])


def _wallet_balance(context: ApiContext) -> Callable[[], Awaitable[WalletBalanceResponse]]:
    async def endpoint() -> WalletBalanceResponse:
        snapshot = await fetch_wallet_balance(
            settings=context.settings,
            reader=context.wallet_balance_reader,
        )
        return WalletBalanceResponse.from_snapshot(snapshot)

    return endpoint
