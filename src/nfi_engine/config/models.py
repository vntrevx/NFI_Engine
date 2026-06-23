from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from nfi_engine.config.enums import Locale, LogLevel, RiskProfileName
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState


class StrictConfigModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class EngineSettings(StrictConfigModel):
    live_trading: bool = False
    live_trading_confirmed: bool = False
    environment: str = "local"


class ExchangeSettings(StrictConfigModel):
    name: str = "simulator"
    trading_mode: TradingMode = TradingMode.SPOT
    margin_mode: MarginMode | None = None
    testnet: bool = True
    api_key: str | None = None
    api_secret: str | None = None
    permission_read: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_trade: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_futures: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_withdrawal: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_ip_allowlist: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN


class StrategySettings(StrictConfigModel):
    name: str = "AdapterSmokeStrategy"
    module: str = "nfi_engine.strategy.demo:AdapterSmokeStrategy"


class DatabaseSettings(StrictConfigModel):
    url: str = "sqlite+aiosqlite:///data/nfi_engine.sqlite3"


class RiskSettings(StrictConfigModel):
    risk_profile: RiskProfileName = RiskProfileName.BALANCED
    expert_risk_confirmed: bool = False
    stake_usdt: Decimal = Decimal(10)
    max_daily_loss_pct: Decimal = Decimal("0.05")
    allocation_cap_pct: Decimal = Decimal("0.10")
    leverage: Decimal = Decimal(1)
    max_leverage: Decimal = Decimal(5)
    liquidation_buffer: Decimal = Decimal("0.05")
    max_open_trades: int = 3
    stoploss_pct: Decimal = Decimal("0.10")
    minimal_roi: Decimal = Decimal("0.03")
    cooldown_seconds: int = 0
    locked_pairs: str = ""


class BacktestSettings(StrictConfigModel):
    timerange: str | None = None
    starting_balance_usdt: Decimal = Decimal(1000)
    stoploss_pct: Decimal = Decimal("0.10")
    fee_rate: Decimal = Decimal("0.001")
    slippage_rate: Decimal = Decimal(0)
    max_open_trades: int = 3


class PaperRunSettings(StrictConfigModel):
    enabled: bool = True
    max_events: int = 100


class ApiSettings(StrictConfigModel):
    host: str = "127.0.0.1"
    port: int = 18080
    auth_token: str | None = None
    csrf_enabled: bool = True
    session_ttl_seconds: int = 1800


class UiSettings(StrictConfigModel):
    enabled: bool = True
    read_only: bool = False
    locale: Locale = Locale.EN


class LoggingSettings(StrictConfigModel):
    level: LogLevel = LogLevel.INFO
    json_logs: bool = False


class PluginSettings(StrictConfigModel):
    enabled: bool = True
    roots: str = ""
    allow_groups: str = "strategy,exchange,risk,notifier,data"


class NotificationSettings(StrictConfigModel):
    enabled: bool = True
    jsonl_path: str = ".omo/evidence/notifications.jsonl"
    webhook_url: str | None = None
    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_api_base_url: str = "https://api.telegram.org"
    timeout_seconds: Decimal = Decimal(3)
    max_attempts: int = 2


class CircuitBreakerSettings(StrictConfigModel):
    enabled: bool = True
    max_daily_loss_usdt: Decimal = Decimal(50)
    max_drawdown_pct: Decimal = Decimal("0.20")
    max_consecutive_losses: int = 3
    max_stale_seconds: int = 300
    max_api_errors: int = 5
    max_slippage_pct: Decimal = Decimal("0.05")
    max_abs_funding_rate: Decimal = Decimal("0.01")
    manual_halt: bool = False
    manual_halt_file: str | None = None
    max_rejected_orders: int = 10
    emergency_exit_enabled: bool = False


DEFAULT_PAIRLIST_WHITELIST: Final = (
    "BTC/USDT:USDT,ETH/USDT:USDT,DOGE/USDT:USDT,SOL/USDT:USDT,"
    "ADA/USDT:USDT,BNB/USDT:USDT,LTC/USDT:USDT,XRP/USDT:USDT"
)


class PairlistSettings(StrictConfigModel):
    whitelist: str = DEFAULT_PAIRLIST_WHITELIST
    blacklist: str = ""
    quote_asset: str = "USDT"
    min_liquidity_usdt: Decimal = Decimal(1000000)
    max_volatility_pct: Decimal = Decimal("0.20")


class ReconciliationSettings(StrictConfigModel):
    required: bool = False
    fixture_path: str | None = None


class RuntimeSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="NFI_ENGINE__",
        env_nested_delimiter="__",
        extra="forbid",
        frozen=True,
    )

    engine: EngineSettings = EngineSettings()
    exchange: ExchangeSettings = ExchangeSettings()
    strategy: StrategySettings = StrategySettings()
    database: DatabaseSettings = DatabaseSettings()
    risk: RiskSettings = RiskSettings()
    backtest: BacktestSettings = BacktestSettings()
    paper_run: PaperRunSettings = PaperRunSettings()
    api: ApiSettings = ApiSettings()
    ui: UiSettings = UiSettings()
    logging: LoggingSettings = LoggingSettings()
    plugins: PluginSettings = PluginSettings()
    notifications: NotificationSettings = NotificationSettings()
    circuit_breakers: CircuitBreakerSettings = CircuitBreakerSettings()
    pairlist: PairlistSettings = PairlistSettings()
    reconciliation: ReconciliationSettings = ReconciliationSettings()
