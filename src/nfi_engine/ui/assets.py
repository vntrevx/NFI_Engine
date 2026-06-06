from __future__ import annotations

from typing import Final

STYLE: Final = """
:root {
  color-scheme: light;
  --bg: #f5f7f6;
  --panel: #ffffff;
  --ink: #17201d;
  --muted: #5b6863;
  --line: #ccd6d1;
  --accent: #0f766e;
  --danger: #b42318;
  --warn: #9a6700;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Aptos, "Segoe UI", ui-sans-serif, system-ui, sans-serif;
  background: var(--bg);
  color: var(--ink);
}
main { max-width: 1160px; margin: 0 auto; padding: 24px; }
header { display: flex; align-items: end; justify-content: space-between; gap: 16px; }
h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); }
nav { display: flex; gap: 8px; }
nav a {
  color: var(--ink);
  border: 1px solid var(--line);
  padding: 8px 12px;
  text-decoration: none;
  background: var(--panel);
}
.workspace { display: grid; grid-template-columns: 1.15fr .85fr; gap: 18px; margin-top: 20px; }
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 16px;
}
h2 { font-size: 15px; margin: 0 0 12px; letter-spacing: 0; }
.field-grid { display: grid; grid-template-columns: minmax(170px, .55fr) 1fr 120px; gap: 10px; }
.field-row { display: contents; }
label, .field-note, th { font-size: 13px; color: var(--muted); }
input, select, button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: var(--ink);
  padding: 7px 9px;
  font: inherit;
}
input[type="checkbox"] { width: 18px; min-height: 18px; align-self: center; }
button { cursor: pointer; }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
button:disabled, input:disabled, select:disabled { opacity: .62; cursor: not-allowed; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.state, .audit, .lock {
  margin-top: 12px;
  border-left: 3px solid var(--accent);
  padding: 8px 10px;
  background: #eef8f6;
  color: var(--ink);
  min-height: 36px;
}
.lock { border-left-color: var(--warn); background: #fff8e1; }
.log-tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
.log-tools input { min-width: 260px; max-width: 100%; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; table-layout: fixed; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 7px; text-align: left; }
td { font-size: 13px; overflow-wrap: anywhere; }
.severity-error { color: var(--danger); font-weight: 700; }
.detail { min-height: 92px; white-space: pre-line; }
@media (max-width: 780px) {
  main { padding: 16px; }
  header, .workspace { display: block; }
  nav { margin-top: 12px; }
  section { margin-top: 14px; }
  .field-grid { grid-template-columns: 1fr; }
}
"""

SETTINGS_SCRIPT: Final = """
<script>
const form = document.querySelector('[data-testid="settings-form"]');
const validation = document.querySelector('[data-testid="validation-state"]');
const draftState = document.querySelector('[data-testid="draft-state"]');
const auditLog = document.querySelector('[data-testid="audit-log"]');
function csrfHeaders() {
  const token = document.querySelector('meta[name="nfi-csrf-token"]')?.content || '';
  return token ? {'x-nfi-csrf-token': token} : {};
}
function fields() {
  return Array.from(form.elements)
    .filter((item) => item.name && !item.disabled)
    .map((item) => ({
      path: item.name,
      value: item.type === 'checkbox' ? String(item.checked) : item.value
    }));
}
async function postConfig(path) {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'content-type': 'application/json', ...csrfHeaders()},
    body: JSON.stringify({fields: fields()})
  });
  if (!response.ok) {
    return {valid: false, errors: [`HTTP ${response.status}`]};
  }
  return response.json();
}
document.querySelector('[data-testid="validate-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/validate');
  validation.textContent = payload.valid ? 'Validation passed' : payload.errors.join('; ');
};
document.querySelector('[data-testid="save-draft-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/draft');
  draftState.textContent = payload.accepted ? `Draft saved: ${payload.draft_id}` : 'Draft rejected';
};
document.querySelector('[data-testid="apply-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/apply');
  const mode = payload.restart_required ? 'reload required' : 'runtime applied';
  auditLog.textContent = payload.applied ? `CONFIG_APPLIED ${mode}` : 'CONFIG_BLOCKED';
};
</script>
"""

PAIRLIST_SCRIPT: Final = (
    "<script>\n"
    "const pairlistBlacklist = document.querySelector('[data-testid=\"pairlist-blacklist\"]');\n"
    "const pairlistPreview = document.querySelector('[data-testid=\"pairlist-preview-state\"]');\n"
    "const pairlistAudit = document.querySelector('[data-testid=\"pairlist-audit-log\"]');\n"
    "async function postPairlist(path) {\n"
    "  const response = await fetch(path, {\n"
    "    method: 'POST',\n"
    "    headers: {'content-type': 'application/json', ...csrfHeaders()},\n"
    "    body: JSON.stringify({blacklist: pairlistBlacklist.value})\n"
    "  });\n"
    "  return response.json();\n"
    "}\n"
    "function pairlistSummary(payload) {\n"
    "  const rejected = payload.rejected_pairs.map((item) => "
    "`${item.pair}: ${item.reasons.join(',')}`);\n"
    "  const accepted = `accepted=${payload.accepted_pairs.join(',') || 'none'}`;\n"
    "  return [accepted, ...rejected].join('\\n');\n"
    "}\n"
    "const pairlistPreviewButton = document.querySelector("
    "'[data-testid=\"pairlist-preview-button\"]');\n"
    "const pairlistDraftButton = document.querySelector("
    "'[data-testid=\"pairlist-save-draft-button\"]');\n"
    "const pairlistApplyButton = document.querySelector("
    "'[data-testid=\"pairlist-apply-button\"]');\n"
    "if (pairlistBlacklist) {\n"
    "  pairlistPreviewButton.onclick = async () => {\n"
    "    const payload = await postPairlist('/api/v1/pairlist/preview');\n"
    "    pairlistPreview.textContent = pairlistSummary(payload);\n"
    "  };\n"
    "  pairlistDraftButton.onclick = async () => {\n"
    "    const payload = await postPairlist('/api/v1/pairlist/draft');\n"
    "    pairlistPreview.textContent = pairlistSummary(payload.preview);\n"
    "    pairlistAudit.textContent = payload.audit_event;\n"
    "  };\n"
    "  pairlistApplyButton.onclick = async () => {\n"
    "    const payload = await postPairlist('/api/v1/pairlist/apply');\n"
    "    pairlistPreview.textContent = pairlistSummary(payload.preview);\n"
    "    pairlistAudit.textContent = payload.audit_event;\n"
    "  };\n"
    "}\n"
    "</script>\n"
)

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
