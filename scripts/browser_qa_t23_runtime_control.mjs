import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { chromium } from "playwright-core";
import {
  browserLaunchEnv,
  freePort,
  isLocalUrl,
  onceExit,
  resolveChromiumExecutable,
  sleep,
  waitForPortClosed,
} from "./browser_qa_runtime.mjs";
import {
  captureMobileViews,
  exerciseHomeControls,
  exerciseSettingsControls,
  runtimeControlPayload,
  storageState,
} from "./browser_qa_t23_runtime_flows.mjs";

const repoRoot = resolve(dirname(new URL(import.meta.url).pathname), "..");
const evidenceDir = resolve(
  repoRoot,
  process.env.NFI_T23_RUNTIME_CONTROL_EVIDENCE_DIR ??
    ".omo/evidence/2026-06-15-product-completion/task-23-runtime-control-browser",
);
const startedAt = new Date().toISOString();
const actionLog = [];
const requests = [];
const consoleMessages = [];
const screenshots = [];
const cleanup = [];

let browser;
let serverProcess;
let tempDir = "";

function record(action, detail = {}) {
  actionLog.push({ at: new Date().toISOString(), action, ...detail });
}

function writeJson(name, value) {
  writeFileSync(join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

function removePriorArtifacts() {
  for (const name of [
    "action-log.json",
    "cleanup.json",
    "console-summary.json",
    "failure.json",
    "home-desktop.png",
    "home-mobile.png",
    "network-summary.json",
    "settings-paused-desktop.png",
    "settings-stopped-desktop.png",
    "settings-mobile.png",
    "server.log",
    "summary.json",
  ]) {
    rmSync(join(evidenceDir, name), { force: true });
  }
}

async function main() {
  mkdirSync(evidenceDir, { recursive: true });
  removePriorArtifacts();
  tempDir = mkdtempSync(join(tmpdir(), "nfi-t23-runtime-control-browser-"));
  const port = Number(process.env.NFI_T23_RUNTIME_CONTROL_PORT ?? (await freePort()));
  const baseUrl = `http://127.0.0.1:${port}`;
  const configPath = join(tempDir, "qa-config.yaml");
  writeFileSync(configPath, qaConfig(tempDir));

  serverProcess = spawn(
    "uv",
    ["run", "nfi-engine", "serve", "--config", configPath, "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: repoRoot,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const serverLogs = [];
  serverProcess.stdout.on("data", (chunk) => serverLogs.push(chunk.toString()));
  serverProcess.stderr.on("data", (chunk) => serverLogs.push(chunk.toString()));
  record("server-started", { baseUrl, config: "qa-temp-config" });

  try {
    await waitForServer(baseUrl);
    browser = await chromium.launch({
      executablePath: resolveChromiumExecutable(repoRoot),
      env: browserLaunchEnv(repoRoot),
      headless: true,
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    record("browser-started");

    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    await page.route("**/favicon.ico", async (route) => {
      await route.fulfill({ status: 204, body: "" });
    });
    page.on("request", (request) => {
      requests.push({
        at: new Date().toISOString(),
        method: request.method(),
        url: request.url(),
        resourceType: request.resourceType(),
        isLocal: isLocalUrl(request.url(), baseUrl),
      });
    });
    page.on("console", (message) => {
      consoleMessages.push({
        at: new Date().toISOString(),
        type: message.type(),
        text: message.text(),
      });
    });

    const flowContext = { layout, record, screenshot };
    const homeFlow = await exerciseHomeControls(page, baseUrl, flowContext);
    const settingsFlow = await exerciseSettingsControls(page, baseUrl, flowContext);
    const finalRuntime = await runtimeControlPayload(page);
    const storage = await storageState(page);
    const desktopSettingsLayout = await layout(page, "settings-desktop");
    const mobileVisual = await captureMobileViews(page, baseUrl, flowContext);
    const externalRequests = requests.filter((request) => !request.isLocal);
    const unexpectedConsoleErrors = consoleMessages.filter((message) => message.type === "error");
    const layouts = [homeFlow.layout, settingsFlow.layout, desktopSettingsLayout, ...mobileVisual.layouts];
    const horizontalOverflow = layouts.reduce(
      (max, item) => Math.max(max, item.horizontalOverflowPx),
      0,
    );
    const runtimeControlRequests = requests.filter((request) =>
      request.url.includes("/api/v1/runtime/control"),
    );
    const summary = {
      startedAt,
      finishedAt: new Date().toISOString(),
      baseUrl,
      homeFlow,
      settingsFlow,
      finalRuntime,
      runtimeControlRequests,
      runtimeControlRequestCount: runtimeControlRequests.length,
      storage,
      storageEmpty: storage.localStorage.length === 0 && storage.sessionStorage.length === 0,
      externalRequestCount: externalRequests.length,
      externalRequests,
      unexpectedConsoleErrorCount: unexpectedConsoleErrors.length,
      layouts,
      horizontalOverflowPx: horizontalOverflow,
      screenshots,
      passed:
        homeFlow.passed &&
        settingsFlow.passed &&
        finalRuntime.state === "stopped" &&
        finalRuntime.new_entries_allowed === false &&
        runtimeControlRequests.length >= 5 &&
        storage.localStorage.length === 0 &&
        storage.sessionStorage.length === 0 &&
        externalRequests.length === 0 &&
        unexpectedConsoleErrors.length === 0 &&
        horizontalOverflow === 0,
    };
    writeJson("summary.json", summary);
    writeJson("action-log.json", actionLog);
    writeJson("network-summary.json", { requests });
    writeJson("console-summary.json", { messages: consoleMessages });
    writeFileSync(join(evidenceDir, "server.log"), serverLogs.join(""));
    if (!summary.passed) {
      throw new Error("T23 runtime-control browser QA failed");
    }
  } catch (error) {
    writeJson("failure.json", {
      message: error instanceof Error ? error.message : String(error),
      actionLog,
      requests,
      consoleMessages,
    });
    throw error;
  } finally {
    await cleanupResources(port);
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
      lang: root.lang,
      viewportWidth: root.clientWidth,
      scrollWidth: root.scrollWidth,
      horizontalOverflowPx: Math.max(0, root.scrollWidth - root.clientWidth),
      title: document.title,
    };
  }, name);
}

async function waitForServer(baseUrl) {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/api/v1/ping`);
      if (response.ok) {
        return;
      }
    } catch {
      // Retry until uvicorn binds the loopback port.
    }
    await sleep(250);
  }
  throw new Error(`server did not start at ${baseUrl}`);
}

async function cleanupResources(port) {
  if (browser) {
    await browser.close();
    cleanup.push({ resource: "browser", status: "closed" });
  }
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
    await onceExit(serverProcess, 5000);
    cleanup.push({ resource: "server", status: `terminated:${serverProcess.exitCode}` });
  }
  await waitForPortClosed(port);
  cleanup.push({ resource: "port", status: "closed", port });
  if (tempDir) {
    rmSync(tempDir, { recursive: true, force: true });
    cleanup.push({ resource: "tempDir", status: "removed" });
  }
  writeJson("cleanup.json", { cleanup });
}

function qaConfig(directory) {
  const example = readFileSync(join(repoRoot, "examples/spot-paper.yaml"), "utf8");
  const databasePath = join(directory, "nfi_engine.sqlite3");
  return example.replace(
    "sqlite+aiosqlite:///data/nfi_engine.sqlite3",
    `sqlite+aiosqlite:///${databasePath}`,
  );
}

await main();
