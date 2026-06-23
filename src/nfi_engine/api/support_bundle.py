from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import ClassVar, Final
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel, ConfigDict

from nfi_engine.api.models import LogListResponse, SupportBundleResponse

CONFIG_NAME: Final = "config.json"
LOGS_NAME: Final = "logs.json"
MANIFEST_NAME: Final = "manifest.json"
LOCAL_PROFILE_NAME: Final = "local-profile.json"


class SupportBundleManifest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    engine_version: str
    generated_at: datetime
    redacted: bool
    files: tuple[str, ...]
    checksums: dict[str, str]


class SupportBundleLocalProfile(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    engine_version: str
    generated_at: datetime
    exchange_name: str
    trading_mode: str
    environment: str
    locale: str
    read_only: bool


@dataclass(frozen=True, slots=True)
class SupportBundleMember:
    name: str
    data: bytes


def support_bundle_zip(bundle: SupportBundleResponse) -> bytes:
    members = _bundle_members(bundle)
    manifest = SupportBundleManifest(
        engine_version=bundle.engine_version,
        generated_at=bundle.generated_at,
        redacted=True,
        files=tuple(member.name for member in members),
        checksums={member.name: _sha256_bytes(member.data) for member in members},
    )
    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, manifest.model_dump_json(indent=2))
        for member in members:
            archive.writestr(member.name, member.data)
    return buffer.getvalue()


def _bundle_members(bundle: SupportBundleResponse) -> tuple[SupportBundleMember, ...]:
    return (
        SupportBundleMember(
            CONFIG_NAME,
            bundle.redacted_config.model_dump_json(indent=2).encode(),
        ),
        SupportBundleMember(
            LOGS_NAME,
            LogListResponse(items=bundle.logs).model_dump_json(indent=2).encode(),
        ),
        SupportBundleMember(
            LOCAL_PROFILE_NAME,
            SupportBundleLocalProfile(
                engine_version=bundle.engine_version,
                generated_at=bundle.generated_at,
                exchange_name=bundle.redacted_config.exchange.name,
                trading_mode=bundle.redacted_config.exchange.trading_mode,
                environment=bundle.redacted_config.engine.environment,
                locale=bundle.redacted_config.ui.locale,
                read_only=bundle.redacted_config.ui.read_only,
            )
            .model_dump_json(indent=2)
            .encode(),
        ),
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
