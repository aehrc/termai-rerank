"""Unit tests for rerank service logic."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.config import Settings
from app.core.exceptions import InferenceFailureError, ValidationFailureError
from app.domain.contracts import Candidate, ScoredCandidate
from app.schemas.rerank import CandidateInput, RerankRequest
from app.services.model_registry import ModelRegistry
from app.services.rerank_service import RerankService


@dataclass
class FakeReranker:
    model_name: str = "msmarco"
    model_type: str = "msmarco"
    model_identifier: str = "fake"
    is_loaded: bool = True
    should_fail: bool = False

    def load(self) -> None:
        return None

    def rerank(self, query: str, candidates: list[Candidate], top_k: int | None) -> list[ScoredCandidate]:
        if self.should_fail:
            raise RuntimeError("inference failed")
        scored = [
            ScoredCandidate(candidate=item, rerank_score=float(len(item.text)), rank=0)
            for item in candidates
        ]
        scored.sort(key=lambda x: x.rerank_score, reverse=True)
        if top_k:
            scored = scored[:top_k]
        return [
            ScoredCandidate(candidate=item.candidate, rerank_score=item.rerank_score, rank=index + 1)
            for index, item in enumerate(scored)
        ]


def _service(fake_reranker: FakeReranker) -> RerankService:
    settings = Settings(
        use_mock_inference=True,
        enabled_models=["msmarco"],
        model_definitions='{"msmarco":{"type":"msmarco","identifier":"x","required":true}}',
    )
    registry = ModelRegistry(default_model_name="msmarco")
    registry.register_loaded(fake_reranker)
    return RerankService(settings=settings, registry=registry)


def test_rerank_service_orders_and_top_k() -> None:
    service = _service(FakeReranker())
    request = RerankRequest(
        query="heart disease",
        top_k=1,
        candidates=[
            CandidateInput(id="1", text="short"),
            CandidateInput(id="2", text="a much longer text"),
        ],
    )
    model_name, scored, original_order, _ = service.rerank(request)
    assert model_name == "msmarco"
    assert len(scored) == 1
    assert scored[0].candidate.id == "2"
    assert original_order == ["1", "2"]


def test_rerank_service_rejects_too_many_candidates() -> None:
    service = _service(FakeReranker())
    service._settings.max_candidates_per_request = 1  # type: ignore[misc]
    request = RerankRequest(
        query="q",
        candidates=[CandidateInput(id="1", text="a"), CandidateInput(id="2", text="b")],
    )
    with pytest.raises(ValidationFailureError):
        service.rerank(request)


def test_rerank_service_maps_inference_errors() -> None:
    service = _service(FakeReranker(should_fail=True))
    request = RerankRequest(query="q", candidates=[CandidateInput(id="1", text="x")])
    with pytest.raises(InferenceFailureError):
        service.rerank(request)

