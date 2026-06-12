from __future__ import annotations

from typing import Final

SETTINGS_SCRIPT: Final = """
<script>
const form = document.querySelector('[data-testid="settings-form"]');
const setupForm = document.querySelector('[data-testid="setup-form"]');
const validation = document.querySelector('[data-testid="validation-state"]');
const draftState = document.querySelector('[data-testid="draft-state"]');
const auditLog = document.querySelector('[data-testid="audit-log"]');
const setupState = document.querySelector('[data-testid="setup-preview-state"]');
const msg = (key) => window.NFI_I18N?.[key] || key;
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
function setupPayload() {
  return Object.fromEntries(
    Array.from(setupForm.elements)
      .filter((item) => item.name)
      .map((item) => [item.name, item.value])
  );
}
async function responsePayload(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}
function errorMessages(response, payload) {
  if (payload.detail?.code) {
    return [`${payload.detail.code}: ${payload.detail.message}`];
  }
  if (Array.isArray(payload.errors) && payload.errors.length) {
    return payload.errors;
  }
  return [`HTTP ${response.status}`];
}
async function postConfig(path) {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'content-type': 'application/json', ...csrfHeaders()},
    body: JSON.stringify({fields: fields()})
  });
  const payload = await responsePayload(response);
  if (!response.ok) {
    return {
      valid: false,
      applied: false,
      accepted: false,
      errors: errorMessages(response, payload)
    };
  }
  return payload;
}
async function fetchCurrentConfig() {
  const response = await fetch('/api/v1/config/current');
  const payload = await responsePayload(response);
  if (!response.ok) {
    throw new Error(errorMessages(response, payload).join('; '));
  }
  return payload;
}
function currentValue(payload, path) {
  return path.split('.').reduce((item, key) => item?.[key], payload);
}
function refreshForm(payload) {
  Array.from(form.elements)
    .filter((item) => item.name && !item.disabled)
    .forEach((item) => {
      const value = currentValue(payload, item.name);
      if (value === undefined || value === null) {
        return;
      }
      if (item.type === 'checkbox') {
        item.checked = value === true;
        return;
      }
      item.value = String(value);
    });
}
document.querySelector('[data-testid="validate-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/validate');
  validation.textContent = payload.valid
    ? msg('settings.validation_passed')
    : payload.errors.join('; ');
};
document.querySelector('[data-testid="save-draft-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/draft');
  draftState.textContent = payload.accepted
    ? `${msg('settings.draft_saved')}: ${payload.draft_id}`
    : msg('settings.draft_rejected');
};
document.querySelector('[data-testid="apply-button"]').onclick = async () => {
  const payload = await postConfig('/api/v1/config/apply');
  let mode = msg('settings.fix_settings');
  if (payload.applied) {
    mode = msg('settings.runtime_applied');
  }
  if (!payload.applied && payload.restart_required) {
    mode = msg('settings.reload_required');
  }
  if (payload.applied) {
    refreshForm(await fetchCurrentConfig());
  }
  const detail = payload.errors?.length ? `: ${payload.errors.join('; ')}` : '';
  auditLog.textContent = payload.applied
    ? `CONFIG_APPLIED ${mode}`
    : `CONFIG_BLOCKED ${mode}${detail}`;
};
document.querySelector('[data-testid="setup-preview-button"]').onclick = async () => {
  const response = await fetch('/api/v1/setup/preview', {
    method: 'POST',
    headers: {'content-type': 'application/json'},
    body: JSON.stringify(setupPayload())
  });
  const payload = await responsePayload(response);
  if (!response.ok) {
    setupState.textContent = errorMessages(response, payload).join('; ');
    return;
  }
  setupState.textContent = payload.valid ? payload.config_preview : payload.errors.join('; ');
};
</script>
"""
