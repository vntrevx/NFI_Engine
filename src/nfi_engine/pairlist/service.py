from __future__ import annotations

from decimal import Decimal
from typing import Final

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.pairlist.models import (
    MarketMetadata,
    PairlistPatchRequest,
    PairlistValidationResult,
    PairRejectionCode,
    RejectedPair,
)

DEFAULT_MARKETS: Final = (
    MarketMetadata(
        pair="BTC/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(250000000),
        volatility_pct=Decimal("0.05"),
        max_leverage=Decimal(10),
    ),
    MarketMetadata(
        pair="ETH/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(150000000),
        volatility_pct=Decimal("0.07"),
        max_leverage=Decimal(8),
    ),
    MarketMetadata(
        pair="DOGE/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(5000000),
        volatility_pct=Decimal("0.18"),
        max_leverage=Decimal(5),
    ),
    MarketMetadata(
        pair="SOL/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(250000),
        volatility_pct=Decimal("0.16"),
        max_leverage=Decimal(5),
    ),
    MarketMetadata(
        pair="ADA/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(3000000),
        volatility_pct=Decimal("0.35"),
        max_leverage=Decimal(5),
    ),
    MarketMetadata(
        pair="BNB/USDT:USDT",
        quote="USDT",
        futures=True,
        liquidity_usdt=Decimal(12000000),
        volatility_pct=Decimal("0.08"),
        max_leverage=Decimal(1),
    ),
    MarketMetadata(
        pair="LTC/USDT:USDT",
        quote="USDT",
        futures=False,
        liquidity_usdt=Decimal(4000000),
        volatility_pct=Decimal("0.10"),
        max_leverage=Decimal(1),
    ),
    MarketMetadata(
        pair="LTC/USDT",
        quote="USDT",
        futures=False,
        liquidity_usdt=Decimal(4000000),
        volatility_pct=Decimal("0.10"),
        max_leverage=Decimal(1),
    ),
)

type MarketIndex = dict[str, MarketMetadata]


def validate_pairlist(
    *,
    settings: RuntimeSettings,
    markets: tuple[MarketMetadata, ...] = DEFAULT_MARKETS,
) -> PairlistValidationResult:
    whitelist = _split_pairs(settings.pairlist.whitelist)
    blacklist = frozenset(_split_pairs(settings.pairlist.blacklist))
    market_index = _market_index(markets)
    accepted: list[str] = []
    rejected: list[RejectedPair] = []
    for pair in sorted(whitelist):
        reasons = _rejection_reasons(
            pair=pair,
            settings=settings,
            blacklist=blacklist,
            market=market_index.get(pair),
        )
        if reasons:
            rejected.append(RejectedPair(pair=pair, reasons=reasons))
        else:
            accepted.append(pair)
    return PairlistValidationResult(
        accepted_pairs=tuple(accepted),
        rejected_pairs=tuple(rejected),
    )


def preview_pairlist_patch(
    *,
    settings: RuntimeSettings,
    request: PairlistPatchRequest,
) -> PairlistValidationResult:
    pairlist = settings.pairlist.model_copy(
        update={
            "blacklist": request.blacklist,
            "whitelist": settings.pairlist.whitelist
            if request.whitelist is None
            else request.whitelist,
        },
    )
    return validate_pairlist(settings=settings.model_copy(update={"pairlist": pairlist}))


def _rejection_reasons(
    *,
    pair: str,
    settings: RuntimeSettings,
    blacklist: frozenset[str],
    market: MarketMetadata | None,
) -> tuple[PairRejectionCode, ...]:
    if _is_blacklisted(pair=pair, blacklist=blacklist):
        return (PairRejectionCode.BLACKLISTED,)
    if market is None:
        return (PairRejectionCode.UNSUPPORTED_PAIR,)
    reasons: list[PairRejectionCode] = []
    if market.quote != settings.pairlist.quote_asset:
        reasons.append(PairRejectionCode.QUOTE_MISMATCH)
    if settings.exchange.trading_mode is TradingMode.FUTURES and not market.futures:
        reasons.append(PairRejectionCode.FUTURES_NOT_SUPPORTED)
    if (
        settings.exchange.trading_mode is TradingMode.FUTURES
        and settings.risk.leverage > market.max_leverage
    ):
        reasons.append(PairRejectionCode.LEVERAGE_UNSUPPORTED)
    if market.liquidity_usdt < settings.pairlist.min_liquidity_usdt:
        reasons.append(PairRejectionCode.LIQUIDITY_TOO_LOW)
    if market.volatility_pct > settings.pairlist.max_volatility_pct:
        reasons.append(PairRejectionCode.VOLATILITY_TOO_HIGH)
    return tuple(reasons)


def _split_pairs(raw: str) -> tuple[str, ...]:
    return tuple(pair.strip() for pair in raw.split(",") if pair.strip() != "")


def _is_blacklisted(*, pair: str, blacklist: frozenset[str]) -> bool:
    return pair in blacklist or _compact_pair(pair) in blacklist


def _compact_pair(pair: str) -> str:
    return pair.split(":", maxsplit=1)[0]


def _market_index(markets: tuple[MarketMetadata, ...]) -> MarketIndex:
    return {market.pair: market for market in markets}
