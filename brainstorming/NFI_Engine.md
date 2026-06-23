# NFI_Engine 브레인스토밍 체크리스트

## 읽는 법

이 문서는 아이디어를 버리는 문서가 아니라, **헷갈리지 않게 상태를 나누는 문서**다.

* `[x] 완료`: repo에 실제 파일/명령/API/UI/문서/테스트 표면이 있음
* `[~] 부분`: 뼈대나 화면은 있으나 제품 흐름으로 더 잠가야 함
* `[ ] 아이디어`: 아직 구현 전이거나 Milestone 밖임

현재 기준은 `README.md`, `src/nfi_engine`, `docs`, `scripts`, `tests`와
로컬 ULW evidence에 보이는 상태다.

## 현재 좌표

기준일: 2026-06-24 KST
현재 재확인: 2026-06-24 KST

* 현재 RC verdict: paper/testnet RC evidence-backed. G072에서 언어/런타임 상태가 F5 없이 반영되고, auth/CSRF/read-only/live-intent 차단과 KO/EN/EL desktop/mobile visual QA가 통과함. 다만 2026-06-23 fresh Docker final smoke 재검증은 WSL 세션의 Docker Desktop 연동 문제로 막혀 있었고, 실거래 live-money 주문 실행은 별도 승인 플랜 전까지 차단
* 상세 상태 문서: `brainstorming/2026-06-24_RC_STATUS.md`
* repo용 상태 문서: `docs/release-status.md`
* 현재 evidence root: `.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/`
* 최종 검증 요약: plan evidence `referenced=22 missing=0`, local pytest `497 passed`, release wording scan `violations=0`. G072 focused UI/i18n/runtime/browser tests는 `50 passed`, browser QA cleanup은 port/temp leftover 없음. 2026-06-23 fresh G050 재검증은 CLI/browser/paper/release checks pass, Docker final smoke만 외부 런타임 blocker

## 날짜 기준

* `구현일`: git commit 또는 파일 생성/수정 timestamp로 구현 표면이 확인된 날짜
* `시작일`: 일부 구현 표면은 있으나 제품 동선이 아직 덜 잠긴 날짜
* `확인일`: 이 문서를 정리하면서 상태를 다시 확인한 날짜
* `미구현 확인일`: repo에서 아직 구현 표면을 확인하지 못한 날짜

주요 증거:

