import { rmSync } from "node:fs";
import { join } from "node:path";
import { onceExit, sleep, waitForPortClosed } from "./browser_qa_runtime.mjs";
import { writeFinalExtraArtifacts, writeJson } from "./browser_qa_t10_artifacts.mjs";

export function qaConfig(port, root) {
  const dbPath = join(root, "nfi-engine.sqlite3");
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
  url: sqlite+aiosqlite:///${dbPath}
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
`;
}

export function createRedactors(qaAuthSecrets, qaExchangeSecret) {
  const authSecrets = Array.isArray(qaAuthSecrets) ? qaAuthSecrets : [qaAuthSecrets];
  const redactSecret = (text) => text.replaceAll(qaExchangeSecret, "<redacted-exchange-secret>");
  return {
    redact: (text) =>
      redactSecret(
        authSecrets.reduce(
          (redacted, secret) =>
            secret ? redacted.replaceAll(secret, "<redacted-auth-secret>") : redacted,
          text,
        ),
      ),
    redactSecret,
  };
}

export function documentRequestCounter(requests) {
  return (pathname) =>
    requests.filter((request) => {
      const url = new URL(request.url);
      return request.resourceType === "document" && url.pathname === pathname;
    }).length;
}

export async function waitForServer(baseUrl, serverProcess, record) {
  const deadline = Date.now() + 30000;
  let lastError = "";
  while (Date.now() < deadline) {
    if (serverProcess.exitCode !== null) {
      throw new Error(`server exited before readiness: ${serverProcess.exitCode}`);
    }
    try {
      const response = await fetch(`${baseUrl}/api/v1/ping`);
      if (response.ok) {
        record("server-ready", { status: response.status });
        return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await sleep(250);
  }
  throw new Error(`server did not become ready: ${lastError}`);
}

export async function cleanupT10Runtime(context) {
  if (context.browser) {
    await context.browser.close();
    context.cleanup.push("browser closed");
  }
  if (context.serverProcess && context.serverProcess.exitCode === null) {
    context.serverProcess.kill("SIGTERM");
    await onceExit(context.serverProcess, 3000);
    context.cleanup.push("server process stopped");
  }
  if (context.port) {
    await waitForPortClosed(context.port);
    context.cleanup.push(`port ${context.port} closed`);
  }
  if (context.tempDir && !context.keepTemp) {
    rmSync(context.tempDir, { recursive: true, force: true });
    context.cleanup.push("temp dir removed");
  }
  writeJson(context.evidenceDir, "cleanup.json", {
    cleanup: context.cleanup,
    at: new Date().toISOString(),
  });
  writeFinalExtraArtifacts(context.extraEvidenceDir, context.cleanup, context.reports);
}
