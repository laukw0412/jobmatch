
# JobMatch

JobMatch is an AI-assisted job matching and career analysis application that uses Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to evaluate candidate qualifications against job descriptions.

The project aims to provide evidence-based candidate-job matching, identify qualification gaps, and generate actionable application recommendations.

JobMatch is also developed as a practical software engineering and applied AI portfolio project.

## Goals

JobMatch aims to support:

- Multi-format candidate document ingestion
- Personal document indexing and semantic retrieval
- Job description input through text, files, and URLs
- LLM-based structured job requirement extraction
- Requirement-based RAG retrieval
- Evidence-based candidate-job matching
- Qualification and skill-gap analysis
- Application recommendations
- A standalone graphical user interface
- Future job discovery and recommendation capabilities
- Future local LLM integration

## Current Status

Core document processing, RAG infrastructure, and job requirement extraction have been implemented and initially tested.

Requirement-based RAG retrieval is operational, but retrieval quality still needs to be validated using a representative collection of real candidate documents.

The final matching analysis and standalone GUI are not yet implemented.

### Implemented Features

**Document Processing**

- PDF, DOCX, XLSX, XLS, image, TXT, and Markdown document support
- Layout-aware document processing using Docling
- OCR-based text extraction for images
- Document chunking using Docling HybridChunker
- RecursiveCharacterTextSplitter fallback for plain text and unsupported chunking cases

**RAG Infrastructure**

- OpenAI embeddings
- Chroma vector database
- Persistent document indexing
- Multi-document indexing
- File hash-based change detection
- Indexing statistics for indexed, updated, skipped, and failed documents
- Semantic retrieval with source metadata

**Job Description Processing**

- Public HTTPS job URL extraction
- Requests and Trafilatura-based HTML extraction
- Playwright fallback for JavaScript-rendered pages
- Basic invalid-page detection
- Manual review and confirmation workflow in the test interface
- LLM-based structured extraction using Pydantic
- Separation of responsibilities, required qualifications, and preferred qualifications

**Requirement-based Retrieval**

- Individual semantic queries for structured job requirements
- Retrieval of candidate evidence from Chroma
- Source-diversity selection
- Requirement-to-evidence associations
- Preservation of source information and retrieval distances

### Work in Progress

- Real-document RAG evaluation
- Evidence relevance and conflict assessment
- LLM-based candidate-job matching
- Matching scores and requirement-level assessments
- Application recommendations
- Readable and editable JD preview GUI

## Architecture

The current workflow is:

```text
Candidate Documents
        |
        v
Document Extraction
        |
        v
Document Chunking
        |
        v
OpenAI Embeddings
        |
        v
Chroma Vector Database
        |
        | Candidate Evidence
        |
Job URL / JD Text
        |
        v
JD Text Extraction
        |
        v
User Review and Confirmation
        |
        v
LLM Structured JD Extraction
        |
        v
Individual Job Requirements
        |
        v
Requirement-based RAG Retrieval
        |
        v
Requirement-Evidence Results
        |
        v
Matching Analysis (Planned)
        |
        v
Matching Table and Recommendations (Planned)
```

The original job description is preserved for final matching analysis.

Structured requirements are used to generate focused retrieval queries instead of relying exclusively on a single embedding of the complete job description.

## Document Processing

Candidate documents are converted into a common document representation before chunking and indexing.

Supported file extensions include:

- `.pdf`
- `.docx`
- `.xlsx`
- `.xls`
- `.png`
- `.jpg`
- `.jpeg`
- `.txt`
- `.md`

Docling is used as the primary layout-aware processing solution where applicable.

Document chunking uses Docling HybridChunker when available and falls back to recursive text splitting when necessary.

## RAG Implementation

The RAG pipeline consists of:

1. Candidate document extraction
2. Document chunking
3. Embedding generation
4. Chroma indexing
5. Semantic retrieval

The multi-document indexing workflow uses file hashes to detect unchanged and modified documents, avoiding unnecessary re-indexing.

Retrieved evidence includes:

- Chunk text
- Source filename
- Source path
- Chunk index
- Vector search distance

Retrieval distance is treated as a semantic relevance signal, not as direct proof that a candidate meets a job requirement.

