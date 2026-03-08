"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_runtime_state
from app.schemas.health import HealthResponse, ReadinessResponse, ReadyModelStatus
from app.services.runtime_state import RuntimeState

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(state: RuntimeState = Depends(get_runtime_state)) -> HealthResponse:
    return HealthResponse(status="ok", service=state.settings.app_name)


@router.get("/ready", response_model=ReadinessResponse)
def ready(state: RuntimeState = Depends(get_runtime_state)) -> ReadinessResponse:
    is_ready, records = state.registry.readiness()
    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        ready=is_ready,
        models=[
            ReadyModelStatus(
                name=item.name,
                type=item.model_type,
                status=item.status,
                default=item.is_default,
                error=item.error,
                model_size_bytes=item.model_size_bytes,
                model_size_mb=item.model_size_mb,
            )
            for item in records
        ],
    )
