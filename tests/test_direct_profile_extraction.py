from pathlib import Path
import json
import os

from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from openai import OpenAI
from pydantic import BaseModel, Field


# ============================================================
# Configuration
# ============================================================

DOCUMENT_DIR = Path(r"E:\Projects\jobmatch\data\documents")

OUTPUT_DIR = Path(r"E:\Projects\jobmatch\data\test_outputs")

MODEL = "gpt-5.4-nano"

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
}


# ============================================================
# Profile Models
# ============================================================

class Identity(BaseModel):
    full_name: str | None = None
    preferred_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    nationality: str | None = None
    languages: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    location: str | None = None
    details: list[str] = Field(default_factory=list)


class WorkExperience(BaseModel):
    organization: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ResearchExperience(BaseModel):
    title: str | None = None
    institution: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    methods: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    url: str | None = None


class Publication(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: str | None = None
    status: str | None = None
    url: str | None = None


class Certification(BaseModel):
    name: str | None = None
    issuer: str | None = None
    date: str | None = None
    level: str | None = None


class SkillProfile(BaseModel):
    programming_languages: list[str] = Field(default_factory=list)
    machine_learning: list[str] = Field(default_factory=list)
    computer_vision: list[str] = Field(default_factory=list)
    generative_ai: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


class PersonalProfile(BaseModel):
    identity: Identity = Field(default_factory=Identity)

    summary: str | None = None

    education: list[Education] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    research_experience: list[ResearchExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)

    skills: SkillProfile = Field(default_factory=SkillProfile)

    awards: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    additional_information: list[str] = Field(default_factory=list)


# ============================================================
# Document Discovery
# ============================================================

def find_documents(document_dir: Path) -> list[Path]:
    """
    Find all supported documents in the target directory.
    """
    if not document_dir.exists():
        raise FileNotFoundError(
            f"Document directory does not exist: {document_dir}"
        )

    document_paths = [
        path
        for path in document_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    document_paths.sort(key=lambda path: path.name.lower())

    if not document_paths:
        raise FileNotFoundError(
            f"No supported documents found in: {document_dir}"
        )

    return document_paths


# ============================================================
# Document Extraction
# ============================================================

def extract_all_documents(document_dir: Path) -> str:
    """
    Convert all supported documents into Markdown using Docling
    and combine them into one structured input.
    """
    document_paths = find_documents(document_dir)

    converter = DocumentConverter()

    combined_documents: list[str] = []

    print("=" * 80)
    print("DOCUMENT DISCOVERY")
    print("=" * 80)

    print(f"Directory: {document_dir}")
    print(f"Documents found: {len(document_paths)}")

    for path in document_paths:
        print(f"  - {path.name}")

    for index, path in enumerate(document_paths, start=1):
        print()
        print("=" * 80)
        print(f"EXTRACTING DOCUMENT {index}/{len(document_paths)}")
        print("=" * 80)

        print(f"File: {path.name}")
        print(f"Type: {path.suffix.lower()}")

        try:
            result = converter.convert(path)

            markdown = result.document.export_to_markdown()

        except Exception as exc:
            print(f"Failed to extract: {path.name}")
            print(f"Error: {exc}")
            continue

        print(f"Extracted characters: {len(markdown)}")

        document_block = f"""
===== DOCUMENT {index} =====
SOURCE FILE: {path.name}
FILE TYPE: {path.suffix.lower()}

{markdown}

===== END DOCUMENT {index} =====
"""

        combined_documents.append(document_block.strip())

    if not combined_documents:
        raise RuntimeError(
            "All documents failed during extraction."
        )

    return "\n\n\n".join(combined_documents)


# ============================================================
# LLM Profile Extraction
# ============================================================

def extract_profile(document_text: str) -> PersonalProfile:
    """
    Extract one unified PersonalProfile from all documents.
    """
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY was not found. "
            "Check your .env file."
        )

    client = OpenAI()

    developer_prompt = """
You are an information extraction system for a job-matching application.

You will receive MULTIPLE personal documents belonging to the same person.

The documents may include:

- resumes or CVs
- academic transcripts
- degree or enrollment documents
- certificates
- research documents
- project descriptions
- application materials
- identification-related documents
- other personal or academic records

Your task is to consolidate information from ALL documents into ONE
structured PersonalProfile.

Follow these rules strictly:

1. Extract only information supported by the provided documents.

2. Do not invent, assume, guess, or embellish unsupported facts.

3. All documents belong to the same person unless the documents explicitly
   indicate otherwise.

4. Combine information across documents when they describe the same fact.

5. Do not duplicate the same education, experience, project, publication,
   certification, or skill simply because it appears in multiple documents.

6. When multiple documents provide complementary information about the same
   item, merge the information into the most complete representation.

7. If documents contain conflicting information, prefer the more specific
   or clearly official source, but do not silently invent a resolution.

8. If a conflict cannot be resolved reliably, preserve the uncertainty in
   additional_information.

9. Distinguish academic research from professional employment.

10. Do not convert graduate research, thesis work, coursework, or laboratory
    activity into professional work experience unless a document explicitly
    identifies it as employment.

11. Do not exaggerate skill proficiency.

12. Technologies may be included as skills when the documents clearly show
    that the person used them in research, projects, coursework, or work.

13. Do not infer proficiency levels unless they are explicitly stated.

14. Preserve important names exactly when possible, including:
    institutions, degrees, research topics, programming languages,
    frameworks, methods, tools, certifications, projects, and publications.

15. Preserve source dates faithfully.
    Do not guess missing months or days.

16. If a value is unavailable, return null or an empty list.

17. The summary must be a factual synthesis of the documents.
    It must not read like marketing copy or an exaggerated resume profile.

18. Use information from all documents rather than treating the first
    document as the primary source by default.

19. Ignore irrelevant document artifacts, OCR noise, headers, footers,
    page numbers, and duplicated extraction text.

20. The final result should represent the person's consolidated factual
    profile, not a summary of each individual document.

The objective is factual cross-document normalization and consolidation.
"""

    user_prompt = f"""
Create one unified PersonalProfile from all of the personal documents below.

Each document is separated by explicit DOCUMENT markers and includes its
source file name.

DOCUMENT COLLECTION START
============================================================

{document_text}

============================================================
DOCUMENT COLLECTION END

Consolidate the information across all documents into one PersonalProfile.
"""

    print()
    print("=" * 80)
    print("LLM PROFILE EXTRACTION")
    print("=" * 80)

    print(f"Model: {MODEL}")
    print(f"Input characters: {len(document_text)}")

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": developer_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        text_format=PersonalProfile,
    )

    profile = response.output_parsed

    if profile is None:
        raise RuntimeError(
            "The model returned no parsed PersonalProfile."
        )

    if response.usage:
        print()
        print("TOKEN USAGE")
        print("-" * 40)

        print(f"Input tokens:  {response.usage.input_tokens}")
        print(f"Output tokens: {response.usage.output_tokens}")
        print(f"Total tokens:  {response.usage.total_tokens}")

    return profile


