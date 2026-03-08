"""Reranking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_runtime_state
from app.schemas.rerank import (
    BatchRerankRequest,
    BatchRerankResponse,
    RerankRequest,
    RerankResponse,
    RerankedCandidate,
)
from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/v1", tags=["rerank"])


@router.post("/rerank", response_model=RerankResponse)
def rerank(payload: RerankRequest, state: RuntimeState = Depends(get_runtime_state)) -> RerankResponse:
    model_name, scored, original_order, elapsed = state.rerank_service.rerank(payload)
    return RerankResponse(
        model_name=model_name,
        total_candidates=len(payload.candidates),
        returned_candidates=len(scored),
        elapsed_ms=round(elapsed * 1000, 3),
        original_order=original_order,
        results=[
            RerankedCandidate(
                id=item.candidate.id,
                text=item.candidate.text,
                title=item.candidate.title,
                source=item.candidate.source,
                original_score=item.candidate.original_score,
                metadata=item.candidate.metadata,
                rerank_score=item.rerank_score,
                rank=item.rank,
                original_index=item.candidate.original_index,
            )
            for item in scored
        ],
    )


@router.post("/rerank/batch", response_model=BatchRerankResponse)
def rerank_batch(
    payload: BatchRerankRequest,
    state: RuntimeState = Depends(get_runtime_state),
) -> BatchRerankResponse:
    responses: list[RerankResponse] = []
    for item in payload.requests:
        model_name, scored, original_order, elapsed = state.rerank_service.rerank(item)
        responses.append(
            RerankResponse(
                model_name=model_name,
                total_candidates=len(item.candidates),
                returned_candidates=len(scored),
                elapsed_ms=round(elapsed * 1000, 3),
                original_order=original_order,
                results=[
                    RerankedCandidate(
                        id=entry.candidate.id,
                        text=entry.candidate.text,
                        title=entry.candidate.title,
                        source=entry.candidate.source,
                        original_score=entry.candidate.original_score,
                        metadata=entry.candidate.metadata,
                        rerank_score=entry.rerank_score,
                        rank=entry.rank,
                        original_index=entry.candidate.original_index,
                    )
                    for entry in scored
                ],
            )
        )
    return BatchRerankResponse(responses=responses)

