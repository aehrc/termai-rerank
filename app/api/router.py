"""Root API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints.health import router as health_router
from app.api.endpoints.metrics import router as metrics_router
from app.api.endpoints.models import router as models_router
from app.api.endpoints.rerank import router as rerank_router


def build_api_router(expose_metrics: bool) -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(models_router)
    router.include_router(rerank_router)
    if expose_metrics:
        router.include_router(metrics_router)
    return router

