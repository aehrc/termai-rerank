"""Unit tests for model registry behavior."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.exceptions import ModelNotLoadedError, UnknownModelError
from app.services.model_registry import ModelRegistry


@dataclass
class DummyReranker:
    model_name: str
    model_type: str = "msmarco"
    model_identifier: str = "dummy"
    is_loaded: bool = True

    def load(self) -> None:
        return None

    def rerank(self, query: str, candidates: list[object], top_k: int | None) -> list[object]:
        return []


def test_registry_returns_default_model() -> None:
    registry = ModelRegistry(default_model_name="default")
    registry.register_loaded(DummyReranker(model_name="default"))

    model = registry.get()
    assert model.model_name == "default"


def test_registry_unknown_model_raises() -> None:
    registry = ModelRegistry(default_model_name="default")
    with pytest.raises(UnknownModelError):
        registry.get("missing")


def test_registry_not_loaded_raises() -> None:
    registry = ModelRegistry(default_model_name="default")
    registry.register_failed("default", "msmarco", "dummy", "boom")
    with pytest.raises(ModelNotLoadedError):
        registry.get("default")

