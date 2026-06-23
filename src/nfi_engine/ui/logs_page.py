from __future__ import annotations

from html import escape

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_logs_body(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    nav: str,
) -> str:
    locale = settings.ui.locale
    rows = "\n".join(_log_row(log) for log in logs)
    return f"""
<main data-testid="logs-root">
  <header>
    <div>
      <h1>NFI Engine</h1>
      <p>{localize(locale, MessageKey.LOGS_TITLE)}</p>
    </div>
    {nav}
  </header>
  <div class="workspace">
    <section>
      <h2>{localize(locale, MessageKey.LOGS_RECENT_EVENTS)}</h2>
      <div class="log-tools">
        <label>{localize(locale, MessageKey.LOGS_SEVERITY)}
          <select data-testid="severity-filter">
            <option value="">{localize(locale, MessageKey.COMMON_ALL)}</option>
            <option value="ERROR">{localize(locale, MessageKey.COMMON_ERROR)}</option>
            <option value="WARNING">{localize(locale, MessageKey.COMMON_WARNING)}</option>
            <option value="INFO">{localize(locale, MessageKey.COMMON_INFO)}</option>
          </select>
        </label>
        <a
          data-testid="export-support-report"
          href="/api/v1/reports/support-bundle.zip"
          download="nfi-support-report.zip"
        >{localize(locale, MessageKey.EXPORT_SUPPORT_REPORT)}</a>
      </div>
      <div class="table-scroll" data-testid="logs-table-scroll">
        <table class="logs-table">
          <thead>
            <tr>
              <th>{localize(locale, MessageKey.LOGS_TIME)}</th>
              <th>{localize(locale, MessageKey.LOGS_LEVEL)}</th>
              <th>{localize(locale, MessageKey.LOGS_CODE)}</th>
              <th>{localize(locale, MessageKey.LOGS_CORRELATION)}</th>
              <th>{localize(locale, MessageKey.LOGS_SUMMARY)}</th>
            </tr>
          </thead>
          <tbody data-testid="log-rows">{rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>{localize(locale, MessageKey.LOGS_ERROR_LOOKUP)}</h2>
      <div class="log-tools">
        <input
          data-testid="error-search"
          value="CONFIG_VALIDATION_ERROR"
          aria-label="{localize(locale, MessageKey.LOGS_ERROR_CODE_LABEL)}"
        >
        <button type="button" data-testid="lookup-button">
          {localize(locale, MessageKey.LOOKUP)}
        </button>
      </div>
      <div class="state detail" data-testid="error-detail">
        {localize(locale, MessageKey.LOGS_SELECT_ERROR_CODE)}
      </div>
    </section>
  </div>
</main>
"""


def _log_row(log: LogEntryResponse) -> str:
    severity_class = "severity-error" if log.level.value == "ERROR" else ""
    full_time = log.at.isoformat()
    display_time = _compact_log_time(full_time)
    return f"""
<tr>
  <td class="log-time" title="{escape(full_time)}">{escape(display_time)}</td>
  <td class="{severity_class}">{escape(log.level.value)}</td>
  <td class="machine-code">{escape(log.code)}</td>
  <td data-testid="correlation-id">{escape(log.correlation_id)}</td>
  <td>{escape(log.safe_summary)}</td>
</tr>
"""


def _compact_log_time(value: str) -> str:
    without_fraction = value.split(".", maxsplit=1)[0]
    return without_fraction.replace("T", " ", 1)[:19]
