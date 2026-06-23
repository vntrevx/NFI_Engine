import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export function credentialWordsAppear(text) {
  return /api\s*(key|secret)|exchange\s*(key|secret)|private\s*key|seed\s*phrase/i.test(text);
}

export async function securityAudit({ invalidLogin, happyPath, storage, visual, failureProbes }, context) {
  const externalRequests = context.requests.filter((request) => !request.isLocal);
  const consoleErrors = context.consoleMessages.filter((message) => message.type === "error");
  const unexpectedConsoleErrors = consoleErrors.filter(
    (message) => !isExpectedConsoleError(message.text),
  );
  const tokenLeakFiles = scanEvidenceForSensitive(context.qaToken, "qa-token", context);
  const exchangeSecretLeakFiles = scanEvidenceForSensitive(
    context.qaExchangeSecret,
    "exchange-secret",
    context,
  );
  const horizontalOverflow = visual.captures.filter((capture) => capture.horizontalOverflowPx > 2);
  const forbiddenWalletWordingCount = forbiddenWalletWordingCountIn(happyPath);
  const failures = [
    invalidLogin.denied ? null : "invalid login did not remain denied",
    happyPath.loginCredentialWordingSeparated ? null : "login token wording overlaps exchange API credentials",
    happyPath.setupWizard.exactOrder ? null : "setup wizard order does not match T14",
    happyPath.setupWizard.dryRunDefault ? null : "dry-run is not the setup default",
    happyPath.setupWizard.recommendedLeverageDefault3x ? null : "recommended leverage is not 3x",
    happyPath.setupWizardGreek.recommendedLeverageDefault3x ? null : "Greek setup wizard lost 3x leverage",
    happyPath.cockpit.present ? null : "home cockpit is incomplete",
    happyPath.setupWizard.updatePanelPresent ? null : "settings update panel is missing",
    happyPath.setupSecurity.setupSecretWriteOnly ? null : "setup secret input is not password-only",
    happyPath.setupSecurity.setupSecretRedacted ? null : "setup secret preview is not redacted",
    happyPath.setupSecurity.liveGateWarningsPresent ? null : "live gate warning is incomplete",
    happyPath.setupSecurity.livePreviewBlocked ? null : "live preview is not blocked",
    happyPath.settingsKoVisible && happyPath.logsKoVisible ? null : "Korean settings/logs did not render",
    happyPath.settingsElVisible && happyPath.logsElVisible ? null : "Greek settings/logs did not render",
    happyPath.languageSwitches.enToKo.manualRefresh === false ? null : "Korean locale required manual refresh",
    happyPath.languageSwitches.koToEl.manualRefresh === false ? null : "Greek locale required manual refresh",
    failureProbes.passed ? null : "failure probes did not block unsafe actions",
    storage.localStorage.length === 0 ? null : "localStorage is not empty",
    storage.sessionStorage.length === 0 ? null : "sessionStorage is not empty",
    externalRequests.length === 0 ? null : "external network request detected",
    tokenLeakFiles.length === 0 ? null : "QA token leaked into evidence",
    exchangeSecretLeakFiles.length === 0 ? null : "exchange secret leaked into evidence",
    unexpectedConsoleErrors.length === 0 ? null : "unexpected browser console error detected",
    horizontalOverflow.length === 0 ? null : "mobile horizontal overflow detected",
    forbiddenWalletWordingCount === 0 ? null : "forbidden wallet key wording detected",
  ].filter(Boolean);
  const audit = {
    passed: failures.length === 0,
    failures,
    invalidLogin,
    storageEmpty: storage.localStorage.length === 0 && storage.sessionStorage.length === 0,
    externalRequestCount: externalRequests.length,
    externalRequests,
    consoleErrorCount: consoleErrors.length,
    consoleErrors,
    unexpectedConsoleErrorCount: unexpectedConsoleErrors.length,
    unexpectedConsoleErrors,
    tokenLeakCount: tokenLeakFiles.length,
    tokenLeakFiles,
    exchangeSecretLeakCount: exchangeSecretLeakFiles.length,
    exchangeSecretLeakFiles,
    forbiddenWalletWordingCount,
    horizontalOverflow,
    failureProbes,
  };
  if (!audit.passed) {
    throw new Error(`browser QA security audit failed: ${failures.join("; ")}`);
  }
  return audit;
}

function forbiddenWalletWordingCountIn(happyPath) {
  const text = JSON.stringify({
    cockpit: happyPath.cockpit.values,
    setupWizard: happyPath.setupWizard,
    setupSecurity: happyPath.setupSecurity,
  });
  return (text.match(/seed phrase|private key|mnemonic|wallet seed/gi) ?? []).length;
}

function isExpectedConsoleError(text) {
  return text.includes("status of 401 (Unauthorized)") || text.includes("status of 403 (Forbidden)");
}

function scanEvidenceForSensitive(secret, label, context) {
  const inMemoryLeaks = [
    ["action-log", JSON.stringify(context.actionLog)],
    ["console-summary", JSON.stringify(context.consoleMessages)],
    ["network-summary", JSON.stringify(context.requests)],
  ]
    .filter(([, text]) => text.includes(secret))
    .map(([name]) => `${label}:${name}:memory`);
  const files = [
    "login-empty-desktop.png",
    "home-desktop.png",
    "settings-ko-desktop.png",
    "settings-el-desktop.png",
    "logs-ko-desktop.png",
    "logs-el-desktop.png",
    "home-mobile.png",
    "settings-ko-mobile.png",
    "settings-el-mobile.png",
    "logs-ko-mobile.png",
    "logs-el-mobile.png",
    "action-log.json",
    "console-summary.json",
    "network-summary.json",
  ];
  const fileLeaks = files.filter((name) => {
    const path = join(context.evidenceDir, name);
    return existsSync(path) && readFileSync(path).includes(secret);
  });
  return [...inMemoryLeaks, ...fileLeaks];
}
