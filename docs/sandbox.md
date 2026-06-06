# Sandbox

The sandbox checks whether a strategy import attempts unsafe behavior before it
is allowed into an operator workflow.

## Check A Strategy

```bash
uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy
```

Unsafe fixture strategies are expected to fail:

```bash
uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy
```

The policy blocks unsafe environment and file access patterns. Safe strategy
compatibility still goes through the strategy adapter contract.

## Boundaries

- Sandbox policy is checked before strategy execution.
- Plugin registration does not disable sandbox checks.
- Support bundles do not include raw strategy secrets.

## Limitations

M1 sandbox checks are local and deterministic. They are not a substitute for
container isolation around untrusted third-party code in later milestones.
