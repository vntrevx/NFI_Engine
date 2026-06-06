from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.pairlist import PairlistApplyResponse, PairlistDraftResponse


@pytest.mark.anyio
async def test_pairlist_ui_preview_draft_and_apply_audit_events() -> None:
    # Given: the local settings app with pairlist controls.
    async with AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://testserver",
    ) as client:
        # When: the frontend is loaded and a DOGE blacklist patch is previewed.
        page = await client.get("/settings")
        csrf_headers = _csrf_headers_from_page(page.text)
        preview = await client.post(
            "/api/v1/pairlist/preview",
            json={"blacklist": "DOGE/USDT:USDT"},
        )
        draft = await client.post(
            "/api/v1/pairlist/draft",
            headers=csrf_headers,
            json={"blacklist": "DOGE/USDT:USDT"},
        )
        applied = await client.post(
            "/api/v1/pairlist/apply",
            headers=csrf_headers,
            json={"blacklist": "DOGE/USDT:USDT"},
        )

    # Then: the UI exposes compact controls and API responses include audit events.
    assert page.status_code == 200
    assert 'data-testid="pairlist-panel"' in page.text
    assert 'data-testid="pairlist-blacklist"' in page.text
    assert preview.status_code == 200
    assert "BLACKLISTED" in preview.text
    draft_payload = PairlistDraftResponse.model_validate_json(draft.content)
    apply_payload = PairlistApplyResponse.model_validate_json(applied.content)
    assert draft_payload.accepted is True
    assert draft_payload.audit_event == "PAIRLIST_DRAFT_SAVED"
    assert apply_payload.applied is True
    assert apply_payload.audit_event == "PAIRLIST_APPLIED"


def _csrf_headers_from_page(html: str) -> dict[str, str]:
    marker = '<meta name="nfi-csrf-token" content="'
    token = html.split(marker, maxsplit=1)[1].split('"', maxsplit=1)[0]
    return {"x-nfi-csrf-token": token}
