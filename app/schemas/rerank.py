"""Rerank request and response DTOs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateInput(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    text: str = Field(min_length=1)
    title: str | None = Field(default=None, max_length=512)
    source: str | None = Field(default=None, max_length=512)
    original_score: float | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("id", "text")
    @classmethod
    def _validate_non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    candidates: list[CandidateInput] = Field(min_length=1)
    model_name: str | None = Field(default=None, min_length=1, max_length=128)
    top_k: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "query": "evidence-based treatment for stage 2 hypertension in adults",
                "model_name": "msmarco",
                "top_k": 3,
                "candidates": [
                    {
                        "id": "doc-001",
                        "text": "Lifestyle changes plus thiazide-like diuretics are recommended first-line options for many adults with stage 2 hypertension.",
                        "title": "ACC/AHA Hypertension Guideline Summary",
                        "source": "guideline",
                        "original_score": 0.72,
                        "metadata": {"specialty": "cardiology", "year": 2024},
                    },
                    {
                        "id": "doc-002",
                        "text": "Type 2 diabetes management should prioritize glycemic control, weight loss, and cardiovascular risk reduction.",
                        "title": "ADA Standards of Care",
                        "source": "guideline",
                        "original_score": 0.69,
                        "metadata": {"specialty": "endocrinology", "year": 2025},
                    },
                    {
                        "id": "doc-003",
                        "text": "Home blood pressure monitoring improves treatment adherence and blood pressure control outcomes.",
                        "title": "Hypertension Home Monitoring Review",
                        "source": "journal",
                        "original_score": 0.66,
                        "metadata": {"study_type": "systematic_review"},
                    },
                ],
            }
        },
    )

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class BatchRerankRequest(BaseModel):
    requests: list[RerankRequest] = Field(min_length=1, max_length=32)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "requests": [
                    {
                        "query": "initial therapy for community-acquired pneumonia",
                        "model_name": "bge",
                        "top_k": 2,
                        "candidates": [
                            {"id": "cap-001", "text": "Empiric antibiotics should consider local resistance patterns."},
                            {"id": "cap-002", "text": "Outpatient CAP can often be treated with amoxicillin in low-risk adults."},
                        ],
                    },
                    {
                        "query": "stroke secondary prevention antiplatelet choice",
                        "model_name": "msmarco",
                        "top_k": 2,
                        "candidates": [
                            {"id": "str-001", "text": "Aspirin remains a common option for non-cardioembolic ischemic stroke prevention."},
                            {"id": "str-002", "text": "Dual antiplatelet therapy may be considered short-term after minor stroke."},
                        ],
                    },
                ]
            }
        }
    )


class RerankedCandidate(BaseModel):
    id: str
    text: str
    title: str | None = None
    source: str | None = None
    original_score: float | None = None
    metadata: dict[str, Any] | None = None
    rerank_score: float
    rank: int
    original_index: int


class RerankResponse(BaseModel):
    model_name: str
    total_candidates: int
    returned_candidates: int
    elapsed_ms: float
    original_order: list[str]
    results: list[RerankedCandidate]
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_name": "msmarco",
                "total_candidates": 3,
                "returned_candidates": 3,
                "elapsed_ms": 18.42,
                "original_order": ["doc-001", "doc-002", "doc-003"],
                "results": [
                    {
                        "id": "doc-001",
                        "text": "Lifestyle changes plus thiazide-like diuretics are recommended first-line options for many adults with stage 2 hypertension.",
                        "title": "ACC/AHA Hypertension Guideline Summary",
                        "source": "guideline",
                        "original_score": 0.72,
                        "metadata": {"specialty": "cardiology", "year": 2024},
                        "rerank_score": 0.948,
                        "rank": 1,
                        "original_index": 0,
                    },
                    {
                        "id": "doc-003",
                        "text": "Home blood pressure monitoring improves treatment adherence and blood pressure control outcomes.",
                        "title": "Hypertension Home Monitoring Review",
                        "source": "journal",
                        "original_score": 0.66,
                        "metadata": {"study_type": "systematic_review"},
                        "rerank_score": 0.903,
                        "rank": 2,
                        "original_index": 2,
                    },
                    {
                        "id": "doc-002",
                        "text": "Type 2 diabetes management should prioritize glycemic control, weight loss, and cardiovascular risk reduction.",
                        "title": "ADA Standards of Care",
                        "source": "guideline",
                        "original_score": 0.69,
                        "metadata": {"specialty": "endocrinology", "year": 2025},
                        "rerank_score": 0.611,
                        "rank": 3,
                        "original_index": 1,
                    },
                ],
            }
        }
    )


class BatchRerankResponse(BaseModel):
    responses: list[RerankResponse]
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "responses": [
                    {
                        "model_name": "bge",
                        "total_candidates": 2,
                        "returned_candidates": 2,
                        "elapsed_ms": 12.1,
                        "original_order": ["cap-001", "cap-002"],
                        "results": [
                            {
                                "id": "cap-002",
                                "text": "Outpatient CAP can often be treated with amoxicillin in low-risk adults.",
                                "title": None,
                                "source": None,
                                "original_score": None,
                                "metadata": None,
                                "rerank_score": 0.884,
                                "rank": 1,
                                "original_index": 1,
                            },
                            {
                                "id": "cap-001",
                                "text": "Empiric antibiotics should consider local resistance patterns.",
                                "title": None,
                                "source": None,
                                "original_score": None,
                                "metadata": None,
                                "rerank_score": 0.771,
                                "rank": 2,
                                "original_index": 0,
                            },
                        ],
                    }
                ]
            }
        }
    )
