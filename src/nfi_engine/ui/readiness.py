from __future__ import annotations

from html import escape

from nfi_engine.preflight.models import PreflightReport, PreflightStatus


def render_readiness_panel(readiness: PreflightReport | None) -> str:
    if readiness is None:
        return _html_lines(
            [
                '<section data-testid="readiness-panel">',
                "  <h2>Readiness</h2>",
                '  <div class="state">No preflight report loaded</div>',
                "</section>",
            ],
        )
    summary = "PREFLIGHT_BLOCKED" if readiness.blocked else "PREFLIGHT_PASSED"
    start_state = "blocked" if readiness.blocked else "ready"
    return _html_lines(
        [
            '<section data-testid="readiness-panel">',
            "  <h2>Readiness</h2>",
            f'  <div class="state" data-testid="readiness-summary">{summary}</div>',
            f"  {_group(readiness, PreflightStatus.PASS, 'readiness-pass', 'Pass')}",
            f"  {_group(readiness, PreflightStatus.WARN, 'readiness-warn', 'Warn')}",
            f"  {_group(readiness, PreflightStatus.BLOCK, 'readiness-block', 'Block')}",
            (
                '  <div class="lock" data-testid="readiness-start-blocked">'
                f"Start state: {start_state}</div>"
            ),
            "</section>",
        ],
    )


def _group(
    report: PreflightReport,
    status: PreflightStatus,
    test_id: str,
    label: str,
) -> str:
    rows = "\n".join(
        _check_row(code=check.code.value, message=check.message)
        for check in report.checks
        if check.status is status
    )
    if rows == "":
        rows = '<li class="muted">none</li>'
    return _html_lines(
        [
            f'<div data-testid="{escape(test_id)}">',
            f"  <h3>{escape(label)}</h3>",
            f"  <ul>{rows}</ul>",
            "</div>",
        ],
    )


def _check_row(*, code: str, message: str) -> str:
    return f"<li><strong>{escape(code)}</strong> {escape(message)}</li>"


def _html_lines(lines: list[str]) -> str:
    return "\n".join(lines)
