# 2026-06-14 M2.5 Action Queue Implementation

## 한 줄 요약

M2.5 첫 구현 웨이브로 Home / dashboard snapshot에 **운영자용 Action Queue**를
추가했다. 이제 대시보드가 단순히 상태를 보여주는 것에서 한 단계 나아가,
운영자가 지금 무엇을 확인해야 하는지 최대 4개 액션으로 압축해서 보여준다.

## 구현한 것

- `DashboardAction` read model 추가
- `DashboardSnapshot.actions` API 필드 추가
- `/api/v1/dashboard/snapshot`에 bounded action queue 직렬화 추가
- Home에 `data-testid="action-queue"` / `data-testid="action-item"` 렌더링 추가
- ready 상태는 `#status` 실제 anchor로 연결
- error 상태는 `/logs`로 연결
- support follow-up은 `/api/v1/reports/support-bundle.zip` 실제 export endpoint로 연결
- EN/KO/EL action queue heading i18n 추가
- 모바일에서 action item 링크가 암묵적 2열을 만들지 않도록 responsive CSS 수정

## 액션 우선순위

현재 우선순위는 제품 흐름 기준으로 작게 고정했다.

1. readiness/preflight blocked
2. recent runtime errors
3. empty pairlist
4. clean paper/testnet ready state
5. error가 있을 때 support bundle follow-up

최대 4개까지만 반환한다. 새 polling loop나 추가 DB scan은 만들지 않았다.

## 검증

로컬 evidence는 ULW 작업 디렉터리에 보관했다. GitHub에 올릴 source 문서에는
로컬 evidence 경로를 박지 않는다.

통과한 targeted gate:

```bash
uv run pytest -q tests/unit/dashboard/test_snapshot.py tests/unit/ui/test_pages.py tests/e2e/test_home_ui.py tests/unit/ui/test_i18n.py
uv run ruff format --check src/nfi_engine/dashboard src/nfi_engine/api src/nfi_engine/ui tests/unit/dashboard/test_snapshot.py tests/unit/ui/test_pages.py tests/e2e/test_home_ui.py tests/unit/ui/test_i18n.py
uv run ruff check src/nfi_engine/dashboard src/nfi_engine/api src/nfi_engine/ui tests/unit/dashboard/test_snapshot.py tests/unit/ui/test_pages.py tests/e2e/test_home_ui.py tests/unit/ui/test_i18n.py
uv run basedpyright src/nfi_engine/dashboard src/nfi_engine/api src/nfi_engine/ui tests/unit/dashboard/test_snapshot.py tests/unit/ui/test_pages.py tests/e2e/test_home_ui.py tests/unit/ui/test_i18n.py
```

실제 surface 검증:

- loopback 서버에서 `/api/v1/dashboard/snapshot` curl 확인
- Playwright Chromium desktop/mobile screenshot 확인
- Home DOM에서 action queue, setup doctor, safety explainer, chart shell, Settings/Logs nav 확인
- `localStorage`, `sessionStorage`, `https://`, `cdn` 문자열 부재 확인
- visual QA에서 잡힌 mobile link layout과 dead-link blocker 수정

## 아직 안 끝난 것

- First-run wizard 완료 UX
- Raspberry Pi 4 실기기 반복 측정
- benchmark 결과의 operator-facing 요약
- 여러 OS/환경 install/uninstall 반복 검증
- live 전환 UX는 계속 설명/차단 중심이며, real-money execution은 아직 범위 밖

## 판단

이번 웨이브는 "운영자가 지금 뭘 해야 하는지"를 Home과 dashboard API에 박은 작업이다.
큰 기능을 벌린 게 아니라 기존 M2 표면을 제품처럼 쓰기 위한 압축도를 올린 작업이다.
쌈%뽕하지만 아직 M2.5의 첫 조각이다.
