from __future__ import annotations

from pathlib import Path

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.ui.pages import render_home_page

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_browser_qa_home_audit_targets_current_cockpit_contract() -> None:
    # Given: the browser QA script and the rendered current home page.
    script = (REPO_ROOT / "scripts/browser_qa_t10_setup_flow.mjs").read_text()
    html = render_home_page(settings=RuntimeSettings(), logs=initial_log_entries())
    react_home_source = (REPO_ROOT / "frontend/src/components/HomePanel.tsx").read_text()
    contract_source = react_home_source if 'id="nfi-react-root"' in html else html

    # When: the script audits the home cockpit.
    required_ids = (
        "operator-cockpit",
        "dashboard-primary-stack",
        "dashboard-ops-rail",
        "cockpit-runtime-health",
        "cockpit-permission-audit",
        "cockpit-capability-level",
        "cockpit-wallet-balance",
        "execution-safety-signals",
        "runtime-controls",
    )

    # Then: every audited marker exists and retired cockpit IDs stay out.
    for test_id in required_ids:
        assert test_id in contract_source
        assert f'"{test_id}"' in script
    for retired_id in (
        "cockpit-safety",
        "cockpit-active-mode",
        "cockpit-allocated-amount",
        "cockpit-where-next",
    ):
        assert retired_id not in script
