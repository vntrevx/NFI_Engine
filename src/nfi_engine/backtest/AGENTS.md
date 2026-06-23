# BACKTEST GUIDE

## OVERVIEW

`backtest` owns deterministic historical execution, pricing, trade lifecycle,
result metadata, serialization, validation, and summaries for research runs.

## STRUCTURE

```text
backtest/
|-- runner.py          # main deterministic loop
|-- execution.py       # entry/exit execution decisions
|-- closing.py         # stop/final close handling
|-- frames.py          # strategy frame construction
|-- pricing.py         # fees, slippage, price helpers
|-- metadata.py        # reproducibility hashes
|-- models.py          # request/result/trade models
|-- validation.py      # input checks
`-- serialization.py, summary.py
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Run behavior | `runner.py`, `execution.py`, `closing.py` | Preserve order of lifecycle decisions. |
| Reproducibility | `metadata.py`, `serialization.py` | Config, strategy, data, engine, lock hashes. |
| Pricing | `pricing.py` | Fees/slippage should stay explicit and deterministic. |
| Result shape | `models.py`, `summary.py` | Keep JSON stable for CLI/evidence consumers. |
| Tests | `tests/unit/backtest`, `tests/e2e/test_backtest_cli.py` | Add fixture-backed cases. |

## CONVENTIONS

- Backtests must be reproducible from config, strategy, data, engine version, and dependency lock metadata.
- No wall-clock randomness in results except an explicit generated metadata timestamp.
- Keep strategy compatibility clean-room; use local NFI-shaped fixtures, not upstream strategy code.
- Reject malformed timeranges, missing columns, invalid strategy shapes, and unsafe assumptions with typed errors.
- Use deterministic fixtures for data and strategy behavior; do not rely on network or live exchange state.
- Public or performance claims need same-machine evidence and the allowed-claim flag from benchmark policy.

## ANTI-PATTERNS

- Do not mutate runtime config, database state, or exchange state from backtest code.
- Do not claim full NFI X7 parity from smoke compatibility alone.
- Do not hide rejected entries, forced exits, fee/slippage assumptions, or metadata gaps.
- Do not introduce pandas into new engine internals; isolate compatibility-only needs outside core execution.
- Do not change result JSON fields without updating CLI/e2e tests and evidence consumers.
