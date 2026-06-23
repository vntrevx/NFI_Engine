# EXCHANGE GUIDE

## OVERVIEW

`exchange` owns exchange-facing protocols, simulator behavior, Bybit testnet
adapter seams, tick loading, fill scenarios, and order/fill models.

## STRUCTURE

```text
exchange/
|-- protocols.py       # adapter contracts
|-- bybit.py           # Bybit testnet-ready adapter boundary
|-- simulator.py       # deterministic local exchange simulation
|-- fill_scenarios.py  # partial fill, latency, slippage, funding cases
|-- ticks.py           # fixture tick loading
|-- models.py          # quotes, orders, fills, balances
`-- errors.py
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Adapter contract | `protocols.py`, `models.py` | Keep simulator and real adapter shapes aligned. |
| Bybit behavior | `bybit.py` | Testnet/sandbox mode is mandatory in current milestone. |
| Paper execution | `simulator.py`, `fill_scenarios.py` | Deterministic risk-modeling approximation. |
| Fixture ticks | `ticks.py`, `tests/fixtures/ticks` | No network fetch in tests. |
| Tests | `tests/integration/exchange`, `tests/unit/exchange` | Use fake clients and fixtures. |

## CONVENTIONS

- Simulator/testnet/paper are the allowed milestone surfaces. Real-money order placement is out of scope.
- Bybit adapters must set sandbox/testnet mode and expose typed failures instead of leaking raw client exceptions.
- Fill scenarios are risk approximations, not exact exchange claims. Keep docs and CLI wording precise.
- Pair parsing, leverage, margin, and side rules must align with `domain` and `risk` services.
- Reconciliation and preflight decide whether runtime may continue; adapters should provide facts, not bypass policy.
- Secrets from exchange settings must never appear in logs, notifications, support bundles, or evidence files.

## ANTI-PATTERNS

- Do not add live-order shortcuts, production exchange defaults, or public-bind deployment behavior here.
- Do not make tests depend on real exchange connectivity.
- Do not silently coerce unsupported market modes, pair symbols, leverage, or margin settings.
- Do not let adapter convenience bypass circuit breakers, reconciliation, pairlist checks, or safety gates.
- Do not claim simulator scenarios exactly match live exchange behavior.
