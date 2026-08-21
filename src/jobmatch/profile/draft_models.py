# Final profile models require complete core fields, but a single document
# may provide only partial information. Draft models allow missing fields 
# so extracted data can be kept without guessing.

"""
Draft models for single-document extraction.

field: Type | None = None
=> allows a field missing from the document to remain None
=> avoids forcing the LLM to invent unsupported information.

Field(default_factory=list)
=> automatically uses [] when the document contains no items in that category
=> allows categories such as experience, research, or skills to be empty.

Draft nested models
=> fields required in final models can temporarily be None
=> allows partially extracted records to be preserved before consolidation.

DraftProfile
=> combines all partially extracted information from one document.

SourcedDraft
=> source_file + file_type + DraftProfile
=> preserves the document source for later deduplication and conflict resolution.

DocumentContent
=> DraftProfile
=> SourcedDraft
=> merge / deduplicate / resolve conflicts
=> PersonalProfile
"""

from pydantic import BaseModel, Field


class DraftLocation(BaseModel):
    city: str | None = None
    country: str | None = None


class DraftWorkAuthorization(BaseModel):
    country: str | None = None
    status: str | None = None
    notes: str | None = None


class DraftIdentity(BaseModel):
    full_name: str | None = None
    preferred_name: str | None = None
    current_location: DraftLocation | None = None
    work_authorization: DraftWorkAuthorization | None = None


class DraftEducation(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    program: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    location: str | None = None
    description: str | None = None


class DraftExperience(BaseModel):
    organization: str | None = None
    title: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    location: str | None = None
    summary: str | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class DraftResearch(BaseModel):
    title: str | None = None
    organization: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    summary: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class DraftProjectLink(BaseModel):
    type: str | None = None
    url: str | None = None


class DraftProject(BaseModel):
    name: str | None = None
    type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    summary: str | None = None
    description: str | None = None
    role: str | None = None
    skills: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    links: list[DraftProjectLink] = Field(default_factory=list)


class DraftSkill(BaseModel):
    name: str | None = None
    category: str | None = None
    level: str | None = None
    years: float | None = None
    description: str | None = None
    evidence: list[str] = Field(default_factory=list)


class DraftLanguage(BaseModel):
    language: str | None = None
    level: str | None = None
    description: str | None = None

class DraftCertification(BaseModel):
    name: str | None = None
    issuer: str | None = None
    result: str | None = None
    date: str | None = None
    description: str | None = None


class DraftSalaryPreference(BaseModel):
    minimum: int | None = None
    preferred: int | None = None
    currency: str | None = None


class DraftJobPreferences(BaseModel):
    target_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    relocation: bool | None = None
    employment_types: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    work_style: list[str] = Field(default_factory=list)
    salary: DraftSalaryPreference | None = None
    notes: str | None = None


# Case: A single document may contain only part of the candidate 
# information.

# DraftProfile allows missing fields instead of forcing incomplete data
# to fit the stricter final PersonalProfile schema.
class DraftProfile(BaseModel):
    identity: DraftIdentity | None = None
    education: list[DraftEducation] = Field(default_factory=list)
    experience: list[DraftExperience] = Field(default_factory=list)
    research: list[DraftResearch] = Field(default_factory=list)
    projects: list[DraftProject] = Field(default_factory=list)
    skills: list[DraftSkill] = Field(default_factory=list)
    languages: list[DraftLanguage] = Field(default_factory=list)
    certifications: list[DraftCertification] = Field(default_factory=list)
    job_preferences: DraftJobPreferences | None = None


# Case: The same information may appear in multiple documents 
# or conflict between sources.

# SourcedDraft keeps the source file attached so the
# system can later deduplicate or resolve conflicts correctly.
class SourcedDraft(BaseModel):
    source_file: str
    file_type: str
    profile: DraftProfile