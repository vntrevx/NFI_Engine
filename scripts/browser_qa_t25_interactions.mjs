import { ensureLocale } from "./browser_qa_t25_locale.mjs";
import {
  postRuntimeCommand,
  readText,
  responseSummary,
  trimEvidenceText,
  waitForFetch,
} from "./browser_qa_t25_interaction_tools.mjs";
import { exerciseSettingsInteractions } from "./browser_qa_t25_settings_interactions.mjs";

export async function exerciseFeatureInteractions(page, baseUrl, redact) {
  await ensureLocale(page, baseUrl, "en", "Local data lifecycle");
  const settings = await exerciseSettingsInteractions(page, baseUrl);
  const logs = await exerciseLogsInteractions(page, baseUrl, redact);
  const runtime = await exerciseRuntimeInteractions(page, baseUrl);
  const checks = {
    settings:
      settings.validate.changed &&
      settings.draft.changed &&
      settings.apply.changed &&
      settings.setupPreview.changed &&
      settings.wallet.changed &&
      settings.updatePreview.changed &&
      settings.updateApply.changed &&
      settings.updateRollback.changed &&
      settings.lifecycleInspect.changed &&
      settings.lifecycleExport.changed &&
      settings.lifecycleDryRun.changed &&
      settings.pairlistPreview.changed &&
      settings.pairlistDraft.changed &&
      settings.pairlistApply.changed,
    logs:
      logs.severityFilter.errorOnly &&
      logs.severityFilter.dynamicMachineCodeClass &&
      logs.errorLookup.resolved &&
      logs.supportBundle.ok,
    runtime:
      runtime.control.ok &&
      runtime.health.ok &&
      runtime.buttonsPresent &&
      runtime.start.posted &&
      runtime.stop.posted,
  };
  return {
    settings,
    logs,
    runtime,
    checks,
    passed: Object.values(checks).every(Boolean),
  };
}

async function exerciseLogsInteractions(page, baseUrl, redact) {
  await page.goto(`${baseUrl}/logs`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="logs-root"]').waitFor();
  const severityFetch = await waitForFetch(page, "/api/v1/logs/recent", async () => {
    await page.locator('[data-testid="severity-filter"]').selectOption("ERROR");
  });
  await page.waitForFunction(() => {
    const rows = document.querySelector('[data-testid="log-rows"]');
    return rows?.textContent?.includes("CONFIG_VALIDATION_ERROR") === true;
  });
  const rowsText = await readText(page, '[data-testid="log-rows"]');
  const dynamicMachineCodeClass =
    (await page.locator('[data-testid="log-rows"] .machine-code').count()) > 0;
  const errorLookupFetch = await waitForFetch(
    page,
    "/api/v1/errors/CONFIG_VALIDATION_ERROR",
    async () => {
      await page.locator('[data-testid="lookup-button"]').click();
    },
  );
  await page.waitForFunction(() => {
    const detail = document.querySelector('[data-testid="error-detail"]');
    return detail?.textContent?.includes("CONFIG_VALIDATION_ERROR") === true;
  });
  const errorDetail = await readText(page, '[data-testid="error-detail"]');
  const supportBundle = await page.evaluate(async () => {
    const link = document.querySelector('[data-testid="export-support-report"]');
    const href = link?.getAttribute("href") || "";
    const download = link?.getAttribute("download") || "";
    const response = href ? await fetch(href) : null;
    return {
      href,
      download,
      status: response?.status ?? 0,
      ok: response?.ok === true,
      contentType: response?.headers.get("content-type") || "",
    };
  });
  return {
    severityFilter: {
      fetch: severityFetch,
      errorOnly: rowsText.includes("CONFIG_VALIDATION_ERROR") && !rowsText.includes("API_STARTED"),
      dynamicMachineCodeClass,
    },
    errorLookup: {
      fetch: errorLookupFetch,
      resolved: errorDetail.includes("CONFIG_VALIDATION_ERROR"),
      detail: trimEvidenceText(errorDetail, redact),
    },
    supportBundle,
  };
}

async function exerciseRuntimeInteractions(page, baseUrl) {
  const controlResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/runtime/control" &&
      response.request().method() === "GET" &&
      response.request().resourceType() === "fetch"
    );
  });
  const healthResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/runtime/health" &&
      response.request().method() === "GET" &&
      response.request().resourceType() === "fetch"
    );
  });
  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="home-root"]').waitFor();
  const control = await responseSummary(await controlResponse, "/api/v1/runtime/control");
  const health = await responseSummary(await healthResponse, "/api/v1/runtime/health");
  const buttons = await page.locator("[data-command]").evaluateAll((items) =>
    items.map((item) => item.getAttribute("data-command") || ""),
  );
  const csrfToken = (await page.locator('meta[name="nfi-csrf-token"]').getAttribute("content")) || "";
  const start = await postRuntimeCommand(page, baseUrl, csrfToken, "start");
  const stop = await postRuntimeCommand(page, baseUrl, csrfToken, "stop");
  return {
    control,
    health,
    buttons,
    buttonsPresent: ["start", "pause", "resume", "stop"].every((command) =>
      buttons.includes(command),
    ),
    start,
    stop,
  };
}