## Job Description Extraction

Job descriptions can currently be extracted from selected public URLs or supplied as local text.

The URL extraction workflow uses:

1. Requests and Trafilatura
2. Playwright fallback when necessary
3. Basic job-related text validation

Website extraction may fail because of authentication, rate limiting, JavaScript rendering, or collapsed job descriptions.

The current test workflow allows users to inspect and confirm the extracted text before further processing.

A dedicated JD preview and editing interface is planned for the GUI.

## Structured Job Requirements

OpenAI Structured Outputs and Pydantic are used to convert job descriptions into structured data.

The current structured representation includes:

- Job title
- Company name
- Location
- Responsibilities
- Candidate requirements
- Requirement categories
- Required or preferred priority

The extraction process aims to preserve the original meaning of requirements, including alternative conditions such as "PyTorch or TensorFlow".

## Requirement-based RAG Retrieval

Each structured requirement is used as an independent semantic retrieval query.

The retrieval workflow:

1. Iterates through job requirements
2. Retrieves candidate chunks from Chroma
3. Sorts retrieved chunks by semantic distance
4. Prioritizes different document sources
5. Associates selected evidence with the original requirement

The default configuration retrieves up to 15 candidate chunks and selects up to 5 evidence chunks per requirement.

The source-diversity strategy is intended to reduce domination by a single document. It does not resolve semantic duplicates, outdated records, or conflicting information.

These issues will be considered during evidence evaluation and matching analysis.

## Testing

Initial tests have covered:

- Multi-format document extraction
- Document chunking
- Vector indexing and retrieval
- Multi-document indexing and change detection
- Public job URL extraction
- Structured job requirement extraction
- Requirement-based RAG retrieval

A real Sony AI Application Engineer job description was used to validate structured extraction and retrieval.

The structured extraction successfully preserved:

- 5 responsibilities
- 8 required qualifications
- 8 preferred qualifications

Requirement-based retrieval successfully processed all 16 qualifications.

Current retrieval evaluation remains limited because the active test collection contains only a small amount of candidate evidence.

Testing against real resumes, academic records, language certificates, and research documents is the next priority.

## Technology Stack

- Python 3.12
- OpenAI API
- Pydantic
- Docling
- LangChain text splitters
- ChromaDB
- Trafilatura
- Requests
- Playwright
- python-dotenv

## Development Environment

- Windows 11
- Conda
- Visual Studio Code
- Git and GitHub

## Roadmap

### Phase 1: Document Processing

- [x] Project initialization
- [x] Multi-format document extraction
- [x] Layout-aware document processing
- [x] Document chunking

### Phase 2: RAG Infrastructure

- [x] Embedding generation
- [x] Persistent Chroma indexing
- [x] Multi-document indexing
- [x] File hash-based change detection
- [x] Basic semantic retrieval

### Phase 3: Job Description Processing

- [x] Basic public URL extraction
- [x] Structured requirement extraction
- [x] Required and preferred requirement classification
- [x] Terminal-based JD review and confirmation
- [ ] GUI-based JD preview and editing

### Phase 4: Evidence-based Matching

- [x] Requirement-based RAG retrieval
- [ ] Real-document retrieval evaluation
- [ ] Evidence relevance and conflict assessment
- [ ] LLM-based matching analysis
- [ ] Matching scores and explanations
- [ ] Skill-gap and application recommendations

### Phase 5: Application Interface

- [ ] Standalone GUI
- [ ] Candidate document management
- [ ] JD input and preview interface
- [ ] Matching results dashboard

### Future Extensions

- [ ] Local LLM provider integration
- [ ] Job discovery and recommendation
- [ ] Company and job information enrichment
- [ ] Career development recommendations

## Privacy and Data Handling

Candidate documents may contain personal or sensitive information.

Local document files, API credentials, and generated test data should not be committed to the repository.

The project uses external OpenAI API services for selected LLM and embedding operations. Documents or extracted text sent to these services are not processed entirely locally.

## Project Purpose

JobMatch is intended to become a practical job application decision-support tool.

Rather than relying solely on general semantic similarity, the project aims to connect individual job requirements with relevant candidate evidence and produce explainable, actionable matching assessments.
