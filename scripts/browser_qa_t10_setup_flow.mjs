import { join } from "node:path";

export async function captureMobileViews(page, baseUrl, context) {
  await page.setViewportSize({ width: 390, height: 844 });
  const captures = [];
  for (const [name, path] of [
    ["home-mobile.png", "/"],
    ["settings-el-mobile.png", "/settings"],
    ["logs-el-mobile.png", "/logs"],
  ]) {
    await page.goto(`${baseUrl}${path}`, { waitUntil: "networkidle" });
    captures.push(await pageLayoutAudit(page, name));
    await screenshot(page, name, context);
  }
  context.record("mobile-captures-complete", { count: captures.length });
  return { captures };
}

export async function exerciseHappyPath(page, baseUrl, invalidLogin, context) {
  await page.locator('[data-testid="login-token"]').fill(context.qaToken);
  await page.locator('[data-testid="login-button"]').click();
  await page.locator('[data-testid="home-root"]').waitFor();
  await page.waitForLoadState("networkidle");
  const homeUrl = page.url();
  const actionCount = await page.locator('[data-testid="action-item"]').count();
  const cockpit = await auditHomeCockpit(page);
  await screenshot(page, "home-desktop.png", context);

  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const beforeLang = await page.locator("html").getAttribute("lang");
  const settingsDocumentRequestsBefore = context.countDocumentRequests("/settings");
  await page.locator('[name="ui.locale"]').selectOption("ko");
  await page.locator('[data-testid="apply-button"]').click();
  await page.waitForFunction(() => document.documentElement.lang === "ko");
  await page.locator("text=로컬 운영자 설정").waitFor();
  await page.waitForLoadState("networkidle");
  const afterLang = await page.locator("html").getAttribute("lang");
  const settingsDocumentRequestsAfter = context.countDocumentRequests("/settings");
  const setupWizard = await auditSetupWizard(page);
  const setupSecurity = await exerciseSetupPreview(page, context);
  await screenshot(page, "settings-ko-desktop.png", context);

  await page.goto(`${baseUrl}/logs`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="logs-root"]').waitFor();
  await page.locator("text=최근 이벤트").waitFor();
  await screenshot(page, "logs-ko-desktop.png", context);

  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const beforeGreekLang = await page.locator("html").getAttribute("lang");
  const settingsDocumentRequestsBeforeGreek = context.countDocumentRequests("/settings");
  await page.locator('[name="ui.locale"]').selectOption("el");
  await page.locator('[data-testid="apply-button"]').click();
  await page.waitForFunction(() => document.documentElement.lang === "el");
  await page.locator("text=Τοπικές ρυθμίσεις χειριστή").waitFor();
  await page.waitForLoadState("networkidle");
  const afterGreekLang = await page.locator("html").getAttribute("lang");
  const settingsDocumentRequestsAfterGreek = context.countDocumentRequests("/settings");
  const setupWizardGreek = await auditSetupWizard(page);
  await screenshot(page, "settings-el-desktop.png", context);

  await page.goto(`${baseUrl}/logs`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="logs-root"]').waitFor();
  await page.locator("text=Πρόσφατα γεγονότα").waitFor();
  await screenshot(page, "logs-el-desktop.png", context);

  const languageSwitch = {
    beforeLang,
    afterLang,
    manualRefresh: false,
    automaticNavigationAfterApply: settingsDocumentRequestsAfter > settingsDocumentRequestsBefore,
    appliedBy: "settings apply button",
  };
  const greekLanguageSwitch = {
    beforeLang: beforeGreekLang,
    afterLang: afterGreekLang,
    manualRefresh: false,
    automaticNavigationAfterApply: settingsDocumentRequestsAfterGreek > settingsDocumentRequestsBeforeGreek,
    appliedBy: "settings apply button",
  };
  context.record("happy-path-complete", {
    homeUrl,
    actionCount,
    languageSwitches: { enToKo: languageSwitch, koToEl: greekLanguageSwitch },
  });
  return {
    loginLoadedHome: homeUrl === `${baseUrl}/`,
    actionCount,
    cockpit,
    setupWizard,
    setupWizardGreek,
    setupSecurity,
    loginCredentialWordingSeparated: invalidLogin.loginCredentialWordingSeparated,
    languageSwitch,
    languageSwitches: { enToKo: languageSwitch, koToEl: greekLanguageSwitch },
    settingsKoVisible: true,
    logsKoVisible: true,
    settingsElVisible: true,
    logsElVisible: true,
  };
}

export async function exerciseInvalidLogin(page, baseUrl, context) {
  const response = await page.goto(baseUrl, { waitUntil: "networkidle" });
  await expectStatus(response, 401, "login page");
  await page.locator('[data-testid="login-root"]').waitFor();
  const loginText = await page.locator('[data-testid="login-root"]').innerText();
  await screenshot(page, "login-empty-desktop.png", context);
  await page.locator('[data-testid="login-token"]').fill("invalid-qa-token");
  await page.locator('[data-testid="login-button"]').click();
  await page.locator('[data-testid="login-state"]').waitFor({ state: "visible" });
  await page.waitForFunction(() => document.body.innerText.includes("HTTP 401"));
  const stillLogin = await page.locator('[data-testid="login-root"]').count();
  await page.locator('[data-testid="login-token"]').fill("");
  context.record("invalid-login-denied", { statusText: "HTTP 401", stillLogin: stillLogin === 1 });
  return {
    denied: stillLogin === 1,
    loginCredentialWordingSeparated: !context.credentialWordsAppear(loginText),
    statusText: "HTTP 401",
  };
}

