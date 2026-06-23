from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails


class ValidationErrorItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    type: str
    loc: tuple[int | str, ...]
    msg: str


class ValidationErrorResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: tuple[ValidationErrorItem, ...]


def redacted_request_validation_error(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    match exc:
        case RequestValidationError() as validation_error:
            errors: tuple[ErrorDetails, ...] = tuple(validation_error.errors())
        case unexpected:
            raise unexpected
    payload = ValidationErrorResponse(
        detail=tuple(_validation_error_item(error) for error in errors),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=payload.model_dump(mode="json"),
    )


def _validation_error_item(error: ErrorDetails) -> ValidationErrorItem:
    return ValidationErrorItem(
        type=error["type"],
        loc=error["loc"],
        msg=error["msg"],
    )
