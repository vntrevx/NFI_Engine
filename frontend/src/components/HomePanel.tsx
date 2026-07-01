import { Pause, Play, RotateCcw, Square } from "lucide-react";
import { useCallback } from "react";
import type { ReactNode } from "react";

import {
  loadDashboard,
  loadRuntimeControl,
  loadRuntimeHealth,
  loadWallet,
  postRuntimeCommand,
} from "../api";
import { FALLBACK_DASHBOARD, FALLBACK_RUNTIME, FALLBACK_WALLET } from "../fallbacks";
import { useActionState, useAsyncResource } from "../hooks";
import { text } from "../i18n";
import type { AccountTruth, Locale } from "../types";
import {
  auditFlags,
  comparisonMetrics,
  formatMoney,
  formatPercent,
  liveGateLabel,
  profitBarWidth,
  profitClass,
} from "./homeMetrics";
import { ActionButton, Pill } from "./primitives";

const BOT_NAME = "X7";
const HOME_REFRESH_MS = 10_000;

export function HomePanel(props: { locale: Locale }): ReactNode {
  const dashboard = useAsyncResource(useCallback(loadDashboard, []), FALLBACK_DASHBOARD, HOME_REFRESH_MS);
  const wallet = useAsyncResource(useCallback(loadWallet, []), FALLBACK_WALLET, HOME_REFRESH_MS);
  const runtime = useAsyncResource(useCallback(loadRuntimeControl, []), FALLBACK_RUNTIME, HOME_REFRESH_MS);
  useAsyncResource(useCallback(loadRuntimeHealth, []), null, HOME_REFRESH_MS);

  const runtimeAction = useActionState("ready");
  const snapshot = dashboard.data ?? FALLBACK_DASHBOARD;
  const walletData = wallet.data ?? FALLBACK_WALLET;
  const runtimeData = runtime.data ?? FALLBACK_RUNTIME;
  const metrics = comparisonMetrics(snapshot, walletData, runtimeData, props.locale);
  const nextAction = snapshot.actions[0] ?? null;
  const auditItems = auditFlags(walletData.permission_audit);

  return (
    <main className="home-grid home-grid-comparison" data-testid="home-root">
      <section className="bot-comparison-panel" data-testid="operator-cockpit">
        <header className="bot-comparison-header">
          <div>
            <h1>{text(props.locale, "botComparison")}</h1>
            <p>
              {snapshot.exchange} / {snapshot.trading_mode} / {walletData.quote_asset}
            </p>
          </div>
          <div className="bot-comparison-state">
            <Pill tone={metrics.runtimeTone} testId="cockpit-runtime-health">
              {metrics.runtimeLabel}
            </Pill>
            <span>{metrics.syncLabel}</span>
          </div>
        </header>

        <div className="comparison-table" data-testid="dashboard-primary-stack" role="table">
          <div className="comparison-row comparison-head" role="row">
            <span>{text(props.locale, "botName")}</span>
            <span>{text(props.locale, "trades")}</span>
            <span>{text(props.locale, "openProfit")}</span>
            <span>{text(props.locale, "closedProfit")}</span>
            <span>{text(props.locale, "balance")}</span>
            <span>{text(props.locale, "winLoss")}</span>
          </div>

          <div className="comparison-row comparison-live" role="row">
            <div className="bot-name-cell">
              <strong>{BOT_NAME}</strong>
              <span>{metrics.exchangeLine}</span>
              <small data-testid="cockpit-leverage">max {metrics.leverage}x</small>
            </div>
            <div className="number-cell" data-testid="open-trades">
              <strong>{metrics.openTrades} / {metrics.maxTrades}</strong>
              <span>{text(props.locale, "positions")}</span>
            </div>
            <ProfitCell
              percent={metrics.openProfitPct}
              quoteAsset={metrics.quoteAsset}
              testId="session-pnl"
              value={metrics.openProfit}
            />
            <ProfitCell
              percent={metrics.closedProfitPct}
              quoteAsset={metrics.quoteAsset}
              testId="cockpit-configured"
              value={metrics.closedProfit}
            />
            <div className="number-cell balance-cell" data-testid="cockpit-wallet-balance">
              <strong>{formatMoney(metrics.balance, metrics.quoteAsset)}</strong>
              <span>{formatMoney(metrics.available, metrics.quoteAsset)} available</span>
            </div>
            <div className="number-cell">
              <strong>{metrics.wins} / {metrics.losses}</strong>
              <span>closed trades</span>
            </div>
          </div>

          <div className="comparison-row comparison-summary" role="row">
            <strong>{text(props.locale, "summary")}</strong>
            <span>{metrics.openTrades} active</span>
            <span>{formatMoney(metrics.openProfit, metrics.quoteAsset)}</span>
            <span>{formatMoney(metrics.closedProfit, metrics.quoteAsset)}</span>
            <span>{formatMoney(metrics.balance, metrics.quoteAsset)} live</span>
            <span>{metrics.wins} / {metrics.losses}</span>
          </div>
        </div>
      </section>

      <section className="home-ops-panel" data-testid="dashboard-ops-rail">
        <div className="action-card" data-testid="action-item">
          <span>{nextAction?.code ?? walletData.code}</span>
          <strong data-testid="cockpit-next-action">{walletData.next_action}</strong>
        </div>
        <div className="gate-list compact-gates">
          <div>
            <span>latest error</span>
            <strong data-testid="cockpit-latest-error">{snapshot.recent_errors[0]?.code ?? "NO_RECENT_ERROR"}</strong>
          </div>
          <div>
            <span>live gate</span>
            <strong data-testid="cockpit-capability-level">{liveGateLabel(walletData, snapshot.readiness.blocked)}</strong>
          </div>
          <div>
            <span>account truth</span>
            <strong data-testid="account-truth-status">{accountTruthLabel(snapshot.account_truth)}</strong>
          </div>
          <div>
            <span>exposure</span>
            <strong data-testid="account-exposure">{formatMoney(metrics.exposure, metrics.quoteAsset)}</strong>
          </div>
        </div>
        <div className="audit-grid compact-audit" data-testid="cockpit-permission-audit">
          {auditItems.map((item) => (
            <div className={`audit-cell audit-${item.tone}`} key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
        <div className="signal-list compact-signals" data-testid="execution-safety-signals">
          {snapshot.execution_signals.map((signal) => (
            <Pill key={signal.code} tone={signalTone(signal.status)}>
              {signal.code}
            </Pill>
          ))}
        </div>
      </section>

      <section className="runtime-strip" data-testid="runtime-controls">
        <div className="runtime-row">
          <Pill tone={runtimeData.state === "running" ? "good" : "warn"}>{runtimeData.state}</Pill>
          <span>{runtimeAction.state}</span>
        </div>
        <p className="runtime-copy">{runtimeData.next_action}</p>
        <div className="runtime-buttons">
          <RuntimeButton command="start" icon={<Play size={16} />} run={runtimeAction.run} />
          <RuntimeButton command="pause" icon={<Pause size={16} />} run={runtimeAction.run} />
          <RuntimeButton command="resume" icon={<RotateCcw size={16} />} run={runtimeAction.run} />
          <RuntimeButton command="stop" icon={<Square size={16} />} run={runtimeAction.run} />
        </div>
      </section>
    </main>
  );
}

function ProfitCell(props: { percent: number; quoteAsset: string; testId: string; value: number }): ReactNode {
  return (
    <div className={`profit-cell ${profitClass(props.value)}`} data-testid={props.testId}>
      <strong>
        {formatPercent(props.percent)} ({formatMoney(props.value, props.quoteAsset)})
      </strong>
      <span className="profit-track" aria-hidden="true">
        <i style={{ width: profitBarWidth(props.percent) }} />
      </span>
    </div>
  );
}

function RuntimeButton(props: {
  command: string;
  icon: ReactNode;
  run: (action: () => Promise<unknown>) => Promise<void>;
}): ReactNode {
  return (
    <ActionButton command={props.command} onClick={() => void props.run(() => postRuntimeCommand(props.command))}>
      {props.icon}
      {props.command}
    </ActionButton>
  );
}

type SignalTone = "neutral" | "good" | "warn" | "bad" | "info";

function accountTruthLabel(truth: AccountTruth): string {
  const balance = truth.balance.stale ? "balance stale" : "balance synced";
  return `${truth.reconciliation.status} / ${balance}`;
}

function signalTone(status: string): SignalTone {
  if (status === "pass") {
    return "good";
  }
  if (status === "blocked") {
    return "bad";
  }
  if (status === "warn") {
    return "warn";
  }
  return "info";
}
