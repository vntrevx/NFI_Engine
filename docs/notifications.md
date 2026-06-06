# Notifications

Notifications send typed operator events to local or test endpoints. They are
for diagnostics and maintenance feedback, not trading signals.

## JSONL Dry Run

```bash
uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message smoke --output .omo/evidence/notify.jsonl
```

The JSONL adapter is the default safe path for local QA.

## HTTP/Webhook Adapters

Webhook settings are validated through config and preflight. Timeout, retry, and
disabled-notifier cases are covered by fixture configs under `tests/fixtures/config`.

## Error Reporting

When a user reports a problem, ask for:

- error code
- correlation ID
- safe summary
- support report zip from `/logs`

Do not ask users to paste raw exchange secrets or unredacted config.