* `2026-06-07`: `fe19748 feat: bootstrap nfi engine m1` 커밋으로 초기 엔진/기본 CLI/API/문서/테스트 표면 확인
* `2026-06-08`: working tree timestamp 기준 setup, install/uninstall, dashboard, i18n, benchmark, UI 확장 확인
* `2026-06-12`: dev-entry hardening 기준일. Task 1-9 로컬 evidence 확인
* `2026-06-12`: 이 브레인스토밍 문서 상태 재분류/검수일
* `2026-06-13`: post-review blocker 수정/검증일. runtime settings provider, Greek catalog, Login desktop evidence, F2-F4 closeout 확인
* `2026-06-14`: M2.5 첫 구현 웨이브. Home/dashboard snapshot action queue 구현 및 HTTP/브라우저 evidence 확인
* `2026-06-14`: S1 product boundary 문서화. `NostalgiaForInfinityX7` clean-room 호환성, exchange support 후보/검증 레벨, public claim audit 기준 정리
* `2026-06-14`: S2 strategy contract core 구현. callback support 분류, data-provider 계약 테스트, `sandbox check --output` clean-room JSON compatibility report 확인
* `2026-06-14`: S3 signal timeline equivalence 구현. backtest/paper 공통 typed timeline, paper `--timeline-output`, clean-room fixture equivalence evidence 확인
* `2026-06-14`: S4 exchange capability registry WP4.1 구현. `verified` / `candidate` / `generic-unverified` profile을 런타임 data로 묶고 config/preflight/CLI에서 unknown exchange를 차단
* `2026-06-15`: S4 exchange discovery WP4.2 구현. `exchange capabilities --format json`으로 candidate/generic-unverified 능력 문서를 출력하고, generic id는 config/live 실행 경로로 승격되지 않게 차단
* `2026-06-15`: S4 closeout 확인. T8/T13 기준 exchange capability spine은 완료, 다음 좌표는 S5의 T9/T10/T14 순서로 고정
* `2026-06-15`: S5 T9/T10 완료. shell/npm/Bun 설치 dry-run matrix와 실제 loopback browser QA gate를 확보했고, 다음 제품 좌표는 T14 first-run/setup cockpit 완성
* `2026-06-15`: S5 T14 완료. first-run setup wizard base path, Home operator cockpit, Settings update preview/apply/rollback 상태, dry-run default, live gate, credential redaction을 실제 loopback browser QA로 검증
* `2026-06-15`: S6 T22 완료. exchange API permission audit와 risk profile guardrail을 setup/preflight/Home/Settings에 연결했고, withdrawal 권한 live block, expert risk confirmation, EN/KO/EL browser QA를 검증
* `2026-06-15`: S7 T23/WP7.2 runtime-control 완료. explicit wallet balance fetch, protected runtime health JSON, Home/Settings 지갑/헬스 표시, pause/resume/stop-safe 컨트롤, CSRF/read-only/live-unsafe/blocked-health edge, 브라우저 no-storage/no-external-request QA를 검증. Pi4 실기기 성능 측정은 별도 과제
* `2026-06-16`: S7 T15/WP7.3 local performance ledger 완료. M2 benchmark 6개 측정이 samples=5로 local budget을 통과했고, Pi4 실기기 측정 전 public claim은 blocked로 고정
* `2026-06-16`: Raspberry Pi 4 Model B Rev 1.5 실기기 세팅/검증 완료. Debian 13 Trixie aarch64, `uv` Python 3.12.13, Docker/Compose, loopback API, auth smoke, restart/log-rotation Compose 설정, M2 benchmark budget 통과, throttling `0x0` 확인
* `2026-06-16`: Raspberry Pi 4 NFI Engine tuned profile 적용. CPU governor `performance`, swappiness/dirty-write/TCP keepalive 조정, Docker live-restore/log policy, journald cap, Bluetooth/Avahi 비활성화 후 M2 benchmark가 전 항목 budget 통과
* `2026-06-16`: Raspberry Pi 4 Bluetooth 완전 off 검증. `bluetooth.service` mask, `/boot/firmware/config.txt`의 `dtoverlay=disable-bt`, 재부팅 후 `/sys/class/bluetooth` 장치 수 `0`, Docker API healthy 확인
* `2026-06-16`: Raspberry Pi 4 팬 소음 대응. `performance` 고정 서비스를 끄고 `schedutil` quiet cpufreq 서비스로 전환, idle 샘플 `600MHz` 확인, M2 benchmark 전 항목 budget pass. 추가로 GPIO14가 UART `TXD0` high로 잡혀 있던 문제를 `enable_uart=0` + `dtoverlay=gpio-fan,gpiopin=14,temp=65000,hyst=10000`로 수정했고, 재부팅 후 `gpio-fan` state `0`, GPIO14 `output low`, Docker healthy 확인
* `2026-06-16`: Raspberry Pi 4 성능 우선 복구. quiet `schedutil` 서비스를 끄고 `performance` governor 서비스를 다시 활성화해 샘플 전부 `1800MHz` 고정 확인. GPIO fan overlay와 Bluetooth off는 유지, Docker healthy, M2 benchmark 전 항목 budget pass
* `2026-06-16`: Raspberry Pi 4 fanless safety guard 추가. 5V/GND 직결 2선 팬은 소프트웨어로 감속할 수 없어서, 팬을 빼고 임시 운용할 때를 대비해 `nfi-engine-thermal-guard.service`를 설치. 70C 이상 `1200MHz`, 78C 이상 `1000MHz`, 60C 이하 performance 복구. fake sysfs branch test와 실제 Docker healthy 확인
* `2026-06-16`: Raspberry Pi 4 실사용 배포 보류 결정. 엔진/성능/thermal guard 검증은 완료됐지만 현재 2선 5V 팬 소음이 운영 UX 기준을 못 맞춰서, 저소음 팬/제어 팬/방열판-only 실측 전까지 Pi4는 lab target으로 유지
* `2026-06-16`: Raspberry Pi 4 보류 후 원복 완료. `nfi-engine-pi4-performance`, `nfi-engine-pi4-quiet-cpufreq`, `nfi-engine-thermal-guard` 서비스/스크립트 제거, sysctl/journald/Docker daemon 튜닝 제거, `disable-bt`/`gpio-fan` boot overlay 제거, 재부팅 후 governor `ondemand`, max `1800MHz`, Docker healthy 확인
* `2026-06-17`: S8 WP8.1 backup/restore/uninstall dry-run safety rehearsal 완료. backup create/verify, restore `--dry-run`, safe uninstall `--dry-run`, purge uninstall `--dry-run`, marker-protected runtime 보존, unsafe purge refusal, restore `--apply` 거절, traversal/checksum-invalid/incomplete backup archive 거절, credential DB URL redaction을 e2e/unit/evidence로 고정
* `2026-06-21`: X7 RC Todo 12 완료. Settings update preview/apply/rollback이 proof-only 정책으로 고정됐고, dirty worktree/source/backup/CSRF/read-only 차단, HTTP happy/failure, browser happy/failure, mobile overflow, focused pytest/ruff/basedpyright 증거 확인
* `2026-06-21`: Pi4 RC Todo 4 완료. Todo 3B resume3 authenticated shell 이후 Pi user-home toolchain에 `uv 0.11.23`, `node v24.17.0`, `npm 11.13.0`, `bun 1.3.14`를 시스템 변경 없이 staging. shell/npm/Bun install dry-run, safe/purge uninstall dry-run, missing-uv failure, `/tmp` cleanup 검증 완료. rollback은 `rm -rf /home/admin/.local/share/nfi-engine/toolchain`. 당시 다음 과제는 Todo 5였고, 최신 상태는 아래 Todo 5 결과가 기준
* `2026-06-21 UTC / 2026-06-22 KST`: Pi4 RC Todo 5 완료-with-warning. Raspberry Pi 4 Model B Rev 1.5 / Debian 13 aarch64에서 M2/X7 benchmark 10개 측정 캡처, 9개 pass, `claim_allowed=false`, invalid sample failure typed, `/tmp` cleanup 통과. 단 `x7_backtest_sample_latency`가 `2275.615ms / 1000ms`로 warn이라 `T5A-pi4-x7-backtest-sample-budget`를 final RC 전 최적화/재예산 과제로 분리
* `2026-06-21 UTC / 2026-06-22 KST`: Pi4 RC Todo 6 완료. Raspberry Pi 4 staged source에서 X7 paper 500 tick soak, stale-data block, loopback runtime health HTTP, pre/post thermal/resource snapshot, cleanup 검증 완료. throttle `0x0`, temp `52.1C -> 56.9C`, Docker log bytes `0 -> 0`, `live_orders=false`, `/tmp`/process leftover 없음. 당시 후속 작업은 reversible deployment profile이었고, 최신 상태는 아래 Todo 13 결과가 기준
* `2026-06-21 UTC / 2026-06-22 KST`: Pi4 RC Todo 13 완료. reversible deployment profile이 loopback/project-scoped Compose 배포, `--project-name`/`--host-port`, Pi4 read-only profile check, safe uninstall/purge rollback receipt까지 검증. RC stack은 `127.0.0.1:18113`, ping/runtime-health HTTP `200`, container `healthy`, X7 inspect `coverage_state=verified`/`pending_modules=[]`, host tuning `not_applied`, CPU max `1800000`, throttle `0x0`, temp `51.1C -> 56.4C -> 55.0C`, token leak scan empty. Final RC는 여전히 `T5A-pi4-x7-backtest-sample-budget` 때문에 대기
* `2026-06-22 KST`: T5A Pi4 X7 backtest sample budget warning 해결. `StrategyRow` feature bulk 적용과 feature dedupe/upsert 선형화를 적용해 로컬 `x7_backtest_sample_latency`가 `682.370ms -> 248.494ms`로 개선됐고, 같은 Pi4 반복 M2/X7 benchmark에서 `832.086ms`, `836.042ms`, `849.583ms / 1000ms` 모두 pass. `claim_allowed=false`, throttle `0x0`, temp `53.5C`, impossible X7 baseline은 `PERFORMANCE_REGRESSION`으로 실패. Final RC 다음 좌표는 Todo 14
* `2026-06-22 KST`: Todo 6 검증 중 X7/preflight 순환 import 수정 완료. `preflight.__init__`의 service eager import를 제거하고 service 사용자는 `preflight.service` 직접 import로 정리. focused paper/X7 e2e `9 passed`, preflight service unit `15 passed`, touched Python ruff/basedpyright 통과
* `2026-06-22 KST`: Todo 14 release docs/status/final RC gate 완료. README/safety/operations/performance/exchange/X7/release-wording/status 문서를 paper/testnet RC 경계로 정리했고, `final_smoke.sh`의 실제 Docker proof를 기본 `.runtime`이 아니라 temp runtime + `nfi-engine-final-smoke` project + `18180` port로 격리. release wording scan `violations=0`, forbidden wording negative probe는 `live-money ready`/`better than Freqtrade`를 잡음. pre-fix smoke가 기본 `.runtime` placeholder를 purge한 사고는 복구했지만 실제 exchange credential 값은 recover 불가라 다시 수동 입력 필요
* `2026-06-22 KST`: Final verification wave F1-F4 완료. plan evidence verifier `PLAN_EVIDENCE_OK referenced=22 missing=0`, final local gate `ruff format/check`, `basedpyright`, `pytest 497 passed`, `git diff --check` 통과. 최종 verdict는 `paper/testnet RC approved`이며 실거래 live-money ready는 아님
* `2026-06-22 KST`: G011 one-line install/uninstall 재검증 완료. shell/npm/Bun install dry-run, config validate, safe uninstall, purge preview, invalid host-port/missing-uv/unsafe purge 실패 경로, Pi4 non-mutating profile, focused install pytest `17 passed`, `git diff --check`, secret scan 통과. npm/Bun wrapper는 credential을 argv가 아니라 환경변수로 받아야 raw secret echo를 피할 수 있음
* `2026-06-23 KST`: G063 Pi4 RC deployment profile 재검증 완료. Task 13/G046 hardware-stamped Pi4 deploy evidence를 다시 파싱해 Raspberry Pi 4 Model B, loopback `127.0.0.1:18113`, `host_tuning=not_applied`, CPU max `1800000`, throttle `0x0`, runtime health HTTP 200, X7 `coverage_state=verified`, rollback receipt, token leak zero를 확인. 로컬 `pi4_rc_profile`은 Docker Compose missing을 안전하게 block하고 invalid host-port는 `PI4_INVALID_HOST_PORT`로 차단. public speed/live-money claim은 여전히 금지
* `2026-06-24 KST`: G072 UI no-forced-refresh / browser security / visual QA 재검증 완료. EN -> KO -> EL -> EN 언어 변경이 수동 F5 없이 적용되고, `html lang`이 `ko`/`el`/`en`으로 바뀌며, Home/Settings/Logs desktop/mobile 스크린샷 6개가 overflow/clipping/overlap/replacement glyph 없이 통과. CSRF 누락/오류, read-only mutation, unsafe live intent는 계속 차단되고, runtime start/pause/resume/stop은 Home/Settings에 F5 없이 반영됨. focused pytest `50 passed`, release wording `violations=0`, secret scan empty, QA port/temp cleanup 통과

