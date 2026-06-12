from __future__ import annotations

from typing import Final

LOGS_SCRIPT: Final = """
<script>
const rows = document.querySelector('[data-testid="log-rows"]');
const detail = document.querySelector('[data-testid="error-detail"]');
const severity = document.querySelector('[data-testid="severity-filter"]');
const search = document.querySelector('[data-testid="error-search"]');
const safe = (value) => String(value).replace(/[&<>]/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;'
}[c]));
function renderLogs(items) {
  rows.innerHTML = items.map((item) => `
    <tr>
      <td>${safe(item.at)}</td>
      <td class="${item.level === 'ERROR' ? 'severity-error' : ''}">${safe(item.level)}</td>
      <td>${safe(item.code)}</td>
      <td data-testid="correlation-id">${safe(item.correlation_id)}</td>
      <td>${safe(item.safe_summary)}</td>
    </tr>`).join('');
}
severity.onchange = async () => {
  const suffix = severity.value ? `?severity=${encodeURIComponent(severity.value)}` : '';
  const response = await fetch(`/api/v1/logs/recent${suffix}`);
  const payload = await response.json();
  renderLogs(payload.items);
};
document.querySelector('[data-testid="lookup-button"]').onclick = async () => {
  const code = encodeURIComponent(search.value || 'CONFIG_VALIDATION_ERROR');
  const response = await fetch(`/api/v1/errors/${code}`);
  const payload = await response.json();
  detail.textContent = [
    payload.code,
    payload.message,
    payload.correlation_id,
    payload.report_hint
  ].join('\\n');
};
</script>
"""
