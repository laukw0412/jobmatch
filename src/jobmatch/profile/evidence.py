"""
Evidence models for document-level information extraction.

The evidence layer preserves useful candidate information from source
documents before normalization, deduplication, and consolidation.

Its main goal is information preservation rather than producing a final
PersonalProfile.
"""

from typing import Literal
from pydantic import BaseModel, Field


EvidenceCategory = Literal[
    "identity",
    "education",
    "experience",
    "research",
    "project",
    "skill",
    "language",
    "certification",
    "preference",
    "other",
]


class Evidence(BaseModel):
    category: EvidenceCategory | None = None # broad category
    source_section: str | None = None # original section heading
                                      # if available
    content: str # LLM text
    source_text: str # original text

    source_verified: bool = False # whether source_text was verified
                                  # as original document text

    source_file: str | None = None
    file_type: str | None = None


class EvidenceSet(BaseModel):
    # Evidence records extracted from one source document
    records: list[Evidence] = Field(default_factory=list)


class MergedEvidence(BaseModel):
    category: EvidenceCategory | None = None
    content: str
    source_files: list[str] = Field(default_factory=list)


class MergedEvidenceSet(BaseModel):
    records: list[MergedEvidence] = Field(default_factory=list)