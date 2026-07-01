export type Locale = "en" | "ko" | "el";
export type PageId = "home" | "settings" | "logs";
export type ApiMethod = "GET" | "POST";

export type BotState = "stopped" | "running" | "paused";

export interface DashboardAction {
  code: string;
  severity: string;
  title: string;
  detail: string;
  target: string;
}

export interface DashboardReadiness {
  profile: string;
  blocked: boolean;
  checks: readonly { code: string; status: string; message: string }[];
}

export interface DashboardSnapshot {
  generated_at: string;
  bot_state: string;
  trading_mode: string;
  exchange: string;
  actions: readonly DashboardAction[];
  readiness: DashboardReadiness;
  pairlist: { total: number; preview: readonly string[]; quote_asset: string };
  execution_signals: readonly { code: string; title: string; status: string; detail: string }[];
  account_truth: AccountTruth;
  equity_points: readonly { at: string; equity: string; available: string }[];
  price_points: readonly { pair: string; at: string; price: string }[];
  open_positions: readonly OpenPosition[];
  recent_trades: readonly RecentTrade[];
  closed_trade_summary: ClosedTradeSummary;
  recent_errors: readonly RecentError[];
  execution_intents: readonly ExecutionIntent[];
  open_execution_orders: readonly ExecutionOrder[];
  recent_execution_fills: readonly ExecutionFill[];
  recent_execution_events: readonly ExecutionEvent[];
}

export interface AccountTruth {
  balance: { equity: string; available: string; synced_at: string | null; stale: boolean };
  pnl: {
    open_profit: string | null;
    closed_profit: string;
    wins: number;
    losses: number;
    breakeven: number;
    stale_data: boolean;
    stale_pairs: readonly string[];
    confident_open_values: boolean;
  };
  exposure: {
    open_notional: string | null;
    account_exposure: string | null;
    exposure_pct: string | null;
    realized_quote_fees: string;
    partial_fills: number;
  };
  reconciliation: {
    status: string;
    trading_halted: boolean;
    mismatch_count: number;
    issue_codes: readonly string[];
    checked_at: string | null;
  };
}


export interface OpenPosition {
  position_id: string;
  pair: string;
  side: string;
  quantity: string;
  entry_price: string;
  leverage: string;
  updated_at: string;
}

export interface RecentTrade {
  trade_id: string;
  pair: string;
  side: string;
  state: string;
  opened_at: string;
  closed_at: string | null;
  profit: string;
}

export interface ClosedTradeSummary {
  closed_trades: number;
  wins: number;
  losses: number;
  profit: string;
}

export interface ExecutionIntent {
  intent_id: string;
  pair: string;
  side: string;
  state: string;
  requested_quantity: string;
  requested_price: string | null;
  updated_at: string;
}

export interface ExecutionOrder {
  execution_order_id: string;
  intent_id: string;
  pair: string;
  side: string;
  state: string;
  requested_quantity: string;
  requested_price: string | null;
  filled_quantity: string;
  average_fill_price: string | null;
  updated_at: string;
}

export interface ExecutionFill {
  execution_fill_id: string;
  intent_id: string;
  execution_order_id: string;
  pair: string;
  side: string;
  quantity: string;
  price: string;
  fee_asset: string | null;
  fee_amount: string | null;
  filled_at: string;
}

export interface ExecutionEvent {
  event_id: number | null;
  intent_id: string;
  event_type: string;
  state: string;
  message: string;
  raw_status_code: string | null;
  occurred_at: string;
}

export interface RecentError {
  at: string;
  code: string;
  safe_summary: string;
  correlation_id: string;
}

export interface ConfigCurrent {
  engine: { live_trading: boolean; live_trading_confirmed: boolean; environment: string };
  exchange: {
    name: string;
    trading_mode: string;
    margin_mode: string | null;
    testnet: boolean;
    api_key: string;
    api_secret: string;
  };
  risk: { stake_usdt: string; max_open_trades: number };
  ui: { locale: Locale; read_only: boolean };
  api: { host: string; port: number; operator_username: string; csrf_enabled: boolean };
}

export interface WalletBalance {
  status: string;
  code: string;
  exchange: string;
  trading_mode: string;
  captured_at: string | null;
  equity: string | null;
  available: string | null;
  quote_asset: string;
  position_count: number;
  allocation_cap_pct: string;
  allocation_cap: string | null;
  configured_stake_usdt: string;
  configured_max_open_trades: number;
  configured_allocation_total: string;
  allocation_cap_exceeded: boolean | null;
  permission_audit: {
    read: string;
    trade: string;
    futures: string;
    withdrawal: string;
    ip_allowlist: string;
    live_safe: boolean;
    live_blocking_codes: readonly string[];
    diagnostic_codes: readonly string[];
    summary: string;
  };
  next_action: string;
  message: string;
}

export interface RuntimeControl {
  previous_state: BotState;
  state: BotState;
  command: string | null;
  accepted: boolean;
  code: string;
  message: string;
  new_entries_allowed: boolean;
  runtime_health_state: string | null;
  next_action: string;
  live_orders_action: string;
}

export interface LogEntry {
  at: string;
  level: string;
  code: string;
  message: string;
  correlation_id: string;
  command: string | null;
  route: string | null;
  safe_summary: string;
  report_hint: string;
}

export interface LogList {
  items: readonly LogEntry[];
}

export interface SetupForm {
  exchange: string;
  trading_mode: "spot" | "futures";
  intent: "paper" | "testnet" | "live";
  api_key: string;
  api_secret: string;
  allocated_amount_usdt: string;
  locale: Locale;
}

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}
