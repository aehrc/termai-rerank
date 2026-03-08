"""HTTP metrics middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response

from app.observability.metrics import REQUEST_COUNTER, REQUEST_LATENCY


async def metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    method = request.method
    path = request.url.path
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start

    REQUEST_COUNTER.labels(method=method, path=path, status_code=response.status_code).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
    return response

