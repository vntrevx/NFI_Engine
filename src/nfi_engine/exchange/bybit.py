from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import NotRequired, Protocol, TypedDict, assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import (
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingPair,
)
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.models import ExchangeOrder, ExchangeOrderRequest, FundingRate


class CcxtOrderPayload(TypedDict):
    id: str
    symbol: str
    side: str
    type: str
    status: str
    amount: str
    average: str | None
    price: NotRequired[str | None]


class CcxtFundingPayload(TypedDict):
    symbol: str
    fundingRate: str


class CcxtClientProtocol(Protocol):
    def set_sandbox_mode(self, enabled: bool) -> None: ...

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: str,
        price: str | None,
    ) -> CcxtOrderPayload: ...

    async def cancel_order(self, order_id: str, symbol: str) -> CcxtOrderPayload: ...

    async def fetch_order(self, order_id: str, symbol: str) -> CcxtOrderPayload: ...

    async def fetch_funding_rate(self, symbol: str) -> CcxtFundingPayload: ...

    async def set_leverage(self, leverage: int, symbol: str) -> CcxtOrderPayload: ...


@dataclass(frozen=True, slots=True)
class BybitTestnetAdapter:
    client: CcxtClientProtocol

    @classmethod
    def from_settings(
        cls,
        *,
        settings: RuntimeSettings,
        client: CcxtClientProtocol | None,
    ) -> BybitTestnetAdapter:
        if not settings.exchange.testnet:
            raise ExchangeError(
                code=ExchangeErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE,
                message="Bybit adapter requires testnet=true in milestone 1",
            )
        if client is None:
            raise ExchangeError(
                code=ExchangeErrorCode.CCXT_CLIENT_REQUIRED,
                message="Bybit adapter requires an injected CCXT client in milestone 1",
            )
        client.set_sandbox_mode(True)
        return cls(client=client)

    async def create_order(self, request: ExchangeOrderRequest) -> ExchangeOrder:
        payload = await self.client.create_order(
            str(request.pair.normalized),
            request.order_type.value,
            _ccxt_side(request.side),
            str(request.quantity),
            None if request.price is None else str(request.price),
        )
        return _order_from_payload(payload=payload, request=request)

    async def cancel_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder:
        payload = await self.client.cancel_order(order_id, str(pair.normalized))
        return _order_from_payload(payload=payload, request=_request_from_payload(payload, pair))

    async def fetch_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder:
        payload = await self.client.fetch_order(order_id, str(pair.normalized))
        return _order_from_payload(payload=payload, request=_request_from_payload(payload, pair))

    async def fetch_funding_rate(self, pair: TradingPair) -> FundingRate:
        try:
            payload = await self.client.fetch_funding_rate(str(pair.normalized))
        except NotImplementedError:
            return FundingRate(pair=pair, rate=Decimal(0), supported=False)
        return FundingRate(pair=pair, rate=Decimal(payload["fundingRate"]), supported=True)

    async def set_leverage(self, pair: TradingPair, leverage: Leverage) -> Leverage:
        await self.client.set_leverage(int(leverage.value), str(pair.normalized))
        return leverage


def _order_from_payload(
    *,
    payload: CcxtOrderPayload,
    request: ExchangeOrderRequest,
) -> ExchangeOrder:
    return ExchangeOrder(
        order_id=payload["id"],
        pair=request.pair,
        side=request.side,
        order_type=request.order_type,
        state=_state_from_ccxt(payload["status"]),
        quantity=Quantity(Decimal(payload["amount"])),
        price=request.price,
        filled_price=_average_from_payload(payload),
        live_exchange=False,
    )


def _request_from_payload(payload: CcxtOrderPayload, pair: TradingPair) -> ExchangeOrderRequest:
    price = payload.get("price")
    return ExchangeOrderRequest(
        pair=pair,
        side=_position_side(payload["side"]),
        order_type=OrderType(payload["type"]),
        quantity=Quantity(Decimal(payload["amount"])),
        price=None if price is None else Price(Decimal(price)),
        leverage=Leverage.one(),
    )


def _ccxt_side(side: PositionSide) -> str:
    match side:
        case PositionSide.LONG:
            return "buy"
        case PositionSide.SHORT:
            return "sell"
        case unreachable:
            assert_never(unreachable)


def _position_side(side: str) -> PositionSide:
    match side:
        case "buy":
            return PositionSide.LONG
        case "sell":
            return PositionSide.SHORT
        case _:
            return PositionSide.LONG


def _state_from_ccxt(status: str) -> OrderState:
    match status:
        case "closed":
            return OrderState.FILLED
        case "open":
            return OrderState.OPEN
        case "canceled":
            return OrderState.CANCELED
        case "rejected":
            return OrderState.REJECTED
        case _:
            return OrderState.OPEN


def _average_from_payload(payload: CcxtOrderPayload) -> Price | None:
    average = payload["average"]
    if average is None:
        return None
    return Price(Decimal(average))
