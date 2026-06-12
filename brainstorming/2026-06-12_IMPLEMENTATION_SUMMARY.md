# 2026-06-12 NFI Engine 구현 요약

작성 기준: 2026-06-12 dev-entry plan.
실제 검증은 KST 2026-06-13 새벽까지 이어졌지만, 계획/증거 경로는
`2026-06-12` 기준으로 고정한다.

## 한 줄 결론

NFI Engine은 이제 단순 아이디어가 아니라 M1 엔진 뼈대와 M2 operator
surface가 있는 상태다. 이번 작업은 새 기능을 크게 벌린 게 아니라,
install -> login -> Home -> Settings -> Logs -> benchmark/final smoke까지
사용자가 믿고 확인할 수 있는 hardening 증거를 쌓은 작업이다.

## 오늘 완료한 것

### 1. 현재 상태 재분류

완료일: 2026-06-12

정리한 것:

* dirty worktree를 지우지 않고 현재 상태를 evidence로 고정했다.
* 기존 M2 구현 표면과 아직 덜 잠긴 hardening 항목을 분리했다.
* `brainstorming/NFI_Engine.md`를 `[x]`, `[~]`, `[ ]` 기준으로 다시 나눴다.

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-1-git-status.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-1-state-classification.md`
* `.omo/evidence/2026-06-12-dev-entry/task-1-brainstorming-map.txt`

### 2. 첫 실행 Docker 동선

완료일: 2026-06-12

구현/검증한 것:

* `scripts/install.sh --yes --paper --testnet` 경로를 실제 Docker smoke로 검증했다.
* `.runtime/docker.env`의 operator token은 출력하지 않고, 인증 경로만 검증했다.
* unauthenticated dashboard snapshot은 401/403으로 막히고, bearer/session 경로는 Home과 dashboard snapshot을 열 수 있음을 확인했다.
* safe uninstall은 runtime을 보존하고, purge uninstall은 `.runtime`을 제거하는 흐름을 확인했다.

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-2-first-run-success.log`
* `.omo/evidence/2026-06-12-dev-entry/task-2-dashboard-unauthenticated.status`
* `.omo/evidence/2026-06-12-dev-entry/task-2-home.html`
* `.omo/evidence/2026-06-12-dev-entry/task-2-secret-scan.txt`

### 3. Settings 적용 의미 고정

완료일: 2026-06-12

구현/검증한 것:

* runtime-safe field는 `/api/v1/config/apply` 후 running `RuntimeSettings`에 반영되도록 의미를 고정했다.
* restart-required field는 `restart_required=true`로 응답하고 running config를 바꾸지 않게 했다.
* invalid field, missing CSRF, live lock 같은 실패가 typed response와 next-action으로 드러나게 했다.
* Settings UI는 apply 후 current config를 다시 읽어 현재 상태를 보여준다.

주요 변경 파일군:

* `src/nfi_engine/api/config_routes.py`
* `src/nfi_engine/api/config_edit.py`
* `src/nfi_engine/ui/assets_settings.py`
* `tests/e2e/test_settings_logs_ui.py`

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-3-settings-apply-rerun.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-3-http-manual-summary-rerun.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-3-browser-settings-apply-current.json`

### 4. Dashboard/Home read-model 연결

완료일: 2026-06-12

구현/검증한 것:

* dashboard snapshot이 bounded persistence read model을 바라보게 했다.
* Home의 open trades / session PnL / recent errors가 fake live claim 대신 read model 또는 honest empty state를 보여주게 했다.
* empty DB, stale state, persisted rows, auth boundary를 함께 검증했다.

주요 변경 파일군:

* `src/nfi_engine/api/dashboard*.py`
* `src/nfi_engine/dashboard/`
* `src/nfi_engine/persistence/repositories/`
* `src/nfi_engine/ui/home.py`
* `tests/unit/dashboard/`
* `tests/integration/persistence/test_dashboard_repository_lists.py`
* `tests/e2e/test_home_ui.py`

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-4-dashboard-readmodels.json`
* `.omo/evidence/2026-06-12-dev-entry/task-4-http-manual-summary-rerun.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-4-home-desktop.png`
* `.omo/evidence/2026-06-12-dev-entry/task-4-home-mobile.png`

