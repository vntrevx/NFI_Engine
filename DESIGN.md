# NFI Engine UI Design System

## Product Surface

NFI Engine is a local operator console for paper/testnet trading research. It is
not a public marketing site. The first screen must stay operational, dense, and
quiet enough for repeated checks.

## Layout

- Main content is constrained to `1160px` with `24px` desktop padding and `16px`
  mobile padding.
- Home uses a compact status strip and a two-column dashboard grid that
  collapses to one column below `780px`.
- Sections are bordered operational panels with `6px` radius; avoid nested
  cards and decorative wrappers.

## Color

- Background: `#f5f7f6`
- Panel: `#ffffff`
- Text: `#17201d`
- Muted text: `#5b6863`
- Border: `#ccd6d1`
- Accent: `#0f766e`
- Danger: `#b42318`
- Warning: `#9a6700`

## Typography

Use the existing system font stack from `src/nfi_engine/ui/assets.py`.
Headings are compact: `24px` for the page title and `15px` for panel headings.
Letter spacing stays `0`.

## Controls

Buttons, inputs, and selects use `5px` radius, local CSS only, and stable
minimum heights. Disabled controls are visual hints only; server-side guards
remain authoritative.

## Localization

Visible operator text must use typed i18n keys for English, Korean, and Greek.
Machine codes, contract ids, API field names, strategy tags, and evidence paths
stay untranslated.

## Safety Copy

UI text may say paper/testnet-ready or gated when the checks support it. It must
not claim live readiness, strategy parity, profit, or superiority.
