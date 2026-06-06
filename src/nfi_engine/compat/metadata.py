from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

DEFAULT_METADATA_PATH: Final = (
    Path(__file__).resolve().parents[3] / "docs" / "compatibility" / "nfi.json"
)


class NfiMetadata(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    checked_at: str
    full_x7_parity: bool
    notes: tuple[str, ...]
    upstream_repo: str
    upstream_sha: str


def load_nfi_metadata(path: Path = DEFAULT_METADATA_PATH) -> NfiMetadata:
    return NfiMetadata.model_validate_json(path.read_text(encoding="utf-8"))
