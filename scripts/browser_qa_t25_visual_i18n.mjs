import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
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
} from "./browser_qa_runtime.mjs";
import {
  countDocumentRequests,
  layoutAudit,
  securitySummary,
  storageState,
  writeSelfDiff,
} from "./browser_qa_t25_audit.mjs";
import { exerciseFeatureInteractions } from "./browser_qa_t25_interactions.mjs";
import {
  captureOperatorSurfaces,
  exerciseLanguageSwitches,
  login,
  probeRenderedText,
} from "./browser_qa_t25_locale.mjs";

const repoRoot = resolve(dirname(new URL(import.meta.url).pathname), "..");
const evidenceDir = resolve(
  repoRoot,
  process.env.NFI_WP9_BROWSER_EVIDENCE_DIR ??
    ".omo/evidence/2026-06-17-product-completion/wp9/browser",
);
const qaToken = process.env.NFI_WP9_BROWSER_TOKEN ?? `wp9-${randomBytes(18).toString("hex")}`;
const requests = [];
const consoleMessages = [];
const screenshots = [];
const cleanup = [];
let browser;
let serverProcess;
let tempDir = "";

if (process.argv.includes("--help")) {
  console.log("Usage: npm run nfi:browser-qa:wp9");
  console.log(`Writes browser evidence to ${evidenceDir}`);
  process.exit(0);
}

try {
  await main();
  process.exitCode = 0;
} catch (error) {
  writeJson("failure.json", {
    message: redact(error instanceof Error ? error.message : String(error)),
    stack: redact(error instanceof Error ? error.stack ?? "" : ""),
    requests,
    consoleMessages,
  });
  process.exitCode = 1;
} finally {
  await cleanupResources();
}

async function main() {
  mkdirSync(evidenceDir, { recursive: true });
  removePriorArtifacts();
  tempDir = mkdtempSync(join(tmpdir(), "nfi-wp9-browser-"));
  const port = Number(process.env.NFI_WP9_BROWSER_PORT ?? (await freePort()));
  const baseUrl = `http://127.0.0.1:${port}`;
  const configPath = join(tempDir, "qa-config.yaml");
  writeFileSync(configPath, qaConfig(port, tempDir));
  const serverLogs = [];
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
    {
      cwd: repoRoot,
      env: { ...process.env, NFI_ENGINE_API_TOKEN: qaToken },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  serverProcess.stdout.on("data", (chunk) => serverLogs.push(redact(chunk.toString())));
  serverProcess.stderr.on("data", (chunk) => serverLogs.push(redact(chunk.toString())));
  try {
    await waitForServer(baseUrl);
    browser = await chromium.launch({
      executablePath: resolveChromiumExecutable(repoRoot),
      env: browserLaunchEnv(repoRoot),
      headless: process.env.NFI_BROWSER_QA_HEADFUL !== "1",
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
        isLocal: isLocalUrl(request.url(), baseUrl),
      });
    });

    await login(page, baseUrl, qaToken);
    page.on("console", (message) => {
      consoleMessages.push({ type: message.type(), text: redact(message.text()) });
    });
    const documentRequestCount = (pathname) => countDocumentRequests(requests, pathname);
    const visualContext = { evidenceDir, layoutAudit, screenshots };
    const languageSwitches = await exerciseLanguageSwitches(page, baseUrl, documentRequestCount);
    const captures = await captureOperatorSurfaces(page, baseUrl, visualContext);
    const textProbe = await probeRenderedText(page, baseUrl);
    const interactions = await exerciseFeatureInteractions(page, baseUrl, redact);
    const storage = await storageState(page);
    const security = securitySummary({ consoleMessages, evidenceDir, qaToken, requests, storage });
    const passed =
      languageSwitches.enKoElNoManualRefresh &&
      captures.every((item) => item.horizontalOverflowPx === 0) &&
      captures.every((item) => item.clippedText.length === 0) &&
      captures.every((item) => item.overlaps.length === 0) &&
      captures.every((item) => item.replacementGlyphCount === 0) &&
      textProbe.passed &&
      interactions.passed &&
      security.passed;
    writeJson("summary.json", {
      baseUrl,
      languageSwitches,
      captures,
      textProbe,
      interactions,
      security,
      screenshots,
      passed,
    });
    writeJson("network-summary.json", { requests });
    writeJson("console-summary.json", { consoleMessages });
    writeFileSync(join(evidenceDir, "server.log"), serverLogs.join(""));
    writeSelfDiff({ evidenceDir, name: "desktop-self-diff.json", screenshotName: "home-ko-desktop.png", writeJson });
    writeSelfDiff({ evidenceDir, name: "mobile-self-diff.json", screenshotName: "settings-el-mobile.png", writeJson });
    if (!passed) {
      throw new Error("WP9 visual/i18n browser QA failed");
    }
  } catch (error) {
    writeFileSync(join(evidenceDir, "server.log"), serverLogs.join(""));
    throw error;
  }
}

function writeJson(name, value) {
  writeFileSync(join(evidenceDir, name), `${JSON.stringify(value, null, 2)}\n`);
}

function removePriorArtifacts() {
  for (const name of [
    "cleanup.json",
    "console-summary.json",
    "desktop-self-diff.json",
    "failure.json",
    "home-ko-desktop.png",
    "home-ko-mobile.png",
    "logs-el-desktop.png",
    "logs-ko-mobile.png",
    "mobile-self-diff.json",
    "network-summary.json",
    "server.log",
    "settings-el-mobile.png",
    "settings-ko-desktop.png",
    "summary.json",
  ]) {
    rmSync(join(evidenceDir, name), { force: true });
  }
}

async function waitForServer(baseUrl) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (serverProcess?.exitCode !== null) {
      throw new Error(`server exited before readiness: ${serverProcess?.exitCode}`);
    }
    try {
      const response = await fetch(`${baseUrl}/api/v1/ping`);
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
  if (serverProcess && serverProcess.exitCode === null) {
    serverProcess.kill("SIGTERM");
    await onceExit(serverProcess, 3000);
    cleanup.push({ resource: "server", status: "stopped" });
  }
  if (tempDir && process.env.NFI_BROWSER_QA_KEEP_TEMP !== "1") {
    rmSync(tempDir, { recursive: true, force: true });
    cleanup.push({ resource: "tempDir", status: "removed" });
  }
  writeJson("cleanup.json", { cleanup, at: new Date().toISOString() });
}

function qaConfig(port, root) {
  return `engine:
  environment: local
  live_trading: false
  live_trading_confirmed: false
exchange:
  name: bybit
  trading_mode: futures
  margin_mode: isolated
  testnet: true
database:
  url: sqlite+aiosqlite:///${join(root, "nfi-engine.sqlite3")}
api:
  host: 127.0.0.1
  port: ${port}
  csrf_enabled: true
ui:
  enabled: true
  read_only: false
  locale: en
logging:
  level: INFO
  json_logs: false
notifications:
  jsonl_path: ${join(root, "notifications.jsonl")}
`;
}

function redact(text) {
  return text.replaceAll(qaToken, "<redacted-token>");
}
