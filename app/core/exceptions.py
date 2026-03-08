"""Application-specific exceptions mapped to structured API errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AppError(Exception):
    """Base application error carrying HTTP and public error payload details."""

    code: str
    message: str
    status_code: int
    details: dict[str, Any] = field(default_factory=dict)


class UnknownModelError(AppError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            code="unknown_model",
            message=f"Model '{model_name}' is not registered",
            status_code=404,
            details={"model_name": model_name},
        )


class ModelNotLoadedError(AppError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            code="model_not_loaded",
            message=f"Model '{model_name}' is not loaded",
            status_code=503,
            details={"model_name": model_name},
        )


class ValidationFailureError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="validation_error",
            message=message,
            status_code=422,
            details=details or {},
        )


class InferenceFailureError(AppError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            code="inference_failed",
            message="Rerank inference failed",
            status_code=500,
            details={"model_name": model_name},
        )

