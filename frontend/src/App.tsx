import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { loadConfig, loadDashboard } from "./api";
import { FALLBACK_CONFIG, FALLBACK_DASHBOARD } from "./fallbacks";
import { useAsyncResource } from "./hooks";
import { normalizeLocale, pageTitle } from "./i18n";
import { HomePanel } from "./components/HomePanel";
import { LogsPanel } from "./components/LogsPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { Shell } from "./components/Shell";
import type { Locale, PageId } from "./types";

export function App(): ReactNode {
  const [locale, setLocale] = useState<Locale>(normalizeLocale(document.documentElement.lang));
  const page = useMemo(pageFromPath, []);
  const config = useAsyncResource(useCallback(loadConfig, []), FALLBACK_CONFIG);
  const dashboard = useAsyncResource(useCallback(loadDashboard, []), FALLBACK_DASHBOARD);
  const currentConfig = config.data ?? FALLBACK_CONFIG;
  const snapshot = dashboard.data ?? FALLBACK_DASHBOARD;

  useEffect(() => {
    document.title = pageTitle(locale, page);
  }, [locale, page]);

  return (
    <Shell
      botState={snapshot.bot_state}
      exchange={currentConfig.exchange.name}
      locale={locale}
      mode={currentConfig.exchange.trading_mode}
      page={page}
    >
      {renderPage(page, locale, setLocale)}
    </Shell>
  );
}

function renderPage(
  page: PageId,
  locale: Locale,
  setLocale: (locale: Locale) => void,
): ReactNode {
  if (page === "settings") {
    return <SettingsPanel locale={locale} onLocaleChange={setLocale} />;
  }
  if (page === "logs") {
    return <LogsPanel locale={locale} />;
  }
  return <HomePanel locale={locale} />;
}

function pageFromPath(): PageId {
  if (window.location.pathname === "/settings") {
    return "settings";
  }
  if (window.location.pathname === "/logs") {
    return "logs";
  }
  return "home";
}
