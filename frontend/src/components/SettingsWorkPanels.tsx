import { RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import {
  lifecycleExport,
  lifecycleFootprint,
  lifecyclePrune,
  pairlistApply,
  pairlistDraft,
  pairlistPreview,
  updateApply,
  updatePreview,
  updateRollback,
} from "../api";
import type { useActionState } from "../hooks";
import { text } from "../i18n";
import type { Locale } from "../types";
import { ActionButton, StateBlock } from "./primitives";

type ActionController = ReturnType<typeof useActionState>;

export function SettingsWorkPanels(props: {
  blacklist: string;
  setBlacklist: (value: string) => void;
  update: ActionController;
  lifecycle: ActionController;
  locale: Locale;
  pairlist: ActionController;
}): ReactNode {
  return (
    <section className="work-panels">
      <UpdatePanel locale={props.locale} update={props.update} />
      <LifecyclePanel lifecycle={props.lifecycle} locale={props.locale} />
      <PairlistPanel
        blacklist={props.blacklist}
        locale={props.locale}
        pairlist={props.pairlist}
        setBlacklist={props.setBlacklist}
      />
    </section>
  );
}

function UpdatePanel(props: { locale: Locale; update: ActionController }): ReactNode {
  return (
    <details data-testid="settings-update-drawer">
      <summary data-testid="settings-update-panel">
        <RefreshCw size={16} />
        {text(props.locale, "developerUpdate")}
      </summary>
      <div className="button-row">
        <ActionButton onClick={() => void props.update.run(updatePreview)} testId="update-preview-button">
          {text(props.locale, "preview")}
        </ActionButton>
        <ActionButton onClick={() => void props.update.run(updateApply)} testId="update-apply-button">
          {text(props.locale, "apply")}
        </ActionButton>
        <ActionButton onClick={() => void props.update.run(updateRollback)} testId="update-rollback-button">
          Rollback
        </ActionButton>
      </div>
      <StateBlock testId="update-preview-state">{props.update.state}</StateBlock>
      <StateBlock testId="update-apply-state">{props.update.state}</StateBlock>
      <StateBlock testId="update-rollback-state">{props.update.state}</StateBlock>
    </details>
  );
}

function LifecyclePanel(props: { lifecycle: ActionController; locale: Locale }): ReactNode {
  return (
    <details data-testid="data-lifecycle-drawer">
      <summary>{text(props.locale, "localLifecycle")}</summary>
      <div className="button-row">
        <ActionButton onClick={() => void props.lifecycle.run(lifecycleFootprint)} testId="data-lifecycle-inspect-button">
          Inspect
        </ActionButton>
        <ActionButton onClick={() => void props.lifecycle.run(lifecycleExport)} testId="data-lifecycle-export-button">
          Export
        </ActionButton>
        <ActionButton onClick={() => void props.lifecycle.run(lifecyclePrune)} testId="data-lifecycle-dry-run-button">
          Dry-run prune
        </ActionButton>
      </div>
      <StateBlock testId="data-lifecycle-footprint-state">{props.lifecycle.state}</StateBlock>
      <StateBlock testId="data-lifecycle-export-state">{props.lifecycle.state}</StateBlock>
      <StateBlock testId="data-lifecycle-prune-state">{props.lifecycle.state}</StateBlock>
    </details>
  );
}

function PairlistPanel(props: {
  blacklist: string;
  locale: Locale;
  setBlacklist: (value: string) => void;
  pairlist: ActionController;
}): ReactNode {
  return (
    <details data-testid="pairlist-drawer">
      <summary>{text(props.locale, "pairlist")}</summary>
      <textarea
        data-testid="pairlist-blacklist"
        onChange={(event) => props.setBlacklist(event.target.value)}
        value={props.blacklist}
      />
      <div className="button-row">
        <ActionButton onClick={() => void props.pairlist.run(() => pairlistPreview(props.blacklist))} testId="pairlist-preview-button">
          {text(props.locale, "preview")}
        </ActionButton>
        <ActionButton onClick={() => void props.pairlist.run(() => pairlistDraft(props.blacklist))} testId="pairlist-save-draft-button">
          {text(props.locale, "saveDraft")}
        </ActionButton>
        <ActionButton onClick={() => void props.pairlist.run(() => pairlistApply(props.blacklist))} testId="pairlist-apply-button">
          {text(props.locale, "apply")}
        </ActionButton>
      </div>
      <StateBlock testId="pairlist-preview-state">{props.pairlist.state}</StateBlock>
      <StateBlock testId="pairlist-audit-log">{props.pairlist.state}</StateBlock>
    </details>
  );
}
