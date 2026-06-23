# UI GUIDE

## OVERVIEW

`ui` renders the local operator console served by FastAPI. It is a compact
operations surface for Home, Settings, Logs, login, pairlist, readiness, i18n,
and local chart snapshots.

## STRUCTURE

```text
ui/
|-- pages.py, document.py      # page shell and render entrypoints
|-- home.py, settings_page.py  # operator screens
|-- logs_page.py, pairlist.py  # diagnostics and pairlist panels
|-- assets*.py                 # local CSS/JS strings
|-- i18n*.py                   # English, Korean, Greek text
`-- readiness.py, chart.py     # setup/safety/chart fragments
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Page shell | `document.py`, `pages.py` | Inject CSRF meta and local assets only. |
| Home | `home.py`, `assets_dashboard.py` | Setup, safety, chart, pairlist, support actions. |
| Settings | `settings_page.py`, `settings_fields.py`, `assets_settings.py` | Simple Mode; write-only secrets. |
| Logs | `logs_page.py`, `assets_logs.py` | Error lookup, events, support report export. |
| Text | `i18n_keys.py`, `i18n_en.py`, `i18n_ko.py`, `i18n_el.py` | Machine codes stay untranslated. |

## CONVENTIONS

- This is not a public marketing dashboard. Keep screens operational, dense enough to scan, and local-first.
- No external CDN, remote font, remote chart library, or third-party browser asset. Use local inline assets.
- Never use `localStorage` or `sessionStorage` for bearer tokens, CSRF tokens, settings drafts, or secrets.
- Browser mutations read CSRF from `<meta name="nfi-csrf-token">` and send `x-nfi-csrf-token`.
- Read-only mode disables visible controls, but the server must still be the real blocker.
- Secrets are write-only: do not put API keys, API secrets, bearer tokens, or webhook values into HTML values.
- Keep contract IDs, machine codes, audit event IDs, and API field names stable across translations.
- UI must stay visually original; do not imitate FreqUI navigation, card composition, colors, or copy.

## ANTI-PATTERNS

- Do not add marketing hero sections, decorative dashboard mosaics, external
  assets, or broad analytics cockpit behavior.
- Do not hide the first-run path behind raw YAML as the primary workflow.
- Do not translate machine codes or make support reports harder to search.
- Do not make client-side JavaScript the source of truth for safety, read-only, auth, or config validation.
- Do not add generated screenshots or browser artifacts to source paths; evidence belongs under `.omo/evidence/`.
