"""Service layer for reranking operations."""

from __future__ import annotations

import logging
from time import perf_counter

from app.core.config import Settings
from app.core.exceptions import InferenceFailureError, ValidationFailureError
from app.domain.contracts import Candidate, ScoredCandidate
from app.observability.metrics import MetricsTimer
from app.schemas.rerank import CandidateInput, RerankRequest
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class RerankService:
    """Coordinates validation, model selection, and inference invocation."""

    def __init__(self, settings: Settings, registry: ModelRegistry) -> None:
        self._settings = settings
        self._registry = registry

    def rerank(self, payload: RerankRequest) -> tuple[str, list[ScoredCandidate], list[str], float]:
        if len(payload.query) > self._settings.max_query_length:
            raise ValidationFailureError(
                message="query length exceeds configured maximum",
                details={"max_query_length": self._settings.max_query_length},
            )

        if len(payload.candidates) > self._settings.max_candidates_per_request:
            raise ValidationFailureError(
                message="too many candidates",
                details={"max_candidates_per_request": self._settings.max_candidates_per_request},
            )

        normalized = self._normalize_candidates(payload.candidates)
        original_order = [item.id for item in normalized]
        selected_model = self._registry.get(payload.model_name)
        timer = MetricsTimer.start_timer(selected_model.model_name)

        start = perf_counter()
        try:
            reranked = selected_model.rerank(
                query=payload.query,
                candidates=normalized,
                top_k=payload.top_k,
            )
        except Exception as exc:  # noqa: BLE001
            timer.observe_failure()
            logger.exception("Model inference failed for model '%s'", selected_model.model_name)
            raise InferenceFailureError(selected_model.model_name) from exc

        timer.observe_success()
        elapsed = perf_counter() - start
        return selected_model.model_name, reranked, original_order, elapsed

    def _normalize_candidates(self, candidates: list[CandidateInput]) -> list[Candidate]:
        normalized: list[Candidate] = []
        for index, item in enumerate(candidates):
            if len(item.text) > self._settings.max_candidate_text_length:
                raise ValidationFailureError(
                    message="candidate text length exceeds configured maximum",
                    details={
                        "candidate_id": item.id,
                        "max_candidate_text_length": self._settings.max_candidate_text_length,
                    },
                )
            if item.metadata is not None and len(str(item.metadata).encode("utf-8")) > self._settings.max_metadata_bytes:
                raise ValidationFailureError(
                    message="candidate metadata exceeds configured maximum size",
                    details={
                        "candidate_id": item.id,
                        "max_metadata_bytes": self._settings.max_metadata_bytes,
                    },
                )

            normalized.append(
                Candidate(
                    id=item.id,
                    text=item.text,
                    title=item.title,
                    source=item.source,
                    original_score=item.original_score,
                    metadata=item.metadata,
                    original_index=index,
                )
            )

        return normalized

