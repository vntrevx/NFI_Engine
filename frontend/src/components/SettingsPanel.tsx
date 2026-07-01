import { ShieldCheck, Wallet } from "lucide-react";
import { useCallback, useState } from "react";
import type { ChangeEvent, ReactNode } from "react";

import {
  applyLocale,
  compactJson,
  draftConfig,
  fetchWallet,
  loadConfig,
  previewSetup,
  validateConfig,
} from "../api";
import { FALLBACK_CONFIG } from "../fallbacks";
import { useActionState, useAsyncResource } from "../hooks";
import { text } from "../i18n";
import type { Locale, SetupForm } from "../types";
import { ActionButton, Field, Panel, StateBlock } from "./primitives";
import { SettingsWorkPanels } from "./SettingsWorkPanels";

const EXCHANGES = ["binance", "bybit", "okx", "bitget", "kraken", "coinbase", "kucoin"];

export function SettingsPanel(props: { locale: Locale; onLocaleChange: (locale: Locale) => void }): ReactNode {
  const config = useAsyncResource(useCallback(loadConfig, []), FALLBACK_CONFIG);
  const [form, setForm] = useState<SetupForm>({
    exchange: config.data?.exchange.name ?? "binance",
    trading_mode: "futures",
    intent: "paper",
    api_key: "",
    api_secret: "",
    allocated_amount_usdt: "",
    locale: props.locale,
  });
  const [blacklist, setBlacklist] = useState("");
  const validation = useActionState("idle");
  const draft = useActionState("idle");
  const audit = useActionState("idle");
  const setup = useActionState("idle");
  const wallet = useActionState("idle");
  const update = useActionState("idle");
  const lifecycle = useActionState("idle");
  const pairlist = useActionState("idle");

  return (
    <main className="settings-layout" data-testid="settings-root">
      <header className="page-heading">
        <span className="eyebrow">{text(props.locale, "settings")}</span>
        <h1>{text(props.locale, "operatorSettings")}</h1>
        <p>{text(props.locale, "localLifecycle")} · {text(props.locale, "developerUpdate")}</p>
      </header>

      <Panel className="setup-panel" kicker={text(props.locale, "guidedPath")} title={text(props.locale, "firstRun")}>
        <div className="setup-grid">
          <Field label={text(props.locale, "exchange")} testId="setup-step-exchange">
            <select name="exchange" onChange={(event) => updateForm(setForm, "exchange", event)} value={form.exchange}>
              {EXCHANGES.map((exchange) => (
                <option key={exchange} value={exchange}>{exchange}</option>
              ))}
            </select>
          </Field>
          <Field label={text(props.locale, "apiKey")} testId="setup-step-api-key">
            <input id="setup-api-key" onChange={(event) => updateForm(setForm, "api_key", event)} value={form.api_key} />
          </Field>
          <Field label={text(props.locale, "apiSecret")} testId="setup-step-api-secret">
            <input
              id="setup-api-secret"
              onChange={(event) => updateForm(setForm, "api_secret", event)}
              type="password"
              value={form.api_secret}
            />
          </Field>
          <Field label={text(props.locale, "leverage")} testId="setup-step-leverage">
            <output data-testid="setup-recommended-leverage">{text(props.locale, "recommendedLeverage")}</output>
          </Field>
          <Field label={text(props.locale, "walletBalance")} testId="setup-step-wallet-balance">
            <div className="inline-action">
              <ActionButton onClick={() => void wallet.run(fetchWallet)} testId="wallet-fetch-button">
                <Wallet aria-hidden="true" size={16} />
                {text(props.locale, "fetch")}
              </ActionButton>
              <span data-testid="wallet-balance-state">{wallet.state}</span>
            </div>
          </Field>
          <Field label={text(props.locale, "allocatedAmount")} testId="setup-step-allocated-amount">
            <input
              id="setup-allocated-amount"
              inputMode="decimal"
              onChange={(event) => updateForm(setForm, "allocated_amount_usdt", event)}
              value={form.allocated_amount_usdt}
            />
          </Field>
          <Field label={text(props.locale, "marketMode")} testId="setup-step-market-mode">
            <select
              name="trading_mode"
              onChange={(event) => updateForm(setForm, "trading_mode", event)}
              value={form.trading_mode}
            >
              <option value="futures">{text(props.locale, "futures")}</option>
              <option value="spot">{text(props.locale, "spot")}</option>
            </select>
          </Field>
          <Field label={text(props.locale, "intent")} note={liveNote(props.locale)} testId="setup-step-intent">
            <select name="intent" onChange={(event) => updateForm(setForm, "intent", event)} value={form.intent}>
              <option value="paper">{text(props.locale, "dryRun")}</option>
              <option value="testnet">{text(props.locale, "testnet")}</option>
              <option value="live">{text(props.locale, "live")}</option>
            </select>
          </Field>
        </div>
        <div className="button-row">
          <ActionButton onClick={() => void setup.run(() => setupPreview(form))} testId="setup-preview-button">
            <ShieldCheck aria-hidden="true" size={16} />
            {text(props.locale, "preview")}
          </ActionButton>
        </div>
        <StateBlock testId="setup-preview-state">{setup.state}</StateBlock>
      </Panel>

      <Panel kicker={text(props.locale, "runtimeSafe")} title={text(props.locale, "config")}>
        <div className="settings-actions">
          <Field label={text(props.locale, "language")}>
            <select
              name="ui.locale"
              onChange={(event) => setForm((current) => ({ ...current, locale: event.target.value as Locale }))}
              value={form.locale}
            >
              <option value="en">English</option>
              <option value="ko">한국어</option>
              <option value="el">Ελληνικά</option>
            </select>
          </Field>
          <ActionButton onClick={() => void validation.run(validateConfig)} testId="validate-button">
            {text(props.locale, "validate")}
          </ActionButton>
          <ActionButton onClick={() => void draft.run(draftConfig)} testId="save-draft-button">
            {text(props.locale, "saveDraft")}
          </ActionButton>
          <ActionButton
            onClick={() => void applySelectedLocale(form.locale, props.onLocaleChange, audit.run)}
            testId="apply-button"
          >
            {text(props.locale, "apply")}
          </ActionButton>
        </div>
        <StateBlock testId="validation-state">{validation.state}</StateBlock>
        <StateBlock testId="draft-state">{draft.state}</StateBlock>
        <StateBlock testId="audit-log">{audit.state}</StateBlock>
      </Panel>

      <SettingsWorkPanels
        blacklist={blacklist}
        lifecycle={lifecycle}
        locale={props.locale}
        pairlist={pairlist}
        setBlacklist={setBlacklist}
        update={update}
      />
    </main>
  );
}

function updateForm<K extends keyof SetupForm>(
  setForm: (updater: (current: SetupForm) => SetupForm) => void,
  key: K,
  event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
): void {
  setForm((current) => ({ ...current, [key]: event.target.value }));
}

async function setupPreview(form: SetupForm): Promise<unknown> {
  const result = await previewSetup(form);
  if (form.intent !== "live") {
    return result;
  }
  return { live_gate: "LIVE_TRADING_REQUIRES_CONFIRMATION", result };
}

function applySelectedLocale(
  locale: Locale,
  onLocaleChange: (locale: Locale) => void,
  run: (action: () => Promise<unknown>) => Promise<void>,
): Promise<void> {
  return run(async () => {
    const result = await applyLocale(locale);
    document.documentElement.lang = locale;
    onLocaleChange(locale);
    return { applied: true, locale, response: compactJson(result) };
  });
}

function liveNote(locale: Locale): string {
  return text(locale, "liveSafetyNote");
}
