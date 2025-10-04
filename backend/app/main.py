from __future__ import annotations

from typing import Dict, List, Literal, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from .ai_detection import analyze_document
from .scoring import ScoreBreakdown, compute_scores
from .storage import get_store

app = FastAPI(title="Essay Evaluation Service", version="0.1.0")


class AnalyzeRequest(BaseModel):
    document: str = Field(..., min_length=10, description="Personal statement or essay content")
    application_level: Optional[Literal["UG", "MS", "PHD"]] = Field(
        default=None, description="Study level e.g. UG, MS, PHD"
    )
    target_major: Optional[str] = None
    school_preferences: Optional[List[str]] = None

    @field_validator("document")
    @classmethod
    def validate_document(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Document cannot be empty")
        return value


class AnalyzeResponse(BaseModel):
    analysis_id: UUID
    total_score: float
    dimension_scores: Dict[str, float]
    weights: Dict[str, float]
    ai_detection: Dict[str, object]
    insights: List[str]
    visuals: Dict[str, object]


class DetectRequest(BaseModel):
    document: str = Field(..., min_length=10)

    @field_validator("document")
    @classmethod
    def validate_document(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Document cannot be empty")
        return value


class DetectResponse(BaseModel):
    ai_detection: Dict[str, object]


class ReportResponse(BaseModel):
    analysis_id: UUID
    payload: Dict[str, object]


INSIGHT_TEMPLATES = {
    "content": "强化与项目资源的对应证据，展示动机与成果闭环。",
    "structure": "检查段落衔接与过渡句，确保叙事聚焦。",
    "language": "优化句式与可读性，避免重复表达。",
    "integrity": "补充写作过程证明材料，准备人工复核。",
}


def _generate_insights(breakdown: ScoreBreakdown) -> List[str]:
    ordered = sorted(breakdown.as_percentage().items(), key=lambda item: item[1])
    lowest = [dimension for dimension, _ in ordered[:2]]
    return [INSIGHT_TEMPLATES[dimension] for dimension in lowest]


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    breakdown, weights, visuals = compute_scores(request.document, request.application_level)
    detection_result = analyze_document(request.document)

    integrity_adjustment = max(0.0, 1 - detection_result.document.completely_generated_prob)
    adjusted_breakdown = ScoreBreakdown(
        content=breakdown.content,
        structure=breakdown.structure,
        language=breakdown.language,
        integrity=min(breakdown.integrity, integrity_adjustment),
    )

    total = round(adjusted_breakdown.weighted_total(weights) * 100, 2)
    dimension_scores = adjusted_breakdown.as_percentage()

    insights = _generate_insights(adjusted_breakdown)

    payload: Dict[str, object] = {
        "total_score": total,
        "dimension_scores": dimension_scores,
        "weights": weights,
        "ai_detection": detection_result.to_payload(),
        "insights": insights,
        "visuals": visuals,
        "meta": {
            "application_level": request.application_level,
            "target_major": request.target_major,
            "school_preferences": request.school_preferences or [],
        },
    }

    store = get_store()
    analysis_id = store.save(payload)

    return AnalyzeResponse(
        analysis_id=analysis_id,
        total_score=total,
        dimension_scores=dimension_scores,
        weights=weights,
        ai_detection=detection_result.to_payload(),
        insights=insights,
        visuals=visuals,
    )


@app.post("/api/ai-detect", response_model=DetectResponse)
def ai_detect(request: DetectRequest) -> DetectResponse:
    detection_result = analyze_document(request.document)
    return DetectResponse(ai_detection=detection_result.to_payload())


@app.get("/api/report/{analysis_id}", response_model=ReportResponse)
def fetch_report(analysis_id: UUID) -> ReportResponse:
    store = get_store()
    payload = store.get(analysis_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(analysis_id=analysis_id, payload=payload)
