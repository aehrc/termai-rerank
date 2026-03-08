"""Model registry for loaded and failed reranker adapters."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import ModelNotLoadedError, UnknownModelError
from app.domain.contracts import Reranker


@dataclass(frozen=True, slots=True)
class ModelRecord:
    name: str
    model_type: str
    identifier: str
    status: str
    is_default: bool
    error: str | None = None
    model_size_bytes: int | None = None
    model_size_mb: float | None = None


class ModelRegistry:
    """Registry tracking model adapters and startup load outcomes."""

    def __init__(self, default_model_name: str) -> None:
        self._default_model_name = default_model_name
        self._models: dict[str, Reranker] = {}
        self._statuses: dict[str, ModelRecord] = {}

    @property
    def default_model_name(self) -> str:
        return self._default_model_name

    def register_loaded(self, reranker: Reranker) -> None:
        size_bytes = getattr(reranker, "model_size_bytes", None)
        self._models[reranker.model_name] = reranker
        self._statuses[reranker.model_name] = ModelRecord(
            name=reranker.model_name,
            model_type=reranker.model_type,
            identifier=reranker.model_identifier,
            status="loaded",
            is_default=reranker.model_name == self._default_model_name,
            model_size_bytes=size_bytes,
            model_size_mb=round(size_bytes / (1024 * 1024), 3) if size_bytes is not None else None,
        )

    def register_failed(self, name: str, model_type: str, identifier: str, error: str) -> None:
        self._statuses[name] = ModelRecord(
            name=name,
            model_type=model_type,
            identifier=identifier,
            status="failed",
            is_default=name == self._default_model_name,
            error=error,
            model_size_bytes=None,
            model_size_mb=None,
        )

    def get(self, model_name: str | None = None) -> Reranker:
        resolved_name = model_name or self._default_model_name
        if resolved_name not in self._statuses:
            raise UnknownModelError(resolved_name)
        model = self._models.get(resolved_name)
        if model is None or not model.is_loaded:
            raise ModelNotLoadedError(resolved_name)
        return model

    def list_records(self) -> list[ModelRecord]:
        return sorted(self._statuses.values(), key=lambda item: item.name)

    def readiness(self) -> tuple[bool, list[ModelRecord]]:
        records = self.list_records()
        all_loaded = all(record.status == "loaded" for record in records)
        return all_loaded and len(records) > 0, records
