from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.runtime_health_models import RuntimeHealthResponse
from nfi_engine.config.models import ApiSettings, CircuitBreakerSettings, RuntimeSettings
from nfi_engine.dashboard import DashboardEquityPoint, DashboardExecutionEvent, DashboardReadModels
from nfi_engine.dashboard.store import StaticDashboardReadStore
from nfi_engine.domain import AccountSnapshot, StakeAmount
from nfi_engine.execution import ExecutionEventType, ExecutionState

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER: Final = "local-test-bearer"
PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.anyio


class StaticWalletReader:
    def __init__(self, *, captured_at: datetime) -> None:
        self._captured_at: datetime = captured_at

    async def fetch_balance(self) -> AccountSnapshot:
        return AccountSnapshot(
            captured_at=self._captured_at,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(900)),
            positions=(),
        )


async def test_runtime_health_api_returns_stable_machine_codes() -> None:
    now = datetime.now(UTC)
    settings = RuntimeSettings.model_validate(
        {
            "api": {"auth_token": LOCAL_BEARER},
            "database": {"url": "sqlite+aiosqlite:///:memory:"},
        },
    )
    async with _client(
        create_app(
            settings=settings,
            dashboard_store=StaticDashboardReadStore(_read_models(now)),
            wallet_balance_reader=StaticWalletReader(captured_at=now),
        ),
    ) as client:
        unauthenticated = await client.get("/api/v1/runtime/health")
        response = await client.get("/api/v1/runtime/health", headers=_auth_headers())

    payload = RuntimeHealthResponse.model_validate_json(response.content)
    codes = {check.code for check in payload.checks}
    assert unauthenticated.status_code == 401
    assert response.status_code == 200
    assert payload.database.state == "healthy"
    assert payload.state == "healthy"
    assert {
        "ENGINE_HEARTBEAT",
        "DATABASE",
        "WALLET_FRESHNESS",
        "RECONCILIATION_AGE",
        "EXCHANGE_API_ERRORS",
    }.issubset(codes)


async def test_runtime_health_api_fails_closed_for_stale_wallet() -> None:
    now = datetime.now(UTC)
    settings = RuntimeSettings(
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
        circuit_breakers=CircuitBreakerSettings(max_stale_seconds=60),
    )
    async with _client(
        create_app(
            settings=settings,
            dashboard_store=StaticDashboardReadStore(_read_models(now)),
            wallet_balance_reader=StaticWalletReader(captured_at=now - timedelta(minutes=5)),
        ),
    ) as client:
        response = await client.get("/api/v1/runtime/health", headers=_auth_headers())

    payload = RuntimeHealthResponse.model_validate_json(response.content)
    checks = {check.code: check.state for check in payload.checks}
    assert response.status_code == 200
    assert payload.state == "blocked"
    assert checks["WALLET_FRESHNESS"] == "blocked"


def test_runtime_health_cli_reports_json_machine_codes(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime-health.yaml"
    db_path = tmp_path / "health.sqlite3"
    config_path.write_text(
        f"""database:
  url: sqlite+aiosqlite:///{db_path}
exchange:
  name: simulator
  trading_mode: spot
  testnet: true
""",
        encoding="utf-8",
    )
    uv_path = shutil.which("uv")
    assert uv_path is not None

    result = subprocess.run(
        [
            uv_path,
            "run",
            "nfi-engine",
            "runtime-health",
            "check",
            "--config",
            str(config_path),
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    payload = RuntimeHealthResponse.model_validate_json(result.stdout)
    codes = {check.code for check in payload.checks}
    assert result.returncode == 0, result.stderr
    assert "DATABASE" in codes
    assert "EXCHANGE_API_ERRORS" in codes
    assert payload.database.writable is True


def _read_models(at: datetime) -> DashboardReadModels:
    return DashboardReadModels(
        equity_points=(DashboardEquityPoint(at=at, equity=Decimal(1000), available=Decimal(900)),),
        recent_execution_events=(
            DashboardExecutionEvent(
                event_id=1,
                intent_id="intent-1",
                event_type=ExecutionEventType.RECONCILED,
                state=ExecutionState.RECONCILED,
                message="reconciliation clear",
                raw_status_code="RECONCILIATION_CLEAR",
                metadata_json='{"issue_codes":[],"mismatch_count":0,"trading_halted":false}',
                occurred_at=at,
            ),
        ),
    )


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LOCAL_BEARER}"}


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