### 5. i18n/readiness 하드코딩 누수 제거

완료일: 2026-06-12

구현/검증한 것:

* Home, Settings, Logs, login, setup, readiness의 주요 사용자 문구를 catalog 경유로 정리했다.
* EN/KO/EL 렌더링을 검사했다.
* machine code, enum value, audit ID는 번역하지 않도록 유지했다.
* Korean Settings/Login 브라우저 스크린샷으로 glyph와 localized readiness 문구를 확인했다.

주요 변경 파일군:

* `src/nfi_engine/ui/i18n_keys.py`
* `src/nfi_engine/ui/i18n_en.py`
* `src/nfi_engine/ui/i18n_ko.py`
* `src/nfi_engine/ui/i18n_el.py`
* `src/nfi_engine/ui/readiness.py`
* `src/nfi_engine/ui/login_page.py`
* `src/nfi_engine/ui/settings_page.py`
* `tests/e2e/test_i18n_ui.py`
* `tests/unit/ui/test_i18n.py`

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-5-i18n-audit-final-rerun.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-5-rendered-leak-check-after-readiness.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-5-ko-settings-mobile-readiness-font.png`
* `.omo/evidence/2026-06-12-dev-entry/task-5-visual-verdict-final.md`

### 6. CSRF/read-only/live 안전 게이트

완료일: 2026-06-12

구현/검증한 것:

* config apply, pairlist apply, backup restore, runtime start/pause/stop이 missing CSRF, invalid CSRF, read-only 모드에서 서버 차단되는지 HTTP로 검증했다.
* UI disabled 상태가 힌트일 뿐이고, 서버가 최종 권한자임을 테스트로 고정했다.
* live setup preview는 `LIVE_TRADING_REQUIRES_CONFIRMATION`을 반환하고 secret을 노출하지 않게 했다.

주요 변경 파일군:

* `tests/e2e/test_frontend_security.py`
* `src/nfi_engine/api/security.py`
* `src/nfi_engine/api/routes.py`
* `src/nfi_engine/ui/settings_page.py`

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-6-safety-gates-rerun.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-6-http/`
* `.omo/evidence/2026-06-12-dev-entry/task-6-http-summary.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-6-secret-scan.txt`

### 7. Benchmark/final smoke release gate

완료일: 2026-06-12

구현/검증한 것:

* `bash scripts/final_smoke.sh`가 끝까지 통과하고 valid `m2-benchmark.json`을 쓰는지 확인했다.
* baseline이 주어진 경우 `PERFORMANCE_REGRESSION`으로 실패하는 음성 경로를 실제 CLI로 검증했다.
* Home, Settings, Logs, login path를 desktop/mobile 브라우저 스크린샷과 redacted HAR로 남겼다.
* 브라우저 network는 loopback only, browser storage는 `localStorage=[]`, `sessionStorage=[]`임을 확인했다.
* Logs 모바일 표에서 텍스트가 겹치던 문제를 가로 스크롤 표로 수정했다.

주요 변경 파일군:

