"""MS MARCO reranker adapter."""

from __future__ import annotations

from app.domain.contracts import Candidate
from app.models.base import BaseRerankerAdapter, FallbackLexicalScorer, estimate_torch_model_size_bytes


class MSMARCORerankerAdapter(BaseRerankerAdapter):
    """Cross-encoder style MS MARCO adapter."""

    def __init__(
        self,
        model_name: str,
        model_identifier: str,
        device: str,
        use_mock_inference: bool,
    ) -> None:
        super().__init__(model_name=model_name, model_type="msmarco", model_identifier=model_identifier)
        self._device = device
        self._use_mock_inference = use_mock_inference
        self._model: object | None = None
        self._fallback = FallbackLexicalScorer()

    def load(self) -> None:
        if self._use_mock_inference:
            self._model = "mock-msmarco"
            self.is_loaded = True
            self.model_size_bytes = None
            return

        try:
            from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for real MS MARCO inference."
            ) from exc

        self._model = CrossEncoder(self.model_identifier, device=self._device)
        self.is_loaded = True
        self.model_size_bytes = estimate_torch_model_size_bytes(self._model)

    def _score_candidates(self, query: str, candidates: list[Candidate]) -> list[float]:
        if not self.is_loaded:
            raise RuntimeError("MS MARCO model is not loaded")

        if self._use_mock_inference:
            return [self._fallback.score(query=query, text=item.text) for item in candidates]

        pairs = [[query, item.text] for item in candidates]
        assert self._model is not None
        scores = self._model.predict(pairs)  # type: ignore[attr-defined]
        return [float(value) for value in scores]
