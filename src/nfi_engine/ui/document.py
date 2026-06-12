from __future__ import annotations

from html import escape

from nfi_engine.config import Locale
from nfi_engine.ui.assets import STYLE
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_document(
    *,
    title: str,
    body: str,
    csrf_token: str = "",
    extra_style: str = "",
    locale: Locale = Locale.EN,
) -> str:
    return f"""<!doctype html>
<html lang="{locale.value}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="nfi-csrf-token" content="{escape(csrf_token)}">
  <title>{escape(title)}</title>
  <style>{STYLE}{extra_style}</style>
</head>
<body>{body}</body>
</html>
"""


def render_nav(*, active: str, locale: Locale) -> str:
    links = (
        ("home", "/", MessageKey.NAV_HOME),
        ("settings", "/settings", MessageKey.NAV_SETTINGS),
        ("logs", "/logs", MessageKey.NAV_LOGS),
    )
    body = "".join(
        _nav_link(
            name=name,
            href=href,
            label=localize(locale, label_key),
            active=active,
        )
        for name, href, label_key in links
    )
    return f'<nav data-testid="home-nav">{body}</nav>'


def _nav_link(*, name: str, href: str, label: str, active: str) -> str:
    current = ' aria-current="page"' if name == active else ""
    return f'<a href="{escape(href)}"{current}>{escape(label)}</a>'
