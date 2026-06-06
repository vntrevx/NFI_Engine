from __future__ import annotations

from html import escape

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.assets import LOGS_SCRIPT, PAIRLIST_SCRIPT, SETTINGS_SCRIPT, STYLE
from nfi_engine.ui.pairlist import render_pairlist_panel
from nfi_engine.ui.readiness import render_readiness_panel
from nfi_engine.ui.settings_fields import render_settings_fields


def render_settings_page(
    *,
    settings: RuntimeSettings,
    readiness: PreflightReport | None = None,
    csrf_token: str = "",
) -> str:
    rows = render_settings_fields(settings)
    readiness_panel = render_readiness_panel(readiness)
    pairlist_panel = render_pairlist_panel(settings, read_only=settings.ui.read_only)
    readonly_panel = _readonly_panel(settings.ui.read_only)
    disabled = _disabled_attrs(settings.ui.read_only)
    return _document(
        title="NFI Engine Settings",
        csrf_token=csrf_token,
        body=f"""
<main data-testid="settings-root">
  <header>
    <div>
      <h1>NFI Engine</h1>
      <p>Local operator settings</p>
    </div>
    <nav><a href="/settings">Settings</a><a href="/logs">Logs</a></nav>
  </header>
  <div class="workspace">
    <section>
      <h2>Runtime-safe settings</h2>
      <form data-testid="settings-form" class="field-grid">{rows}</form>
      <div class="toolbar">
        <button type="button" data-testid="validate-button">Validate</button>
        <button data-testid="save-draft-button"{disabled} type="button">Save draft</button>
        <button data-testid="apply-button"{disabled} type="button" class="primary">Apply</button>
      </div>
      <div class="state" data-testid="validation-state">No validation run</div>
      <div class="state" data-testid="draft-state">No draft saved</div>
      <div class="audit" data-testid="audit-log">No config audit event</div>
    </section>
    {readonly_panel}
    {readiness_panel}
    {pairlist_panel}
    <section>
      <h2>Safety gates</h2>
      <div class="lock" data-testid="live-trading-locked">
        Live trading controls are locked in milestone 1.
      </div>
      <div class="toolbar">
        <button data-testid="restore-button"{disabled} type="button">Restore</button>
        <button data-testid="start-button"{disabled} type="button">Start</button>
        <button data-testid="stop-button"{disabled} type="button">Stop</button>
      </div>
    </section>
  </div>
</main>
{SETTINGS_SCRIPT}
{PAIRLIST_SCRIPT}
""",
    )


def render_logs_page(*, logs: tuple[LogEntryResponse, ...], csrf_token: str = "") -> str:
    rows = "\n".join(_log_row(log) for log in logs)
    return _document(
        title="NFI Engine Logs",
        csrf_token=csrf_token,
        body=f"""
<main data-testid="logs-root">
  <header>
    <div>
      <h1>NFI Engine</h1>
      <p>Recent logs and report bundle</p>
    </div>
    <nav><a href="/settings">Settings</a><a href="/logs">Logs</a></nav>
  </header>
  <div class="workspace">
    <section>
      <h2>Recent events</h2>
      <div class="log-tools">
        <label>Severity
          <select data-testid="severity-filter">
            <option value="">All</option>
            <option value="ERROR">Error</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>
        </label>
        <a
          data-testid="export-support-report"
          href="/api/v1/reports/support-bundle.zip"
          download="nfi-support-report.zip"
        >Export support report</a>
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Level</th><th>Code</th><th>Correlation</th><th>Summary</th>
          </tr>
        </thead>
        <tbody data-testid="log-rows">{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Error lookup</h2>
      <div class="log-tools">
        <input
          data-testid="error-search"
          value="CONFIG_VALIDATION_ERROR"
          aria-label="error code"
        >
        <button type="button" data-testid="lookup-button">Lookup</button>
      </div>
      <div class="state detail" data-testid="error-detail">Select an error code.</div>
    </section>
  </div>
</main>
{LOGS_SCRIPT}
""",
    )


def _document(*, title: str, body: str, csrf_token: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="nfi-csrf-token" content="{escape(csrf_token)}">
  <title>{escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>{body}</body>
</html>
"""


def _readonly_panel(read_only: bool) -> str:
    if not read_only:
        return ""
    return """
    <section data-testid="readonly-panel">
      <h2>Access</h2>
      <div class="lock" data-testid="readonly-reason">
        Read-only mode blocks changes. Settings, pairlists, backups, and runtime controls are
        inspection-only.
      </div>
    </section>
"""


def _disabled_attrs(read_only: bool) -> str:
    if not read_only:
        return ""
    return ' disabled title="Read-only mode blocks changes"'


def _log_row(log: LogEntryResponse) -> str:
    severity_class = "severity-error" if log.level.value == "ERROR" else ""
    return f"""
<tr>
  <td>{escape(log.at.isoformat())}</td>
  <td class="{severity_class}">{escape(log.level.value)}</td>
  <td>{escape(log.code)}</td>
  <td data-testid="correlation-id">{escape(log.correlation_id)}</td>
  <td>{escape(log.safe_summary)}</td>
</tr>
"""
