# JobMatch

JobMatch is an AI-assisted job matching and career analysis application designed to compare structured candidate profiles with job descriptions and provide actionable application recommendations.

## Goals

JobMatch aims to combine:

- Personal profile management
- Multi-format candidate document processing
- LLM-based structured information extraction
- Job description analysis
- Candidate-job matching
- Application recommendations
- Job and company information enrichment
- Career growth and skill-gap analysis

The project is also being developed as a practical software engineering and AI application portfolio project.


## Planned Workflow

### Personal Profile

Multiple candidate documents will be processed and consolidated into a structured Personal Profile:

`CV / Resume / Transcript / Certificates / Research / Projects`

`-> DocumentContent`

`-> DraftProfile`

`-> SourcedDraft`

`-> Consolidation`

`-> PersonalProfile`

`DraftProfile` represents potentially incomplete information extracted from individual documents.

`SourcedDraft` keeps the extracted information connected to its original source document for later deduplication and conflict resolution.

`PersonalProfile` represents the final standardized candidate profile after information from multiple documents has been consolidated.

The Profile system is planned to support:

- Machine-readable JSON representation
- Human-readable representation
- Natural-language Profile editing
- Version history and rollback


### Document Input

The current document ingestion layer supports:

- PDF
- DOCX
- XLSX
- XLS
- JPG
- JPEG
- PNG

Native document text is extracted when available.

Scanned/image-only PDF pages automatically fall back to OCR when native text is unavailable.

Image and scanned-PDF OCR uses Tesseract with support for:

- English
- Japanese
- Simplified Chinese
- Traditional Chinese

All supported document formats are converted into a common:

`DocumentContent`

representation before further processing.


### LLM Profile Extraction

JobMatch currently supports structured candidate information extraction using the OpenAI API.

Current pipeline:

`DocumentContent -> OpenAI Structured Output -> DraftProfile`

The extraction layer is designed to:

- Preserve source-supported information
- Avoid inventing missing factual information
- Preserve explicit document section structure when possible
- Allow incomplete fields during single-document extraction
- Keep extraction separate from later job-matching inference

The current default extraction model is:

`gpt-5.4-nano`

Higher-capability models can be used when needed.

OpenAI API usage is tracked locally, including:

- Input tokens
- Output tokens
- Cached/cache-write tokens when available
- Reasoning tokens when available
- Estimated request cost
- Daily cumulative usage and estimated cost


### Job Analysis

Job descriptions will eventually support multiple input methods:

`Text / PDF / URL -> JobDocument -> Matcher`

The analysis is planned to include:

- Match scores
- Strengths
- Skill and experience gaps
- Missing requirements
- Application risks
- Application recommendations
- Recruitment and selection process information


### Future Features

Planned later-stage features include:

- Multi-document Profile consolidation
- Profile deduplication and conflict resolution
- Local LLM support
- RAG-based information retrieval
- Desktop GUI
- Job analysis history
- Automatic job discovery
- Job ranking
- Growth and skill-gap advisor
- Exportable reports


## Current Status

**Document Ingestion v1 + LLM Profile Extraction v1 — Functional**

Completed so far:

- Development environment setup
- Git and GitHub integration
- Modular `src` project structure
- Python package configuration using `pyproject.toml`
- Editable package installation
- Personal Profile v1 Pydantic models
- Profile JSON loading
- Pydantic Profile validation
- Valid and invalid Profile validation testing
- Common `DocumentContent` model
- Multi-format document loader
- PDF native text extraction
- PDF OCR fallback for scanned/image-only pages
- DOCX text extraction
- XLSX spreadsheet extraction
- XLS spreadsheet extraction
- JPG / JPEG / PNG OCR
- Local Tesseract OCR configuration
- English, Japanese, Simplified Chinese, and Traditional Chinese OCR support
- OpenAI API integration
- OpenAI Structured Output integration
- OpenAI token and estimated cost tracking
- Draft Profile models for partial document extraction
- Source-aware Draft Profile design
- Successful real DOCX Resume -> DraftProfile extraction
- Initial comparison of `gpt-5.4-nano` and `gpt-5.6-terra`

Currently working on:

- Integrating `SourcedDraft`
- Testing additional candidate documents
- Consolidating multiple Draft Profiles
- Deduplicating repeated information
- Resolving conflicting information between source documents
- Generating the final standardized `PersonalProfile`


## Project Structure

```text
jobmatch/
├── src/
│   └── jobmatch/
│       ├── document/
│       │   ├── models.py
│       │   ├── loader.py
│       │   └── extractor.py
│       ├── profile/
│       │   ├── models.py
│       │   ├── draft_models.py
│       │   ├── extractor.py
│       │   ├── loader.py
│       │   └── validator.py
│       ├── llm/
│       │   └── openai_usage.py
│       ├── enrichment/
│       ├── jobs/
│       ├── matching/
│       ├── recommendations/
│       ├── ui/
│       └── main.py
├── data/
│   ├── applications/
│   ├── documents/
│   ├── jobs/
│   ├── profile/
│   └── usage/
├── docs/
│   └── development-log.md
├── prompts/
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore