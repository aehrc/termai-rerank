"""Prometheus metrics registry and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoopMetric:
        def labels(self, **_: object) -> "_NoopMetric":
            return self

        def inc(self) -> None:
            return None

        def observe(self, _: float) -> None:
            return None

    def Counter(*_: object, **__: object) -> _NoopMetric:
        return _NoopMetric()

    def Histogram(*_: object, **__: object) -> _NoopMetric:
        return _NoopMetric()

    def generate_latest() -> bytes:
        return b""


REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
RERANK_COUNTER = Counter(
    "rerank_requests_total",
    "Total rerank requests",
    ["model_name", "outcome"],
)
RERANK_LATENCY = Histogram(
    "rerank_duration_seconds",
    "Rerank execution latency in seconds",
    ["model_name"],
)


@dataclass(slots=True)
class MetricsTimer:
    model_name: str
    start: float

    @classmethod
    def start_timer(cls, model_name: str) -> "MetricsTimer":
        return cls(model_name=model_name, start=perf_counter())

    def observe_success(self) -> None:
        elapsed = perf_counter() - self.start
        RERANK_LATENCY.labels(model_name=self.model_name).observe(elapsed)
        RERANK_COUNTER.labels(model_name=self.model_name, outcome="success").inc()

    def observe_failure(self) -> None:
        elapsed = perf_counter() - self.start
        RERANK_LATENCY.labels(model_name=self.model_name).observe(elapsed)
        RERANK_COUNTER.labels(model_name=self.model_name, outcome="error").inc()


def metrics_payload() -> tuple[bytes, str]:
    """Serialize current Prometheus metrics."""
    return generate_latest(), CONTENT_TYPE_LATEST
