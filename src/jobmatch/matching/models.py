from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class EvidenceCitation(BaseModel):
    evidence_id: str
    quote: str = Field(min_length=1)


class EvidenceReference(BaseModel):
    evidence_id: str
    start_line: int
    end_line: int


class CitationIssue(BaseModel):
    evidence_id: str
    code: str
    message: str
    start_line: int | None = None
    end_line: int | None = None


class SupportingEvidence(EvidenceCitation):
    source_type: Literal["core", "rag"]
    source_file: str
    source_path: str
    text: str
    chunk_index: int | None = None
    start_line: int | None = None
    end_line: int | None = None


class RequirementMatch(BaseModel):
    requirement_id: int
    status: Literal["matched", "partial", "missing", "unknown"]
    reason: str
    requirement: str = ""
    model_status: Literal["matched", "partial", "missing", "unknown"] | None = None
    model_reason: str | None = None
    review_required: bool = False
    citation_issues: list[CitationIssue] = Field(default_factory=list)
    supporting_evidence_indices: list[int] = Field(default_factory=list)
    supporting_evidence: list[SupportingEvidence] = Field(default_factory=list)


class MatchingResult(BaseModel):
    matches: list[RequirementMatch]
    overall_summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    application_recommendation: str
    validation_warnings: list[str] = Field(default_factory=list)
    summary_review_required: bool = False
