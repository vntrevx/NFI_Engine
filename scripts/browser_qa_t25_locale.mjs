import { join } from "node:path";

export async function captureOperatorSurfaces(page, baseUrl, context) {
  const captures = [];
  await ensureLocale(page, baseUrl, "ko", "로컬 데이터 관리");
  captures.push(await capture(page, `${baseUrl}/`, "home-ko-desktop.png", "home-ko-desktop", context));
  captures.push(
    await capture(
      page,
      `${baseUrl}/settings`,
      "settings-ko-desktop.png",
      "settings-ko-desktop",
      context,
    ),
  );
  await ensureLocale(page, baseUrl, "el", "Τοπική διαχείριση δεδομένων");
  captures.push(
    await capture(page, `${baseUrl}/logs`, "logs-el-desktop.png", "logs-el-desktop", context),
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await ensureLocale(page, baseUrl, "ko", "로컬 데이터 관리");
  captures.push(await capture(page, `${baseUrl}/`, "home-ko-mobile.png", "home-ko-mobile", context));
  captures.push(await capture(page, `${baseUrl}/logs`, "logs-ko-mobile.png", "logs-ko-mobile", context));
  await ensureLocale(page, baseUrl, "el", "Τοπική διαχείριση δεδομένων");
  captures.push(
    await capture(
      page,
      `${baseUrl}/settings`,
      "settings-el-mobile.png",
      "settings-el-mobile",
      context,
    ),
  );
  return captures;
}

export async function ensureLocale(page, baseUrl, locale, visibleText) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const current = await page.locator("html").getAttribute("lang");
  if (current !== locale) {
    await switchLocale(page, locale, visibleText);
  }
}

export async function exerciseLanguageSwitches(page, baseUrl, countDocumentRequests) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const initialLang = await page.locator("html").getAttribute("lang");
  const ko = await switchLocale(page, "ko", "로컬 데이터 관리", countDocumentRequests);
  const el = await switchLocale(page, "el", "Τοπική διαχείριση δεδομένων", countDocumentRequests);
  const en = await switchLocale(page, "en", "Local data lifecycle", countDocumentRequests);
  return {
    initialLang,
    ko,
    el,
    en,
    enKoElNoManualRefresh: ko.applied && el.applied && en.applied,
  };
}

export async function login(page, baseUrl, qaUsername, qaPassword) {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator('[data-testid="login-root"]').waitFor();
  await page.locator('[data-testid="login-username"]').fill(qaUsername);
  await page.locator('[data-testid="login-password"]').fill(qaPassword);
  await page.locator('[data-testid="login-button"]').click();
  await page.locator('[data-testid="home-root"]').waitFor();
  await page.waitForLoadState("networkidle");
}

export async function probeRenderedText(page, baseUrl) {
  await ensureLocale(page, baseUrl, "ko", "로컬 데이터 관리");
  const korean = await textAt(page, `${baseUrl}/settings`);
  await ensureLocale(page, baseUrl, "el", "Τοπική διαχείριση δεδομένων");
  const greekSettings = await textAt(page, `${baseUrl}/settings`);
  const greekLogs = await textAt(page, `${baseUrl}/logs`);
  const oldGreekEnglishLabels = [
    "Developer update",
    "Runtime-safe",
    "Runtime safe",
    "Pass",
    "Warn",
    "Block",
    "Rollback",
    "wallet balance",
    "draft",
    "Blacklist",
    "pairlist blacklist",
    "pairlist preview",
    "Pairlist",
  ];
  const greekOldEnglishLabelsFound = oldGreekEnglishLabels.filter((label) =>
    greekSettings.includes(label),
  );
  const checks = {
    koreanLifecycle: korean.includes("로컬 데이터 관리"),
    koreanUpdate: korean.includes("개발자 업데이트"),
    koreanSetup: korean.includes("첫 실행 설정"),
    koreanNoOldLifecycleEnglish: !korean.includes("Local data lifecycle"),
    greekLifecycle: greekSettings.includes("Τοπική διαχείριση δεδομένων"),
    greekSetup: greekSettings.includes("Ρύθμιση πρώτης εκτέλεσης"),
    greekLogs: greekLogs.includes("Πρόσφατα γεγονότα"),
    greekNoOldEnglishLabels: greekOldEnglishLabelsFound.length === 0,
    machineCodePreserved: greekLogs.includes("CONFIG_VALIDATION_ERROR"),
  };
  return {
    checks,
    greekOldEnglishLabelsFound,
    passed: Object.values(checks).every(Boolean),
  };
}

async function capture(page, url, screenshotName, label, { evidenceDir, layoutAudit, screenshots }) {
  await page.goto(url, { waitUntil: "networkidle" });
  const rootId = rootTestId(url);
  await page.locator(`[data-testid="${rootId}"]`).waitFor();
  const layout = await layoutAudit(page, label);
  await page.screenshot({ path: join(evidenceDir, screenshotName), fullPage: true });
  screenshots.push(screenshotName);
  return layout;
}

function rootTestId(url) {
  if (url.endsWith("/settings")) {
    return "settings-root";
  }
  if (url.endsWith("/logs")) {
    return "logs-root";
  }
  return "home-root";
}

async function switchLocale(page, locale, visibleText, countDocumentRequests = () => 0) {
  const beforeDocuments = countDocumentRequests("/settings");
  await page.locator('[name="ui.locale"]').selectOption(locale);
  await page.locator('[data-testid="apply-button"]').click();
  await page.waitForFunction((expected) => document.documentElement?.lang === expected, locale);
  await page.waitForFunction(
    (text) => document.body?.innerText?.includes(text) === true,
    visibleText,
  );
  await page.waitForLoadState("networkidle");
  const afterDocuments = countDocumentRequests("/settings");
  return {
    locale,
    applied: true,
    manualRefresh: false,
    automaticDocumentRefresh: afterDocuments > beforeDocuments,
    htmlLang: await page.locator("html").getAttribute("lang"),
  };
}

async function textAt(page, url) {
  await page.goto(url, { waitUntil: "networkidle" });
  return await page.locator("body").innerText();
}
