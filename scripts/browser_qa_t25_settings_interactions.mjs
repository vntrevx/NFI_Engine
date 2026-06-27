import { clickForState } from "./browser_qa_t25_interaction_tools.mjs";

export async function exerciseSettingsInteractions(page, baseUrl) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const validate = await clickForState(
    page,
    '[data-testid="validate-button"]',
    '[data-testid="validation-state"]',
    "/api/v1/config/validate",
  );
  const draft = await clickForState(
    page,
    '[data-testid="save-draft-button"]',
    '[data-testid="draft-state"]',
    "/api/v1/config/draft",
  );
  const apply = await clickForState(
    page,
    '[data-testid="apply-button"]',
    '[data-testid="audit-log"]',
    "/api/v1/config/apply",
  );
  const setupPreview = await clickForState(
    page,
    '[data-testid="setup-preview-button"]',
    '[data-testid="setup-preview-state"]',
    "/api/v1/setup/preview",
  );
  const wallet = await clickForState(
    page,
    '[data-testid="wallet-fetch-button"]',
    '[data-testid="wallet-balance-state"]',
    "/api/v1/wallet/balance/fetch",
  );
  await openDrawer(page, '[data-testid="settings-update-drawer"]');
  const updatePreview = await clickForState(
    page,
    '[data-testid="update-preview-button"]',
    '[data-testid="update-preview-state"]',
    "/api/v1/update/preview",
  );
  const updateApply = await clickForState(
    page,
    '[data-testid="update-apply-button"]',
    '[data-testid="update-apply-state"]',
    "/api/v1/update/apply",
  );
  const updateRollback = await clickForState(
    page,
    '[data-testid="update-rollback-button"]',
    '[data-testid="update-rollback-state"]',
    "/api/v1/update/rollback",
  );
  await openDrawer(page, '[data-testid="data-lifecycle-drawer"]');
  const lifecycleInspect = await clickForState(
    page,
    '[data-testid="data-lifecycle-inspect-button"]',
    '[data-testid="data-lifecycle-footprint-state"]',
    "/api/v1/data-lifecycle/footprint",
  );
  const lifecycleExport = await clickForState(
    page,
    '[data-testid="data-lifecycle-export-button"]',
    '[data-testid="data-lifecycle-export-state"]',
    "/api/v1/data-lifecycle/export",
  );
  const lifecycleDryRun = await clickForState(
    page,
    '[data-testid="data-lifecycle-dry-run-button"]',
    '[data-testid="data-lifecycle-prune-state"]',
    "/api/v1/data-lifecycle/prune",
  );
  await openDrawer(page, '[data-testid="pairlist-drawer"]');
  await page.locator('[data-testid="pairlist-blacklist"]').fill("DOGE/USDT:USDT");
  const pairlistPreview = await clickForState(
    page,
    '[data-testid="pairlist-preview-button"]',
    '[data-testid="pairlist-preview-state"]',
    "/api/v1/pairlist/preview",
  );
  const pairlistDraft = await clickForState(
    page,
    '[data-testid="pairlist-save-draft-button"]',
    '[data-testid="pairlist-audit-log"]',
    "/api/v1/pairlist/draft",
  );
  const pairlistApply = await clickForState(
    page,
    '[data-testid="pairlist-apply-button"]',
    '[data-testid="pairlist-audit-log"]',
    "/api/v1/pairlist/apply",
  );
  return {
    validate,
    draft,
    apply,
    setupPreview,
    wallet,
    updatePreview,
    updateApply,
    updateRollback,
    lifecycleInspect,
    lifecycleExport,
    lifecycleDryRun,
    pairlistPreview,
    pairlistDraft,
    pairlistApply,
  };
}

async function openDrawer(page, selector) {
  await page.locator(selector).evaluate((element) => {
    if (element instanceof HTMLDetailsElement) {
      element.open = true;
    }
  });
}
