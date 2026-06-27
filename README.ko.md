# NFI Engine

[English](README.md) | [한국어](README.ko.md)

NFI-shaped X7 연구, 결정론적 paper run, testnet 운영, 안전한 거래소 workflow를
위한 local-first crypto trading engine.

NFI Engine은 original clean-room software다. Freqtrade가 아니고, 공식
NostalgiaForInfinity 프로젝트도 아니며, fork도 아니다. 외부 프로젝트는 참고
대상일 뿐이고, 이 저장소는 그쪽 strategy source, UI, docs, runtime code를
vendoring하지 않는다.

## 현재 상태

`v0.1.0-rc1`은 paper/testnet RC다.

실거래 주문 실행은 별도 승인된 execution 설계와 evidence가 나오기 전까지
차단된다.

| 구간 | 현재 상태 |
| --- | --- |
| 전략 | native X7-shaped semantic runtime을 inspect, dry-run, paper, testnet 중심 경로에서 사용. |
| 운영 UI | username/password login, Home cockpit, Settings setup, Logs, EN/KO/EL 언어 전환. |
| 거래소 설정 | capability registry, API permission audit, wallet balance fetch, leverage/allocation setup. |
| 안전장치 | CSRF, read-only mode, live-intent blocker, wallet cap, reconciliation, circuit breaker, rollback gate. |
| 저사양 기준 | Raspberry Pi 4는 내부 engineering budget이다. 공개 속도 claim으로 쓰지 않는다. |
| 실거래 주문 | 별도 승인된 execution 설계와 evidence가 나오기 전까지 차단. |

릴리즈 노트: [docs/release-notes-v0.1.0-rc1.md](docs/release-notes-v0.1.0-rc1.md)
현재 경계: [docs/release-status.md](docs/release-status.md)

## 설치

Docker-first:

```bash
bash scripts/install.sh --yes --paper --testnet
```

npm / Bun:

```bash
npm run nfi:install
bun run nfi:install
```

실행 없이 미리보기:

```bash
bash scripts/install.sh --yes --paper --testnet --dry-run
npm run nfi:install:dry-run
bun run nfi:install:dry-run
```

제거:

```bash
bash scripts/uninstall.sh --yes
npm run nfi:uninstall
bun run nfi:uninstall
```

기본 제거는 runtime file과 volume을 보존한다. 완전 삭제는 명시적으로만:

```bash
bash scripts/uninstall.sh --purge --yes
```

## 첫 실행

1. `http://127.0.0.1:18080/` 접속.
2. username `admin`, `.runtime/docker.env`의 generated password로 로그인.
3. Settings에서 exchange, API key/secret, permission audit, leverage, wallet balance, allocation, spot/futures, dry-run/live intent 순서로 설정.
4. 기본은 dry-run 유지. live intent는 잠긴 경로를 테스트할 때만 건드린다.
5. 언어 선택으로 English, Korean, Greek UI를 전환한다.
6. Logs에서 redacted support output을 확인한다.

API 확인:

```bash
curl -i http://127.0.0.1:18080/api/v1/ping
```

## 핵심 기능

- CDN 없는 local operator console.
- username/password session auth와 CSRF protection.
- 거래소는 capability evidence가 있어야 승격.
- wallet balance probe와 permission audit를 runtime 전에 확인.
- deterministic backtest, paper-run, simulator, reconciliation surface.
- upstream code vendoring 없는 native X7-shaped strategy inspection.
- shell, npm, Bun 한 줄 설치/제거.
- profit, parity, live-money 과장 문구를 막는 release wording scan.

## X7 Runtime

native X7-shaped runtime inspect:

```bash
uv run nfi-engine strategy inspect \
  --config examples/x7-futures-paper.yaml \
  --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy \
  --json
```

이 명령은 engine-owned runtime boundary를 확인한다. 실거래 주문을 여는 명령이
아니다.

## 개발자 경로

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/spot-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

확인할 화면:

- `http://127.0.0.1:18080/`
- `http://127.0.0.1:18080/settings`
- `http://127.0.0.1:18080/logs`

protected API는 session cookie와 `x-nfi-csrf-token`이 필요하다. exchange
credential은 write-only/redacted로 다루고, issue/chat/commit/shell history에
남기지 않는다.

## 주요 명령

```bash
uv run nfi-engine profile list
uv run nfi-engine config show --config examples/futures-paper.yaml
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25
uv run nfi-engine exchange capabilities --exchange bybit --trading-mode futures --format json
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
```

## 검수

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
uv run python scripts/release_wording_scan.py
bash scripts/final_smoke.sh
```

문서만 바꿨을 때:

```bash
bash scripts/quality_gate.sh --docs-only
git diff --check
```

## 구조

| 경로 | 역할 |
| --- | --- |
| `src/nfi_engine/config` | typed runtime settings, migration, redaction. |
| `src/nfi_engine/domain` | market, pair, order, trading-mode value object. |
| `src/nfi_engine/strategy` | clean strategy adapter와 X7-shaped runtime boundary. |
| `src/nfi_engine/backtest` | deterministic backtest와 reproducibility metadata. |
| `src/nfi_engine/paper` | paper runtime loop와 state transition. |
| `src/nfi_engine/exchange` | capability registry, fixture, reconciliation, fill simulation. |
| `src/nfi_engine/risk`, `safety`, `circuit_breakers` | guardrail과 hard stop. |
| `src/nfi_engine/api`, `src/nfi_engine/ui` | FastAPI API와 local operator console. |
| `scripts` | install, uninstall, smoke, release, evidence helper. |

## 문서

- [Docker](docs/docker.md)
- [UI](docs/ui.md)
- [Exchange Support Matrix](docs/exchange-support-matrix.md)
- [NFI X7 Compatibility](docs/nfi-x7-compatibility.md)
- [Release Wording Rules](docs/release-wording.md)
