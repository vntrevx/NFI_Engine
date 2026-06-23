export async function exerciseFailureProbes(page, baseUrl, context) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  const csrfToken = await page.locator('meta[name="nfi-csrf-token"]').getAttribute("content");
  if (!csrfToken) {
    throw new Error("missing CSRF token meta for failure probes");
  }

  const missingCsrf = await postJsonFromPage(page, "/api/v1/config/apply", {
    fields: [{ path: "risk.max_open_trades", value: "4" }],
  });
  const invalidCsrf = await postJsonFromPage(
    page,
    "/api/v1/config/apply",
    { fields: [{ path: "risk.max_open_trades", value: "4" }] },
    "wrong-csrf-token",
  );
  const unsafeLiveIntent = await postJsonFromPage(page, "/api/v1/setup/preview", {
    exchange: "bybit",
    trading_mode: "futures",
    intent: "live",
    api_key: "qa-live-key",
    api_secret: context.qaExchangeSecret,
    risk_preset: "conservative",
    allocated_amount_usdt: "42.5",
    permission_read: "enabled",
    permission_trade: "enabled",
    permission_futures: "enabled",
    permission_withdrawal: "disabled",
  });
  const badWalletPermission = await postJsonFromPage(page, "/api/v1/setup/preview", {
    exchange: "bybit",
    trading_mode: "futures",
    intent: "live",
    api_key: "qa-withdrawal-key",
    api_secret: context.qaExchangeSecret,
    risk_profile: "safe",
    live_trading_confirmed: true,
    permission_withdrawal: "enabled",
  });
  const readOnlyEnable = await postJsonFromPage(
    page,
    "/api/v1/config/apply",
    { fields: [{ path: "ui.read_only", value: "true" }] },
    csrfToken,
  );
  const readOnlyApply = await postJsonFromPage(
    page,
    "/api/v1/config/apply",
    { fields: [{ path: "risk.max_open_trades", value: "4" }] },
    csrfToken,
  );
  const readOnlyRuntime = await postJsonFromPage(
    page,
    "/api/v1/runtime/control",
    { command: "start" },
    csrfToken,
  );
  const securityAuditLog = await page.evaluate(async () => {
    const response = await fetch("/api/v1/security/audit", { credentials: "same-origin" });
    const text = await response.text();
    let payload = null;
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
    return { status: response.status, ok: response.ok, payload, text };
  });

  const raw = {
    missingCsrf,
    invalidCsrf,
    unsafeLiveIntent,
    badWalletPermission,
    readOnlyEnable,
    readOnlyApply,
    readOnlyRuntime,
    securityAuditLog,
  };
  const rawText = JSON.stringify(raw);
  const failures = [
    errorCode(missingCsrf) === "CSRF_TOKEN_REQUIRED" ? null : "missing CSRF did not block config apply",
    errorCode(invalidCsrf) === "CSRF_TOKEN_INVALID" ? null : "invalid CSRF did not block config apply",
    setupErrors(unsafeLiveIntent).includes("LIVE_TRADING_REQUIRES_CONFIRMATION")
      ? null
      : "unsafe live intent was not blocked",
    setupErrors(badWalletPermission).includes("EXCHANGE_WITHDRAWAL_PERMISSION_ENABLED")
      ? null
      : "withdrawal permission was not blocked",
    readOnlyEnable.status === 200 && readOnlyEnable.payload?.applied === true
      ? null
      : "read-only mode could not be enabled",
    errorCode(readOnlyApply) === "READONLY_ACTION_BLOCKED" ? null : "read-only config apply was not blocked",
    errorCode(readOnlyRuntime) === "READONLY_ACTION_BLOCKED"
      ? null
      : "read-only runtime control was not blocked",
    auditCodes(securityAuditLog).includes("READONLY_ACTION_BLOCKED")
      ? null
      : "read-only audit event was not recorded",
    rawText.includes(context.qaExchangeSecret) ? "exchange secret leaked in failure probe response" : null,
    rawText.includes(context.qaToken) ? "QA token leaked in failure probe response" : null,
  ].filter(Boolean);

  const report = {
    passed: failures.length === 0,
    failures,
    missingCsrf: redactForEvidence(missingCsrf, context.redact),
    invalidCsrf: redactForEvidence(invalidCsrf, context.redact),
    unsafeLiveIntent: redactForEvidence(unsafeLiveIntent, context.redact),
    badWalletPermission: redactForEvidence(badWalletPermission, context.redact),
    readOnlyEnable: redactForEvidence(readOnlyEnable, context.redact),
    readOnlyApply: redactForEvidence(readOnlyApply, context.redact),
    readOnlyRuntime: redactForEvidence(readOnlyRuntime, context.redact),
    securityAuditLog: redactForEvidence(securityAuditLog, context.redact),
  };
  context.record("failure-probes-complete", {
    passed: report.passed,
    failures,
  });
  return report;
}

async function postJsonFromPage(page, path, body, csrfToken = null) {
  return await page.evaluate(
    async ({ path, body, csrfToken }) => {
      const headers = { "content-type": "application/json" };
      if (csrfToken !== null) {
        headers["x-nfi-csrf-token"] = csrfToken;
      }
      const response = await fetch(path, {
        method: "POST",
        headers,
        credentials: "same-origin",
        body: JSON.stringify(body),
      });
      const text = await response.text();
      let payload = null;
      try {
        payload = JSON.parse(text);
      } catch {
        payload = null;
      }
      return { status: response.status, ok: response.ok, payload, text };
    },
    { path, body, csrfToken },
  );
}

function auditCodes(result) {
  return Array.isArray(result.payload?.items) ? result.payload.items.map((item) => item.code) : [];
}

function errorCode(result) {
  return result.payload?.detail?.code ?? null;
}

function redactForEvidence(value, redact) {
  return JSON.parse(redact(JSON.stringify(value)));
}

function setupErrors(result) {
  return Array.isArray(result.payload?.errors) ? result.payload.errors : [];
}