## 한 줄 정의

**NFI_Engine은 NFI 전략을 Freqtrade 안에 구겨 넣는 프로젝트가 아니라, NFI를 더 빠르고 가볍고 안전하게 굴리기 위한 전용 운전석이다.**

Freqtrade는 참고서다.
NFI_Engine은 제품이다.

## 이미 한 것

여기는 “아이디어”가 아니라 repo에 표면이 있는 것들이다.

### 엔진 뼈대

* [x] Python 3.12 패키지 구조 (구현일: 2026-06-07)
* [x] `nfi-engine` CLI 엔트리포인트 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] 모듈 경계: config / domain / strategy / backtest / paper / exchange / risk / safety / persistence / api / ui (구현일: 2026-06-07, dashboard/setup/benchmark 확장일: 2026-06-08)
* [x] clean-room 방향 명시: Freqtrade/NFI 코드를 vendoring하지 않고 기능 기준점으로만 사용 (구현일: 2026-06-07, 문서 확장일: 2026-06-08)
* [x] Milestone 1 제한 명시: real-money trading, risky live shortcut, profit claim 제외 (구현일: 2026-06-08)

### CLI 표면

* [x] `config` (구현일: 2026-06-07)
* [x] `profile` (구현일: 2026-06-07)
* [x] `preflight` (구현일: 2026-06-07)
* [x] `backtest` (구현일: 2026-06-07)
* [x] `validate` (구현일: 2026-06-07)
* [x] `paper-run` (구현일: 2026-06-07)
* [x] `exchange` (구현일: 2026-06-07)
* [x] `exchange capabilities` typed capability JSON/text 출력 (구현일: 2026-06-15)
* [x] `pairlist` (구현일: 2026-06-07)
* [x] `simulate` (구현일: 2026-06-07)
* [x] `circuit-breaker` (구현일: 2026-06-07)
* [x] `notify` (구현일: 2026-06-07)
* [x] `plugins` (구현일: 2026-06-07)
* [x] `sandbox` (구현일: 2026-06-07)
* [x] `backup` (구현일: 2026-06-07)
* [x] `db` (구현일: 2026-06-07)
* [x] `setup` (구현일: 2026-06-08)
* [x] `benchmark` (구현일: 2026-06-08)
* [x] `serve` (구현일: 2026-06-07)

### API / UI 표면

* [x] FastAPI 앱 생성 (구현일: 2026-06-07)
* [x] `/api/v1` 라우터 구조 (구현일: 2026-06-07, setup/dashboard 확장일: 2026-06-08)
* [x] `/` Home 페이지 (구현일: 2026-06-08)
* [x] `/settings` Settings 페이지 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] `/logs` Logs 페이지 (구현일: 2026-06-08)
* [x] login/session/CSRF server gate (구현일: 2026-06-08, HTTP/브라우저 검증일: 2026-06-12)
* [x] read-only mode server enforcement (구현일: 2026-06-08, 안전 검증일: 2026-06-12)
* [x] runtime-safe config apply 뒤 UI/security가 최신 `RuntimeSettings`를 보는 provider 구조 (구현일: 2026-06-12, post-review 검증일: 2026-06-13)
* [x] settings/logs/pairlist/dashboard 관련 UI 파일 분리 (구현일: 2026-06-08)
* [x] dashboard read store / repository 계층 (구현일: 2026-06-08)
* [x] Logs 모바일 표 가로 스크롤 처리로 텍스트 겹침 제거 (구현일: 2026-06-12)
* [x] Home / dashboard snapshot action queue (구현일: 2026-06-14, HTTP/브라우저 검증일: 2026-06-14)
* [x] 실제 loopback 서버 브라우저 QA gate. login -> Home action queue -> Settings locale apply -> Logs -> desktop/mobile screenshot -> local-only network/storage/token-leak audit를 `npm run nfi:browser-qa`로 재현 (구현일: 2026-06-15)
* [x] Home/Settings에 API permission audit와 risk profile 상태 노출. read/trade/futures/withdrawal/IP allowlist 상태와 `safe`/`balanced`/`expert` profile이 operator workflow에 보임 (구현/브라우저 검증일: 2026-06-15)
* [x] 보호된 지갑 잔액 조회 API. `GET /api/v1/wallet/balance`와 explicit `POST /api/v1/wallet/balance/fetch`가 typed/redacted wallet state를 반환하고 simulator happy path에서 `1000 / 1000 USDT`를 보여줌 (구현/HTTP/브라우저 검증일: 2026-06-15)
* [x] 보호된 runtime health API. `GET /api/v1/runtime/health`가 heartbeat/preflight/wallet/data freshness/manual halt/disk/memory 체크를 `healthy`/`degraded`/`blocked`로 요약 (구현/HTTP 검증일: 2026-06-15)
* [x] 보호된 runtime control API. `POST /api/v1/start`, `/pause`, `/resume`, `/stop`, `/runtime/control`이 pause new entries, resume after preflight/runtime-health, stop-safe state를 typed machine code로 처리하고 live-order cancel을 가장하지 않음 (구현/HTTP/브라우저 검증일: 2026-06-15)

