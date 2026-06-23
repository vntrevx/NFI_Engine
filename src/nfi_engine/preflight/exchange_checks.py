from __future__ import annotations

from nfi_engine.config import RuntimeSettings
from nfi_engine.exchange import get_exchange_profile
from nfi_engine.preflight.models import PreflightCheck, PreflightCode, PreflightStatus


def exchange_mode_check(settings: RuntimeSettings) -> PreflightCheck:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        return PreflightCheck(
            code=PreflightCode.CONFIG_INVALID,
            status=PreflightStatus.BLOCK,
            message=f"unsupported exchange: {settings.exchange.name}",
        )
    if profile.exchange_id != "simulator" and not settings.exchange.testnet:
        return PreflightCheck(
            code=PreflightCode.EXCHANGE_TESTNET_REQUIRED,
            status=PreflightStatus.BLOCK,
            message=f"{profile.exchange_id} requires testnet=true in current milestone",
        )
    if settings.exchange.testnet and not profile.supports_testnet:
        return PreflightCheck(
            code=PreflightCode.EXCHANGE_TESTNET_REQUIRED,
            status=PreflightStatus.BLOCK,
            message=f"{profile.exchange_id} has no registry-backed testnet support",
        )
    return PreflightCheck(
        code=PreflightCode.EXCHANGE_TESTNET_REQUIRED,
        status=PreflightStatus.PASS,
        message=f"exchange registry ok: {profile.exchange_id} ({profile.support_level.value})",
    )
