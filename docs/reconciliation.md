# Exchange Reconciliation

Reconciliation compares local runtime state with exchange-like snapshots before
startup or recovery.

## Match Check

```bash
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
```

## Mismatch Check

```bash
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_mismatch.json
```

Mismatch output includes typed drift categories such as orphan orders, missing
fills, balance drift, position mismatch, leverage mismatch, margin mismatch,
duplicate trades, and stale locks.

## Startup Rule

If reconciliation says startup recovery is required, do not start paper/live
loops until the drift is explained or intentionally repaired.

## Limitations

M1 reconciliation uses fixtures and adapter contracts. Real exchange account
repair is later milestone work.
