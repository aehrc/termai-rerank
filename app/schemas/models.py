"""Model listing DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    type: str
    identifier: str
    status: str
    default: bool
    error: str | None = None


class ModelsResponse(BaseModel):
    models: list[ModelInfo]

