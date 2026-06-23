import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { chromium } from "playwright-core";

const repoRoot = resolve(new URL("..", import.meta.url).pathname);
const evidenceDir = resolve(
  repoRoot,
  process.env.NFI_T23_BROWSER_EVIDENCE_DIR ??
    ".omo/evidence/2026-06-15-product-completion/task-23-browser",
);
const baseUrl = process.env.NFI_T23_BROWSER_BASE_URL ?? "http://127.0.0.1:18084";
const requests = [];
const consoleMessages = [];
const screenshots = [];

mkdirSync(evidenceDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: resolveChromiumExecutable(),
  env: browserLaunchEnv(),
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  page.on("request", (request) => {
    requests.push({
      method: request.method(),
      url: request.url(),
      resourceType: request.resourceType(),
    });
  });
  page.on("console", (message) => {
    consoleMessages.push({ type: message.type(), text: message.text() });
  });
  await page.route("**/favicon.ico", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator('[data-testid="home-root"]').waitFor();
  const homeWallet = await page.locator('[data-testid="cockpit-wallet-balance"]').innerText();
  const homeRuntime = await page.locator('[data-testid="cockpit-runtime-health"]').innerText();
  await screenshot(page, "home-desktop.png");

  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const walletBefore = await page.locator('[data-testid="wallet-balance-state"]').innerText();
  await page.locator('[data-testid="wallet-fetch-button"]').click();
  await page.waitForFunction(() => {
    const text = document.querySelector('[data-testid="wallet-balance-state"]')?.textContent ?? "";
    return text.includes("1000 / 1000 USDT");
  });
  const walletAfter = await page.locator('[data-testid="wallet-balance-state"]').innerText();
  await screenshot(page, "settings-wallet-desktop.png");

  const storage = await page.evaluate(() => ({
    localStorage: Object.entries(window.localStorage),
    sessionStorage: Object.entries(window.sessionStorage),
  }));
  const desktopLayout = await layout(page, "settings-desktop");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator('[data-testid="home-root"]').waitFor();
  const homeMobileLayout = await layout(page, "home-mobile");
  await screenshot(page, "home-mobile.png");

  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const settingsMobileLayout = await layout(page, "settings-mobile");
  await screenshot(page, "settings-mobile.png");

  const walletFetchRequests = requests.filter((request) =>
    request.url.endsWith("/api/v1/wallet/balance/fetch"),
  );
  const externalRequests = requests.filter((request) => !request.url.startsWith(baseUrl));
  const summary = {
    baseUrl,
    homeWallet,
    homeRuntime,
    walletBefore,
    walletAfter,
    walletFetchRequests,
    walletFetchUsedPost: walletFetchRequests.some((request) => request.method === "POST"),
    storage,
    storageEmpty: storage.localStorage.length === 0 && storage.sessionStorage.length === 0,
    externalRequestCount: externalRequests.length,
    externalRequests,
    consoleMessages,
    unexpectedConsoleErrorCount: consoleMessages.filter((message) => message.type === "error")
      .length,
    layouts: [desktopLayout, homeMobileLayout, settingsMobileLayout],
    screenshots,
    passed:
      homeWallet.includes("1000 / 1000 USDT") &&
      homeRuntime.includes("degraded") &&
      walletBefore.length > 0 &&
      walletAfter.includes("1000 / 1000 USDT") &&
      walletFetchRequests.some((request) => request.method === "POST") &&
      storage.localStorage.length === 0 &&
      storage.sessionStorage.length === 0 &&
      externalRequests.length === 0,
  };
  writeJson("summary.json", summary);
  writeJson("network-summary.json", { requests });
  writeJson("console-summary.json", { consoleMessages });
  if (!summary.passed) {
    throw new Error("T23 browser QA failed");
  }
} finally {
  await browser.close();
}

async function screenshot(page, name) {
  await page.screenshot({ path: join(evidenceDir, name), fullPage: true });
  screenshots.push(name);
}

async function layout(page, name) {
  return await page.evaluate((label) => {
    const root = document.documentElement;
    return {
      name: label,
      lang: root.lang,
      viewportWidth: root.clientWidth,
      scrollWidth: root.scrollWidth,
      horizontalOverflowPx: Math.max(0, root.scrollWidth - root.clientWidth),
      title: document.title,
    };
  }, name);
}

function writeJson(name, value) {
  writeFileSync(join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

function resolveChromiumExecutable() {
  const candidates = [
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    join(process.env.HOME ?? "", ".cache/ms-playwright/chromium-1223/chrome-linux64/chrome"),
    join(process.env.HOME ?? "", ".cache/ms-playwright/chromium-1200/chrome-linux64/chrome"),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error("Chromium executable not found");
}

function browserLaunchEnv() {
  const localLibDir = join(repoRoot, ".omo/tools/browser-libs/root/usr/lib/x86_64-linux-gnu");
  const fontConfig = join(repoRoot, ".omo/tools/browser-libs/fonts.conf");
  const env = { ...process.env };
  if (existsSync(localLibDir)) {
    const existing = process.env.LD_LIBRARY_PATH;
    env.LD_LIBRARY_PATH = existing ? `${localLibDir}:${existing}` : localLibDir;
  }
  if (existsSync(fontConfig)) {
    env.FONTCONFIG_FILE = fontConfig;
  }
  return env;
}
