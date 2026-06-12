# NFI_Engine 브레인스토밍 체크리스트

## 읽는 법

이 문서는 아이디어를 버리는 문서가 아니라, **헷갈리지 않게 상태를 나누는 문서**다.

* `[x] 완료`: repo에 실제 파일/명령/API/UI/문서/테스트 표면이 있음
* `[~] 부분`: 뼈대나 화면은 있으나 제품 흐름으로 더 잠가야 함
* `[ ] 아이디어`: 아직 구현 전이거나 Milestone 밖임

현재 기준은 `README.md`, `src/nfi_engine`, `docs`, `scripts`, `tests`,
`.omo/evidence/2026-06-12-dev-entry/`에 보이는 상태다.

## 날짜 기준

* `구현일`: git commit 또는 파일 생성/수정 timestamp로 구현 표면이 확인된 날짜
* `시작일`: 일부 구현 표면은 있으나 제품 동선이 아직 덜 잠긴 날짜
* `확인일`: 이 문서를 정리하면서 상태를 다시 확인한 날짜
* `미구현 확인일`: repo에서 아직 구현 표면을 확인하지 못한 날짜

주요 증거:

* `2026-06-07`: `fe19748 feat: bootstrap nfi engine m1` 커밋으로 초기 엔진/기본 CLI/API/문서/테스트 표면 확인
* `2026-06-08`: working tree timestamp 기준 setup, install/uninstall, dashboard, i18n, benchmark, UI 확장 확인
* `2026-06-12`: dev-entry hardening 기준일. Task 1-9 증거가 `.omo/evidence/2026-06-12-dev-entry/`에 있음
* `2026-06-12`: 이 브레인스토밍 문서 상태 재분류/검수일
* `2026-06-13`: post-review blocker 수정/검증일. runtime settings provider, Greek catalog, Login desktop evidence, F2-F4 closeout 확인

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

### 설치 / 실행

* [x] `scripts/install.sh` (구현일: 2026-06-08)
* [x] `scripts/uninstall.sh` (구현일: 2026-06-08)
* [x] `Dockerfile` (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] `compose.yaml` (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Docker docs (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] safe uninstall / purge 흐름 문서화 (구현일: 2026-06-08)
* [x] `scripts/final_smoke.sh` (구현일: 2026-06-07, 확장일: 2026-06-08, release gate 검증일: 2026-06-12)

### 문서 / 테스트

* [x] README에 clean-room 정체성, quickstart, architecture map 정리 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] operations / docker / ui / performance / feature coverage 문서 (구현일: 2026-06-08)
* [x] e2e 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] unit 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] integration 테스트 표면 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Freqtrade feature coverage 문서로 “따라 만들기”가 아니라 “기능 범위 비교” 방향 잡음 (구현일: 2026-06-08)
* [x] `brainstorming/2026-06-12_IMPLEMENTATION_SUMMARY.md` 작성 및 최종 gate 결과 반영 (작성일: 2026-06-12, 업데이트일: 2026-06-13)

## 부분 구현 / 더 잠가야 하는 것

여기는 “없다”는 뜻이 아니다.
겉면은 있는데, 제품처럼 믿고 쓰려면 연결과 검증을 더 해야 하는 것들이다.

### 첫 사용자 동선

* [x] 한 줄 설치는 있음 (구현일: 2026-06-08, Docker smoke 검증일: 2026-06-12)
* [x] 설치 후 token login -> Home 진입 흐름 있음 (구현일: 2026-06-08, 브라우저/HTTP 검증일: 2026-06-12)
* [~] setup preview -> Home -> Settings -> Dashboard snapshot 흐름은 검증됨. 다만 "wizard 완료" 제품 UX는 아직 더 다듬어야 함 (시작일: 2026-06-08, hardening 검증일: 2026-06-12)
* [~] 실패했을 때 typed error / next action은 늘었지만, 모든 사용자 실패를 한 화면에서 안내하는 UX는 더 필요함 (시작일: 2026-06-12)

### Settings

