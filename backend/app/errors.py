from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


async def api_exception_handler(request: Request, exception: ApiError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return error_response(
        status_code=exception.status_code,
        code=exception.code,
        message=exception.message,
        details=exception.details,
        request_id=request_id,
        headers=exception.headers,
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any],
    request_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="A requisição contém dados inválidos.",
        details={"errors": exception.errors()},
        request_id=request_id,
    )