# ============================================================
# Output
# ============================================================

def save_outputs(
    document_text: str,
    profile: PersonalProfile,
) -> None:
    """
    Save the combined Docling output and final profile JSON.
    """
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined_path = (
        OUTPUT_DIR
        / "direct_profile_combined_documents.md"
    )

    profile_path = (
        OUTPUT_DIR
        / "direct_profile_result.json"
    )

    combined_path.write_text(
        document_text,
        encoding="utf-8",
    )

    profile_json = json.dumps(
        profile.model_dump(),
        ensure_ascii=False,
        indent=2,
    )

    profile_path.write_text(
        profile_json,
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("OUTPUT FILES")
    print("=" * 80)

    print(f"Combined documents:")
    print(f"  {combined_path}")

    print()
    print(f"Personal profile:")
    print(f"  {profile_path}")


# ============================================================
# Main
# ============================================================

def main() -> None:
    print()
    print("=" * 80)
    print("DIRECT MULTI-DOCUMENT PROFILE EXTRACTION TEST")
    print("=" * 80)

    document_text = extract_all_documents(
        DOCUMENT_DIR
    )

    print()
    print("=" * 80)
    print("COMBINED DOCUMENT INPUT")
    print("=" * 80)

    print(document_text)

    profile = extract_profile(
        document_text
    )

    print()
    print("=" * 80)
    print("FINAL PERSONAL PROFILE")
    print("=" * 80)

    profile_json = json.dumps(
        profile.model_dump(),
        ensure_ascii=False,
        indent=2,
    )

    print(profile_json)

    save_outputs(
        document_text=document_text,
        profile=profile,
    )


if __name__ == "__main__":
    main()