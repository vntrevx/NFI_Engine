# NFI Engine UI Design System

## Product Surface

NFI Engine is a local operator console for paper/testnet trading research. It is
not a public marketing site. The first screen must stay operational, dense, and
quiet enough for repeated checks.

## Layout

- Main content is constrained to `1180px` with `24px` desktop padding and `16px`
  mobile padding.
- Home uses a compact status strip and a two-column dashboard grid that
  collapses to one column below `780px`.
- Settings uses a two-column operator layout: first-run setup stays primary on
  the left, while config editing, exchange registry, readiness, runtime
  controls, pairlist, data lifecycle, updates, and safety gates live in a
  compact disclosure rail on the right.
  Safety limit presets stay out of first-run setup and Simple Mode; they belong
  in Safety gates as a separate guardrail control.
- The first viewport is an operator cockpit, not a landing page. Status,
  safety, and next action must stay visible without scrolling on desktop.
- Sections are bordered operational panels with `6px` radius; avoid nested
  cards and decorative wrappers.
- Login is a focused operator account panel with a narrow system-status rail,
  not a token paste utility.
- Exchange selection must come from the local capability registry. Verified,
  candidate, and generic support levels stay visible as badges; do not hide
  unverified status behind a friendly label.

## Color

- Background: `#f3f6f4`
- Background rail: `#e7eeea`
- Panel: `#ffffff`
- Panel subtle: `#f9fbfa`
- Text: `#16201c`
- Muted text: `#61706a`
- Border: `#c8d5cf`
- Border strong: `#a9bbb2`
- Accent: `#0f766e`
- Accent strong: `#0b5f59`
- Accent soft: `#dff1ed`
- Danger: `#b42318`
- Danger soft: `#fff1f0`
- Warning: `#9a6700`
- Warning soft: `#fff7df`
- Focus: `#134e4a`

## Typography

Use the existing system font stack from `src/nfi_engine/ui/assets.py`.
Headings are compact: `24px` for the page title and `15px` for panel headings.
Letter spacing stays `0`. Data, timestamps, machine codes, and money figures use
tabular numbers.

## Controls

Buttons, inputs, and selects use `5px` radius, local CSS only, and stable
minimum heights. Disabled controls are visual hints only; server-side guards
remain authoritative.

Repeated operational cells use the `.metric`, `.cockpit-item`, `.update-state`,
and `.x7-status-item` patterns: subtle panel fill, one-token border, tabular
numbers, and no heavy shadows.

Exchange registry rows use compact button rows with `.support-badge`,
`.capability-pills`, and `.exchange-evidence`. They are controls, not
decorative cards, and must keep long evidence paths wrapping safely.

Settings disclosure rails use `.settings-drawer` with one visible summary row
per secondary tool. Drawers preserve every control in the DOM, but avoid making
diagnostics, update actions, and capability evidence compete with the first-run
setup path in the first viewport.

## Localization

Visible operator text must use typed i18n keys for English, Korean, and Greek.
Machine codes, contract ids, API field names, strategy tags, and evidence paths
stay untranslated.

## Safety Copy

UI text may say paper/testnet-ready or gated when the checks support it. It must
not claim live readiness, strategy parity, profit, or superiority.
