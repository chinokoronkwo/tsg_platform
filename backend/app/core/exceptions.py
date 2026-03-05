"""Custom exception classes and FastAPI exception handlers."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        code: str = "ERROR",
        message: str = "An error occurred",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class ConflictException(AppException):
    """Conflict (e.g. duplicate resource)."""

    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None):
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)


class ForbiddenException(AppException):
    """Access forbidden."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, details=details)


class ValidationException(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422, details=details)


def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""
    app.add_exception_handler(AppException, _app_exception_handler)
