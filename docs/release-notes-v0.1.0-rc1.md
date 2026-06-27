# v0.1.0-rc1 Release Notes

Date: 2026-06-28 KST

`v0.1.0-rc1` is the first paper/testnet release-candidate tag for NFI Engine.
It is intended for local evaluation, deterministic research, and testnet
operator workflow checks.

## Included

- Native NFI-shaped X7 semantic runtime for dry-run, paper, and testnet-oriented
  paths.
- One-line shell, npm, and Bun install/uninstall paths.
- Local username/password operator login with CSRF-protected mutations.
- Operator cockpit, Settings setup, wallet fetch surface, runtime controls,
  logs, EN/KO/EL locale switching, and local browser QA coverage.
- Capability/evidence-based exchange registry with deterministic fixture,
  sandbox, and report-only runtime checks.
- `nfi-engine exchange testnet-pilot` readiness report for the testnet-only
  pilot boundary.
- `scripts/testnet_credential_probe.sh` for secret-safe Binance, Bybit, OKX,
  and Bitget testnet credential readiness checks.
- `scripts/pi4_soak.sh` for repeatable non-mutating Raspberry Pi 4 profile
  probes.

## Boundary

- Real-money order execution is not enabled by this tag.
- Real priority-exchange testnet API evidence remains `blocked-no-key` until
  the operator supplies safe local testnet credentials.
- Raspberry Pi 4 long-run soak evidence must be captured on the target device
  before public hardware-performance wording is expanded.
- Public wording is governed by `docs/release-wording.md`.

## Verification

Before publishing the tag, rerun:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
uv run python scripts/release_wording_scan.py
git diff --check
```
