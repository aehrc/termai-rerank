"""BGE reranker adapter."""

from __future__ import annotations

from app.domain.contracts import Candidate
from app.models.base import BaseRerankerAdapter, FallbackLexicalScorer, estimate_torch_model_size_bytes


class BGERerankerAdapter(BaseRerankerAdapter):
    """BGE reranker adapter using FlagEmbedding when available."""

    def __init__(
        self,
        model_name: str,
        model_identifier: str,
        device: str,
        use_mock_inference: bool,
    ) -> None:
        super().__init__(model_name=model_name, model_type="bge", model_identifier=model_identifier)
        self._device = device
        self._use_mock_inference = use_mock_inference
        self._model: object | None = None
        self._fallback = FallbackLexicalScorer()

    def load(self) -> None:
        if self._use_mock_inference:
            self._model = "mock-bge"
            self.is_loaded = True
            self.model_size_bytes = None
            return

        try:
            from FlagEmbedding import FlagReranker  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("FlagEmbedding is required for real BGE inference.") from exc

        try:
            self._model = FlagReranker(self.model_identifier, use_fp16=False, devices=self._device)
        except TypeError:
            self._model = FlagReranker(self.model_identifier, use_fp16=False, device=self._device)
        self.is_loaded = True
        self.model_size_bytes = estimate_torch_model_size_bytes(self._model)

    def _score_candidates(self, query: str, candidates: list[Candidate]) -> list[float]:
        if not self.is_loaded:
            raise RuntimeError("BGE model is not loaded")

        if self._use_mock_inference:
            return [self._fallback.score(query=query, text=item.text) for item in candidates]

        pairs = [[query, item.text] for item in candidates]
        assert self._model is not None
        scores = self._model.compute_score(pairs)  # type: ignore[attr-defined]
        if isinstance(scores, float):
            return [scores]
        return [float(value) for value in scores]
