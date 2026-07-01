import type { ReactNode } from "react";

type Tone = "neutral" | "good" | "warn" | "bad" | "info";

export function Panel(props: {
  title: string;
  kicker?: string;
  children: ReactNode;
  className?: string;
  testId?: string;
}): ReactNode {
  return (
    <section className={`panel ${props.className ?? ""}`} data-testid={props.testId}>
      <div className="panel-head">
        {props.kicker === undefined ? null : <span>{props.kicker}</span>}
        <h2>{props.title}</h2>
      </div>
      {props.children}
    </section>
  );
}

export function Pill(props: { children: ReactNode; tone?: Tone; testId?: string }): ReactNode {
  return (
    <span className={`pill pill-${props.tone ?? "neutral"}`} data-testid={props.testId}>
      {props.children}
    </span>
  );
}

export function DataTile(props: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  testId?: string;
}): ReactNode {
  return (
    <div className="data-tile" data-testid={props.testId}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      {props.detail === undefined ? null : <small>{props.detail}</small>}
    </div>
  );
}

export function ActionButton(props: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  testId?: string;
  command?: string;
  disabled?: boolean;
}): ReactNode {
  return (
    <button
      className="action-button"
      data-command={props.command}
      data-testid={props.testId}
      disabled={props.disabled}
      onClick={props.onClick}
      type={props.type ?? "button"}
    >
      {props.children}
    </button>
  );
}

export function Field(props: {
  id?: string;
  label: string;
  children: ReactNode;
  testId?: string;
  note?: string;
}): ReactNode {
  return (
    <label className="field" data-testid={props.testId}>
      <span>{props.label}</span>
      {props.children}
      {props.note === undefined ? null : <em className="field-note">{props.note}</em>}
    </label>
  );
}

export function MiniTape(props: { values: readonly number[] }): ReactNode {
  const max = Math.max(...props.values, 1);
  return (
    <div className="mini-tape" aria-hidden="true">
      {props.values.map((value, index) => (
        <span className={`bar-${barLevel(value, max)}`} key={`${value}-${index}`} />
      ))}
    </div>
  );
}

export function StateBlock(props: { children: ReactNode; testId: string }): ReactNode {
  return (
    <pre className="state-block" data-testid={props.testId}>
      {props.children}
    </pre>
  );
}

function barLevel(value: number, max: number): number {
  if (max <= 0) {
    return 1;
  }
  return Math.min(10, Math.max(1, Math.ceil((value / max) * 10)));
}
