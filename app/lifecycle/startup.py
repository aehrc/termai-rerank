"""Startup lifecycle for model initialization and registry population."""

from __future__ import annotations

import logging
from time import perf_counter

from app.core.config import ModelConfig, Settings
from app.models.bge import BGERerankerAdapter
from app.models.msmarco import MSMARCORerankerAdapter
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


def _build_adapter(config: ModelConfig, settings: Settings) -> MSMARCORerankerAdapter | BGERerankerAdapter:
    if config.model_type == "msmarco":
        return MSMARCORerankerAdapter(
            model_name=config.name,
            model_identifier=config.identifier,
            device=settings.device,
            use_mock_inference=settings.use_mock_inference,
        )

    return BGERerankerAdapter(
        model_name=config.name,
        model_identifier=config.identifier,
        device=settings.device,
        use_mock_inference=settings.use_mock_inference,
    )


def initialize_registry(settings: Settings) -> ModelRegistry:
    """Initialize models and return populated registry."""
    registry = ModelRegistry(default_model_name=settings.default_model_name)
    model_configs = settings.build_model_configs()
    total_models = len(model_configs)

    logger.info("Initializing %s configured model(s)", total_models)

    for index, config in enumerate(model_configs, start=1):
        percent = round((index / total_models) * 100, 1) if total_models else 100.0
        logger.info(
            "Loading model %s/%s (%.1f%%): name=%s type=%s",
            index,
            total_models,
            percent,
            config.name,
            config.model_type,
        )
        adapter = _build_adapter(config=config, settings=settings)
        started_at = perf_counter()
        try:
            adapter.load()
            registry.register_loaded(adapter)
            elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.info(
                "Loaded model %s/%s: name=%s type=%s elapsed_ms=%s",
                index,
                total_models,
                config.name,
                config.model_type,
                elapsed_ms,
            )
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
            registry.register_failed(
                name=config.name,
                model_type=config.model_type,
                identifier=config.identifier,
                error=error,
            )
            logger.exception(
                "Failed model %s/%s: name=%s type=%s elapsed_ms=%s",
                index,
                total_models,
                config.name,
                config.model_type,
                elapsed_ms,
            )
            if settings.startup_mode == "strict" and config.required:
                raise RuntimeError(f"Required model '{config.name}' failed to load: {error}") from exc

    return registry
