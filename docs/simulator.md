# Fill Simulator

The fill simulator models execution conditions that a naive candle backtest
would miss.

## Run A Scenario

```bash
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/slippage_spike.yaml --output .omo/evidence/slippage.json
```

Scenario fixtures cover:

- partial fills
- latency
- maker/taker fees
- funding accrual
- slippage anomalies
- exchange rejects
- liquidation near misses

## Backtest With Simulator Metadata

```bash
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --simulator-scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/backtest-sim.json
```

Simulator hash and seed are recorded in backtest metadata.

## Limitations

The simulator is deterministic. It is designed for repeatable QA and strategy
research, not a prediction of future fills.
