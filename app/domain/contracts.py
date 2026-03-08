"""Domain contracts and value objects for reranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class Candidate:
    """Normalized candidate passed to reranker backends."""

    id: str
    text: str
    title: str | None
    source: str | None
    original_score: float | None
    metadata: dict[str, Any] | None
    original_index: int


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    """Candidate with model score and rank information."""

    candidate: Candidate
    rerank_score: float
    rank: int


class Reranker(Protocol):
    """Contract implemented by each reranker adapter."""

    model_name: str
    model_type: str
    model_identifier: str
    is_loaded: bool
    model_size_bytes: int | None

    def load(self) -> None:
        """Load model resources into memory."""

    def rerank(self, query: str, candidates: list[Candidate], top_k: int | None) -> list[ScoredCandidate]:
        """Score and rank candidates against the query."""
