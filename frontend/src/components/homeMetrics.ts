import { text } from "../i18n";
import type {
  DashboardSnapshot,
  Locale,
  OpenPosition,
  RuntimeControl,
  WalletBalance,
} from "../types";

type Tone = "neutral" | "good" | "warn" | "bad" | "info";

export interface ComparisonMetrics {
  available: number;
  balance: number;
  closedProfit: number;
  closedProfitPct: number;
  exposure: number;
  exchangeLine: string;
  leverage: string;
  losses: number;
  maxTrades: number;
  openProfit: number;
  openProfitPct: number;
  openTrades: number;
  quoteAsset: string;
  runtimeLabel: string;
  runtimeTone: Tone;
  syncLabel: string;
  wins: number;
}

export function comparisonMetrics(
  snapshot: DashboardSnapshot,
  walletData: WalletBalance,
  runtimeData: RuntimeControl,
  locale: Locale,
): ComparisonMetrics {
  const prices = latestPrices(snapshot);
  const clientOpenProfit = snapshot.open_positions.reduce(
    (total, position) => total + positionProfit(position, prices.get(position.pair)),
    0,
  );
  const clientOpenNotional = snapshot.open_positions.reduce((total, position) => total + positionCost(position), 0);
  const truth = snapshot.account_truth;
  const openProfit =
    truth.pnl.open_profit === null ? clientOpenProfit : decimalNumber(truth.pnl.open_profit);
  const openNotional =
    truth.exposure.open_notional === null
      ? clientOpenNotional
      : decimalNumber(truth.exposure.open_notional);
  const balance = positiveOrFallback(
    walletData.equity,
    positiveOrFallbackText(truth.balance.equity, lastEquity(snapshot)),
  );
  return {
    available: positiveOrFallback(
      walletData.available,
      positiveOrFallbackText(truth.balance.available, lastAvailable(snapshot)),
    ),
    balance,
    closedProfit: decimalNumber(truth.pnl.closed_profit),
    closedProfitPct: percentOf(decimalNumber(truth.pnl.closed_profit), balance),
    exposure: decimalNumber(truth.exposure.account_exposure),
    exchangeLine: `${snapshot.exchange} ${snapshot.trading_mode}`,
    leverage: maxLeverageValue(snapshot),
    losses: truth.pnl.losses,
    maxTrades: Math.max(walletData.configured_max_open_trades, snapshot.open_positions.length),
    openProfit,
    openProfitPct: percentOf(openProfit, openNotional),
    openTrades: snapshot.open_positions.length,
    quoteAsset: walletData.quote_asset,
    runtimeLabel: runtimeData.state === "running" ? "running" : runtimeData.state,
    runtimeTone: snapshot.readiness.blocked ? "bad" : runtimeData.state === "running" ? "good" : "warn",
    syncLabel: walletSyncLabel(walletData, locale),
    wins: truth.pnl.wins,
  };
}

export function formatMoney(value: number, quoteAsset: string): string {
  return `${formatSignedNumber(value)} ${quoteAsset}`;
}

export function formatPercent(value: number): string {
  return `${formatSignedNumber(value).replace(/(\d+\.\d{2})\d$/, "$1")}%`;
}

export function profitBarWidth(value: number): string {
  const magnitude = Math.abs(value);
  if (magnitude === 0) {
    return "0%";
  }
  return `${Math.min(100, Math.max(6, magnitude * 2))}%`;
}

export function profitClass(value: number): string {
  if (value > 0) {
    return "profit-positive";
  }
  if (value < 0) {
    return "profit-negative";
  }
  return "profit-flat";
}

export function auditFlags(audit: WalletBalance["permission_audit"]): { label: string; value: string; tone: string }[] {
  return [
    { label: "read", value: audit.read, tone: auditTone(audit.read) },
    { label: "trade", value: audit.trade, tone: auditTone(audit.trade) },
    { label: "futures", value: audit.futures, tone: auditTone(audit.futures) },
    { label: "withdraw", value: audit.withdrawal, tone: auditTone(audit.withdrawal) },
    { label: "ip", value: audit.ip_allowlist, tone: auditTone(audit.ip_allowlist) },
  ];
}

export function liveGateLabel(walletData: WalletBalance, readinessBlocked: boolean): string {
  if (readinessBlocked || walletData.status !== "ready") {
    return "live gate locked";
  }
  if (walletData.permission_audit.live_safe) {
    return "credential audit clear";
  }
  return "review required";
}

function latestPrices(snapshot: DashboardSnapshot): Map<string, number> {
  const prices = new Map<string, number>();
  for (const point of snapshot.price_points) {
    prices.set(point.pair, decimalNumber(point.price));
  }
  return prices;
}

function positionProfit(position: OpenPosition, currentPrice: number | undefined): number {
  const entry = decimalNumber(position.entry_price);
  const quantity = decimalNumber(position.quantity);
  if (entry <= 0 || quantity <= 0 || currentPrice === undefined || currentPrice <= 0) {
    return 0;
  }
  const side = position.side.toLowerCase();
  const direction = side.includes("short") || side.includes("sell") ? -1 : 1;
  return (currentPrice - entry) * quantity * direction;
}

function positionCost(position: OpenPosition): number {
  const entry = decimalNumber(position.entry_price);
  const quantity = decimalNumber(position.quantity);
  const leverage = Math.max(1, decimalNumber(position.leverage));
  return entry > 0 && quantity > 0 ? (entry * quantity) / leverage : 0;
}


function decimalNumber(value: string | null | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function positiveOrFallback(primary: string | null, fallback: string): number {
  const value = decimalNumber(primary);
  return value > 0 ? value : decimalNumber(fallback);
}

function positiveOrFallbackText(primary: string, fallback: string): string {
  return decimalNumber(primary) > 0 ? primary : fallback;
}

function lastEquity(snapshot: DashboardSnapshot): string {
  return snapshot.equity_points.at(-1)?.equity ?? "0";
}

function lastAvailable(snapshot: DashboardSnapshot): string {
  return snapshot.equity_points.at(-1)?.available ?? "0";
}

function maxLeverageValue(snapshot: DashboardSnapshot): string {
  if (snapshot.open_positions.length === 0) {
    return "3";
  }
  return `${Math.max(...snapshot.open_positions.map((position) => decimalNumber(position.leverage)))}`;
}

function percentOf(value: number, base: number): number {
  return base > 0 ? (value / base) * 100 : 0;
}

function formatSignedNumber(value: number): string {
  const absolute = Math.abs(value).toFixed(3);
  if (value > 0) {
    return `+${absolute}`;
  }
  if (value < 0) {
    return `-${absolute}`;
  }
  return "0.000";
}

function walletSyncLabel(walletData: WalletBalance, locale: Locale): string {
  if (walletData.captured_at === null) {
    return text(locale, "walletSyncPending");
  }
  const capturedAt = new Date(walletData.captured_at);
  if (Number.isNaN(capturedAt.getTime())) {
    return text(locale, "walletSyncPending");
  }
  return `${text(locale, "walletSynced")} ${capturedAt.toLocaleTimeString(locale, { hour12: false })}`;
}

function auditTone(value: string): string {
  const normalized = value.toLowerCase();
  if (["ok", "allowed", "enabled", "true", "read"].some((token) => normalized.includes(token))) {
    return "good";
  }
  if (["denied", "disabled", "blocked", "false", "missing"].some((token) => normalized.includes(token))) {
    return "bad";
  }
  return "warn";
}
