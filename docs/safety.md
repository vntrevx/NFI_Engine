# Safety Guardrails

NFI Engine M1 is limited to simulator, paper, and testnet workflows. Confirmed live
configuration can be parsed for validation, but runtime commands reject it with
`LIVE_TRADING_OUT_OF_SCOPE`.

The API defaults to `127.0.0.1`, does not enable CORS by default, and rejects weak
operator tokens outside local/dev/test environments. Config and support surfaces redact
API tokens and exchange credentials as `REDACTED`.

Futures mode emits operator warnings for the one-bot-per-account assumption, leverage
risk, and cross-margin account risk. These warnings are surfaced through the typed
`safety` service so later UI and preflight tasks can expose them without copying trading
logic.
