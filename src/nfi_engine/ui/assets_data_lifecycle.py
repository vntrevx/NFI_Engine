from __future__ import annotations

from typing import Final

DATA_LIFECYCLE_SCRIPT: Final = """
<script>
const lifecycleInspectButton = document.querySelector(
  '[data-testid="data-lifecycle-inspect-button"]'
);
const lifecycleExportButton = document.querySelector(
  '[data-testid="data-lifecycle-export-button"]'
);
const lifecycleDryRunButton = document.querySelector(
  '[data-testid="data-lifecycle-dry-run-button"]'
);
const lifecycleApplyButton = document.querySelector(
  '[data-testid="data-lifecycle-apply-button"]'
);
const lifecycleRetentionDays = document.querySelector(
  '[data-testid="data-lifecycle-retention-days"]'
);
const lifecyclePreviewToken = document.querySelector(
  '[data-testid="data-lifecycle-preview-token"]'
);
const lifecycleFootprintState = document.querySelector(
  '[data-testid="data-lifecycle-footprint-state"]'
);
const lifecycleExportState = document.querySelector(
  '[data-testid="data-lifecycle-export-state"]'
);
const lifecyclePruneState = document.querySelector(
  '[data-testid="data-lifecycle-prune-state"]'
);
function dataLifecycleCsrfHeaders() {
  const token = document.querySelector('meta[name="nfi-csrf-token"]')?.content || '';
  return token ? {'x-nfi-csrf-token': token} : {};
}
async function dataLifecyclePayload(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}
function dataLifecycleError(response, payload) {
  if (payload.detail?.code) {
    return `${payload.detail.code}: ${payload.detail.message}`;
  }
  return `HTTP ${response.status}`;
}
function retentionDaysValue() {
  const parsed = Number.parseInt(lifecycleRetentionDays?.value || '7', 10);
  return Number.isNaN(parsed) ? 7 : parsed;
}
function footprintText(payload) {
  const categories = (payload.categories || [])
    .map((item) => `${item.name}:${item.file_count}/${item.total_bytes}`)
    .join(' | ');
  return `bytes=${payload.total_bytes || 0} ${categories}`;
}
function pruneText(payload) {
  const state = payload.accepted ? 'ACCEPTED' : 'BLOCKED';
  const reasons = payload.blocked_reasons?.join('; ') || '';
  const counts = `candidates=${payload.candidate_count || 0} deleted=${payload.deleted_count || 0}`;
  return `${state} ${counts} ${reasons}`.trim();
}
async function runPrune(applyCleanup) {
  const response = await fetch('/api/v1/data-lifecycle/prune', {
    method: 'POST',
    headers: {'content-type': 'application/json', ...dataLifecycleCsrfHeaders()},
    body: JSON.stringify({
      dry_run: !applyCleanup,
      apply: applyCleanup,
      retention_days: retentionDaysValue(),
      preview_token: applyCleanup ? lifecyclePreviewToken?.value || null : null,
      confirm_scope: applyCleanup ? 'DELETE_GENERATED_LOCAL_ARTIFACTS' : null
    })
  });
  const payload = await dataLifecyclePayload(response);
  if (!response.ok) {
    lifecyclePruneState.textContent = dataLifecycleError(response, payload);
    return;
  }
  if (!applyCleanup && payload.preview_token && lifecyclePreviewToken) {
    lifecyclePreviewToken.value = payload.preview_token;
  }
  lifecyclePruneState.textContent = pruneText(payload);
}
if (lifecycleInspectButton && lifecycleFootprintState) {
  lifecycleInspectButton.onclick = async () => {
    const response = await fetch('/api/v1/data-lifecycle/footprint');
    const payload = await dataLifecyclePayload(response);
    lifecycleFootprintState.textContent = response.ok
      ? footprintText(payload)
      : dataLifecycleError(response, payload);
  };
}
if (lifecycleExportButton && lifecycleExportState) {
  lifecycleExportButton.onclick = async () => {
    const response = await fetch('/api/v1/data-lifecycle/export');
    const payload = await dataLifecyclePayload(response);
    lifecycleExportState.textContent = response.ok
      ? `EXPORT_READY ${payload.receipt_id}`
      : dataLifecycleError(response, payload);
  };
}
if (lifecycleDryRunButton && lifecyclePruneState) {
  lifecycleDryRunButton.onclick = async () => {
    await runPrune(false);
  };
}
if (lifecycleApplyButton && lifecyclePruneState) {
  lifecycleApplyButton.onclick = async () => {
    await runPrune(true);
  };
}
</script>
"""
