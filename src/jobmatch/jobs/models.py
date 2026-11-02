from typing import Literal
from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    description: str
    category: Literal[
        "technical_skill",
        "experience",
        "education",
        "language",
        "certification",
        "other",
    ]
    priority: Literal["required", "preferred"]


class JobDescription(BaseModel):
    job_title: str | None
    company_name: str | None
    location: str | None

    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[JobRequirement] = Field(default_factory=list)