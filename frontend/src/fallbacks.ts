import type { ConfigCurrent, DashboardSnapshot, RuntimeControl, WalletBalance } from "./types";

export const FALLBACK_DASHBOARD: DashboardSnapshot = {
  generated_at: new Date(0).toISOString(),
  bot_state: "stopped",
  trading_mode: "futures",
  exchange: "binance",
  actions: [
    {
      code: "SETUP_REVIEW_REQUIRED",
      severity: "warn",
      title: "Review setup",
      detail: "Connect exchange API, verify wallet balance, then run dry-run first.",
      target: "settings",
    },
  ],
  readiness: {
    profile: "local-paper",
    blocked: false,
    checks: [{ code: "LOCAL_READY", status: "warn", message: "Waiting for live data" }],
  },
  pairlist: { total: 0, preview: ["BTC/USDT:USDT", "ETH/USDT:USDT"], quote_asset: "USDT" },
  execution_signals: [
    {
      code: "DRY_RUN_FIRST",
      title: "Dry-run first",
      status: "warn",
      detail: "Live order path remains gated until testnet proof is complete.",
    },
  ],
  account_truth: {
    balance: { equity: "0", available: "0", synced_at: null, stale: true },
    pnl: {
      open_profit: null,
      closed_profit: "0",
      wins: 0,
      losses: 0,
      breakeven: 0,
      stale_data: true,
      stale_pairs: [],
      confident_open_values: false,
    },
    exposure: {
      open_notional: null,
      account_exposure: null,
      exposure_pct: null,
      realized_quote_fees: "0",
      partial_fills: 0,
    },
    reconciliation: {
      status: "missing",
      trading_halted: true,
      mismatch_count: 0,
      issue_codes: [],
      checked_at: null,
    },
  },
  equity_points: [
    { at: new Date(Date.now() - 180000).toISOString(), equity: "0", available: "0" },
    { at: new Date(Date.now() - 120000).toISOString(), equity: "0", available: "0" },
    { at: new Date(Date.now() - 60000).toISOString(), equity: "0", available: "0" },
  ],
  price_points: [],
  open_positions: [],
  recent_trades: [],
  closed_trade_summary: { closed_trades: 0, wins: 0, losses: 0, profit: "0" },
  recent_errors: [
    {
      at: new Date(0).toISOString(),
      code: "CONFIG_VALIDATION_ERROR",
      safe_summary: "No recent engine log loaded",
      correlation_id: "fallback",
    },
  ],
  execution_intents: [],
  open_execution_orders: [],
  recent_execution_fills: [],
  recent_execution_events: [],
};

export const FALLBACK_CONFIG: ConfigCurrent = {
  engine: { live_trading: false, live_trading_confirmed: false, environment: "local" },
  exchange: {
    name: "binance",
    trading_mode: "futures",
    margin_mode: "isolated",
    testnet: true,
    api_key: "REDACTED",
    api_secret: "REDACTED",
  },
  risk: { stake_usdt: "0", max_open_trades: 0 },
  ui: { locale: "en", read_only: false },
  api: { host: "127.0.0.1", port: 18180, operator_username: "", csrf_enabled: true },
};

export const FALLBACK_WALLET: WalletBalance = {
  status: "unknown",
  code: "WALLET_NOT_LOADED",
  exchange: "binance",
  trading_mode: "futures",
  captured_at: null,
  equity: null,
  available: null,
  quote_asset: "USDT",
  position_count: 0,
  allocation_cap_pct: "0",
  allocation_cap: null,
  configured_stake_usdt: "0",
  configured_max_open_trades: 0,
  configured_allocation_total: "0",
  allocation_cap_exceeded: null,
  permission_audit: {
    read: "unknown",
    trade: "unknown",
    futures: "unknown",
    withdrawal: "unknown",
    ip_allowlist: "unknown",
    live_safe: false,
    live_blocking_codes: ["WALLET_NOT_LOADED"],
    diagnostic_codes: ["WALLET_NOT_LOADED"],
    summary: "Wallet balance has not been fetched.",
  },
  next_action: "Open settings and fetch wallet balance.",
  message: "Wallet balance has not been fetched.",
};

export const FALLBACK_RUNTIME: RuntimeControl = {
  previous_state: "stopped",
  state: "stopped",
  command: null,
  accepted: true,
  code: "RUNTIME_CONTROL_STATE",
  message: "runtime control state snapshot",
  new_entries_allowed: false,
  runtime_health_state: null,
  next_action: "Use start, pause, resume, or stop through protected controls.",
  live_orders_action: "No live exchange order cancellation is performed by this control.",
};
