from __future__ import annotations

from nfi_engine.exchange.runtime_verification_models import (
    ExchangeRuntimeCheck,
    ExchangeRuntimeCheckStatus,
)


def pass_check(*, stage: str, code: str, message: str) -> ExchangeRuntimeCheck:
    return ExchangeRuntimeCheck(
        stage=stage,
        status=ExchangeRuntimeCheckStatus.PASS,
        code=code,
        message=message,
        next_action="",
    )


def block_check(
    *,
    stage: str,
    code: str,
    message: str,
    next_action: str,
) -> ExchangeRuntimeCheck:
    return ExchangeRuntimeCheck(
        stage=stage,
        status=ExchangeRuntimeCheckStatus.BLOCK,
        code=code,
        message=message,
        next_action=next_action,
    )


def manual_check(
    *,
    stage: str,
    code: str,
    message: str,
    next_action: str,
) -> ExchangeRuntimeCheck:
    return ExchangeRuntimeCheck(
        stage=stage,
        status=ExchangeRuntimeCheckStatus.MANUAL,
        code=code,
        message=message,
        next_action=next_action,
    )


def not_required_check(*, stage: str, code: str, message: str) -> ExchangeRuntimeCheck:
    return ExchangeRuntimeCheck(
        stage=stage,
        status=ExchangeRuntimeCheckStatus.NOT_REQUIRED,
        code=code,
        message=message,
        next_action="",
    )
