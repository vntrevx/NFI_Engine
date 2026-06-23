from __future__ import annotations

from typing import Final

RUNTIME_CONTROL_SCRIPT: Final = """
<script>
const runtimeControlButtons = Array.from(document.querySelectorAll('[data-command]'));
const runtimeControlStates = Array.from(
  document.querySelectorAll('[data-testid="runtime-control-state"]')
);
const runtimeHealthStates = Array.from(
  document.querySelectorAll('[data-testid="runtime-health-state"]')
);
const botStateMetrics = Array.from(document.querySelectorAll('[data-testid="bot-state"] strong'));
const runtimeMsg = (key) => window.NFI_I18N?.[key] || key;
function runtimeCsrfHeaders() {
  const token = document.querySelector('meta[name="nfi-csrf-token"]')?.content || '';
  return token ? {'x-nfi-csrf-token': token} : {};
}
function setText(nodes, text) {
  nodes.forEach((node) => {
    node.textContent = text;
  });
}
async function runtimeJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}
function runtimeErrorText(response, payload) {
  if (payload.detail?.code) {
    const fallback = runtimeMsg('settings.runtime_control_blocked');
    return `${payload.detail.code}: ${payload.detail.message || fallback}`;
  }
  return `HTTP ${response.status}`;
}
function applyRuntimeControlPayload(payload) {
  setText(runtimeControlStates, payload.state || runtimeMsg('settings.runtime_control_blocked'));
  if (payload.state) {
    setText(botStateMetrics, payload.state);
  }
}
async function refreshRuntimeControl() {
  const response = await fetch('/api/v1/runtime/control', {credentials: 'same-origin'});
  const payload = await runtimeJson(response);
  if (!response.ok) {
    setText(runtimeControlStates, runtimeErrorText(response, payload));
    return;
  }
  applyRuntimeControlPayload(payload);
}
async function refreshRuntimeHealth() {
  const response = await fetch('/api/v1/runtime/health', {credentials: 'same-origin'});
  const payload = await runtimeJson(response);
  if (!response.ok) {
    setText(runtimeHealthStates, runtimeErrorText(response, payload));
    return;
  }
  const detail = payload.next_action ? `${payload.state}: ${payload.next_action}` : payload.state;
  setText(runtimeHealthStates, detail);
}
async function sendRuntimeCommand(command) {
  setText(runtimeControlStates, runtimeMsg('settings.runtime_control_loading'));
  const response = await fetch('/api/v1/runtime/control', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'content-type': 'application/json', ...runtimeCsrfHeaders()},
    body: JSON.stringify({command})
  });
  const payload = await runtimeJson(response);
  if (!response.ok) {
    setText(runtimeControlStates, runtimeErrorText(response, payload));
    await refreshRuntimeHealth();
    return;
  }
  applyRuntimeControlPayload(payload);
  await refreshRuntimeHealth();
}
runtimeControlButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const command = button.dataset.command || '';
    if (!command || button.disabled) {
      return;
    }
    sendRuntimeCommand(command);
  });
});
if (runtimeHealthStates.length) {
  refreshRuntimeControl();
  refreshRuntimeHealth();
}
</script>
"""
