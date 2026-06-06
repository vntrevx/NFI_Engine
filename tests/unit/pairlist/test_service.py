from __future__ import annotations

from decimal import Decimal

from nfi_engine.config.models import (
    ExchangeSettings,
    PairlistSettings,
    RiskSettings,
    RuntimeSettings,
)
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.pairlist import PairRejectionCode, validate_pairlist


def test_pairlist_validation_applies_filters_and_deterministic_order() -> None:
    # Given: futures settings with a broad whitelist and one explicit blacklist.
    settings = RuntimeSettings(
        pairlist=PairlistSettings(
            whitelist=(
                "ETH/USDT:USDT,BTC/USDT:USDT,DOGE/USDT:USDT,"
                "SOL/USDT:USDT,ADA/USDT:USDT,BNB/USDT:USDT,"
                "LTC/USDT:USDT,XRP/USDT:USDT"
            ),
            blacklist="DOGE/USDT:USDT",
            min_liquidity_usdt=Decimal(1000000),
            max_volatility_pct=Decimal("0.20"),
        ),
        exchange=ExchangeSettings(
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
        ),
        risk=RiskSettings(leverage=Decimal(2)),
    )

    # When: the pairlist is validated against fixture market metadata.
    result = validate_pairlist(settings=settings)

    # Then: accepted pairs are sorted and every rejection reason remains visible.
    rejected = {item.pair: item.reasons for item in result.rejected_pairs}
    assert result.accepted_pairs == ("BTC/USDT:USDT", "ETH/USDT:USDT")
    assert rejected["DOGE/USDT:USDT"] == (PairRejectionCode.BLACKLISTED,)
    assert PairRejectionCode.LIQUIDITY_TOO_LOW in rejected["SOL/USDT:USDT"]
    assert PairRejectionCode.VOLATILITY_TOO_HIGH in rejected["ADA/USDT:USDT"]
    assert PairRejectionCode.LEVERAGE_UNSUPPORTED in rejected["BNB/USDT:USDT"]
    assert PairRejectionCode.FUTURES_NOT_SUPPORTED in rejected["LTC/USDT:USDT"]
    assert PairRejectionCode.UNSUPPORTED_PAIR in rejected["XRP/USDT:USDT"]


def test_pairlist_spot_mode_allows_spot_pair_when_quote_matches() -> None:
    # Given: spot settings with a spot-only market.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(trading_mode=TradingMode.SPOT),
        pairlist=PairlistSettings(whitelist="LTC/USDT", blacklist=""),
    )

    # When: the pairlist is validated.
    result = validate_pairlist(settings=settings)

    # Then: spot eligibility does not require futures metadata.
    assert result.accepted_pairs == ("LTC/USDT",)
    assert result.rejected_pairs == ()


def test_pairlist_blacklist_matches_futures_pair_without_settle_suffix() -> None:
    # Given: futures settings where the UI submits the compact base/quote symbol.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
        ),
        pairlist=PairlistSettings(
            whitelist="DOGE/USDT:USDT",
            blacklist="DOGE/USDT",
        ),
    )

    # When: the pairlist is validated.
    result = validate_pairlist(settings=settings)

    # Then: the compact symbol still blocks the settled futures market.
    rejected = {item.pair: item.reasons for item in result.rejected_pairs}
    assert rejected["DOGE/USDT:USDT"] == (PairRejectionCode.BLACKLISTED,)
