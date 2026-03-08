"""Model inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_runtime_state
from app.schemas.models import ModelInfo, ModelsResponse
from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def list_models(state: RuntimeState = Depends(get_runtime_state)) -> ModelsResponse:
    records = state.registry.list_records()
    return ModelsResponse(
        models=[
            ModelInfo(
                name=item.name,
                type=item.model_type,
                identifier=item.identifier,
                status=item.status,
                default=item.is_default,
                error=item.error,
            )
            for item in records
        ]
    )

