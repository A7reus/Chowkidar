from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ExtractedObligation(BaseModel):
    signal_id: str
    source_id: str
    title: str = Field(min_length=3, max_length=500)
    description: str = ""
    jurisdiction: str = "GLOBAL"
    obligation_type: str = "due_diligence"
    applies_to: str = "company"
    effective_date: date | None = None
    confidence: float = Field(default=0.7, ge=0, le=1)
    citation_url: str = ""
    citation_quote: str = ""
    section_path: str = ""
    signal_title: str = ""

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class MappedRisk(BaseModel):
    signal_id: str
    obligation_title: str
    supplier_id: str | None = None
    title: str
    description: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    likelihood: Literal["rare", "unlikely", "possible", "likely"]
    exposure: Literal["limited", "moderate", "significant", "severe"]
    rationale: str
    confidence: float = 0.75
    evidence_quote: str
    citation_url: str
    citation_label: str


class DraftAction(BaseModel):
    title: str
    description: str
    owner_role: str = "analyst"
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    automated: bool = False


class VerificationResult(BaseModel):
    status: Literal["verified", "needs_review", "insufficient_evidence"]
    notes: list[str] = Field(default_factory=list)
    confidence: float = 0.8
