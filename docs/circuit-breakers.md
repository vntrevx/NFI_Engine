# Circuit Breakers

Circuit breakers stop unsafe operation before an order workflow can continue.
They are part of the runtime safety boundary, not UI decoration.

## Simulate

```bash
uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml
uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/stale-data-breaker.yaml
```

Typical events include:

- daily loss limit breach
- stale market data
- locked pair
- liquidation buffer breach
- exchange reconciliation required

## Operator Rules

- Treat breaker output as blocking unless the command explicitly says it is a warning.
- Do not retry a blocked paper/live workflow without fixing the underlying state.
- Keep breaker artifacts in `.omo/evidence/` during QA.

## Limitations

M1 breaker simulation is deterministic and fixture-driven. Later milestones can
bind the same typed decisions to real exchange streams.
