# JobMatch

JobMatch is an AI-assisted job matching and career analysis application designed to compare structured candidate profiles with job descriptions and provide actionable application recommendations.

## Goals

JobMatch aims to combine:

- Personal profile management
- Multi-format candidate document processing
- Job description analysis
- Candidate-job matching
- Application recommendations
- Job and company information enrichment
- Career growth and skill-gap analysis

The project is also being developed as a practical software engineering and AI application portfolio project.

## Planned Workflow

### Personal Profile

Multiple candidate documents will be consolidated into a structured Personal Profile:

`CV / Resume / Transcript / Certificates / Research / Projects -> DocumentContent -> PersonalProfile`

The Profile is planned to support:

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

Image files are processed using Tesseract OCR with support for English, Japanese, Simplified Chinese, and Traditional Chinese.

All supported document formats are converted into a common `DocumentContent` representation before further processing.

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

- Desktop GUI
- Job analysis history
- Automatic job discovery
- Job ranking
- Growth and skill-gap advisor
- Exportable reports

## Current Status

**Personal Profile v1 + Document Ingestion v1 — In Development**

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
- DOCX text extraction
- XLSX spreadsheet extraction
- XLS spreadsheet extraction
- JPG / JPEG / PNG OCR
- Local Tesseract OCR configuration
- English, Japanese, Simplified Chinese, and Traditional Chinese OCR support
- Initial testing with real candidate documents

Currently working on:

- OCR fallback for scanned PDFs
- Completing Document Ingestion v1
- Converting extracted document content into structured Personal Profile data
- Consolidating information from multiple candidate documents

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
│       │   ├── loader.py
│       │   └── validator.py
│       ├── enrichment/
│       ├── jobs/
│       ├── llm/
│       ├── matching/
│       ├── recommendations/
│       ├── ui/
│       └── main.py
├── data/
│   ├── applications/
│   ├── documents/
│   ├── jobs/
│   └── profile/
├── docs/
│   └── development-log.md
├── prompts/
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore