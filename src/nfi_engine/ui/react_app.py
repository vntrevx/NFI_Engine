from __future__ import annotations

from html import escape
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, TypeAdapter

from nfi_engine.config import Locale
from nfi_engine.ui.document import FAVICON_HREF

REACT_DIST_DIR: Final = Path(__file__).with_name("react_dist")
REACT_MANIFEST_PATH: Final = REACT_DIST_DIR / ".vite" / "manifest.json"
REACT_APP_ROOT: Final = "nfi-react-root"


class ViteManifestEntry(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    file: str
    css: tuple[str, ...] = ()


MANIFEST_ADAPTER: Final = TypeAdapter(dict[str, ViteManifestEntry])


def react_static_dir() -> Path:
    return REACT_DIST_DIR


def react_app_available() -> bool:
    return REACT_MANIFEST_PATH.exists()


def render_react_app_page(
    *,
    title: str,
    locale: Locale,
    csrf_token: str,
    page: str,
    fallback_body: str = "",
) -> str:
    entry = _index_entry()
    styles = "".join(
        f'  <link rel="stylesheet" href="/ui-react/{escape(path)}">\n' for path in entry.css
    )
    return f"""<!doctype html>
<html lang="{locale.value}" data-nfi-page="{escape(page)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="nfi-csrf-token" content="{escape(csrf_token)}">
  <link rel="icon" href="{FAVICON_HREF}">
  <title>{escape(title)}</title>
{styles}</head>
<body>
  <div id="{REACT_APP_ROOT}"></div>
  <noscript>{fallback_body or "NFI Engine operator console requires JavaScript."}</noscript>
  <script type="module" src="/ui-react/{escape(entry.file)}"></script>
</body>
</html>
"""


def _index_entry() -> ViteManifestEntry:
    manifest = MANIFEST_ADAPTER.validate_json(REACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = manifest.get("index.html")
    if entry is None:
        entry = next(iter(manifest.values()))
    return entry
