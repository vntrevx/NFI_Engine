# NFI Engine

[English](README.md) | [한국어](README.ko.md)

NFI Engine은 spot/futures paper trading, testnet 중심 운영 workflow,
결정론적 simulation, native NFI-shaped X7 전략 연구를 위한 original
clean-room crypto trading engine이다.

이 프로젝트는 Freqtrade가 아니고, 공식 NostalgiaForInfinity 프로젝트도
아니며, 둘 중 어느 쪽의 fork도 아니다. Freqtrade는 기능 범위와 운영 표면을
정의할 때 참고하는 benchmark일 뿐이다. Upstream NFI 전략 소스는 이 저장소에
vendoring하지 않고 runtime import하지 않는다.

## 현재 상태

기준일: 2026-06-26 KST

현재 NFI Engine은 증거가 붙은 **paper/testnet RC** 상태다.

실거래 주문 실행은 별도 승인된 live-execution 설계와 증거 세트가 나오기 전까지
계속 차단된다.

| 영역 | 현재 경계 |
| --- | --- |
| 전략 runtime | native NFI-shaped X7 semantic runtime을 dry-run, paper, testnet 중심 경로에서 사용할 수 있다. |
| 운영 workflow | 한 줄 설치/제거, admin/password login, Home cockpit, Settings setup, wallet balance fetch, runtime control, Logs, EN/KO/EL UI가 구현되어 있다. |
| 안전 게이트 | auth, CSRF, read-only mode, live-intent blocker, preflight, wallet cap, reconciliation, circuit breaker, update rollback gate를 유지한다. |
| 거래소 지원 | 거래소는 capability evidence로만 승격한다. candidate/generic-unverified 거래소는 runtime trade path에 들어가지 않는다. |
| Raspberry Pi 4 | 한 대의 Pi4 기준 내부 RC evidence가 있다. `claim_allowed=false`라서 공개 속도 비교 문구로 쓰지 않는다. |
| live execution | real-money live order execution은 이 RC의 범위 밖이다. |

상태 원문은 [docs/release-status.md](docs/release-status.md), 공개 문구 정책은
[docs/release-wording.md](docs/release-wording.md)에 있다.

## 빠른 시작

Docker가 기본 first-run 경로다. 로컬 checkout에서 바로 실행한다.

```bash
bash scripts/install.sh --yes --paper --testnet
```

npm과 Bun wrapper도 같은 설치 경로를 제공한다.

```bash
npm run nfi:install
bun run nfi:install
```

Docker를 시작하기 전에 dry-run receipt만 확인할 수도 있다.

```bash
bash scripts/install.sh --yes --paper --testnet --dry-run
npm run nfi:install:dry-run
bun run nfi:install:dry-run
```

첫 실행 순서:

1. `http://127.0.0.1:18080/`을 연다.
2. `admin`과 `.runtime/docker.env`의 generated operator password로 로그인한다. installer는 env file 경로만 출력하고 password 값은 출력하지 않는다.
3. Home에서 runtime state, Setup Doctor, Safety Explainer, chart status, runtime controls, recent errors, pairlist 상태를 확인한다.
4. Settings에서 exchange, exchange API key, exchange API secret, API permission audit, 권장 3x leverage, risk profile, wallet balance fetch, allocation amount, futures/spot, dry-run/live intent를 설정한다.
5. 기본은 dry-run이다. withdrawal 성격의 API 권한은 live setup을 막고, expert risk는 명시 확인을 요구한다. API key/secret 입력값은 write-only이며 출력에서 redacted 처리된다.
6. 언어 선택으로 English, Korean, Greek UI를 전환한다.
7. Logs에서 error code와 redacted support report를 확인한다.

기본 확인:

```bash
curl -i http://127.0.0.1:18080/api/v1/ping
bash scripts/uninstall.sh --yes
npm run nfi:uninstall
bun run nfi:uninstall
```

Safe uninstall은 runtime file과 data volume을 보존한다. purge는 명시적으로만
실행한다.

```bash
bash scripts/uninstall.sh --purge --yes
npm run nfi:uninstall:purge:dry-run
bun run nfi:uninstall:purge:dry-run
```

실제 exchange credential은 issue, chat log, commit file, shell history에
남기지 않는다. 로컬 실험은 paper/testnet credential을 우선 사용하고, 실험 후
rotate한다. installer에서는 exchange credential을 process argument로 넘기지
않고, `0600` credential file 또는 `NFI_ENGINE_SETUP_*` 환경변수로만 전달한다.

## X7 Runtime 확인

native X7 semantic-runtime inspect는 upstream 전략 코드를 복사하지 않고
engine-owned runtime 경계에서 실행된다.

```bash
uv run nfi-engine strategy inspect --config examples/x7-futures-paper.yaml --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy --json
```

이 명령은 X7 runtime 상태, provenance, semantic coverage, live-readiness gate를
확인하는 operator/developer 표면이다. 결과가 semantic coverage를 의미하더라도
real-money live order 허용을 뜻하지 않는다.

