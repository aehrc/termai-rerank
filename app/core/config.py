"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Normalized model configuration consumed by startup lifecycle."""

    name: str
    model_type: Literal["msmarco", "bge"]
    identifier: str
    required: bool


class Settings(BaseModel):
    """Environment-driven settings for service behavior and runtime."""

    app_name: str = "termai-rerank"
    app_env: str = "dev"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8080

    startup_mode: Literal["strict", "best_effort"] = "best_effort"
    default_model_name: str = "msmarco"
    enabled_models: list[str] = Field(default_factory=lambda: ["msmarco", "bge"])

    model_definitions: str = (
        '{"msmarco":{"type":"msmarco","identifier":"cross-encoder/ms-marco-MiniLM-L-6-v2",'
        '"required":true},"bge":{"type":"bge","identifier":"BAAI/bge-reranker-base","required":true}}'
    )
    msmarco_model_identifier: str | None = None
    bge_model_identifier: str | None = None

    device: str = "cpu"
    inference_timeout_seconds: float = 15.0
    use_mock_inference: bool = True

    max_candidates_per_request: int = 100
    max_query_length: int = 2048
    max_candidate_text_length: int = 5000
    max_metadata_bytes: int = 16384

    metrics_enabled: bool = True
    expose_metrics_endpoint: bool = True

    @field_validator("enabled_models", mode="before")
    @classmethod
    def _parse_enabled_models(cls, value: object) -> list[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            return cleaned
        if isinstance(value, str):
            cleaned = [item.strip() for item in value.split(",") if item.strip()]
            return cleaned
        raise ValueError("enabled_models must be a comma-separated string or list[str]")

    @field_validator("default_model_name")
    @classmethod
    def _validate_default_model_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("default_model_name must not be empty")
        return cleaned

    @classmethod
    def load(cls) -> "Settings":
        """Build validated settings from environment and `.env` file."""
        return cls(**_load_environment_values())

    def build_model_configs(self) -> list[ModelConfig]:
        """Construct model configurations from environment settings."""
        try:
            raw_definitions = json.loads(self.model_definitions)
        except json.JSONDecodeError as exc:
            raise ValueError(f"model_definitions contains invalid JSON: {exc}") from exc

        if not isinstance(raw_definitions, dict):
            raise ValueError("model_definitions must decode to an object keyed by model name")

        definitions: dict[str, dict[str, object]] = raw_definitions
        configs: list[ModelConfig] = []

        for model_name in self.enabled_models:
            model_definition = definitions.get(model_name)
            if model_definition is None:
                raise ValueError(f"Enabled model '{model_name}' missing from model_definitions")

            model_type_raw = model_definition.get("type")
            identifier_raw = model_definition.get("identifier")
            required_raw = model_definition.get("required", True)

            if model_type_raw not in {"msmarco", "bge"}:
                raise ValueError(f"Model '{model_name}' has unsupported type '{model_type_raw}'")
            if not isinstance(identifier_raw, str) or not identifier_raw.strip():
                raise ValueError(f"Model '{model_name}' must include a non-empty identifier")

            identifier = identifier_raw.strip()
            if model_type_raw == "msmarco" and self.msmarco_model_identifier:
                identifier = self.msmarco_model_identifier.strip()
            if model_type_raw == "bge" and self.bge_model_identifier:
                identifier = self.bge_model_identifier.strip()

            configs.append(
                ModelConfig(
                    name=model_name,
                    model_type=model_type_raw,
                    identifier=identifier,
                    required=bool(required_raw),
                )
            )

        return configs


def _load_environment_values() -> dict[str, object]:
    raw: dict[str, object] = {}
    for field_name in Settings.model_fields:
        env_name = field_name.upper()
        if env_name in os.environ:
            raw[field_name] = os.environ[env_name]
    return raw
