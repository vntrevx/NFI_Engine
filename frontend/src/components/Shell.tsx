import { Activity, FileText, Gauge, Settings } from "lucide-react";
import type { ReactNode } from "react";

import { text } from "../i18n";
import type { Locale, PageId } from "../types";
import { Pill } from "./primitives";

const NAV_ITEMS: readonly { id: PageId; href: string; icon: ReactNode }[] = [
  { id: "home", href: "/", icon: <Gauge aria-hidden="true" size={17} /> },
  { id: "settings", href: "/settings", icon: <Settings aria-hidden="true" size={17} /> },
  { id: "logs", href: "/logs", icon: <FileText aria-hidden="true" size={17} /> },
];

export function Shell(props: {
  children: ReactNode;
  locale: Locale;
  page: PageId;
  exchange: string;
  mode: string;
  botState: string;
}): ReactNode {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand-lockup" href="/">
          <span className="brand-mark">N</span>
          <span>
            <strong>{text(props.locale, "brand")}</strong>
            <small>X7 native operator</small>
          </span>
        </a>
        <nav aria-label="Primary" data-testid="home-nav">
          {NAV_ITEMS.map((item) => (
            <a
              aria-current={item.id === props.page ? "page" : undefined}
              href={item.href}
              key={item.id}
            >
              {item.icon}
              {text(props.locale, item.id)}
            </a>
          ))}
        </nav>
        <div className="status-strip">
          <Pill tone="info">{props.exchange}</Pill>
          <Pill tone="neutral">{props.mode}</Pill>
          <Pill tone={props.botState === "running" ? "good" : "warn"}>
            <Activity aria-hidden="true" size={14} />
            {props.botState}
          </Pill>
        </div>
      </header>
      {props.children}
    </div>
  );
}
