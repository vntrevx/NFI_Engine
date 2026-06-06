# Pairlist Management

Pairlist validation keeps unsupported or risky markets out of strategy and
runtime workflows.

## CLI

```bash
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
```

Validation checks:

- exchange symbol support
- quote/base eligibility
- blacklist aliases
- liquidity threshold
- volatility threshold
- futures and leverage eligibility

## UI

The `/settings` page includes a pairlist panel. Operators can preview rejected
pairs and, when not read-only, save or apply a draft. Read-only mode allows
preview only.

## Limitations

M1 pairlist data is deterministic and fixture-backed. Live exchange market
metadata refresh is a later adapter concern.
