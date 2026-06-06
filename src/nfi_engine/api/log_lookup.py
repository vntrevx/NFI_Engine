from __future__ import annotations

from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.api.models import ErrorLookupResponse, LogEntryResponse


def error_lookup_response(
    *,
    logs: tuple[LogEntryResponse, ...],
    code: str,
) -> ErrorLookupResponse:
    entry = _find_log_entry(logs=logs, code=code)
    return ErrorLookupResponse(
        code=code,
        message=_error_message(code),
        reportable=True,
        correlation_id="not-found" if entry is None else entry.correlation_id,
        safe_summary=_error_summary(code=code, entry=entry),
        report_hint=_error_hint(code=code, entry=entry),
    )


def _find_log_entry(
    *,
    logs: tuple[LogEntryResponse, ...],
    code: str,
) -> LogEntryResponse | None:
    for entry in logs:
        if entry.code == code:
            return entry
    return None


def _error_message(code: str) -> str:
    match code:
        case "CONFIG_VALIDATION_ERROR":
            return "config validation failed"
        case value if value == ApiErrorCode.TICK_PARSE_ERROR.value:
            return "tick stream could not be parsed"
        case _:
            return "unknown error code"


def _error_summary(*, code: str, entry: LogEntryResponse | None) -> str:
    if entry is not None:
        return entry.safe_summary
    if code == "CONFIG_VALIDATION_ERROR":
        return "config validation failed"
    return "event code was not found in recent logs"


def _error_hint(*, code: str, entry: LogEntryResponse | None) -> str:
    if entry is not None:
        return entry.report_hint
    if code == "CONFIG_VALIDATION_ERROR":
        return "attach redacted config, command output, and recent logs"
    return "attach command output and recent logs"