* [x] config model / metadata / settings field 구조 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] UI에서 설정을 다루는 표면 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] runtime-safe 저장 -> 검증 -> 적용 -> 재조회 흐름 고정 (구현일: 2026-06-12)
* [x] runtime-safe apply 뒤 Settings locale과 read-only write gate가 같은 running config를 보도록 post-review 수정 (구현일: 2026-06-12, 검증일: 2026-06-13)
* [x] restart-required field는 running config를 바꾸지 않고 reload 필요로 응답 (구현일: 2026-06-12)
* [x] secret write-only / redaction 검증 (구현일: 2026-06-12)
* [~] live 전환 같은 위험 설정은 서버에서 막지만, 사용자용 마찰/설명 UX는 더 강해져야 함 (시작일: 2026-06-12)

### Dashboard

* [x] dashboard module / model / route / repository 표면 있음 (구현일: 2026-06-08)
* [x] dashboard가 persistence/read-store 기반 bounded snapshot으로 연결됨 (구현일: 2026-06-12)
* [x] Home 지표가 read-model snapshot 또는 정직한 empty state를 보여줌 (구현일: 2026-06-12)
* [~] 실제 paper/live 상태를 운영자가 3초 안에 판단할 정도의 압축도는 더 필요함 (시작일: 2026-06-12)
* [~] 포지션, 계좌, 손익, 위험 상태를 “운영 화면”답게 더 밀도 있게 묶는 작업은 다음 단계 (시작일: 2026-06-12)

### i18n

* [x] 한국어 / 영어 / 그리스어 언어팩 파일 있음 (구현일: 2026-06-08)
* [x] UI i18n 구조 있음 (구현일: 2026-06-08)
* [x] Home / Settings / Logs / login / setup / readiness 주요 사용자 문구 catalog 경유 검증 (구현일: 2026-06-12)
* [x] machine code / enum / audit ID는 번역하지 않도록 테스트 고정 (구현일: 2026-06-12)
* [x] EN/KO/EL catalog completeness 테스트와 Greek Settings title 누락 수정 (구현일: 2026-06-12, 검증일: 2026-06-13)
* [~] 새 화면 추가 시 하드코딩 문구가 다시 들어가지 않게 계속 테스트를 확장해야 함 (시작일: 2026-06-12)

### Benchmark / Performance

* [x] benchmark CLI 있음 (구현일: 2026-06-08)
* [x] `scripts/benchmark_m2.sh` 있음 (구현일: 2026-06-08)
* [x] performance 문서 있음 (구현일: 2026-06-08)
* [x] `scripts/final_smoke.sh`가 valid local benchmark JSON을 쓰는 release gate 검증 (검증일: 2026-06-12)
* [x] baseline이 있을 때 `PERFORMANCE_REGRESSION`으로 실패하는 음성 테스트 검증 (검증일: 2026-06-12)
* [~] 숫자 기반 비교를 README에서 더 짧고 강하게 보여줄 수 있음. 단, public speed claim은 아직 금지 (시작일: 2026-06-08, 확인일: 2026-06-12)
* [ ] Raspberry Pi 4 / 저사양 VPS 기준의 반복 측정은 아직 별도 검증 필요 (미구현 확인일: 2026-06-12)

### Docker / Compose QA

* [x] Docker-first quickstart 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] Compose 실행 방향 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] final smoke 스크립트 있음 (구현일: 2026-06-07, 확장일: 2026-06-08, release gate 검증일: 2026-06-12)
* [x] Docker Compose 기준 최종 smoke를 “릴리즈 전 필수 관문”으로 문서화/검증 (구현일: 2026-06-12, post-review 재검증일: 2026-06-13)
* [ ] 여러 OS/환경에서 install/uninstall 반복 검증은 아직 더 필요함 (미구현 확인일: 2026-06-12)

### Freqtrade / NFI 호환

