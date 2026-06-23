import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { chromium } from "playwright-core";
import {
  browserLaunchEnv,
  freePort,
  resolveChromiumExecutable,
  sleep,
} from "./browser_qa_runtime.mjs";
import {
  exerciseLifecyclePanel,
  qaConfig,
  seedRuntime,
} from "./browser_qa_t24_data_lifecycle_flow.mjs";

const repoRoot = resolve(dirname(new URL(import.meta.url).pathname), "..");
const evidenceDir = resolve(
  repoRoot,
  process.env.NFI_WP83_BROWSER_EVIDENCE_DIR ??
    ".omo/evidence/2026-06-17-product-completion/wp8-3/browser",
);
const requests = [];
const consoleMessages = [];
const screenshots = [];
const cleanup = [];
let browser;
let serverProcess;
let tempDir = "";

await main();

async function main() {
  mkdirSync(evidenceDir, { recursive: true });
  removePriorArtifacts();
  tempDir = mkdtempSync(join(tmpdir(), "nfi-wp83-browser-"));
  const runtimeDir = join(tempDir, "runtime");
  seedRuntime(runtimeDir);
  const port = Number(process.env.NFI_WP83_BROWSER_PORT ?? (await freePort()));
  const baseUrl = `http://127.0.0.1:${port}`;
  const configPath = join(tempDir, "qa-config.yaml");
  writeFileSync(configPath, qaConfig(port, runtimeDir));
  serverProcess = spawn(
    "uv",
    [
      "run",
      "nfi-engine",
      "serve",
      "--config",
      configPath,
      "--host",
      "127.0.0.1",
      "--port",
      String(port),
    ],
    { cwd: repoRoot, stdio: ["ignore", "pipe", "pipe"] },
  );
  const serverLogs = [];
  serverProcess.stdout.on("data", (chunk) => serverLogs.push(chunk.toString()));
  serverProcess.stderr.on("data", (chunk) => serverLogs.push(chunk.toString()));

  try {
    await waitForServer(baseUrl);
    browser = await chromium.launch({
      executablePath: resolveChromiumExecutable(repoRoot),
      env: browserLaunchEnv(repoRoot),
      headless: true,
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    await page.route("**/favicon.ico", async (route) => {
      await route.fulfill({ status: 204, body: "" });
    });
    page.on("request", (request) => {
      requests.push({
        method: request.method(),
        url: request.url(),
        resourceType: request.resourceType(),
        isLocal: request.url().startsWith(baseUrl),
      });
    });
    page.on("console", (message) => {
      consoleMessages.push({ type: message.type(), text: message.text() });
    });

    const flow = await exerciseLifecyclePanel(page, baseUrl, runtimeDir);
    await screenshot(page, "settings-lifecycle-desktop.png");
    const desktopLayout = await layout(page, "settings-desktop");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
    await page.locator('[data-testid="settings-root"]').waitFor();
    await screenshot(page, "settings-lifecycle-mobile.png");
    const mobileLayout = await layout(page, "settings-mobile");
    const storage = await storageState(page);
    const externalRequests = requests.filter((request) => !request.isLocal);
    const unexpectedConsoleErrors = consoleMessages.filter((message) => message.type === "error");
    const horizontalOverflowPx = Math.max(
      desktopLayout.horizontalOverflowPx,
      mobileLayout.horizontalOverflowPx,
    );
    const lifecycleRequests = requests.filter((request) =>
      request.url.includes("/api/v1/data-lifecycle/"),
    );
    const summary = {
      baseUrl,
      flow,
      lifecycleRequests,
      lifecycleRequestCount: lifecycleRequests.length,
      storage,
      storageEmpty: storage.localStorage.length === 0 && storage.sessionStorage.length === 0,
      externalRequestCount: externalRequests.length,
      externalRequests,
      unexpectedConsoleErrorCount: unexpectedConsoleErrors.length,
      consoleMessages,
      layouts: [desktopLayout, mobileLayout],
      horizontalOverflowPx,
      screenshots,
      passed:
        flow.passed &&
        lifecycleRequests.some((request) => request.url.endsWith("/footprint")) &&
        lifecycleRequests.some((request) => request.url.endsWith("/export")) &&
        lifecycleRequests.filter((request) => request.url.endsWith("/prune")).length >= 2 &&
        storage.localStorage.length === 0 &&
        storage.sessionStorage.length === 0 &&
        externalRequests.length === 0 &&
        unexpectedConsoleErrors.length === 0 &&
        horizontalOverflowPx === 0,
    };
    writeJson("summary.json", summary);
    writeJson("network-summary.json", { requests });
    writeJson("console-summary.json", { consoleMessages });
    writeFileSync(join(evidenceDir, "server.log"), serverLogs.join(""));
    if (!summary.passed) {
      throw new Error("WP8.3 data lifecycle browser QA failed");
    }
  } catch (error) {
    writeFileSync(join(evidenceDir, "server.log"), serverLogs.join(""));
    writeJson("failure.json", {
      message: error instanceof Error ? error.message : String(error),
      requests,
      consoleMessages,
    });
    throw error;
  } finally {
    await cleanupResources();
  }
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
      viewportWidth: root.clientWidth,
      scrollWidth: root.scrollWidth,
      horizontalOverflowPx: Math.max(0, root.scrollWidth - root.clientWidth),
      title: document.title,
    };
  }, name);
}

async function storageState(page) {
  return await page.evaluate(() => ({
    localStorage: Object.entries(window.localStorage),
    sessionStorage: Object.entries(window.sessionStorage),
  }));
}

function writeJson(name, value) {
  writeFileSync(join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

function removePriorArtifacts() {
  for (const name of [
    "console-summary.json",
    "failure.json",
    "network-summary.json",
    "server.log",
    "settings-lifecycle-desktop.png",
    "settings-lifecycle-mobile.png",
    "summary.json",
  ]) {
    rmSync(join(evidenceDir, name), { force: true });
  }
}

async function waitForServer(baseUrl) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      const response = await fetch(`${baseUrl}/api/v1/health`);
      if (response.ok) {
        return;
      }
    } catch {
    }
    await sleep(250);
  }
  throw new Error("server did not become ready");
}

async function cleanupResources() {
  if (browser) {
    await browser.close();
    cleanup.push({ resource: "browser", status: "closed" });
  }
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
    cleanup.push({ resource: "server", status: "terminated" });
  }
  if (tempDir) {
    rmSync(tempDir, { recursive: true, force: true });
    cleanup.push({ resource: "tempDir", status: "removed" });
  }
  writeJson("cleanup.json", { cleanup });
}
