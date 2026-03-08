"""Health and readiness DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: str


class ReadyModelStatus(BaseModel):
    name: str
    type: str
    status: str
    default: bool
    error: str | None = None
    model_size_bytes: int | None = None
    model_size_mb: float | None = None


class ReadinessResponse(BaseModel):
    status: str
    ready: bool
    models: list[ReadyModelStatus]
