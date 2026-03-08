"""Runtime container for dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.services.model_registry import ModelRegistry
from app.services.rerank_service import RerankService


@dataclass(slots=True)
class RuntimeState:
    settings: Settings
    registry: ModelRegistry
    rerank_service: RerankService