### 설치 / 실행

* [x] `scripts/install.sh` (구현일: 2026-06-08)
* [x] `scripts/uninstall.sh` (구현일: 2026-06-08)
* [x] `package.json` npm/Bun 한 줄 wrapper (`nfi:install`, `nfi:install:dry-run`, safe uninstall, purge dry-run preview) (구현일: 2026-06-15, shell/npm/Bun matrix 재검증일: 2026-06-22)
* [x] `package.json` browser QA wrapper (`nfi:browser-qa:deps`, `nfi:browser-qa`) (구현일: 2026-06-15)
* [x] `Dockerfile` (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] `compose.yaml` (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Docker docs (구현일: 2026-06-07, 확장일: 2026-06-08, npm/Bun wrapper 반영일: 2026-06-15)
* [x] safe uninstall / purge 흐름 문서화 (구현일: 2026-06-08, purge dry-run preview 명확화일: 2026-06-15)
* [x] `scripts/final_smoke.sh` (구현일: 2026-06-07, 확장일: 2026-06-08, release gate 검증일: 2026-06-12, install/uninstall dry-run receipt 추가일: 2026-06-15)
* [x] backup/restore/uninstall dry-run rehearsal. backup create -> verify -> restore `--dry-run` -> safe uninstall dry-run -> purge dry-run을 marker-protected runtime dir에서 한 번에 재현하고, unmarked/home purge refusal, restore `--apply` refusal, traversal/checksum-invalid/incomplete archive refusal, credential DB URL redaction을 stable code/test로 검증 (검증일: 2026-06-17)

### 문서 / 테스트

* [x] README에 clean-room 정체성, quickstart, architecture map 정리 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] operations / docker / ui / performance / feature coverage 문서 (구현일: 2026-06-08)
* [x] e2e 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] unit 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] integration 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Freqtrade feature coverage 문서로 “따라 만들기”가 아니라 “기능 범위 비교” 방향 잡음 (구현일: 2026-06-08)
* [x] `brainstorming/2026-06-12_IMPLEMENTATION_SUMMARY.md` 작성 및 최종 gate 결과 반영 (작성일: 2026-06-12, 업데이트일: 2026-06-13)
* [x] T10 live-server browser QA evidence summary 작성 (작성일: 2026-06-15)

## 부분 구현 / 더 잠가야 하는 것

여기는 “없다”는 뜻이 아니다.
겉면은 있는데, 제품처럼 믿고 쓰려면 연결과 검증을 더 해야 하는 것들이다.

### 첫 사용자 동선

* [x] 한 줄 설치는 있음 (구현일: 2026-06-08, Docker smoke 검증일: 2026-06-12, shell/npm/Bun dry-run matrix 검증일: 2026-06-15)
* [x] 설치 host tool 누락 시 `INSTALL_MISSING_COMMAND` + `install_hint`로 바로 고칠 수 있게 안내 (구현일: 2026-06-15)
* [x] 설치 후 token login -> Home 진입 흐름 있음 (구현일: 2026-06-08, 브라우저/HTTP 검증일: 2026-06-12)
* [x] 실제 브라우저에서 token login -> Home action queue -> Settings -> Logs 이동을 loopback 서버로 재현 (검증일: 2026-06-15)
* [x] first-run setup wizard base path. 거래소 -> API key -> API secret -> API 권한 점검 -> 권장 3x -> risk profile -> explicit 지갑 잔액 fetch -> 할당 금액 -> 선물/현물 -> 드라이런/라이브 순서가 Settings에서 실제 렌더링되고 브라우저 QA로 검증됨 (구현/검증일: 2026-06-15, 권한/risk 보강일: 2026-06-15, wallet fetch 보강일: 2026-06-15)
* [x] 운영자가 지금 봐야 할 next action을 Home action queue와 dashboard snapshot API에 노출 (구현일: 2026-06-14, HTTP/브라우저 검증일: 2026-06-14)
* [~] 모든 사용자 실패를 wizard까지 포함해 한 화면에서 끝내는 UX는 더 필요함 (시작일: 2026-06-12, action queue 1차 구현일: 2026-06-14)

### Settings

* [x] config model / metadata / settings field 구조 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] UI에서 설정을 다루는 표면 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] runtime-safe 저장 -> 검증 -> 적용 -> 재조회 흐름 고정 (구현일: 2026-06-12)
* [x] runtime-safe apply 뒤 Settings locale과 read-only write gate가 같은 running config를 보도록 post-review 수정 (구현일: 2026-06-12, 검증일: 2026-06-13)
* [x] restart-required field는 running config를 바꾸지 않고 reload 필요로 응답 (구현일: 2026-06-12)
* [x] secret write-only / redaction 검증 (구현일: 2026-06-12)
* [x] 엔진+전략 업데이트용 preview/apply/rollback proof-only gate. 현재 버전/전략/config/lock provenance, dirty worktree 차단, `local_proof` source 정책, backup requirement, CSRF/read-only 차단을 HTTP/브라우저로 검증. 실제 GitHub pull/source mutation은 여전히 별도 live-safe 설계 전까지 금지 (구현일: 2026-06-15, 안전 gate 완성/검증일: 2026-06-21)
* [x] setup/config/preflight에 exchange API permission audit와 risk profile guardrail 연결. withdrawal 권한은 live setup을 차단하고, dry-run/testnet은 redacted diagnostics로 유지됨 (구현/HTTP 검증일: 2026-06-15)
* [x] `balanced` risk profile은 권장 3x, `expert`는 명시 확인 없으면 setup/preflight에서 차단 (구현/검증일: 2026-06-15)
* [x] Settings의 지갑 잔액 버튼이 `POST /api/v1/wallet/balance/fetch`를 호출하고 새로고침 없이 `1000 / 1000 USDT` 같은 typed 상태를 반영. 브라우저 storage는 비어 있고 외부 요청 없음 (구현/브라우저 검증일: 2026-06-15)
* [x] Settings runtime control이 페이지 진입 시 현재 state를 동기화하고, start/pause/resume/stop 명령 뒤 F5 없이 상태와 Home bot-state를 반영. read-only mode에서는 서버가 `READONLY_ACTION_BLOCKED`로 차단 (구현/브라우저 검증일: 2026-06-15, G072 재검증일: 2026-06-24)
* [~] live 전환 같은 위험 설정은 서버에서 막지만, 사용자용 마찰/설명 UX는 더 강해져야 함 (시작일: 2026-06-12)

