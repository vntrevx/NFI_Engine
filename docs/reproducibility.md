# Reproducibility

Backtests and walk-forward validation write deterministic metadata so an
operator can compare runs without guessing which config or candle file was used.

## Backtest Metadata

```bash
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/backtest.json
```

The JSON output includes summary results plus metadata for:

- config digest
- strategy identity
- candle source
- timerange
- command arguments
- simulator scenario hash and seed when provided

## Walk-Forward Validation

```bash
uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/walk-forward.json
```

Validation splits are serialized to make run comparisons stable.

## Simulator-Aware Runs

```bash
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --simulator-scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/backtest-sim.json
```

Use this when reviewing slippage, partial fills, fees, funding, or exchange
reject behavior.

## Limitations

Reproducibility metadata proves which inputs and code path produced a local
result. It does not prove strategy profitability, exchange fill realism, or
future performance. Keep simulator scenario hashes and candle fixtures with the
review packet when comparing runs.