export async function storageState(page) {
  return await page.evaluate(() => ({
    localStorage: Object.entries(window.localStorage),
    sessionStorage: Object.entries(window.sessionStorage),
  }));
}

async function auditHomeCockpit(page) {
  const ids = [
    "operator-cockpit",
    "cockpit-configured",
    "cockpit-safety",
    "cockpit-capability-level",
    "cockpit-active-mode",
    "cockpit-wallet-balance",
    "cockpit-allocated-amount",
    "cockpit-leverage",
    "cockpit-latest-error",
    "cockpit-next-action",
    "cockpit-where-next",
  ];
  const values = {};
  for (const id of ids) {
    await page.locator(`[data-testid="${id}"]`).waitFor();
    values[id] = await page.locator(`[data-testid="${id}"]`).innerText();
  }
  return {
    present: ids.every((id) => Boolean(values[id])),
    values,
  };
}

async function auditSetupWizard(page) {
  const orderedStepIds = [
    "setup-step-exchange",
    "setup-step-api-key",
    "setup-step-api-secret",
    "setup-step-leverage",
    "setup-step-wallet-balance",
    "setup-step-allocated-amount",
    "setup-step-market-mode",
    "setup-step-intent",
  ];
  const positions = await page.evaluate((ids) => {
    const all = Array.from(document.querySelectorAll("[data-testid]"));
    return ids.map((id) => all.findIndex((element) => element.dataset.testid === id));
  }, orderedStepIds);
  const missing = orderedStepIds.filter((_, index) => positions[index] < 0);
  const exactOrder =
    missing.length === 0 && positions.every((position, index) => index === 0 || position > positions[index - 1]);
  const dryRunDefault = await page.locator('select[name="intent"]').inputValue() === "paper";
  const recommendedLeverage = await page.locator('[data-testid="setup-recommended-leverage"]').innerText();
  const updateStates = {
    preview: await page.locator('[data-testid="update-preview-state"]').innerText(),
    apply: await page.locator('[data-testid="update-apply-state"]').innerText(),
    rollback: await page.locator('[data-testid="update-rollback-state"]').innerText(),
  };
  await page.locator('[data-testid="settings-update-panel"]').waitFor();
  return {
    orderedStepIds,
    positions,
    missing,
    exactOrder,
    dryRunDefault,
    recommendedLeverage,
    recommendedLeverageDefault3x: recommendedLeverage.includes("3x"),
    updateStates,
    updatePanelPresent: true,
  };
}

async function exerciseSetupPreview(page, context) {
  await page.locator("#setup-api-key").fill("qa-preview-key");
  await page.locator("#setup-api-secret").fill(context.qaExchangeSecret);
  await page.locator("#setup-allocated-amount").fill("42.5");
  await page.locator('select[name="trading_mode"]').selectOption("futures");
  const dryRunDefault = await page.locator('select[name="intent"]').inputValue() === "paper";
  await page.locator('[data-testid="setup-preview-button"]').click();
  await page.waitForFunction(() => {
    const text = document.querySelector('[data-testid="setup-preview-state"]')?.textContent ?? "";
    return text.includes("REDACTED") || text.includes("valid:");
  });
  const previewText = await page.locator('[data-testid="setup-preview-state"]').innerText();
  await page.locator('select[name="intent"]').selectOption("live");
  const liveWarningText = await page.locator('[data-testid="setup-step-intent"] .field-note').innerText();
  await page.locator('[data-testid="setup-preview-button"]').click();
  await page.waitForFunction((previousText) => {
    const text = document.querySelector('[data-testid="setup-preview-state"]')?.textContent ?? "";
    return (
      text !== previousText &&
      (text.includes("LIVE_TRADING_REQUIRES_CONFIRMATION") ||
        text.includes("live") ||
        text.includes("라이브"))
    );
  }, previewText);
  const livePreviewText = await page.locator('[data-testid="setup-preview-state"]').innerText();
  const liveGateWarningsPresent = [
    /confirm|확인/i,
    /preflight/i,
    /limit|한도/i,
    /kill switch/i,
    /reconciliation/i,
  ].every((pattern) => pattern.test(liveWarningText));
  return {
    dryRunDefault,
    setupSecretWriteOnly: await page.locator("#setup-api-secret").getAttribute("type") === "password",
    setupSecretRedacted: previewText.includes("REDACTED") && !previewText.includes(context.qaExchangeSecret),
    previewText: context.redactSecret(previewText),
    liveGateWarningsPresent,
    livePreviewBlocked: livePreviewText.includes("LIVE_TRADING_REQUIRES_CONFIRMATION"),
    liveWarningText,
    livePreviewText: context.redactSecret(livePreviewText),
  };
}

async function expectStatus(response, expected, label) {
  if (!response || response.status() !== expected) {
    throw new Error(`${label} expected HTTP ${expected}, got ${response?.status() ?? "none"}`);
  }
}

async function pageLayoutAudit(page, name) {
  const audit = await page.evaluate(() => ({
    lang: document.documentElement.lang,
    viewportWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    title: document.title,
  }));
  return {
    name,
    ...audit,
    horizontalOverflowPx: Math.max(0, audit.scrollWidth - audit.viewportWidth),
  };
}

async function screenshot(page, name, { evidenceDir, record, screenshots }) {
  const path = join(evidenceDir, name);
  await page.screenshot({ path, fullPage: true });
  screenshots.push(name);
  record("screenshot", { name });
}