### Dashboard

* [x] dashboard module / model / route / repository 표면 있음 (구현일: 2026-06-08)
* [x] dashboard가 persistence/read-store 기반 bounded snapshot으로 연결됨 (구현일: 2026-06-12)
* [x] Home 지표가 read-model snapshot 또는 정직한 empty state를 보여줌 (구현일: 2026-06-12)
* [x] dashboard snapshot에 bounded action queue 추가. readiness/errors/pairlist/paper-testnet 상태를 최대 4개 액션으로 압축 (구현일: 2026-06-14)
* [x] Home operator cockpit base. configured/safety/capability/active mode/wallet/allocated amount/leverage/risk profile/API permission audit/latest error/next action/where next를 한 화면에 압축 (구현/브라우저 검증일: 2026-06-15, permission/risk 보강일: 2026-06-15)
* [x] Home cockpit에 runtime health와 wallet balance가 실제 typed API 상태로 표시됨. simulator happy path는 wallet `1000 / 1000 USDT`, bybit/testnet credential 없음은 `WALLET_BALANCE_MISSING_CREDENTIALS` blocker로 표시 (구현/HTTP/브라우저 검증일: 2026-06-15)
* [x] Home runtime control panel이 start/pause/resume/stop 버튼과 runtime health state를 노출. pause는 `new_entries_allowed=false`로 entries를 막고, resume은 preflight/runtime-health clear 없이는 `RUNTIME_HEALTH_BLOCKED` 같은 stable code로 거절 (구현/HTTP/브라우저 검증일: 2026-06-15)
* [~] 실제 paper/live 상태를 운영자가 3초 안에 판단할 정도의 압축도는 1차 개선됨. 포지션/계좌/위험 묶음은 더 필요함 (시작일: 2026-06-12, action queue 1차 구현일: 2026-06-14)
* [~] 포지션, 계좌, 손익, 위험 상태를 “운영 화면”답게 더 밀도 있게 묶는 작업은 다음 단계 (시작일: 2026-06-12)

### i18n

* [x] 한국어 / 영어 / 그리스어 언어팩 파일 있음 (구현일: 2026-06-08)
* [x] UI i18n 구조 있음 (구현일: 2026-06-08)
* [x] Home / Settings / Logs / login / setup / readiness 주요 사용자 문구 catalog 경유 검증 (구현일: 2026-06-12)
* [x] machine code / enum / audit ID는 번역하지 않도록 테스트 고정 (구현일: 2026-06-12)
* [x] EN/KO/EL catalog completeness 테스트와 Greek Settings title 누락 수정 (구현일: 2026-06-12, 검증일: 2026-06-13)
* [x] Settings에서 `ui.locale`을 EN -> KO -> EL -> EN으로 바꾸면 운영자가 F5를 누르지 않아도 페이지와 `html lang`이 자동 반영되는 브라우저 gate 확보 (검증일: 2026-06-15, G072 재검증일: 2026-06-24)
* [x] QA 브라우저 환경의 CJK 폰트 누락을 rootless Noto CJK deps로 보강해 모바일 한국어 캡처에서 글리프 네모 현상을 제거 (검증일: 2026-06-15)
* [~] 새 화면 추가 시 하드코딩 문구가 다시 들어가지 않게 계속 테스트를 확장해야 함 (시작일: 2026-06-12)

### Benchmark / Performance

