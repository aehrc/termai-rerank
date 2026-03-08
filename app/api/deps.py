"""Dependency helpers for API routers."""

from __future__ import annotations

from fastapi import Request

from app.services.runtime_state import RuntimeState


def get_runtime_state(request: Request) -> RuntimeState:
    state = getattr(request.app.state, "runtime_state", None)
    if state is None:
        raise RuntimeError("Runtime state is not initialized")
    return state

