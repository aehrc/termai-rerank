"""Test fixtures for FastAPI app client."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def _set_env() -> Iterator[None]:
    original = dict(os.environ)
    os.environ["USE_MOCK_INFERENCE"] = "true"
    os.environ["STARTUP_MODE"] = "best_effort"
    os.environ["ENABLED_MODELS"] = "msmarco,bge"
    os.environ["DEFAULT_MODEL_NAME"] = "msmarco"
    yield
    os.environ.clear()
    os.environ.update(original)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