* [x] benchmark CLI 있음 (구현일: 2026-06-08)
* [x] `scripts/benchmark_m2.sh` 있음 (구현일: 2026-06-08)
* [x] performance 문서 있음 (구현일: 2026-06-08)
* [x] `scripts/final_smoke.sh`가 valid local benchmark JSON을 쓰는 release gate 검증 (검증일: 2026-06-12)
* [x] baseline이 있을 때 `PERFORMANCE_REGRESSION`으로 실패하는 음성 테스트 검증 (검증일: 2026-06-12)
* [x] T15 local no-regression benchmark ledger: startup/dashboard/Home/chart/backtest/install 6개 측정 samples=5 budget 통과, WSL2 x86_64 evidence 고정 (검증일: 2026-06-16)
* [x] Raspberry Pi 4 실기기 baseline: Model B Rev 1.5 / Debian 13 aarch64 / Python 3.12.13에서 M2 benchmark 6개 측정 budget 통과, throttling `0x0`, Docker loopback API healthy 확인 (검증일: 2026-06-16)
* [~] Raspberry Pi 4 lab verification: Pi 전용 성능/팬/thermal guard 튜닝으로 startup `471.405ms`, 720-candle backtest `39.013ms`, 전체 budget pass를 확인했지만, 현재는 2선 5V 팬 소음 때문에 실사용 배포를 보류하고 해당 host 튜닝을 제거함 (검증/보류 결정일: 2026-06-16)
* [x] Raspberry Pi 4 hold cleanup: Pi 전용 클럭/팬/thermal guard/sysctl/journald/Docker daemon/boot overlay 튜닝 제거. 재부팅 후 custom service/file 없음, governor `ondemand`, max `1800MHz`, sysctl 기본값, Bluetooth service enabled/device `1`, Docker healthy 확인 (정리일: 2026-06-16)
* [x] Raspberry Pi 4 RC install/bootstrap gate: 2026-06-21 Todo 3B authenticated-shell proof 후 Todo 4 완료. Pi4 inventory 기준 throttle `0x0`, temp 44.3 C, CPU max 1.8GHz, memory available 3.4Gi, root disk available 21G. 사용자 홈 전용 toolchain으로 `uv`/Node/npm/Bun 확보, shell/npm/Bun install dry-run과 safe/purge uninstall dry-run 통과, missing-uv failure와 cleanup 검증 완료 (검증일: 2026-06-21)
* [x] Raspberry Pi 4 RC X7 benchmark/resource gate: Todo 5에서는 `x7_backtest_sample_latency`가 `2275.615ms / 1000ms`로 warn이었지만, T5A에서 feature-row allocation을 최적화해 같은 Pi4 반복 측정 `832.086ms`, `836.042ms`, `849.583ms / 1000ms` 모두 pass. `claim_allowed=false`, throttle `0x0`, temp `53.5C`, impossible baseline `PERFORMANCE_REGRESSION`, full local quality gate `494 passed`까지 확인 (검증일: 2026-06-22 KST)
* [x] Raspberry Pi 4 RC X7 paper soak/thermal/log gate: staged source로 500 tick paper-run 완료, `processed_events=500`, `created_trades=3`, `live_orders=false`, timeline `step_count=500`/`truncated=false`. stale stream은 `breaker=stale_data`, `new_orders_blocked=true`, `blocked_actions=1`로 통제 차단. runtime health HTTP 200, throttle `0x0`, temp `52.1C -> 56.9C`, Docker log bytes `0`, cleanup 통과 (검증일: 2026-06-21 UTC / 2026-06-22 KST)
* [x] Raspberry Pi 4 RC reversible deployment profile: `scripts/pi4_rc_profile.sh`, loopback/project-scoped Compose install, Pi4 RC stack `127.0.0.1:18113`, ping/runtime-health HTTP 200, Docker container healthy, packaged X7 semantic inspect `verified`, stock CPU max `1800000`, throttle `0x0`, safe uninstall/purge rollback receipt, token leak scan empty, `/tmp` cleanup 통과. Host tuning은 적용하지 않음 (검증일: 2026-06-21 UTC / 2026-06-22 KST)
* [ ] Raspberry Pi 4 cooling UX 재검증: 팬 제거 + 방열판-only 온도 실측, 저소음 5V 팬, 또는 GPIO/PWM 제어 팬으로 교체 후 재측정 필요 (미구현 확인일: 2026-06-16)
* [~] 숫자 기반 비교를 README에서 더 짧고 강하게 보여줄 수 있음. 단, public speed claim은 아직 금지 (시작일: 2026-06-08, 확인일: 2026-06-12)
* [~] 저사양 VPS 기준의 반복 측정은 아직 별도 검증 필요. Pi4 실기기 baseline은 확보했지만 Freqtrade 대비 public speed claim은 같은 기기 black-box 비교 전까지 금지 (미구현 확인일: 2026-06-12, Pi4 baseline 검증일: 2026-06-16)

### Docker / Compose QA

* [x] Docker-first quickstart 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Compose 실행 방향 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] final smoke 스크립트 있음. CLI/config/preflight/backtest/walk-forward/paper-run/X7 inspect/release wording/install/uninstall/Docker proof까지 묶고, 2026-06-22 Todo 14에서 실제 Docker 구간을 temp runtime으로 격리해 기본 `.runtime`을 건드리지 않게 수정 (구현일: 2026-06-07, 확장일: 2026-06-08, release gate 검증일: 2026-06-12, 격리 보강일: 2026-06-22)
* [x] Docker Compose 기준 최종 smoke를 “릴리즈 전 필수 관문”으로 문서화/검증 (구현일: 2026-06-12, post-review 재검증일: 2026-06-13)
* [x] local shell/npm/Bun install dry-run, safe uninstall dry-run, purge dry-run, missing-tool path 매트릭스 검증 (검증일: 2026-06-15)
* [x] G011 one-line install/uninstall 재검증. shell/npm/Bun wrapper는 환경변수 credential 입력 방식으로 검증했고, argv secret echo 위험을 문서화. invalid port, missing `uv`, unsafe purge, unmarked runtime, Pi4 invalid host-port 실패 경로와 secret scan까지 통과 (재검증일: 2026-06-22)
* [x] S8 WP8.1 dry-run safety rehearsal: backup archive redaction/manifest, credential DB URL redaction, restore apply=false, unsupported apply refusal, traversal/checksum-invalid/incomplete archive refusal, safe/purge uninstall scope, runtime marker/token/operator file preservation, unsafe purge refusal를 e2e/unit/tmux transcript로 고정 (검증일: 2026-06-17)
* [x] Raspberry Pi 4 Docker-first install smoke: `docker.io`/Compose v2 설치, `bash scripts/install.sh --yes --paper --testnet` 성공, `/api/v1/ping`, token auth dashboard/Home, loopback bind, restart/log rotation 확인 (검증일: 2026-06-16)
* [ ] 여러 OS/환경에서 install/uninstall 반복 검증은 아직 더 필요함 (미구현 확인일: 2026-06-15)

### Freqtrade / NFI 호환

* [x] Freqtrade는 기능 benchmark로만 본다는 원칙 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] strategy adapter / compat 문서 / feature coverage 문서 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] `docs/nfi-x7-compatibility.md`로 `NostalgiaForInfinityX7` target facts / Supported / Partial / Excluded / Clean-room provenance 분리 (문서 구현일: 2026-06-14)
* [x] public claim에서 upstream NFI full parity, profit claim, vendoring 주장을 막는 기준 문서화 (문서 구현일: 2026-06-14)
* [x] strategy inspection이 callback을 `supported` / `partial` / `excluded`로 분류하고, 계약 밖 public callback을 compat report에 노출 (구현일: 2026-06-14)
* [x] data-provider visible-row, missing informative frame, lookahead rejection 계약 테스트 고정 (구현일: 2026-06-14)
* [x] `nfi-engine sandbox check --output`이 clean-room fixture 기준 JSON compatibility report 생성 (구현일: 2026-06-14, CLI 검증일: 2026-06-14)
* [x] strategy-native signal/protection timeline을 backtest와 paper 결과에 공통 typed event log로 연결. raw frame은 저장하지 않고 compact JSON payload bytes를 evidence로 남김 (구현일: 2026-06-14)
* [x] `paper-run --timeline-output`으로 paper timeline JSON을 별도 출력하는 CLI 표면 추가 (구현일: 2026-06-14, CLI 검증일: 2026-06-14)
* [x] clean-room fixture 기준 backtest/paper typed field equivalence 테스트와 evidence 작성. entry side까지 비교하고 범위는 `NFI-shaped clean-room fixture only`로 고정 (구현일: 2026-06-14, side-equivalence 보강일: 2026-06-14)
* [~] Freqtrade-shaped 전략 감각을 살리는 호환 레이어는 core contract와 timeline/equivalence까지 진행됨. multi-timeframe/protection-rich fixture와 NFI-native 전략 구조화는 다음 단계 (시작일: 2026-06-07, S3 구현일: 2026-06-14)
* [~] NFI X7 callback 이름과 `5m`/informative timeframe 목표는 정리됨. data-provider 기본 계약과 실행 timeline은 잠겼지만, 다중 timeframe 실행 증거는 다음 구현 필요 (부분 확인일: 2026-06-14)
* [ ] upstream NFI와 완전 parity 구현/주장은 하지 않음. 실사용 비교 리포트도 clean-room fixture 기반으로 따로 만들어야 함 (미구현 확인일: 2026-06-14)
* [ ] NFI 전용 전략 구조로 완전히 독립하는 건 아직 다음 단계 (미구현 확인일: 2026-06-14)