## 개발자 경로

Docker 없이 engine을 개발할 때는 `uv` 경로를 사용한다.

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/spot-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/quickstart-backtest.json
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

열어볼 표면:

- `http://127.0.0.1:18080/`
- `http://127.0.0.1:18080/settings`
- `http://127.0.0.1:18080/logs`

local operator username/password로 browser session을 만든 뒤 protected page를
사용한다. mutation API는 session cookie와 `x-nfi-csrf-token`이 필요하며,
credentials는 browser local storage에 저장하지 않는다.

## Console

Console은 public dashboard가 아니라 local operator surface다.

- `/`: Home cockpit. setup readiness, runtime health, pause/resume/stop-safe, wallet balance, action queue, local chart, safety, support shortcut을 보여준다.
- `/settings`: first-run setup wizard, config metadata editor, validation, draft/apply, readiness, pairlist, update state, safety lock을 다룬다.
- `/logs`: recent logs, severity filter, error-code lookup, correlation ID, support report export를 제공한다.
- Read-only mode: inspect는 가능하지만 save/apply/restore/start/pause/resume/stop은 UI와 server 양쪽에서 차단된다.
- Security: authenticated session cookie, CSRF token, protected wallet/runtime-health JSON, logout, expiry, protected audit log, no browser token storage.

자세한 내용은 [docs/ui.md](docs/ui.md)에 있다.

## 핵심 설계

- `src/nfi_engine/config`: Pydantic runtime settings, metadata, migration, redaction.
- `src/nfi_engine/domain`: market, pair, order, trading-mode value object.
- `src/nfi_engine/strategy`: Freqtrade-shaped 전략을 clean adapter contract로 다루는 경계.
- `src/nfi_engine/backtest`: deterministic backtest runner와 reproducibility metadata.
- `src/nfi_engine/paper`: paper-run lifecycle과 tick-driven state transition.
- `src/nfi_engine/exchange`: exchange adapter, fixture, reconciliation, fill scenario.
- `src/nfi_engine/risk`, `orders`, `circuit_breakers`, `safety`: risk decision과 hard stop.
- `src/nfi_engine/persistence`, `maintenance`: SQLite storage, migration, backup, restore.
- `src/nfi_engine/api`, `ui`: FastAPI REST/WebSocket API와 local operator console.

Config parsing은 edge에서 끝내고, service 내부에는 typed value를 넘긴다. UI는 raw
YAML을 직접 고치지 않고 typed API endpoint를 호출한다.

## 주요 명령

```bash
uv run nfi-engine profile list
uv run nfi-engine config show --config examples/futures-paper.yaml
uv run nfi-engine config schema --config examples/futures-paper.yaml
uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/walk-forward.json
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25
uv run nfi-engine plugins list --config examples/futures-paper.yaml
uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml
uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy
```

운영 전에는 profile과 preflight를 먼저 확인한다.

```bash
uv run nfi-engine profile list
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
```

거래소와 시장 점검:

```bash
uv run nfi-engine exchange capabilities --exchange bybit --trading-mode futures --format json
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
```

`exchange capabilities`는 registry profile과 report-only generic id를 구분한다.
증거가 없는 unknown exchange를 config, paper/testnet, live path로 승격하지 않는다.

## Evidence와 Quality Gate

최종 smoke와 release wording scan:

```bash
bash scripts/final_smoke.sh
uv run python scripts/release_wording_scan.py
```

현재 주요 evidence root:

```text
.omo/evidence/2026-06-12-dev-entry/
.omo/evidence/2026-06-20-nfi-x7-semantic-port/
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
```

Core quality gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

Scripted quality gate:

```bash
bash scripts/quality_gate.sh --docs-only
bash scripts/quality_gate.sh --strict
bash scripts/quality_gate.sh --coverage-only
```

`--docs-only`는 문서/governance 변경용 빠른 gate다. `--strict`는 전체 local gate,
`--coverage-only`는 config/domain focused coverage smoke다.

Browser QA:

```bash
npm install
npm run nfi:browser-qa:deps
npm run nfi:browser-qa
```

이 QA는 loopback server를 띄우고 실제 browser login, Settings locale switch,
Home/Settings/Logs desktop/mobile screenshot, external request 차단, browser token
storage 비어 있음을 확인한다.

## 더 보기

- [README.md](README.md)
- [docs/release-wording.md](docs/release-wording.md)
- [docs/release-status.md](docs/release-status.md)
- [docs/docker.md](docs/docker.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md)
- [docs/nfi-x7-compatibility.md](docs/nfi-x7-compatibility.md)
- [docs/exchange-support-matrix.md](docs/exchange-support-matrix.md)
- [docs/performance.md](docs/performance.md)
- [docs/ui.md](docs/ui.md)
- [docs/operations.md](docs/operations.md)
