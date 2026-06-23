# API GUIDE

## OVERVIEW

`api` owns FastAPI app construction, HTTP contracts, route wiring, auth/session
security, read-only enforcement, config editing, dashboard data, and HTML page
handoffs to `ui`.

## STRUCTURE

```text
api/
|-- app.py                 # application factory
|-- routes.py              # core public/protected/write API routes
|-- security.py            # bearer/session/CSRF/read-only enforcement
|-- security_routes.py     # login/logout/session/audit routes
|-- config_*.py            # current/schema/validate/draft/apply flows
|-- dashboard*.py          # dashboard read models and routes
|-- setup_routes.py        # setup preview/apply boundary
|-- ui.py                  # HTML route adapter into src/nfi_engine/ui
`-- models.py              # API request/response contracts
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Add route | `routes.py` or focused `*_routes.py` | Choose public, protected, or write dependency deliberately. |
| Auth/session change | `security.py`, `security_routes.py` | Cover bearer, cookie session, CSRF, expiry, audit. |
| Config mutation | `config_edit.py`, `config_routes.py` | Validate, draft, apply; redact secrets. |
| UI page access | `ui.py` | Hydrate session and pass CSRF into renderers. |
| API contracts | `models.py` | Stable machine codes and redacted responses. |

## CONVENTIONS

- Public routes are rare. Protected routes require operator auth; write routes also require CSRF and non-read-only mode.
- Mutating browser requests need both a valid session cookie and matching `x-nfi-csrf-token`.
- Read-only mode is enforced server-side through `require_write()` and must create an audit event when blocked.
- Reject URL/query bearer-token patterns for WebSocket or browser flows; session cookie plus CSRF is the UI path.
- Weak operator tokens are allowed only in local/dev/test contexts; production-like config must fail startup/readiness.
- Redacted API responses must never expose exchange keys, API secrets, bearer
  tokens, webhook URLs, or support-bundle secrets.
- API tests should cover both the direct contract and the user surface that calls it when behavior is operator-visible.

## ANTI-PATTERNS

- Do not rely on disabled UI controls as the only write protection.
- Do not add a write endpoint without auth, CSRF, read-only, validation, and a targeted test.
- Do not pass raw YAML, raw storage rows, or unredacted config through response models.
- Do not store bearer tokens in page state, URLs, local storage, session storage, logs, screenshots, or support reports.
- Do not broaden anonymous access because a local test is inconvenient; configure the test context explicitly.