### 거래소 지원 / exchange support

* [x] Freqtrade 문서 기준 Binance, Bingx, Bitmart, Bitget, Bybit, Gate.io, HTX, Hyperliquid, Kraken, Kraken Futures, OKX, Bitvavo, Kucoin 후보군 정리 (문서 구현일: 2026-06-14)
* [x] `verified` / `candidate` / `generic-unverified` 레벨을 분리해서 “모든 거래소 verified” 착각 방지 (문서 구현일: 2026-06-14)
* [x] spot / futures / margin / stoploss / market-order 차이를 runtime capability registry로 연결하고 config/preflight/`exchange check`에서 사용 (구현일: 2026-06-14)
* [x] `nfi-engine exchange capabilities --exchange <id> --trading-mode <spot|futures> --format json`으로 typed capability document 출력. Bybit/OKX 같은 후보와 MEXC 같은 generic-unverified를 같은 표면에서 구분 (구현일: 2026-06-15, CLI 증거일: 2026-06-15)
* [x] generic-unverified id는 report-only로만 보여주고 config validate에서는 계속 `EXCHANGE_UNSUPPORTED`로 차단 (구현일: 2026-06-15, safety 증거일: 2026-06-15)
* [x] 직접 `exchange check --exchange` 입력도 capability discovery와 같은 exchange-id 검증을 거쳐 unsafe id가 stdout에 새지 않게 차단 (구현일: 2026-06-15, review hardening일: 2026-06-15)
* [x] S4 exchange capability spine closeout. T8/T13 실제 CLI 표면, unsupported config 차단, targeted exchange/config/preflight/e2e 테스트 재검증 완료 (closeout일: 2026-06-15)
* [x] exchange API permission audit typed model. read/trade/futures/withdrawal/IP allowlist 상태를 `enabled`/`disabled`/`unknown`/`not_applicable`로 다루고 live blocker와 Home/Settings 표시까지 연결 (구현/HTTP/브라우저 검증일: 2026-06-15)
* [x] Bybit testnet wallet balance reader seam. 실제 credential이 없으면 live/testnet 네트워크로 억지 호출하지 않고 `WALLET_BALANCE_MISSING_CREDENTIALS`로 안전하게 막음. simulator는 deterministic balance reader로 QA 가능 (구현/테스트일: 2026-06-15)
* [~] 거래소 설정 UI가 registry profile을 직접 렌더링하고 live blocker를 operator workflow에 보여주는 작업은 다음 단계 (부분 확인일: 2026-06-14)
* [~] Hyperliquid 같은 특수 credential 모델은 exchange credential 경로로만 다루고, 로그인 토큰/지갑 seed phrase/메인 private key와 분리해야 함 (부분 확인일: 2026-06-14)
* [ ] fixture / testnet / sandbox evidence로 exchange profile을 `verified`로 승격하는 구현은 아직 남음 (미구현 확인일: 2026-06-15)

## 아직 안 한 것 / 브레인스토밍

여기는 기존 메모에 있었지만 아직 “완료”라고 보면 안 되는 부분이다.

### 운영 편의

* [x] 버튼 하나로 엔진 업데이트 proof gate: Settings에서 preview/apply/rollback dry-run proof가 가능하고, dirty worktree/source/backup/read-only/CSRF 차단이 증거로 고정됨. 실제 source mutation은 하지 않음 (구현일: 2026-06-21)
* [x] 버튼 하나로 전략 업데이트 proof gate: 엔진+전략 provenance digest/config/lock 상태를 같이 보여주고, `local_proof`만 허용하는 안전 receipt를 발급함. 원격 전략 다운로드나 upstream code import는 하지 않음 (구현일: 2026-06-21)
* [ ] 실제 GitHub self-update: 개발자 버튼 한 번으로 GitHub에서 엔진+전략을 받아 재시작하고 rollback까지 수행하는 기능은 아직 구현하지 않음. 현재 제품은 proof-only/update-safety gate까지 완료 (미구현 확인일: 2026-06-21)
* [x] UI에서 Dry Run / Live 선택 표면. dry-run이 기본이고 live preview는 `LIVE_TRADING_REQUIRES_CONFIRMATION`으로 차단됨 (구현/검증일: 2026-06-15)
* [~] live 전환 전 명시 확인 / preflight / 한도 / kill switch / reconciliation 위험 설명은 보이고, withdrawal permission audit는 live blocker로 연결됨. 최종 live confirm flow와 실제 주문 실행은 아직 별도 과제 (부분 구현일: 2026-06-15, permission 보강일: 2026-06-15)
* [~] 자동 복구/rollback 흐름: backup/restore/uninstall dry-run safety rehearsal은 완료했고 update rollback proof receipt도 완료. 하지만 실제 restore apply, 실제 source update rollback, retention cleanup은 별도 구현 필요 (부분 검증일: 2026-06-17, update proof 보강일: 2026-06-21)
* [x] 운영자용 “지금 뭘 해야 하는지” 액션 큐 1차 구현 (구현일: 2026-06-14, HTTP/브라우저 검증일: 2026-06-14)

### 실거래

* [ ] real-money live trading (미구현 확인일: 2026-06-12)
* [ ] 실제 거래소 키로 주문 실행 (미구현 확인일: 2026-06-12)
* [ ] 모든 거래소 verified 실거래 지원 (미구현 확인일: 2026-06-14)
* [ ] 자동 포지션 진입/청산의 실거래 보장 (미구현 확인일: 2026-06-12)
* [ ] profit claim / 수익률 주장 (미구현 확인일: 2026-06-12)
* [ ] upstream NFI와 동일 결과 주장 (미구현 확인일: 2026-06-12)

README 기준으로도 Milestone 1은 dry-run/paper 중심이다.
여기는 일부러 천천히 가야 하는 영역이다.

