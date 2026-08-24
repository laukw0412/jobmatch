# JobMatch

JobMatch is an AI-assisted job matching and career analysis application designed to compare structured candidate profiles with job descriptions and provide actionable application recommendations.

The project is also being developed as a practical software engineering and AI application portfolio project.

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

## Current Architecture Direction

Candidate documents are first converted into a common `DocumentContent` representation.

Current document ingestion:

`PDF / DOCX / XLSX / XLS / Images -> DocumentContent`

PDF and DOCX extraction now use Docling as the primary layout-aware parser, with existing format-specific extraction methods retained as fallbacks where appropriate.

An evidence-based multi-document pipeline was implemented and tested:

`DocumentContent -> EvidenceSet -> MergedEvidenceSet -> ProfileContent`

This pipeline is currently considered **experimental**. Testing showed that repeated LLM transformations can introduce information loss, duplicate records, category drift, multilingual inconsistencies, additional latency, and unnecessary complexity.

The next architecture to evaluate is therefore a simpler direct pipeline:

`Multiple DocumentContent -> OpenAI Structured Output -> ProfileContent`

If the direct approach preserves candidate information reliably, the Evidence extraction / merge stages will be removed from the MVP path. Source provenance can be added later when required by GUI or explanation features.

## Document Input

The document ingestion layer supports:

- PDF
- DOCX
- XLSX
- XLS
- JPG
- JPEG
- PNG

### PDF / DOCX

Docling is the primary layout-aware extraction method:

`PDF / DOCX -> Docling -> Markdown -> DocumentContent`

Fallbacks remain available:

- PDF: PyMuPDF + Tesseract OCR fallback
- DOCX: `python-docx`

### Spreadsheet Input

- XLSX: `openpyxl`
- XLS: `xlrd`

### Image OCR

Image OCR uses Tesseract with support for:

- English
- Japanese
- Simplified Chinese
- Traditional Chinese

All supported document formats produce the common `DocumentContent` model before Profile processing.

## Profile Models

The current final Profile schema is represented by `ProfileContent` and includes:

- metadata
- identity
- education
- experience
- research
- projects
- skills
- languages
- certifications
- job preferences
- additional information

Current experimental evidence models include:

- `Evidence`
- `EvidenceSet`
- `MergedEvidence`
- `MergedEvidenceSet`

These models are being evaluated and are not yet considered permanent parts of the MVP architecture.

## LLM Integration

JobMatch uses the OpenAI Responses API with Structured Outputs for structured Profile generation.

The active model name is centralized in:

`src/jobmatch/llm/config.py`

API usage tracking is implemented in:

`src/jobmatch/llm/openai_usage.py`

Tracking includes:

- Input tokens
- Output tokens
- Cached/cache-write tokens when available
- Reasoning tokens when available
- Estimated request cost
- Daily cumulative usage and estimated cost

Local API usage records are excluded from Git.

## Current Status

**Document Ingestion v2 + Multi-Document Profile Architecture Evaluation**

Completed so far:

- Development environment and Git/GitHub setup
- `src` package structure and editable installation
- Final Profile Pydantic schema
- Profile validation foundation
- Common `DocumentContent` model
- PDF, DOCX, XLSX, XLS, JPG, JPEG, and PNG input support
- Tesseract multilingual OCR
- PDF OCR fallback
- Docling integration for layout-aware PDF / DOCX parsing
- OpenAI Responses API integration
- OpenAI Structured Outputs
- Centralized LLM model configuration
- OpenAI token and estimated-cost tracking
- Experimental source-grounded Evidence extraction
- Experimental multilingual Evidence merging
- Experimental `MergedEvidenceSet -> ProfileContent` builder
- Cache-controlled pipeline testing using `--no-cache`
- Real English + Japanese resume multi-document testing

Current architectural finding:

The Evidence-based pipeline works technically but has not demonstrated enough reliability or efficiency to justify its complexity for the MVP. A direct multi-document-to-Profile approach will be tested next before continuing with RAG and job matching.

## Job Analysis

Job descriptions are planned to support:

`Text / PDF / URL -> JobDocument -> Matcher`

Planned analysis includes:

- Match scores
- Strengths
- Skill and experience gaps
- Missing requirements
- Application risks
- Application recommendations
- Recruitment and selection process information

## Future Features

Planned later-stage features include:

- RAG-based information retrieval
- Desktop GUI
- Natural-language Profile editing
- Profile version history and rollback
- Job analysis history
- Automatic job discovery
- Job ranking
- Job/company information enrichment
- Growth and skill-gap advisor
- Exportable reports
- Optional source provenance / evidence explanation

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
│       │   ├── schema.py
│       │   ├── evidence.py
│       │   ├── evidence_extraction.py
│       │   ├── evidence_merge.py
│       │   ├── profile_builder.py
│       │   ├── storage.py
│       │   └── validation.py
│       ├── llm/
│       │   ├── config.py
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
│   ├── test_outputs/
│   └── usage/
├── docs/
│   └── development-log.md
├── prompts/
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Next Step

The next development session will compare the current Evidence pipeline against a simpler direct approach:

`Multiple DocumentContent -> ProfileContent`

The comparison should focus on:

- information preservation
- multilingual consolidation
- duplicate handling
- output stability
- latency
- API cost
- implementation complexity

If the direct approach performs adequately, the experimental Evidence extraction and merge layers will be retired from the MVP path. The project can then proceed to JD processing, matching, and RAG with a substantially simpler Profile pipeline.
