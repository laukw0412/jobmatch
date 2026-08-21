"""
Final profile models.

field: Type
=> required field
=> guarantees that core information must exist before a record is accepted
   into the final profile.

field: Type | None = None
=> optional field
=> allows genuinely unknown or non-essential information to remain empty
   instead of forcing a value.

field: list[Type]
=> required section
=> guarantees that the section itself exists in PersonalProfile,
   even if its value is an empty list.

Field(default_factory=list)
=> automatically uses [] when no items exist
=> allows valid empty categories without sharing the same list object.

Field(default_factory=dict)
=> automatically uses {} when no additional information exists.

PersonalProfile
=> all main sections must exist
=> records inside those sections must satisfy the stricter final models
=> provides a standardized profile for validation, storage, and job matching.
"""

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    schema_version: str = "1.0"
    profile_version: int = 1


class Location(BaseModel):
    city: str | None = None
    country: str | None = None


class WorkAuthorization(BaseModel):
    country: str | None = None
    status: str | None = None
    notes: str | None = None


class Identity(BaseModel):
    full_name: str | None = None
    preferred_name: str | None = None
    current_location: Location | None = None
    work_authorization: WorkAuthorization | None = None


class Education(BaseModel):
    institution: str
    degree: str
    field: str | None = None
    program: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    location: str | None = None
    description: str | None = None


class Experience(BaseModel):
    organization: str
    title: str
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


class Research(BaseModel):
    title: str
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


class ProjectLink(BaseModel):
    type: str
    url: str


class Project(BaseModel):
    name: str
    type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    summary: str | None = None
    description: str | None = None
    role: str | None = None
    skills: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    links: list[ProjectLink] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    category: str
    level: str | None = None
    years: float | None = None
    description: str | None = None
    evidence: list[str] = Field(default_factory=list)


class Language(BaseModel):
    language: str
    level: str | None = None
    description: str | None = None


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    result: str | None = None
    date: str | None = None
    description: str | None = None


class SalaryPreference(BaseModel):
    minimum: int | None = None
    preferred: int | None = None
    currency: str = "JPY"


class JobPreferences(BaseModel):
    target_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    relocation: bool | None = None
    employment_types: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    work_style: list[str] = Field(default_factory=list)
    salary: SalaryPreference | None = None
    notes: str | None = None


# Final standardized profile after information from multiple documents
# has been merged. Main profile sections must always exist.
class PersonalProfile(BaseModel):
    metadata: Metadata
    identity: Identity
    education: list[Education]
    experience: list[Experience]
    research: list[Research]
    projects: list[Project]
    skills: list[Skill]
    languages: list[Language]
    certifications: list[Certification]
    job_preferences: JobPreferences
    additional_information: dict = Field(default_factory=dict)