* [x] Freqtrade는 기능 benchmark로만 본다는 원칙 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [x] strategy adapter / compat 문서 / feature coverage 문서 있음 (구현일: 2026-06-07, 확장일: 2026-06-08)
* [~] Freqtrade-shaped 전략 감각을 살리는 호환 레이어는 진행 중 (시작일: 2026-06-07, 확인일: 2026-06-12)
* [ ] upstream NFI와 완전 parity를 말하면 안 됨 (미구현 확인일: 2026-06-12)
* [ ] NFI 전용 전략 구조로 완전히 독립하는 건 아직 다음 단계 (미구현 확인일: 2026-06-12)

## 아직 안 한 것 / 브레인스토밍

여기는 기존 메모에 있었지만 아직 “완료”라고 보면 안 되는 부분이다.

### 운영 편의

* [ ] 버튼 하나로 엔진 업데이트 (미구현 확인일: 2026-06-12)
* [ ] 버튼 하나로 전략 업데이트 (미구현 확인일: 2026-06-12)
* [ ] UI에서 Dry Run / Live를 안전하게 전환 (미구현 확인일: 2026-06-12)
* [ ] live 전환 전 다중 확인 / preflight / 위험 설명 UX (미구현 확인일: 2026-06-12)
* [ ] 자동 복구/rollback 흐름 (미구현 확인일: 2026-06-12)
* [ ] 운영자용 “지금 뭘 해야 하는지” 액션 큐 (미구현 확인일: 2026-06-12)

### 실거래

* [ ] real-money live trading (미구현 확인일: 2026-06-12)
* [ ] 실제 거래소 키로 주문 실행 (미구현 확인일: 2026-06-12)
* [ ] 자동 포지션 진입/청산의 실거래 보장 (미구현 확인일: 2026-06-12)
* [ ] profit claim / 수익률 주장 (미구현 확인일: 2026-06-12)
* [ ] upstream NFI와 동일 결과 주장 (미구현 확인일: 2026-06-12)

README 기준으로도 Milestone 1은 dry-run/paper 중심이다.
여기는 일부러 천천히 가야 하는 영역이다.

### 제품 확장

* [ ] 웹 UI에서 전체 설정 wizard 완성 (미구현 확인일: 2026-06-12)
* [ ] dashboard를 진짜 운영 cockpit 수준으로 확장 (미구현 확인일: 2026-06-12)
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
* benchmark / performance 문서가 생겨서 속도 이야기를 감으로 하지 않아도 된다
* final smoke, baseline regression, 브라우저 screenshot/HAR가 release gate 증거로 묶이기 시작했다
* read-only / CSRF / live safety가 UI 힌트가 아니라 서버 차단으로 검증됐다

## 지금 제일 조심할 점

* 화면이 있다고 제품 동선이 완성된 건 아니다. 이제 smoke는 있지만 wizard polish는 남았다
* CLI 명령이 있다고 운영자가 안전하게 쓸 수 있다는 뜻은 아니다. HTTP/브라우저 증거를 계속 붙여야 한다
* dashboard read model이 있다고 실제 live cockpit이 된 건 아니다
* i18n 누수는 한 번 잡아도 새 화면이 들어오면 다시 생길 수 있다
* benchmark 명령이 있다고 저사양 환경 성능이 증명된 건 아니다
* Freqtrade compatibility가 있다고 NFI parity를 주장하면 안 된다

## 다음 타격점

지금은 기능을 더 벌리기보다, 이미 생긴 표면을 하나의 사용 흐름으로 묶는 게 좋아 보인다.

1. setup preview를 진짜 first-run wizard 완료 UX로 다듬기
2. Dashboard에 paper-run/persistence 상태를 더 직접 연결해서 운영자가 3초 안에 상태를 판단하게 만들기
3. 위험/live 전환 UX에 더 강한 friction과 설명을 붙이기
4. benchmark 결과를 README에 짧게 노출하되 public speed claim은 계속 금지하기
5. 여러 OS/환경에서 install/uninstall 반복 검증하기
6. feature coverage 문서를 지원/부분/제외로 계속 갱신하기
7. 백테스트 UI, plugin gallery, update button은 M3+로 따로 계획하기

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
