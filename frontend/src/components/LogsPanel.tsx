import { Download, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { loadLogs, lookupError } from "../api";
import { useActionState } from "../hooks";
import { text } from "../i18n";
import type { Locale, LogEntry } from "../types";
import { ActionButton, Panel, Pill, StateBlock } from "./primitives";

const FALLBACK_LOGS: readonly LogEntry[] = [
  {
    at: new Date(0).toISOString(),
    level: "ERROR",
    code: "CONFIG_VALIDATION_ERROR",
    message: "Configuration validation failed.",
    correlation_id: "fallback",
    command: null,
    route: "/settings",
    safe_summary: "Configuration validation failed.",
    report_hint: "Open support report for redacted details.",
  },
  {
    at: new Date(0).toISOString(),
    level: "INFO",
    code: "API_STARTED",
    message: "API server started.",
    correlation_id: "fallback",
    command: null,
    route: "/",
    safe_summary: "API server started.",
    report_hint: "No action required.",
  },
];

export function LogsPanel(props: { locale: Locale }): ReactNode {
  const [severity, setSeverity] = useState("");
  const [logs, setLogs] = useState<readonly LogEntry[]>(FALLBACK_LOGS);
  const lookup = useActionState("idle");
  const refreshLogs = useCallback(async (nextSeverity: string) => {
    const response = await loadLogs(nextSeverity);
    setLogs(response.items.length === 0 ? FALLBACK_LOGS : response.items);
  }, []);

  useEffect(() => {
    void refreshLogs(severity);
  }, [refreshLogs, severity]);

  return (
    <main className="logs-layout" data-testid="logs-root">
      <header className="page-heading">
        <span className="eyebrow">{text(props.locale, "logs")}</span>
        <h1>{text(props.locale, "recentEvents")}</h1>
        <p>{logsLead(props.locale)}</p>
      </header>

      <Panel kicker="filter" title={text(props.locale, "severity")}>
        <div className="logs-toolbar">
          <select
            data-testid="severity-filter"
            onChange={(event) => setSeverity(event.target.value)}
            value={severity}
          >
            <option value="">ALL</option>
            <option value="ERROR">ERROR</option>
            <option value="WARN">WARN</option>
            <option value="INFO">INFO</option>
          </select>
          <ActionButton onClick={() => void lookup.run(() => lookupError("CONFIG_VALIDATION_ERROR"))} testId="lookup-button">
            <Search aria-hidden="true" size={16} />
            {text(props.locale, "lookup")}
          </ActionButton>
          <a
            className="action-button"
            data-testid="export-support-report"
            download="nfi-support-report.json"
            href="/api/v1/reports/support-bundle"
          >
            <Download aria-hidden="true" size={16} />
            {text(props.locale, "supportReport")}
          </a>
        </div>
      </Panel>

      <Panel kicker="event tape" title={text(props.locale, "eventTape")}>
        <div className="log-rows" data-testid="log-rows">
          {logs.map((item) => (
            <article className="log-row" key={`${item.code}-${item.correlation_id}-${item.at}`}>
              <Pill tone={item.level === "ERROR" ? "bad" : item.level === "WARN" ? "warn" : "info"}>
                {item.level}
              </Pill>
              <strong className="machine-code">{item.code}</strong>
              <span>{item.safe_summary}</span>
              <small>{item.route ?? item.command ?? "runtime"}</small>
            </article>
          ))}
        </div>
      </Panel>

      <Panel kicker="lookup" title="CONFIG_VALIDATION_ERROR">
        <StateBlock testId="error-detail">{lookup.state === "idle" ? "CONFIG_VALIDATION_ERROR" : lookup.state}</StateBlock>
      </Panel>
    </main>
  );
}

function logsLead(locale: Locale): string {
  if (locale === "ko") {
    return "기계 코드와 상관 ID는 언어를 바꿔도 그대로 유지됩니다.";
  }
  if (locale === "el") {
    return "Οι κωδικοί μηχανής και τα correlation ID μένουν σταθερά σε κάθε γλώσσα.";
  }
  return "Machine codes and correlation IDs stay stable across every language.";
}
