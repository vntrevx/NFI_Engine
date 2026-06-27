import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { chromium } from "playwright-core";
import {
  browserLaunchEnv,
  freePort,
  isLocalUrl,
  resolveChromiumExecutable,
} from "./browser_qa_runtime.mjs";
import { removePriorArtifacts, writeJson as writeArtifactJson } from "./browser_qa_t10_artifacts.mjs";
import { exerciseFailureProbes } from "./browser_qa_t10_failure_probes.mjs";
import {
  cleanupT10Runtime,
  createRedactors,
  documentRequestCounter,
  qaConfig,
  waitForServer,
} from "./browser_qa_t10_runtime.mjs";
import {
  captureMobileViews,
  exerciseHappyPath,
  exerciseInvalidLogin,
  storageState,
} from "./browser_qa_t10_setup_flow.mjs";
import { credentialWordsAppear, securityAudit } from "./browser_qa_t10_security_audit.mjs";

const repoRoot = resolve(dirname(new URL(import.meta.url).pathname), "..");
const evidenceDir = resolve(
  repoRoot,
  process.env.NFI_BROWSER_QA_EVIDENCE_DIR
    ?? ".omo/evidence/2026-06-15-product-completion/task-10-browser",
);
const extraEvidenceDir = process.env.NFI_BROWSER_QA_EXTRA_EVIDENCE_DIR
  ? resolve(repoRoot, process.env.NFI_BROWSER_QA_EXTRA_EVIDENCE_DIR)
  : null;
const qaToken = process.env.NFI_BROWSER_QA_TOKEN ?? `qa-${randomBytes(18).toString("hex")}`;
const qaUsername = process.env.NFI_BROWSER_QA_USERNAME ?? "admin";
const qaPassword = process.env.NFI_BROWSER_QA_PASSWORD ?? qaToken;
const qaExchangeSecret =
  process.env.NFI_BROWSER_QA_EXCHANGE_SECRET ?? `exchange-secret-${randomBytes(12).toString("hex")}`;
const { redact, redactSecret } = createRedactors([qaToken, qaPassword], qaExchangeSecret);
const startedAt = new Date().toISOString();
const actionLog = [];
const requests = [];
const consoleMessages = [];
const screenshots = [];
const cleanup = [];

let browser;
let extraFailureProbeReport;
let extraLiveGateReport;
let extraSecurityReport;
let serverProcess;
let tempDir = "";
let port = 0;

function record(action, detail = {}) {
  actionLog.push({ at: new Date().toISOString(), action, ...detail });
}

function writeJson(name, value) {
  writeArtifactJson(evidenceDir, name, value);
}