### 제품 확장

* [x] 웹 UI에서 first-run 설정 wizard base path, exchange permission audit, risk profile guardrail, explicit 지갑 잔액 fetch까지 연결 (구현/검증일: 2026-06-15, permission/risk 보강일: 2026-06-15, wallet fetch 보강일: 2026-06-15)
* [~] dashboard를 진짜 운영 cockpit 수준으로 확장 (action queue 1차 구현일: 2026-06-14, operator cockpit base 구현일: 2026-06-15, 포지션/계좌/위험 통합은 추가 필요)
* [ ] 백테스트 결과 비교 화면 (미구현 확인일: 2026-06-12)
* [ ] benchmark 결과 시각화 (미구현 확인일: 2026-06-12)
* [ ] plugin marketplace 느낌의 전략/확장 관리 (미구현 확인일: 2026-06-12)
* [ ] 모바일에서 운영자가 상태만 빠르게 보는 화면 (미구현 확인일: 2026-06-12)

## 지금 제일 좋은 점

* CLI, API, UI가 같은 엔진을 바라보기 시작했다
* 설정이 하드코딩 화면에서 metadata 기반으로 넘어가고 있다
* Docker가 “나중 배포”가 아니라 첫 실행 경로가 됐다
* 언어팩이 붙어서 로컬 장난감보다 제품 쪽으로 기울었다
* feature coverage 문서가 있어서 Freqtrade를 복붙 대상으로 보지 않게 막아준다
* strategy timeline이 생겨서 backtest/paper가 조용히 갈라지는지 entry side 포함 typed field로 잡을 수 있다
* benchmark / performance 문서가 생겨서 속도 이야기를 감으로 하지 않아도 된다
* final smoke, baseline regression, 브라우저 screenshot/HAR가 release gate 증거로 묶이기 시작했다
* read-only / CSRF / live safety가 UI 힌트가 아니라 서버 차단으로 검증됐다

## 지금 제일 조심할 점

* first-run wizard, exchange API permission audit, 지갑 balance fetch, pause/resume/stop-safe 컨트롤은 붙었지만, 최종 live confirm/order path 없이는 live-ready라고 말하면 안 된다
* CLI 명령이 있다고 운영자가 안전하게 쓸 수 있다는 뜻은 아니다. HTTP/브라우저 증거를 계속 붙여야 한다
* dashboard read model이 있다고 실제 live cockpit이 된 건 아니다
* i18n 누수는 한 번 잡아도 새 화면이 들어오면 다시 생길 수 있다
* Pi4 실기기 baseline은 확보됐지만 Freqtrade 대비 속도 우위나 실거래 안정성까지 증명된 건 아니다
* Todo 13 배포 profile에서 `.omo/evidence` 없는 staged/package 런타임의 X7 semantic status는 `verified`로 정리됐다. 다만 기본 install runtime-health가 wallet credential/preflight/dashboard seed 부족으로 `blocked`인 건 정상 운영 설정 전 상태라 live-ready 증거로 쓰면 안 된다
* Freqtrade compatibility가 있다고 NFI parity를 주장하면 안 된다
* clean-room equivalence가 생겼지만 upstream NFI X7 trade parity나 수익률 보장은 아직 절대 아니다
* generic-unverified 거래소는 “찾아볼 수 있음”이지 “쓸 수 있음”이 아니다. evidence 없이 paper/testnet/live로 승격하면 안 된다

## 다음 타격점

지금은 기능을 더 벌리기보다, 이미 생긴 표면을 하나의 사용 흐름으로 묶는 게 좋아 보인다.

1. 별도 live-execution design plan 작성: permission audit, allocation cap, reconciliation, manual halt, kill switch, dry-run preview, rollback evidence를 먼저 설계하고 나서만 실거래 unlock 검토
2. Pi4 baseline/soak/RC deployment/T5A 결과는 internal RC evidence로 유지하고 Freqtrade 대비 public speed claim은 계속 금지하기
3. Dashboard에 paper-run/persistence 상태를 더 직접 연결해서 운영자가 3초 안에 상태를 판단하게 만들기
4. `.runtime/secrets/exchange-wallet.env`에는 실제 exchange API key를 사용자가 다시 수동 입력해야 함. seed/private key/withdrawal key/local login token은 금지
5. 방열판-only 또는 저소음 팬으로 Pi4 cooling UX를 다시 잡은 뒤 long-run thermal evidence 재측정하기
6. Pi4 기준 nightly/수동 regression 비교 baseline을 추가하기
7. 여러 OS/환경에서 install/uninstall 반복 검증하기
8. feature coverage 문서를 지원/부분/제외로 계속 갱신하기
9. generic-unverified 거래소를 fixture/testnet evidence로 verified 승격하는 루틴 만들기
10. update button은 provenance/digest/rollback 증거가 붙을 때까지 안전 상태 UI로 유지하기
11. 백테스트 UI, plugin gallery는 M3+로 따로 계획하기

## 안티 슬롭 룰

이 프로젝트에서 피해야 할 냄새:

* UI 문구 하드코딩
* 설정 값을 화면마다 따로 해석
* Docker만 되고 로컬은 깨지는 구조
* 로컬만 되고 Compose는 깨지는 구조
* “일단 문자열로 처리”하는 설정/상태 모델
* 테스트가 CLI만 보고 실제 API/UI 표면을 놓치는 것
* Freqtrade 흉내만 내고 NFI 전용 장점을 못 만드는 것
* 구현 안 된 기능을 README나 브레인스토밍에서 완료처럼 말하는 것

## 태그라인 후보

* NFI 전용 트레이딩 엔진
* Freqtrade 감옥 밖의 NFI
* Install fast. Configure safely. Trade deliberately.
* NFI를 전략 파일에서 운영 제품으로
* 봇이 아니라 운전석

## 최종 그림

NFI_Engine의 완성형은 이런 모습이다.

사용자는 한 줄로 설치한다.
브라우저를 연다.
언어를 고른다.
거래소와 지갑을 연결한다.
preflight가 위험을 막는다.
dashboard가 현재 상태를 보여준다.
settings에서 전략과 리스크를 조정한다.
logs에서 문제를 추적한다.
benchmark와 backtest로 변경 전후를 비교한다.
업데이트와 제거까지 같은 톤으로 끝난다.

**아직 전부 끝난 게 아니다. 하지만 방향은 맞다. 지금 할 일은 더 벌리는 게 아니라, 이미 있는 표면을 사용자가 헷갈리지 않는 하나의 제품 흐름으로 잠그는 것이다.**