* `src/nfi_engine/ui/assets.py`
* `src/nfi_engine/ui/logs_page.py`
* `tests/unit/ui/test_pages.py`
* `docs/performance.md`
* `README.md`

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/final_smoke.log`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/m2-benchmark.json`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/regression-stderr.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-home-desktop.png`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-settings-mobile.png`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-logs-mobile.png`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-console-network-storage.json`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-secret-scan.txt`

### 8. 문서/브레인스토밍 정리

완료일: 2026-06-12

정리한 것:

* `brainstorming/NFI_Engine.md`를 완료 / 부분 / 미구현으로 다시 나눴다.
* `README.md`에 현재 M2 hardening evidence path와 release gate 명령을 명시했다.
* `docs/freqtrade-feature-coverage.md`에서 M2 상태를 build에서 hardening으로 더 정확하게 표현했다.
* `docs/performance.md`에 final smoke와 baseline regression gate의 차이를 명확히 적었다.

## 오늘 실행한 핵심 검증

```bash
uv run pytest -q tests/e2e/test_benchmark_cli.py tests/e2e/test_install_script.py tests/e2e/test_home_ui.py tests/e2e/test_settings_logs_ui.py tests/e2e/test_i18n_ui.py
bash scripts/final_smoke.sh
uv run nfi-engine benchmark m2 --output .omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/regression-output.json --baseline .omo/tmp/task-7/baseline.json --samples 1
uv run pytest -q tests/unit/ui/test_pages.py tests/e2e/test_settings_logs_ui.py
uv run ruff check src/nfi_engine/ui/assets.py src/nfi_engine/ui/logs_page.py tests/unit/ui/test_pages.py tests/e2e/test_settings_logs_ui.py
```

## Post-review 수정

수정일: 2026-06-13 KST

재검토 중 실제 blocker 2개를 발견해서 바로 고쳤다.

* runtime-safe config apply 뒤에도 UI/security가 초기 `RuntimeSettings`를 보는 문제를 수정했다. 이제 Home/Settings/Logs와 write gate는 `ApiContext.settings` provider를 통해 최신 runtime settings를 본다.
* Greek i18n catalog에 빠져 있던 Settings title을 추가하고, 모든 locale이 모든 `MessageKey`를 채우도록 테스트를 강화했다.
* 빠져 있던 Login desktop 브라우저 PNG/HAR 증거를 추가했다.

증거:

* `.omo/evidence/2026-06-12-dev-entry/task-9-final-verification/runtime-apply-fix-focused-tests.txt`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-login-desktop.png`
* `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/task-7-login-desktop-har-check.txt`
* `.omo/evidence/2026-06-12-dev-entry/f2-code-quality-review.md`
* `.omo/evidence/2026-06-12-dev-entry/f3-real-manual-qa.md`
* `.omo/evidence/2026-06-12-dev-entry/f4-scope-fidelity.md`

## 아직 완료라고 말하면 안 되는 것

* real-money live trading
* 실제 거래소 키로 live order 실행
* upstream NFI와 full parity
* Freqtrade보다 빠르다는 public speed claim
* update button
* plugin marketplace/gallery
* backtest UI
* benchmark visualization
* Raspberry Pi 4 / 저사양 VPS 반복 측정

## 남은 위험

* M2 operator surface는 꽤 올라왔지만, setup preview가 아직 완전한 wizard UX는 아니다.
* Dashboard는 bounded read model과 empty state를 갖췄지만, 운영자가 3초 안에 판단하는 live cockpit 수준은 아니다.
* i18n은 주요 화면을 잡았지만 새 화면이 생기면 누수가 다시 생길 수 있다.
* final smoke는 로컬/Docker path를 검증하지만, 여러 OS 반복 검증은 아직 부족하다.
* 성능 benchmark는 local baseline evidence이며 공개 속도 주장 근거가 아니다.

## 다음 개발 우선순위

1. setup preview를 first-run wizard 완료 UX로 다듬기
2. Dashboard에 paper-run/persistence 상태를 더 직접 연결하기
3. live 전환 UX에 더 강한 friction과 설명 붙이기
4. benchmark 결과를 README에 짧게 노출하되 speed claim은 금지하기
5. 여러 OS에서 install/uninstall 반복 검증하기
6. feature coverage를 supported / partial / excluded로 계속 갱신하기

## 최종 verification 상태

완료. 최종 gate 결과는
`.omo/evidence/2026-06-12-dev-entry/task-9-final-verification/`에 남겼다.

최종 통과:

* `uv run ruff format --check .`: pass, 320 files already formatted
* `uv run ruff check .`: pass
* `uv run basedpyright`: pass, 0 errors / 0 warnings / 0 notes
* `uv run pytest -q`: pass, 284 passed
* `bash scripts/final_smoke.sh`: pass
* plan evidence verifier: `PLAN_EVIDENCE_OK referenced=9 missing=0`
* evidence secret scan: pass, 1369 text artifacts scanned after final redaction
* `git diff --check`: pass
* cleanup receipt: no dev-entry bound ports or task temp paths remain

최종 결론: 2026-06-12 dev-entry / M2 hardening 계획의 Tasks 1-9와 F1-F4는
구현/검증 완료다. 다만 real-money live trading, full NFI parity, update
button, plugin marketplace, backtest UI, benchmark visualization, public speed
claim은 여전히 미구현/금지 범위다.
