"""Error response DTOs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Public-safe error message")
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = Field(..., description="Correlation ID from request context")

