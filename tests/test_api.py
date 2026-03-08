"""API integration tests."""

from __future__ import annotations


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_ready(client) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert "ready" in payload
    assert len(payload["models"]) >= 1


def test_models(client) -> None:
    response = client.get("/v1/models")
    assert response.status_code == 200
    payload = response.json()
    names = {item["name"] for item in payload["models"]}
    assert {"msmarco", "bge"}.issubset(names)


def test_rerank_success(client) -> None:
    response = client.post(
        "/v1/rerank",
        json={
            "query": "heart failure",
            "candidates": [
                {"id": "1", "text": "heart failure treatment guidance"},
                {"id": "2", "text": "sports news"},
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "msmarco"
    assert payload["results"][0]["id"] == "1"
    assert payload["results"][0]["rank"] == 1


def test_rerank_unknown_model(client) -> None:
    response = client.post(
        "/v1/rerank",
        json={
            "query": "heart",
            "model_name": "unknown",
            "candidates": [{"id": "1", "text": "x"}],
        },
    )
    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "unknown_model"


def test_rerank_validation_error(client) -> None:
    response = client.post("/v1/rerank", json={"query": "", "candidates": []})
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] in {"request_validation_error", "validation_error"}


def test_batch_rerank(client) -> None:
    response = client.post(
        "/v1/rerank/batch",
        json={
            "requests": [
                {"query": "kidney", "candidates": [{"id": "1", "text": "kidney disease"}]},
                {"query": "lung", "candidates": [{"id": "2", "text": "lung cancer screening"}]},
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["responses"]) == 2

