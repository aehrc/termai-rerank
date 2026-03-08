"""Base adapter and shared deterministic fallback scoring helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from math import sqrt

from app.domain.contracts import Candidate, ScoredCandidate


class BaseRerankerAdapter(ABC):
    """Abstract class for concrete reranker adapters."""

    def __init__(self, model_name: str, model_type: str, model_identifier: str) -> None:
        self.model_name = model_name
        self.model_type = model_type
        self.model_identifier = model_identifier
        self.is_loaded = False
        self.model_size_bytes: int | None = None

    @abstractmethod
    def load(self) -> None:
        """Load model resources."""

    @abstractmethod
    def _score_candidates(self, query: str, candidates: list[Candidate]) -> list[float]:
        """Return raw model scores aligned with candidates."""

    def rerank(self, query: str, candidates: list[Candidate], top_k: int | None) -> list[ScoredCandidate]:
        scores = self._score_candidates(query=query, candidates=candidates)
        paired = list(zip(candidates, scores, strict=True))
        paired.sort(key=lambda item: item[1], reverse=True)

        if top_k is not None:
            paired = paired[:top_k]

        return [
            ScoredCandidate(candidate=candidate, rerank_score=float(score), rank=index + 1)
            for index, (candidate, score) in enumerate(paired)
        ]


class FallbackLexicalScorer:
    """Simple lexical scorer used when heavyweight inference is disabled/unavailable."""

    def score(self, query: str, text: str) -> float:
        q_tokens = query.lower().split()
        d_tokens = text.lower().split()
        if not q_tokens or not d_tokens:
            return 0.0

        q_counts = Counter(q_tokens)
        d_counts = Counter(d_tokens)
        dot = sum(q_counts[token] * d_counts[token] for token in q_counts)
        q_norm = sqrt(sum(value * value for value in q_counts.values()))
        d_norm = sqrt(sum(value * value for value in d_counts.values()))
        if q_norm == 0 or d_norm == 0:
            return 0.0
        return dot / (q_norm * d_norm)


def estimate_torch_model_size_bytes(container: object) -> int | None:
    """Best-effort parameter size estimation for torch-backed models."""
    model = getattr(container, "model", container)
    parameters = getattr(model, "parameters", None)
    if parameters is None or not callable(parameters):
        return None

    total = 0
    try:
        for param in parameters():
            numel = getattr(param, "numel", None)
            element_size = getattr(param, "element_size", None)
            if not callable(numel) or not callable(element_size):
                return None
            total += int(numel()) * int(element_size())
    except Exception:  # noqa: BLE001
        return None

    return total if total > 0 else None
