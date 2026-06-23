from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import NotRequired, Protocol, TypedDict, assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import (
    AccountSnapshot,
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    StakeAmount,
    TradingPair,
)
from nfi_engine.domain.primitives import DecimalInput
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


class CcxtBalancePayload(TypedDict):
    total: Mapping[str, DecimalInput | None]
    free: Mapping[str, DecimalInput | None]


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

    async def fetch_balance(self) -> CcxtBalancePayload: ...


@dataclass(frozen=True, slots=True)
class BybitTestnetAdapter:
    client: CcxtClientProtocol
    quote_asset: str

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
        return cls(client=client, quote_asset=settings.pairlist.quote_asset)

    async def fetch_balance(self) -> AccountSnapshot:
        payload = await self.client.fetch_balance()
        return AccountSnapshot(
            captured_at=datetime.now(UTC),
            equity=StakeAmount(_balance_amount(payload["total"], self.quote_asset)),
            available=StakeAmount(_balance_amount(payload["free"], self.quote_asset)),
            positions=(),
        )

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
        order_type=_order_type_from_ccxt(payload["type"]),
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
    match side.lower():
        case "buy":
            return PositionSide.LONG
        case "sell":
            return PositionSide.SHORT
        case _:
            raise ExchangeError(
                code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
                message=f"unknown ccxt order side: {side}",
            )


def _state_from_ccxt(status: str) -> OrderState:
    match status.lower():
        case "closed":
            return OrderState.FILLED
        case "open":
            return OrderState.OPEN
        case "partially_filled":
            return OrderState.PARTIALLY_FILLED
        case "canceled":
            return OrderState.CANCELED
        case "rejected":
            return OrderState.REJECTED
        case _:
            raise ExchangeError(
                code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
                message=f"unknown ccxt order status: {status}",
            )


def _order_type_from_ccxt(order_type: str) -> OrderType:
    try:
        return OrderType(order_type.lower())
    except ValueError as exc:
        raise ExchangeError(
            code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
            message=f"unknown ccxt order type: {order_type}",
        ) from exc


def _average_from_payload(payload: CcxtOrderPayload) -> Price | None:
    average = payload["average"]
    if average is None:
        return None
    return Price(Decimal(average))


def _balance_amount(values: Mapping[str, DecimalInput | None], asset: str) -> Decimal:
    raw_value = values.get(asset)
    if raw_value is None:
        return Decimal(0)
    try:
        amount = Decimal(str(raw_value))
    except InvalidOperation as exc:
        raise ExchangeError(
            code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
            message=f"invalid ccxt balance amount for {asset}",
        ) from exc
    if not amount.is_finite():
        raise ExchangeError(
            code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
            message=f"non-finite ccxt balance amount for {asset}",
        )
    return amount
