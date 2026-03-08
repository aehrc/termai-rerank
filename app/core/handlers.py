"""Global exception handlers."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)


def _trace_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def install_exception_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        payload = ErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            trace_id=_trace_id(request),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        payload = ErrorResponse(
            code="request_validation_error",
            message="Request payload validation failed",
            details={"errors": exc.errors()},
            trace_id=_trace_id(request),
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception during request processing")
        payload = ErrorResponse(
            code="internal_error",
            message="An internal error occurred",
            details={},
            trace_id=_trace_id(request),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())