async function main() {
  mkdirSync(evidenceDir, { recursive: true });
  removePriorArtifacts(evidenceDir);
  tempDir = mkdtempSync(join(tmpdir(), "nfi-t10-browser-"));
  port = Number(process.env.NFI_BROWSER_QA_PORT ?? await freePort());
  const baseUrl = `http://127.0.0.1:${port}`;
  const configPath = join(tempDir, "qa-config.yaml");
  writeFileSync(configPath, qaConfig(port, tempDir));

  serverProcess = spawn(
    "uv",
    ["run", "nfi-engine", "serve", "--config", configPath, "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        NFI_ENGINE_API_TOKEN: qaToken,
        NFI_ENGINE_OPERATOR_PASSWORD: qaPassword,
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const serverLogs = [];
  serverProcess.stdout.on("data", (chunk) => serverLogs.push(redact(chunk.toString())));
  serverProcess.stderr.on("data", (chunk) => serverLogs.push(redact(chunk.toString())));
  record("server-started", { baseUrl, config: "qa-temp-config" });

  await waitForServer(baseUrl, serverProcess, record);
  const executablePath = resolveChromiumExecutable(repoRoot);
  browser = await chromium.launch({
    executablePath,
    env: browserLaunchEnv(repoRoot),
    headless: process.env.NFI_BROWSER_QA_HEADFUL !== "1",
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  record("browser-started", { executable: executablePath });

  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  await page.route("**/favicon.ico", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
  page.on("request", (request) => {
    const url = request.url();
    requests.push({
      at: new Date().toISOString(),
      method: request.method(),
      url,
      resourceType: request.resourceType(),
      isLocal: isLocalUrl(url),
    });
  });
  page.on("console", (message) => {
    consoleMessages.push({
      at: new Date().toISOString(),
      type: message.type(),
      text: redact(message.text()),
    });
  });

  const flowContext = {
    countDocumentRequests: documentRequestCounter(requests),
    credentialWordsAppear,
    evidenceDir,
    qaExchangeSecret,
    qaPassword,
    qaToken,
    qaUsername,
    record,
    redactSecret,
    screenshots,
  };
  const invalidLogin = await exerciseInvalidLogin(page, baseUrl, flowContext);
  const happyPath = await exerciseHappyPath(page, baseUrl, invalidLogin, flowContext);
  const storage = await storageState(page);
  const visual = await captureMobileViews(page, baseUrl, flowContext);
  const failureProbes = await exerciseFailureProbes(page, baseUrl, {
    qaExchangeSecret,
    qaToken,
    record,
    redact,
  });
  extraFailureProbeReport = failureProbes;
  const security = await securityAudit({
    invalidLogin,
    happyPath,
    storage,
    visual,
    failureProbes,
  }, {
    actionLog,
    consoleMessages,
    evidenceDir,
    qaExchangeSecret,
    qaPassword,
    qaToken,
    requests,
  });

  const summary = {
    startedAt,
    finishedAt: new Date().toISOString(),
    baseUrl,
    browserExecutable: executablePath,
    happyPath,
    invalidLogin,
    storage,
    visual,
    failureProbes,
    security: {
      externalRequestCount: security.externalRequestCount,
      tokenLeakCount: security.tokenLeakCount,
      localStorageEntries: storage.localStorage.length,
      sessionStorageEntries: storage.sessionStorage.length,
      unexpectedConsoleErrorCount: security.unexpectedConsoleErrorCount,
      exchangeSecretLeakCount: security.exchangeSecretLeakCount,
      forbiddenWalletWordingCount: security.forbiddenWalletWordingCount,
      failureProbePassed: failureProbes.passed,
    },
    screenshots,
    artifacts: [
      "action-log.json",
      "console-summary.json",
      "network-summary.json",
      "security.json",
      "summary.json",
    ],
  };
  writeJson("summary.json", summary);
  writeJson("action-log.json", actionLog);
  writeJson("console-summary.json", { messages: consoleMessages });
  writeJson("network-summary.json", { requests });
  writeJson("security.json", security);
  extraSecurityReport = {
    passed: security.passed,
    secretLeakCount: security.exchangeSecretLeakCount,
    tokenLeakCount: security.tokenLeakCount,
    browserStorageEmpty: security.storageEmpty,
    forbiddenWalletWordingAbsent: security.forbiddenWalletWordingCount === 0,
    loginCredentialWordingSeparated: happyPath.loginCredentialWordingSeparated,
    setupSecretWriteOnly: happyPath.setupSecurity.setupSecretWriteOnly,
    setupSecretRedacted: happyPath.setupSecurity.setupSecretRedacted,
    failureProbesPassed: failureProbes.passed,
    externalRequestCount: security.externalRequestCount,
  };
  extraLiveGateReport = {
    dryRunDefault: happyPath.setupWizard.dryRunDefault,
    livePreviewBlocked: happyPath.setupSecurity.livePreviewBlocked,
    livePreviewText: happyPath.setupSecurity.livePreviewText,
    liveWarningText: happyPath.setupSecurity.liveWarningText,
    passed: happyPath.setupSecurity.liveGateWarningsPresent,
  };
  writeFileSync(join(evidenceDir, "server.log"), redact(serverLogs.join("")));
}

try {
  await main();
  record("qa-pass");
  process.exitCode = 0;
} catch (error) {
  record("qa-fail", { message: redact(error.message) });
  writeJson("failure.json", {
    message: redact(error.message),
    stack: redact(error.stack ?? ""),
    actionLog,
    requests,
    consoleMessages,
  });
  process.exitCode = 1;
} finally {
  await cleanupT10Runtime({
    browser,
    cleanup,
    evidenceDir,
    extraEvidenceDir,
    keepTemp: process.env.NFI_BROWSER_QA_KEEP_TEMP === "1",
    port,
    reports: {
      failureProbes: extraFailureProbeReport,
      liveGate: extraLiveGateReport,
      security: extraSecurityReport,
    },
    serverProcess,
    tempDir,
  });
}
