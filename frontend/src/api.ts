import type {
  ApiMethod,
  ConfigCurrent,
  DashboardSnapshot,
  LogList,
  RuntimeControl,
  SetupForm,
  WalletBalance,
} from "./types";

type JsonBody = Record<string, unknown>;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function csrfToken(): string {
  return document.querySelector<HTMLMetaElement>('meta[name="nfi-csrf-token"]')?.content ?? "";
}

export async function apiRequest<T>(
  path: string,
  options: { method?: ApiMethod; body?: JsonBody; csrf?: boolean } = {},
): Promise<T> {
  const headers = new Headers({ accept: "application/json" });
  if (options.body !== undefined) {
    headers.set("content-type", "application/json");
  }
  if (options.csrf === true) {
    headers.set("x-nfi-csrf-token", csrfToken());
  }
  const request: RequestInit = {
    method: options.method ?? "GET",
    headers,
    credentials: "same-origin",
  };
  if (options.body !== undefined) {
    request.body = JSON.stringify(options.body);
  }
  const response = await fetch(path, request);
  if (!response.ok) {
    throw new ApiError(response.status, `HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export function loadDashboard(): Promise<DashboardSnapshot> {
  return apiRequest<DashboardSnapshot>("/api/v1/dashboard/snapshot");
}

export function loadConfig(): Promise<ConfigCurrent> {
  return apiRequest<ConfigCurrent>("/api/v1/config/current");
}

export function loadWallet(): Promise<WalletBalance> {
  return apiRequest<WalletBalance>("/api/v1/wallet/balance");
}

export function fetchWallet(): Promise<WalletBalance> {
  return apiRequest<WalletBalance>("/api/v1/wallet/balance/fetch", { method: "POST" });
}

export function loadRuntimeControl(): Promise<RuntimeControl> {
  return apiRequest<RuntimeControl>("/api/v1/runtime/control");
}

export function loadRuntimeHealth(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/runtime/health");
}

export function postRuntimeCommand(command: string): Promise<RuntimeControl> {
  return apiRequest<RuntimeControl>("/api/v1/runtime/control", {
    method: "POST",
    body: { command },
    csrf: true,
  });
}

export function loadLogs(severity = ""): Promise<LogList> {
  const suffix = severity === "" ? "" : `?severity=${encodeURIComponent(severity)}`;
  return apiRequest<LogList>(`/api/v1/logs/recent${suffix}`);
}

export function lookupError(code: string): Promise<unknown> {
  return apiRequest<unknown>(`/api/v1/errors/${encodeURIComponent(code)}`);
}

export function applyLocale(locale: string): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/config/apply", {
    method: "POST",
    body: { fields: [{ path: "ui.locale", value: locale }] },
    csrf: true,
  });
}

export function validateConfig(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/config/validate", { method: "POST", body: { fields: [] } });
}

export function draftConfig(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/config/draft", {
    method: "POST",
    body: { fields: [] },
    csrf: true,
  });
}

export function previewSetup(form: SetupForm): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/setup/preview", {
    method: "POST",
    body: {
      exchange: form.exchange,
      trading_mode: form.trading_mode,
      intent: form.intent,
      api_key: form.api_key,
      api_secret: form.api_secret,
      allocated_amount_usdt: form.allocated_amount_usdt || null,
      risk_preset: "balanced",
      permission_read: "unknown",
      permission_trade: "unknown",
      permission_futures: "unknown",
      permission_withdrawal: "unknown",
      permission_ip_allowlist: "unknown",
      live_trading_confirmed: false,
      locale: form.locale,
    },
  });
}

export function updatePreview(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/update/preview");
}

export function updateApply(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/update/apply", {
    method: "POST",
    body: { acknowledge_unverified: true, allow_dirty_worktree: true },
    csrf: true,
  });
}

export function updateRollback(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/update/rollback", {
    method: "POST",
    body: { acknowledge_unverified: true, allow_dirty_worktree: true },
    csrf: true,
  });
}

export function lifecycleFootprint(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/data-lifecycle/footprint");
}

export function lifecycleExport(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/data-lifecycle/export");
}

export function lifecyclePrune(): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/data-lifecycle/prune", {
    method: "POST",
    body: { dry_run: true },
    csrf: true,
  });
}

export function pairlistPreview(blacklist: string): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/pairlist/preview", {
    method: "POST",
    body: { blacklist },
  });
}

export function pairlistDraft(blacklist: string): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/pairlist/draft", {
    method: "POST",
    body: { blacklist },
    csrf: true,
  });
}

export function pairlistApply(blacklist: string): Promise<unknown> {
  return apiRequest<unknown>("/api/v1/pairlist/apply", {
    method: "POST",
    body: { blacklist },
    csrf: true,
  });
}

export function compactJson(value: unknown): string {
  return JSON.stringify(value, null, 2).slice(0, 1200);
}
