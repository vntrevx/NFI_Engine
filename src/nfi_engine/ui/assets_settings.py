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
const updatePreviewState = document.querySelector('[data-testid="update-preview-state"]');
const updateApplyState = document.querySelector('[data-testid="update-apply-state"]');
const updateRollbackState = document.querySelector('[data-testid="update-rollback-state"]');
const updateBackupReference = document.querySelector('[data-testid="update-backup-reference"]');
const updateAcknowledge = document.querySelector('[data-testid="update-acknowledge-unverified"]');
const updateAllowDirty = document.querySelector('[data-testid="update-allow-dirty-worktree"]');
const updateSource = document.querySelector('[data-testid="update-source"]');
const walletButton = document.querySelector('[data-testid="wallet-fetch-button"]');
const walletState = document.querySelector('[data-testid="wallet-balance-state"]');
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
function selectedRuntimeLocale() {
  return Array.from(form.elements)
    .find((item) => item.name === 'ui.locale' && !item.disabled)?.value || '';
}
function setupPayload() {
  return Object.fromEntries(
    Array.from(setupForm.elements)
      .filter((item) => item.name && !item.disabled)
      .map((item) => [item.name, item.type === 'checkbox' ? item.checked : item.value])
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
function walletText(payload) {
  if (payload.status === 'fetched' && payload.available && payload.equity) {
    return msg('setup.wallet_fetched')
      .replace('{available}', payload.available)
      .replace('{equity}', payload.equity)
      .replace('{asset}', payload.quote_asset || 'USDT');
  }
  const code = payload.code || msg('setup.wallet_fetch_failed');
  const action = payload.next_action || payload.message || '';
  return action ? `${code}: ${action}` : code;
}
function updateProofPayload() {
  return {
    backup_reference: updateBackupReference?.value?.trim() || null,
    acknowledge_unverified: updateAcknowledge?.checked === true,
    allow_dirty_worktree: updateAllowDirty?.checked === true,
    update_source: updateSource?.value || 'local_proof'
  };
}
function updatePreviewText(payload) {
  return [
    `engine + strategy: ${payload.engine_version} / ${payload.strategy_name}`,
    `compatibility: ${payload.compatibility_status}`,
    `workspace: ${payload.workspace_state}`,
    `config: ${payload.config_source}`,
    `rollback: ${payload.rollback_state.status}`
  ].join(' | ');
}
function updateReceiptText(payload) {
  if (payload.accepted) {
    return `PROOF_READY ${payload.action} ${payload.backup_reference || ''}`.trim();
  }
  const reasons = payload.blocked_reasons?.join('; ') || payload.compatibility_status;
  return `PROOF_BLOCKED ${payload.action}: ${reasons}`;
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
  const currentLocale = document.documentElement.lang || '';
  const requestedLocale = selectedRuntimeLocale();
  const payload = await postConfig('/api/v1/config/apply');
  let mode = msg('settings.fix_settings');
  if (payload.applied) {
    mode = msg('settings.runtime_applied');
  }
  if (!payload.applied && payload.restart_required) {
    mode = msg('settings.reload_required');
  }
  if (payload.applied && requestedLocale && requestedLocale !== currentLocale) {
    window.location.reload();
    return;
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
document.querySelector('[data-testid="update-preview-button"]').onclick = async () => {
  const response = await fetch('/api/v1/update/preview');
  const payload = await responsePayload(response);
  updatePreviewState.textContent = response.ok
    ? updatePreviewText(payload)
    : errorMessages(response, payload).join('; ');
};
document.querySelector('[data-testid="update-apply-button"]').onclick = async () => {
  const response = await fetch('/api/v1/update/apply', {
    method: 'POST',
    headers: {'content-type': 'application/json', ...csrfHeaders()},
    body: JSON.stringify(updateProofPayload())
  });
  const payload = await responsePayload(response);
  updateApplyState.textContent = response.ok
    ? updateReceiptText(payload)
    : errorMessages(response, payload).join('; ');
};
document.querySelector('[data-testid="update-rollback-button"]').onclick = async () => {
  const response = await fetch('/api/v1/update/rollback', {
    method: 'POST',
    headers: {'content-type': 'application/json', ...csrfHeaders()},
    body: JSON.stringify(updateProofPayload())
  });
  const payload = await responsePayload(response);
  updateRollbackState.textContent = response.ok
    ? updateReceiptText(payload)
    : errorMessages(response, payload).join('; ');
};
if (walletButton && walletState) {
  walletButton.onclick = async () => {
    walletButton.disabled = true;
    walletState.textContent = msg('setup.wallet_loading');
    try {
      const response = await fetch('/api/v1/wallet/balance/fetch', {
        method: 'POST',
        headers: csrfHeaders()
      });
      const payload = await responsePayload(response);
      walletState.textContent = response.ok
        ? walletText(payload)
        : errorMessages(response, payload).join('; ');
    } catch {
      walletState.textContent = msg('setup.wallet_fetch_failed');
    } finally {
      walletButton.disabled = false;
    }
  };
}
</script>
"""
