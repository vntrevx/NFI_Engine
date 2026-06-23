# TEST GUIDE

## OVERVIEW

`tests` verifies unit services, integration boundaries, e2e surfaces, fixtures,
docs contracts, Docker/install behavior, UI security, and evidence tooling.

## STRUCTURE

```text
tests/
|-- unit/          # pure service/domain/UI/docs/tool contracts
|-- integration/   # persistence, exchange, notification boundaries
|-- e2e/           # CLI/API/UI/install/Docker/runtime flows
`-- fixtures/      # canonical configs, data, strategies, DBs, scenarios
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Service behavior | `tests/unit/<domain>/test_*.py` | Narrow, deterministic, no runtime services. |
| Boundary behavior | `tests/integration/<domain>/` | Fake clients, temp DBs, async repos. |
| User surface | `tests/e2e/test_*.py` | CLI, API, UI, install, Docker, scripts. |
| Strategy fixtures | `tests/fixtures/strategies/` | Clean-room NFI-shaped and unsafe fixtures. |
| Config fixtures | `tests/fixtures/config/` | Safety, live-block, preflight, secret scenarios. |
| Evidence verifier | `tests/unit/tools/test_plan_evidence.py` | `.omo/evidence` path contract. |

## CONVENTIONS

- Filenames follow `test_<subject>.py`; functions should name behavior and condition.
- Use Given/When/Then comments where they clarify scenario setup and expected safety behavior.
- Async tests use `pytest.mark.anyio`; persistence/UI async suites may pin `anyio_backend` to `asyncio`.
- Fixtures are canonical inputs. Add them under the domain folder that owns the scenario.
- Tests that prove redaction should assert both the safe replacement and absence of the original secret.
- E2E tests should drive the matching surface: subprocess CLI, FastAPI client,
  rendered HTML, scripts, Docker config, or filesystem artifact.
- User-visible or hot-path changes still need manual evidence in `.omo/evidence/` when docs/contributing requires it.

## ANTI-PATTERNS

- Do not weaken assertions or delete failing tests to make a gate pass.
- Do not use live exchange connectivity, real credentials, network-only data, or public services in tests.
- Do not leave secrets, generated tokens, screenshots, support bundles, or
  runtime DBs outside temp paths or `.omo/evidence/`.
- Do not duplicate large fixtures per test when a shared canonical fixture fits.
- Do not hide warnings; pytest treats warnings as errors by project policy.
