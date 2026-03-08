"""Application entrypoint for the termai-rerank service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import build_api_router
from app.core.config import Settings
from app.core.handlers import install_exception_handlers
from app.lifecycle.startup import initialize_registry
from app.middleware.metrics import metrics_middleware
from app.middleware.request_id import request_id_middleware
from app.observability.logging import configure_logging
from app.services.rerank_service import RerankService
from app.services.runtime_state import RuntimeState

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.load()
    configure_logging(settings.log_level)
    registry = initialize_registry(settings)
    rerank_service = RerankService(settings=settings, registry=registry)
    app.state.runtime_state = RuntimeState(
        settings=settings,
        registry=registry,
        rerank_service=rerank_service,
    )

    ready, records = registry.readiness()
    logger.info(
        "Startup complete",
        extra={
            "ready": ready,
            "models": [
                {"name": item.name, "type": item.model_type, "status": item.status} for item in records
            ],
        },
    )
    yield
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    settings = Settings.load()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

    app.middleware("http")(request_id_middleware)
    if settings.metrics_enabled:
        app.middleware("http")(metrics_middleware)

    app.include_router(build_api_router(expose_metrics=settings.expose_metrics_endpoint))
    install_exception_handlers(app)
    return app


app = create_app()
