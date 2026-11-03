from typing import Literal

from pydantic import BaseModel, Field


class RequirementMatch(BaseModel):
    requirement_id: int
    status: Literal["matched", "partial", "missing", "unknown"]
    reason: str
    supporting_evidence_indices: list[int] = Field(default_factory=list)


class MatchingResult(BaseModel):
    matches: list[RequirementMatch]
    overall_summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    application_recommendation: str