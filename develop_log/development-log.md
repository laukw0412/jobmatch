# Development Log

## 2026-08-19

### Environment Setup

- Created a dedicated Conda environment: `jobmatch`
- Python version: 3.12
- Project directory: `E:\Projects\jobmatch`
- Configured VS Code as the development environment
- Configured Git user information

### Project Initialization

- Created `README.md`
- Created `.gitignore`
- Created `docs/development-log.md`
- Initialized the local Git repository
- Connected the project to GitHub
- Configured GitHub SSH authentication
- Completed the first GitHub push

### Project Structure

Created the initial modular project structure based on the `src` layout.

Main application package:

`src/jobmatch/`

The project is planned to separate responsibilities such as:

- Personal profile management
- Job description input and processing
- Job matching
- Job/company information enrichment
- Recommendations
- LLM integration
- User interface

The structure is intentionally kept modular while avoiding unnecessary complexity during the MVP stage.

### Python Package Setup

Created `pyproject.toml` and configured the project as an installable Python package using the `src` layout.

Installed JobMatch in editable mode:

`python -m pip install -e .`

This allows application modules to use imports such as:

`from jobmatch.profile.loader import load_profile`

while keeping the actual source code under:

`src/jobmatch/`

The generated `*.egg-info/` package metadata is excluded from Git.

### Personal Profile v1

Designed the first version of the Personal Profile structure.

Current top-level fields:

- `metadata`
- `identity`
- `education`
- `experience`
- `research`
- `projects`
- `skills`
- `languages`
- `certifications`
- `job_preferences`
- `additional_information`

The Profile uses JSON as the machine-readable representation.

A future Markdown representation (`profile.md`) will provide a human-readable view of the same profile information.

Created a minimal test profile at:

`data/profile/profile.json`

### Profile Loader

Created:

`src/jobmatch/profile/loader.py`

Implemented the initial loading pipeline:

`profile.json -> json.load() -> Python dictionary`

Verified that the test Profile can be successfully loaded and printed from `main.py`.

### Profile Validation

Created:

`src/jobmatch/profile/validator.py`

Initially implemented manual validation to understand the validation process, including:

- Checking that the Profile itself is a dictionary
- Checking required top-level fields
- Checking which top-level fields should be dictionaries
- Checking which top-level fields should be lists
- Testing validation errors for missing fields
- Testing nested validation using `skills`

This manual implementation was used primarily to understand how schema validation works.

### Pydantic Models

Started migrating Profile schema definitions to Pydantic.

Created:

`src/jobmatch/profile/models.py`

The purpose of this module is to define structured Profile data models instead of manually writing validation logic for every nested field.

Initial Profile models are being designed for:

- Metadata
- Identity
- Education
- Experience
- Research
- Projects
- Skills
- Languages
- Certifications
- Job Preferences
- Personal Profile

Pydantic `Field(default_factory=list)` is used for optional list fields that should default to an empty list.

This migration is currently **in progress and has not yet been fully tested**.

### Design Decisions

Current design separates:

- `models.py` — defines what valid Profile data should look like
- `validator.py` — controls the validation process
- `loader.py` — loads Profile data from files
- `main.py` — application/test entry point

The Profile structure is considered **v1 and intentionally changeable**. It should be possible to revise the schema later without redesigning the entire JobMatch application.

### Future Profile Requirements

The Profile system is planned to support:

- Multiple source documents such as CVs, Japanese resumes, transcripts, certificates, research descriptions, and project documents
- PDF information extraction
- Consolidation of multiple documents into one Personal Profile
- `profile.json` for machine-readable data
- `profile.md` for human inspection
- Natural-language/Profile Prompt modifications
- Profile version history
- Keeping at least the five most recent Profile versions
- Profile rollback

### Future Job Analysis Requirements

The architecture should later support:

`Text / PDF / URL -> JobDocument -> Matcher`

Job analysis should eventually include not only JD matching but also:

- Company information
- Selection/recruitment process
- Coding test information
- Whether a coding test is online or conducted during an interview
- Web research when selection-process information is uncertain
- Possible original company job pages when the JD comes from a recruiter

The recommendation system should eventually distinguish between cases such as:

- Apply now
- Apply casually / low application cost
- Improve first, then apply
- Do not apply yet

This is particularly important for companies where repeated applications within a short period may be restricted.

### Long-Term Features

Planned later-stage features include:

- Desktop GUI
- Job analysis history
- Automatic job discovery
- Job ranking
- PDF reports with clickable job URLs
- Growth Advisor / skill-gap analysis
- Learning and project recommendations

These are future features and are not part of the current MVP implementation.

### Next Step

Next development session:

1. Review the current `models.py`
2. Review the Profile v1 field definitions
3. Test Pydantic installation and model imports
4. Test `PersonalProfile` validation against the current `profile.json`
5. Intentionally test invalid Profile data and inspect Pydantic validation errors
6. Decide whether the current manual validation in `validator.py` should be replaced or simplified
7. Continue refining the Personal Profile v1 schema

Do not proceed to JD matching until the basic Personal Profile model is stable.

----------------------------------------------------------------

## 2026-08-20

### Personal Profile v1 Validation

Completed the initial Personal Profile v1 schema and validation pipeline using Pydantic.

The Profile models are defined in:

`src/jobmatch/profile/models.py`

The current schema includes structured models for:

- Metadata
- Identity and location
- Work authorization
- Education
- Experience
- Research
- Projects and project links
- Skills
- Languages and language certifications
- Certifications
- Job preferences and salary preferences
- Personal Profile

Updated:

`src/jobmatch/profile/validator.py`

Profile validation now uses:

`PersonalProfile.model_validate(profile)`

Pydantic `ValidationError` is caught and exposed as a Profile validation error.

Tested the validation pipeline with both valid and intentionally invalid Profile data.

Confirmed that:

- A valid Profile passes validation and loads successfully
- Missing required nested fields are detected
- Invalid nested field types are detected
- Validation errors identify the location of invalid data

The basic Personal Profile v1 validation framework is now considered functional.


### Document Ingestion v1

Created the initial document ingestion system under:

`src/jobmatch/document/`

Current components include:

- `models.py` — defines extracted document data
- `loader.py` — identifies file types and routes files to the appropriate extractor
- `extractor.py` — extracts content from supported document formats

Created the `DocumentContent` model containing:

- `source_file`
- `file_type`
- `text`

The common document pipeline is:

`Source Document -> Extractor -> DocumentContent`


### PDF Support

Added PDF text extraction using PyMuPDF.

Current pipeline:

`PDF -> PyMuPDF -> page.get_text() -> DocumentContent`

Successfully tested extraction using a real English resume PDF.

Native text PDFs can now be converted into plain text for later Profile extraction.


### DOCX Support

Added DOCX text extraction using `python-docx`.

Current pipeline:

`DOCX -> Document -> Paragraphs -> Text -> DocumentContent`

Successfully tested DOCX document loading and text extraction.


### Excel Support

Added support for both modern and legacy Excel formats.

XLSX files are processed using `openpyxl`:

`XLSX -> Workbook -> Worksheet -> Row -> Cell -> Text`

XLS files are processed using `xlrd`:

`XLS -> Workbook -> Worksheet -> Row -> Cell -> Text`

Cell values from the same row are joined while preserving basic row-level relationships.

This support is intended particularly for structured documents such as Japanese resume templates.


### Image OCR Support

Added initial image OCR support for:

- `.jpg`
- `.jpeg`
- `.png`

Installed and configured:

- Tesseract OCR
- `pytesseract`
- Pillow

Configured Tesseract language data for:

- English (`eng`)
- Japanese (`jpn`)
- Simplified Chinese (`chi_sim`)
- Traditional Chinese (`chi_tra`)

Added image extraction using:

`Image -> Pillow -> Tesseract OCR -> Text -> DocumentContent`

Configured the Windows PATH so that `pytesseract` can locate the locally installed Tesseract executable.

Successfully tested OCR using a real Japanese JLPT result screenshot.

The OCR successfully recovered most important information, although some recognition noise remains in complex Japanese text, furigana, and mixed-layout content.

For v1, OCR is intended as an information extraction source rather than a perfectly accurate document transcription system.


### Supported Document Inputs

The document ingestion layer currently supports:

| Format | Method | Status |
| --- | --- | --- |
| PDF | PyMuPDF | Working |
| DOCX | python-docx | Working |
| XLSX | openpyxl | Working |
| XLS | xlrd | Working |
| JPG / JPEG / PNG | Tesseract OCR | Working |

TXT support was considered but intentionally deferred because it currently provides little practical value for the expected JobMatch document workflow.

Plain-text job descriptions and future prompt-based Profile editing will be handled as text input rather than requiring `.txt` files.


### Design Decisions

Document format detection is separated from document extraction:

`loader.py`

- Detects the source file type
- Routes the file to the correct extractor

`extractor.py`

- Contains format-specific extraction logic

`models.py`

- Defines the common `DocumentContent` output structure

All supported document types therefore produce a common output:

`DocumentContent`

This allows later Profile extraction logic to operate independently of the original file format.

OCR is currently kept inside `extractor.py` to avoid unnecessary module complexity during v1 development. It can be separated into a dedicated OCR module later if OCR functionality becomes more complex.


### Current Document Ingestion Limitation

Image OCR is supported, but scanned/image-only PDFs do not yet automatically fall back to OCR.

Current PDF behavior:

`PDF -> Native text extraction`

Planned behavior:

`PDF -> Native text extraction -> OCR fallback when native text is unavailable`

Embedded images inside otherwise normal PDF or DOCX files are not currently OCR-processed.


### Next Step

Next development session:

1. Add OCR fallback for scanned/image-only PDF files
2. Complete the Document Ingestion v1 layer
3. Begin processing multiple real candidate documents
4. Design the pipeline from `DocumentContent` to structured `PersonalProfile`
5. Begin automatic consolidation of information from resumes, transcripts, certificates, research documents, and other candidate materials

Avoid spending unnecessary time optimizing OCR accuracy before testing the complete document-to-Profile pipeline.

----------------------------------------------------------------

## 2026-08-21

### Document Ingestion v1 Completion

Completed the initial OCR fallback for scanned/image-only PDF pages.

PDF extraction now follows:

`PDF -> Native Text Extraction -> OCR Fallback -> DocumentContent`

For each PDF page:

- Native text is extracted using PyMuPDF when available
- If no native text is detected, the page is rendered as an image
- The rendered page is processed using Tesseract OCR

Created a reusable OCR helper inside:

`src/jobmatch/document/extractor.py`

Current OCR pipeline:

`Image -> Pillow Image -> Tesseract OCR -> Text`

The same OCR helper is now used by:

- Image extraction
- Scanned PDF fallback

Document Ingestion v1 now supports:

- PDF native text
- PDF OCR fallback
- DOCX
- XLSX
- XLS
- JPG
- JPEG
- PNG

All supported formats continue to produce the common:

`DocumentContent`

representation.


### OpenAI API Integration

Added the first OpenAI API integration for structured candidate information extraction.

Installed and configured the OpenAI Python SDK.

Successfully verified the API connection using the OpenAI Responses API.

Current API flow:

`Python -> OpenAI SDK -> Responses API -> OpenAI Model -> Response`

API credentials are stored outside the source code using the:

`OPENAI_API_KEY`

environment variable.

API keys are not stored in the repository.


### OpenAI API Usage Tracking

Created:

`src/jobmatch/llm/openai_usage.py`

Implemented reusable OpenAI API usage tracking.

The tracker records:

- Model name
- Input tokens
- Cached input tokens
- Cache-write tokens when available
- Output tokens
- Reasoning tokens when available
- Total tokens
- Estimated input cost
- Estimated output cost
- Estimated total request cost
- Daily cumulative request count
- Daily cumulative token usage
- Daily cumulative estimated cost

Usage history is stored locally in:

`data/usage/openai_usage.json`

The public tracking function is:

`track_openai_usage(response, model)`

Pricing values are stored by model and include a pricing verification date so that future pricing changes can be reviewed.

API cost calculations are estimates and are intended primarily for development monitoring.


### Draft Profile Models

Identified an important distinction between:

- Partial information extracted from a single document
- The final consolidated Personal Profile

Created:

`src/jobmatch/profile/draft_models.py`

Draft models use optional fields to preserve incomplete document information without forcing the LLM to invent unsupported values.

Examples include:

- `DraftIdentity`
- `DraftEducation`
- `DraftExperience`
- `DraftResearch`
- `DraftProject`
- `DraftSkill`
- `DraftLanguage`
- `DraftCertification`
- `DraftJobPreferences`
- `DraftProfile`

The intended data flow is now:

`DocumentContent -> DraftProfile -> Consolidation -> PersonalProfile`

The final models in:

`src/jobmatch/profile/models.py`

remain stricter and are intended for standardized profile storage and validation.


### Source-Aware Draft Profiles

Added:

`SourcedDraft`

A SourcedDraft combines:

- `source_file`
- `file_type`
- `DraftProfile`

This will allow later consolidation logic to determine where extracted information came from.

This is intended to support:

- Deduplication
- Conflict detection
- Source comparison
- Multi-document consolidation

The SourcedDraft consolidation logic has not yet been implemented.


### Structured Profile Extraction

Created:

`src/jobmatch/profile/extractor.py`

Implemented the first LLM-based structured extraction pipeline using OpenAI Structured Outputs.

Current pipeline:

`DocumentContent -> OpenAI -> DraftProfile`

The extractor:

- Receives `DocumentContent`
- Sends extracted document text to the OpenAI Responses API
- Uses a developer prompt focused on source-grounded extraction
- Requires structured output following the `DraftProfile` Pydantic schema
- Records API usage and estimated cost
- Returns the parsed `DraftProfile`

The extraction prompt currently emphasizes:

- Extract only information explicitly stated or directly supported by the document
- Do not invent unsupported factual information
- Leave unsupported fields as `None` or empty lists
- Follow explicit document section headings
- Avoid duplicating the same entry across multiple Profile sections
- Preserve document meaning while organizing information into the Profile schema
- Keep extraction separate from later job-matching inference


### Real Resume Extraction Test

Successfully tested the complete extraction pipeline using a real English DOCX resume.

End-to-end pipeline:

`DOCX`
`-> load_document()`
`-> extract_docx()`
`-> DocumentContent`
`-> OpenAI Structured Output`
`-> DraftProfile`

The extracted DraftProfile successfully contained structured information for:

- Identity
- Education
- Research
- Projects
- Skills
- Languages
- Certifications
- Job preferences

The test also confirmed that unsupported fields could remain `None` or empty rather than being automatically fabricated.


### Model Comparison

Tested Profile extraction using:

- `gpt-5.4-nano`
- `gpt-5.6-terra`

Initial testing showed that the extraction quality depends significantly on both:

- Model capability
- Prompt/schema design

After improving the extraction prompt and DraftProfile structure, `gpt-5.4-nano` produced sufficiently accurate structured extraction for the current Resume test while remaining substantially cheaper than `gpt-5.6-terra`.

Current default extraction model:

`gpt-5.4-nano`

`gpt-5.6-terra` remains a potential higher-capability fallback for more difficult documents.

Model choice is intentionally kept configurable and may change after broader testing.


### Current Profile Pipeline

The current candidate document pipeline is:

`Source Document`
`-> Document Loader`
`-> Document Extractor`
`-> DocumentContent`
`-> LLM Structured Extraction`
`-> DraftProfile`
`-> SourcedDraft`
`-> [Future Consolidation]`
`-> PersonalProfile`
`-> Profile Validation`


### Design Decisions

The LLM extraction layer should primarily preserve source-supported facts.

Inference and interpretation should be separated from extraction.

For example:

`Document Extraction`
`-> What does the source explicitly provide?`

Later:

`Profile + Job Description`
`-> What do those facts imply for job matching?`

This separation is intended to reduce unsupported LLM assumptions while still allowing richer reasoning during later JobMatch analysis.


### Next Step

Next development session:

1. Integrate `SourcedDraft` into the extraction pipeline
2. Test extraction using additional real candidate documents
3. Begin multi-document Profile consolidation
4. Design initial deduplication rules
5. Design initial conflict-handling rules
6. Convert consolidated Draft data into `PersonalProfile`
7. Validate the generated `PersonalProfile`
8. Begin testing Profile version persistence after the consolidation pipeline is stable

Do not begin RAG or JD matching until the basic multi-document candidate Profile consolidation pipeline is functional.

----------------------------------------------------------------

## 2026-08-24

### Document Parsing Upgrade with Docling

Upgraded the document extraction layer to use Docling as the primary layout-aware parser for PDF and DOCX documents.

Current PDF / DOCX strategy:

`PDF / DOCX -> Docling DocumentConverter -> DoclingDocument -> Markdown -> DocumentContent`

Docling is now preferred because it preserves document structure such as headings, lists, tables, and layout relationships better than plain-text extraction.

Fallback extraction remains available:

- PDF: PyMuPDF for embedded text, with Tesseract OCR for pages without native text
- DOCX: `python-docx` paragraph extraction

The `DocumentConverter` instance was moved to module scope so that it can be reused instead of being recreated for every document conversion.

Testing with an image-based Japanese student-card PDF confirmed that Docling can invoke RapidOCR and recover substantially better structured Japanese text than the previous fallback path.

### Evidence-Based Multi-Document Experiment

The previous `DraftProfile -> SourcedDraft -> PersonalProfile` design was reconsidered because the relationship between multiple similarly shaped intermediate models was becoming difficult to understand and maintain.

A new experimental evidence pipeline was implemented:

`DocumentContent -> EvidenceSet -> MergedEvidenceSet -> ProfileContent`

The purpose was to separate:

- source-document parsing
- source-grounded fact extraction
- cross-document deduplication / merging
- final Profile construction

Evidence extraction stored supporting source text and source metadata so extracted information could be checked against the original `DocumentContent`.

Source verification was tested using exact and normalized text matching. This exposed limitations caused by OCR / Markdown formatting differences and demonstrated that increasingly complex source-span verification did not provide enough practical benefit for the current MVP.

### Multi-Document Evidence Merge Testing

Tested the evidence pipeline using English and Japanese versions of the same resume.

A typical test produced approximately:

`48 extracted evidence records -> 24 merged evidence records -> ProfileContent`

The merge stage successfully combined many equivalent multilingual facts, but several important failure cases remained:

- semantically identical English and Japanese records were sometimes retained separately
- specific information could be weakened during merging
- language proficiency such as `Native` could be reduced to `Fluent` or lost
- one academic research activity could be represented as both `research` and `project`
- category labels generated at an earlier stage could incorrectly influence later Profile construction

The final Profile builder also showed output variation between repeated runs using the same cached merged evidence.

These tests demonstrated that adding more prompt rules to each intermediate stage was not reliably solving the underlying problem.

### Profile Builder

Implemented an experimental Profile builder using OpenAI Structured Outputs:

`MergedEvidenceSet -> ProfileContent`

The builder successfully generated the complete final Profile schema, including:

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

`additional_information` was changed from an unrestricted `dict` to `list[str]` because OpenAI Structured Outputs rejected the unrestricted dictionary JSON Schema.

Testing confirmed that the Profile schema itself can be generated successfully, but also showed that a multi-stage LLM pipeline can introduce information loss and classification drift between stages.

### Cache-Controlled Testing

Added cache-based testing for the multi-document Profile pipeline.

The test runner supports:

`python tests/test_build_profile.py`

which uses cached merged evidence when available, and:

`python tests/test_build_profile.py --no-cache`

which forces document extraction, evidence extraction, and evidence merging to run again before rebuilding the Profile.

This reduced repeated API calls while debugging later pipeline stages.

### Naming and Structure Cleanup

Several Profile-related names were revised so that relationships between files, models, and functions are easier to understand.

Important model naming changes during today's refactor included moving away from the earlier Draft/Sourced terminology toward:

- `DocumentContent`
- `Evidence`
- `EvidenceSet`
- `MergedEvidence`
- `MergedEvidenceSet`
- `ProfileContent`

Important function naming changes included:

- evidence extraction: `extract_evidence()`
- evidence consolidation renamed to evidence merge: `merge_evidence()`
- final Profile construction: `build_profile()`

Important module naming changes included:

- generic Profile extraction naming -> `evidence_extraction.py`
- `consolidation.py` -> `evidence_merge.py`
- final Profile construction -> `profile_builder.py`
- final Profile schema consolidated under `schema.py`
- validation module standardized as `validation.py`

Earlier experimental modules such as `draft_models.py` and the previous Profile `extractor.py` became obsolete under the evidence-based experiment and were removed / replaced during the refactor.

The earlier `models.py` / `validator.py` Profile naming was also revised toward the clearer `schema.py` / `validation.py` convention.

### Centralized LLM Configuration

Added centralized model configuration under:

`src/jobmatch/llm/config.py`

LLM-related modules now import the configured `MODEL` rather than independently defining the model name in every extraction / merge / builder module.

This makes model changes easier to control during testing.

### Architecture Review and Reflection

A major design review was performed after the evidence pipeline consumed substantial development time without reliably solving the original multi-document consolidation problem.

The main concern is that the current experimental architecture:

`DocumentContent -> EvidenceSet -> MergedEvidenceSet -> ProfileContent`

requires multiple LLM transformations over the same information.

Each transformation creates another opportunity for:

- information loss
- category drift
- duplicate records
- multilingual inconsistency
- prompt complexity
- additional API latency and cost

The evidence layer originally aimed to improve traceability and source verification, but current testing indicates that this benefit may not justify the added complexity for the MVP.

A review of alternative approaches suggests that Docling already provides a useful document-level intermediate representation. Therefore, a substantially simpler architecture should be evaluated before further investing in custom Evidence merging.

Proposed alternative:

`Multiple Source Documents`
`-> DocumentContent / Docling structured content`
`-> one multi-document LLM structured extraction`
`-> ProfileContent`

In this design, duplicate resolution and multilingual consolidation happen in a single structured extraction step instead of being distributed across multiple LLM stages.

Source provenance / evidence tracking can be added later if required by the GUI or explanation features rather than blocking the main MVP pipeline now.

### Updated Experimental Project Structure

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
│   ├── test_docling.py
│   ├── test_multi_evidence.py
│   ├── test_merge.py
│   └── test_build_profile.py
├── pyproject.toml
├── README.md
└── .gitignore
```

The Evidence modules are currently considered experimental rather than a finalized architectural requirement.

### Next Step

Next development session should begin with an architecture decision rather than further prompt tuning.

Priority evaluation:

1. Prototype a direct multi-document extraction path:
   `list[DocumentContent] -> ProfileContent`
2. Test the same English and Japanese resumes against the direct approach.
3. Compare accuracy, information preservation, latency, API cost, and code complexity with the Evidence pipeline.
4. If the direct approach performs adequately, retire the Evidence extraction / merge pipeline from the MVP path.
5. Keep provenance / source evidence as a later optional feature instead of a prerequisite for Profile construction.
6. After the Profile pipeline is simplified and stable, proceed to JD processing, matching, and RAG without further over-optimizing intermediate extraction architecture.

### Development Reflection

Today's work produced useful implementation experience but also exposed an important engineering lesson: additional architectural layers are not automatically improvements simply because they make responsibilities appear theoretically cleaner.

The Evidence design improved conceptual separation, but in practice it increased model count, naming complexity, API calls, latency, prompt tuning, and opportunities for information loss. A simpler pipeline may provide better reliability and allow the project to reach its actual JobMatch functionality sooner.

Future development should prefer the smallest architecture that preserves enough correctness for the MVP, and add provenance, conflict-resolution machinery, or additional intermediate representations only after a concrete product requirement demonstrates that they are necessary.

----------------------------------------------------------------

## 2026-10-29

### Architecture Review: RAG-First MVP

Resumed JobMatch development and reviewed the project's architecture and implementation priorities.

Key decisions:

- RAG is a mandatory component of the MVP, as gaining practical experience with RAG is one of the project's primary objectives.
- A consolidated Personal Profile is no longer required before implementing RAG.
- Original documents and their associated metadata will serve as the primary information sources.
- Previous Profile extraction and Evidence/Merge experiments are retained for reference but are not part of the current MVP pipeline.
- The project will use existing libraries for specialized functionality while keeping the overall RAG workflow under direct Python control.
- Local LLM integration remains a future feature. A lightweight provider abstraction may be added later.

### RAG Chunking Implementation

Created and updated:

- `src/jobmatch/rag/chunking.py`
- `tests/test_chunking.py`
- `tests/test_multiformat_chunking.py`

Implemented:

- `chunk_document()` — routes supported documents through parsing and chunking.
- `chunk_plain_text()` — uses LangChain's `RecursiveCharacterTextSplitter` for plain-text chunking.
- Docling `HybridChunker` for structure-aware chunking.
- Standardized chunk dictionaries containing `chunk_id`, `source_file`, `chunk_index`, `text`, and `method`.
- Fallback document loading when Docling conversion or chunking fails.

Current document handling:

| Format | Primary Method |
|---|---|
| PDF / DOCX | Docling + HybridChunker |
| XLSX / PNG / JPG / JPEG | Docling + HybridChunker, with fallback |
| XLS | Existing document loader + RecursiveCharacterTextSplitter |
| TXT / MD | Direct text loading + RecursiveCharacterTextSplitter |

The legacy XLS format is handled directly by the existing loader because Docling requires LibreOffice for XLS-to-XLSX conversion.

### Multi-Format Document Testing

Successfully tested three real documents:

**English Resume (PDF)**

- Generated 6 chunks.
- Preserved the main resume sections, including education, research, projects, and skills.
- Identified layout-related duplication and incorrect associations between some fields.
- Confirmed that the previously suspected missing Honeywell project was present in the complete chunk output.

**Japanese JLPT Result (PNG)**

- Generated 5 chunks.
- Successfully extracted important information, including JLPT N1 qualification and passing status.
- Identified OCR noise involving Japanese furigana and inconsistent table relationships.
- Observed that related certificate information was distributed across multiple chunks.

**Japanese Resume (XLS)**

- Generated 1 chunk containing 1,136 characters.
- Confirmed successful extraction through the legacy Excel loader.
- Added a direct XLS handling branch to avoid unnecessary Docling conversion failures.
- Identified reading-order problems caused by complex spreadsheet formatting and merged cells.

These issues are documented but will not block further MVP development unless they materially affect retrieval or matching accuracy.

### OpenAI Embedding and Chroma Integration

Created:

- `tests/test_vector_search.py`

Successfully tested the following pipeline:

`PDF -> Docling -> Chunking -> OpenAI Embedding -> Chroma -> Vector Retrieval`

Implementation details:

- Used OpenAI `text-embedding-3-small`.
- Generated 1,536-dimensional embedding vectors.
- Stored 6 resume chunks in a local persistent Chroma collection.
- Embedded an English search query and retrieved the three nearest chunks.
- Verified that research-related sections were ranked among the most relevant results.

Test query:

`Experience with transformer-based AI models`

The first two retrieval results were Self-Introduction and Research Experience, both containing relevant Transformer-based AI experience.

Chroma stores embeddings, chunk text, and metadata locally under `data/chroma/`.

**Current limitation:** The test script reprocesses and re-embeds the source document each time it runs. Incremental indexing and embedding reuse have not yet been implemented.

### Dependency and Environment Management

Added or introduced the following dependencies:

- `chromadb`
- `langchain-text-splitters`

An initial Chroma installation was accidentally performed in the Anaconda `base` environment, producing dependency conflicts involving Streamlit and MLflow.

Subsequent project development and testing used the dedicated `jobmatch` Conda environment.

The local Chroma database directory must remain excluded from Git because it may contain private document text and embeddings.

### Development Decisions and Reflection

- Prefer established parsing and chunking libraries instead of maintaining custom implementations unnecessarily.
- Use Docling for document-aware processing and LangChain's text splitter for plain-text fallback.
- Keep Embedding and Chroma operations explicit rather than introducing the complete LangChain workflow framework.
- Avoid excessive optimization of OCR and document layouts before evaluating their practical impact on RAG retrieval.
- Preserve source-document references so future job-matching results can be traced back to supporting evidence.
- Distinguish successful text extraction from accurate structural interpretation.

The main development priority is to complete a working end-to-end RAG-based job-matching application before introducing advanced features.

### Current Progress

**Implemented and tested:**

- Multi-format document chunking
- English PDF processing
- Japanese PNG OCR and chunking
- Legacy XLS processing
- OpenAI text embeddings
- Local Chroma vector storage
- Single-document semantic retrieval

**Not yet implemented or validated:**

- Multi-document indexing with change detection
- Reuse of previously stored document embeddings during indexing
- Cross-language retrieval testing
- Job description matching and evaluation
- RAG-based matching explanations
- Standalone GUI
- Local LLM integration

### Next Step

Implement `src/jobmatch/rag/indexing.py` for persistent multi-document indexing.

The next development stage should:

1. Discover supported documents under `data/documents/`.
2. Generate chunks and embeddings for new or modified documents.
3. Store embeddings and source metadata in Chroma.
4. Skip unchanged documents to avoid unnecessary API calls.
5. Support retrieval across multiple source documents.
6. Test English, Japanese, and Chinese cross-language queries.

The multi-document indexing implementation was discussed and drafted but **was not executed during this session**.

----------------------------------------------------------------

## 2026-10-30

### Development Focus

Continued JobMatch development with a focus on multi-document RAG indexing, incremental updates, and semantic retrieval.

The primary objective was to extend the existing single-document RAG pipeline into a multi-document retrieval system while keeping the implementation simple and reusable.

### 1. Chunking Module Review and Refinement

Reviewed and refined `src/jobmatch/rag/chunking.py`.

Changes and decisions:

- Reorganized document processing branches using `if / elif / else` to improve readability.
- Retained `RecursiveCharacterTextSplitter` for TXT, Markdown, and fallback text processing.
- Retained Docling `HybridChunker` for structured documents and images.
- Continued using the existing `load_document()` function for legacy XLS processing and fallback extraction.
- Improved variable naming to avoid overwriting `path` with a filename string.
- Clarified code comments and exception handling.
- Preserved chunk metadata, including `chunk_id`, `source_file`, `chunk_index`, `text`, and `method`.

Current chunking workflow:

```text
Document
  ├── TXT / MD
  │     └── RecursiveCharacterTextSplitter
  ├── XLS
  │     └── load_document()
  │           └── RecursiveCharacterTextSplitter
  └── PDF / DOCX / XLSX / Images
        └── Docling DocumentConverter
              └── HybridChunker
                    └── Fallback to load_document() if needed
```

The current implementation is sufficient for the initial RAG MVP. Further optimization of document conversion and fallback behavior is deferred.

### 2. Multi-Document Indexing

Created:

- `src/jobmatch/rag/indexing.py`

Implemented functions:

- `calculate_file_hash()`
- `index_document()`
- `index_directory()`

Key features:

- Recursively discover supported documents in a directory.
- Reuse the existing document chunking module.
- Generate embeddings with OpenAI `text-embedding-3-small`.
- Store document chunks and embeddings in a persistent Chroma collection.
- Calculate SHA-256 hashes to detect file content changes.
- Skip unchanged files to avoid unnecessary API calls.
- Re-index modified documents.
- Remove outdated chunks before inserting updated content.
- Generate stable document-specific chunk IDs using normalized file paths.
- Preserve source file paths, file hashes, chunk indices, and chunking methods as metadata.
- Continue processing other files when an individual file fails.

Current indexing workflow:

```text
Multiple Documents
       |
       v
File Discovery
       |
       v
SHA-256 Change Detection
       |
       v
Document Chunking
       |
       v
OpenAI Embeddings
       |
       v
Chroma Vector Database
```

### 3. OpenAI API Configuration

Encountered an API initialization error during the first indexing test:

```text
openai.OpenAIError: Missing credentials.
```

Cause:

- The OpenAI client was initialized before loading environment variables from `.env`.

Resolution:

- Added `load_dotenv()` before `OpenAI()` initialization in `index_directory()`.

The indexing test subsequently completed successfully.

### 4. Multi-Document Indexing Tests

Created:

- `tests/test_multi_index.py`

Test documents:

- `research.txt`
- `skills.txt`

Initial successful test:

```text
=== First run ===
indexed: research.txt
indexed: skills.txt
Total stored chunks: 2

{'indexed': 2, 'updated': 0, 'skipped': 0, 'empty': 0, 'failed': 0}

=== Second run ===
skipped: research.txt
skipped: skills.txt
Total stored chunks: 2

{'indexed': 0, 'updated': 0, 'skipped': 2, 'empty': 0, 'failed': 0}
```

The test confirmed that multiple documents can be indexed into the same Chroma collection and that unchanged documents are skipped.

### 5. Incremental Index Update Test

Extended `tests/test_multi_index.py` to modify `research.txt` and run indexing again.

Observed results:

```text
=== Third run: modified document ===
updated: research.txt
skipped: skills.txt
Total stored chunks: 2

{'indexed': 0, 'updated': 1, 'skipped': 1, 'empty': 0, 'failed': 0}
```

Verified:

- Modified files are detected through SHA-256 hash comparison.
- Unchanged files are skipped.
- Updated chunks replace the previous indexed content.
- The total number of stored chunks remains consistent for the test documents.

The next retrieval test also confirmed that the updated text was available in Chroma.

### 6. Cross-Document Semantic Retrieval

Created:

- `tests/test_multi_retrieval.py`

Test query:

```text
Experience with computer vision and image generation
```

Observed results:

```text
=== Result 1 ===
Source: research.txt
Distance: 0.7455
Text: Research in computer vision, generative AI, and omnidirectional image generation using PyTorch.

=== Result 2 ===
Source: skills.txt
Distance: 1.4661
Text: Programming skills include Python, machine learning, deep learning, and data analysis.
```

Verified:

- A query embedding can be generated using OpenAI.
- Chroma retrieves relevant chunks from multiple indexed documents.
- Retrieval results preserve source metadata.
- Updated document content is searchable.
- Vector distance provides a relative similarity measure, not a matching percentage.

The test used two indexed chunks. Larger-scale retrieval quality remains to be evaluated.

### 7. Reusable Retrieval Interface

Prepared:

- `src/jobmatch/rag/retrieval.py`
- `tests/test_retrieval_function.py`

Designed the reusable function:

```python
retrieve_chunks(query: str, top_k: int = 5) -> list[dict]
```

The function:

- Validates the input query and `top_k`.
- Connects to the persistent Chroma collection.
- Generates a query embedding.
- Performs Top-K vector similarity search.
- Returns chunk text, source information, chunk index, and distance.

The implementation was provided, but successful execution of the standalone retrieval-function test has not yet been confirmed.

### 8. RAG Architecture and Design Decisions

Confirmed the following MVP architecture:

```text
Candidate Documents
        |
        v
Document Parsing
        |
        v
Chunking
        |
        v
OpenAI Embeddings
        |
        v
Chroma Vector Store
        |
        v
Semantic Retrieval
        |
        v
JD Matching (Next Phase)
```

Design decisions:

- RAG remains a required component of the MVP.
- Use direct document-based retrieval instead of requiring a consolidated Profile.
- Keep the current implementation lightweight and avoid unnecessary intermediate layers.
- Reuse existing document parsing and LLM components wherever possible.
- Continue using OpenAI APIs initially.
- Reserve local LLM integration for a later stage.
- Keep code comments and docstrings in English.
- Prioritize working end-to-end functionality over premature optimization.

### 9. Current Limitations

Known limitations:

- Multi-document indexing tests currently cover a small TXT dataset.
- PDF, DOCX, XLSX, and image indexing require additional end-to-end testing.
- Documents deleted from the source directory are not automatically removed from Chroma.
- Embeddings are generated in a single request per document without batching.
- The current update procedure is not transactional.
- Stable chunk IDs are based on normalized file paths, not global content identity.
- Retrieval does not yet include requirement-specific query generation.
- The standalone `retrieve_chunks()` interface still requires execution verification.
- JD parsing and matching have not yet been implemented.

These limitations do not prevent continuation toward the initial JD Matching MVP.

### 10. Next Steps

Next development session:

1. Verify `retrieve_chunks()` through `tests/test_retrieval_function.py`.
2. Implement JD requirement extraction using an OpenAI LLM.
3. Extract individual technical, experience, education, and language requirements from job descriptions.
4. Perform RAG retrieval separately for each relevant requirement.
5. Connect retrieved evidence to an initial LLM-based matching analysis.
6. Produce an initial matching table with strengths, gaps, evidence sources, and application recommendations.

Planned workflow:

```text
Job Description
      |
      v
Requirement Extraction
      |
      v
Requirement-Based RAG Retrieval
      |
      v
Evidence-Based LLM Matching
      |
      v
Matching Report
```

### End-of-Day Summary

Successfully implemented and tested multi-document RAG indexing, SHA-256-based incremental updates, and cross-document semantic retrieval.

The project now has a working foundation for retrieving relevant candidate information from a shared vector database.

The next priority is to connect the existing RAG system to JD requirement extraction and candidate-job matching rather than further expanding the RAG infrastructure.


----------------------------------------------------------------


## 2026-11-02

### Development Summary

Continued development of the JobMatch MVP, focusing on job description acquisition, structured requirement extraction, and requirement-based RAG retrieval.

The main objective was to connect previously implemented document retrieval capabilities with real job descriptions while preserving the information needed for reliable candidate-job matching.

### 1. Job Description URL Extraction

Implemented and tested the URL extraction workflow in:

- `src/jobmatch/jobs/web_extractor.py`
- `tests/test_job_url_extraction.py`

Implementation:

- Added HTTPS URL validation.
- Used Requests and Trafilatura for initial HTML extraction.
- Added Playwright as a fallback for JavaScript-rendered pages.
- Introduced basic job-related content validation using `JOB_MARKERS`.
- Added detection of common blocked or invalid pages.
- Provided a manual text input fallback when automatic extraction fails.

Testing:

- Successfully extracted a real Sony AI Application Engineer job description from a Workday URL.
- Retrieved approximately 5,092 characters.
- Confirmed that the extracted text included the main responsibilities, required qualifications, preferred qualifications, and development environment.
- Saved the extracted text to `data/test_extracted_job.txt`.

Limitations:

- Automatic extraction does not guarantee that expandable job descriptions are complete.
- Websites may return truncated descriptions, login pages, or unrelated recommended jobs.
- Basic keyword validation cannot reliably determine JD completeness.
- Website-specific extraction implementations were avoided to keep the MVP maintainable.

### 2. JD Completeness and User Confirmation

Discussed how incomplete job descriptions could cause inaccurate matching results.

Decisions:

- Preserve the extracted JD text for user inspection.
- Require user confirmation before structured extraction in the current test workflow.
- Allow manual editing of the JD text before analysis.
- Plan a readable and editable JD preview page for the future GUI.
- Do not treat successful text extraction as proof that the entire JD was retrieved.

The current confirmation mechanism is implemented in:

- `tests/test_job_extraction.py`

The planned GUI will replace terminal confirmation with a JD preview and confirmation interface.

### 3. Structured Job Description Extraction

Implemented:

- `src/jobmatch/jobs/models.py`
- `src/jobmatch/jobs/extractor.py`
- `tests/test_job_extraction.py`

Added Pydantic models:

- `JobRequirement`
- `JobDescription`

`JobRequirement` fields:

- `description`
- `category`
- `priority`

`JobDescription` fields:

- `job_title`
- `company_name`
- `location`
- `responsibilities`
- `requirements`

Implemented `extract_job_description()` using OpenAI Structured Outputs.

The extraction prompt was designed to:

- Identify the primary job posting.
- Exclude navigation controls, advertisements, and unrelated job listings.
- Separate responsibilities from candidate qualifications.
- Preserve required and preferred qualification priorities.
- Preserve logical alternatives such as "PyTorch or TensorFlow".
- Avoid inventing qualifications.
- Avoid treating development environment information as mandatory requirements.

Testing:

- Processed the extracted Sony AI Application Engineer JD.
- Successfully extracted 5 responsibilities.
- Successfully extracted all 8 required qualifications.
- Successfully extracted all 8 preferred qualifications.
- Preserved the main qualification meanings and priorities.
- Saved the structured result to `data/test_structured_job.json`.

The current schema does not separately capture application process requirements, such as essay submissions or coding tests. This may be considered in a later iteration.

### 4. Requirement-based RAG Retrieval

Implemented:

- `src/jobmatch/matching/__init__.py`
- `src/jobmatch/matching/retriever.py`
- `tests/test_requirement_retrieval.py`

Added functions:

- `select_evidence()`
- `retrieve_job_requirements()`

`retrieve_job_requirements()`:

- Iterates through structured JD requirements.
- Uses each requirement description as a semantic search query.
- Calls the existing `retrieve_chunks()` function.
- Associates retrieved candidate evidence with its corresponding requirement.
- Preserves requirement category, priority, source information, and retrieval distance.

`select_evidence()`:

- Sorts candidate chunks by semantic distance.
- Prioritizes evidence from different source documents.
- Fills remaining result slots with additional relevant chunks.
- Returns up to the configured `top_k` results.

Default retrieval settings:

- `top_k = 5`
- `candidate_multiplier = 3`
- Up to 15 initial candidate chunks per requirement.
- Up to 5 selected evidence chunks per requirement.

Simplified the selection logic by removing the earlier `seen` and `unique` deduplication structures.

Reason:

- Chroma normally returns distinct records within a single query.
- The previous deduplication key included document source, chunk index, and text.
- It would not effectively remove repeated content across different resume versions.
- Source diversity was retained as a more immediately useful retrieval strategy.

### 5. Requirement Retrieval Testing

Ran requirement-based retrieval using the structured Sony JD.

Results:

- Successfully processed all 16 job requirements.
- Returned source metadata and semantic distances.
- Saved results to `data/test_requirement_evidence.json`.
- Confirmed that requirement-specific queries were successfully passed to Chroma.

Observed limitations:

- The active Chroma collection returned only two short test documents: `skills.txt` and `research.txt`.
- Technical requirements retrieved semantically relevant content.
- Education, language, and publication requirements lacked appropriate supporting evidence.
- Chroma returned the closest available documents even when they did not demonstrate the requested qualification.

Key conclusion:

Successful vector retrieval does not mean that valid matching evidence has been found. Retrieved chunks must be evaluated before being used to determine candidate suitability.

### 6. Architecture Decisions

Confirmed the following architecture:

JD URL / Text
    -> JD Text
    -> User Review and Confirmation
    -> LLM Structured Extraction
    -> Requirement-based RAG Retrieval
    -> Evidence Assessment and Matching Analysis
    -> Matching Table and Application Recommendations

Additional decisions:

- Retain the complete original JD for final matching analysis.
- Use structured requirements as individual retrieval queries.
- Preserve Required and Preferred distinctions.
- Keep requirement-to-evidence associations.
- Do not use vector distance as a direct matching score.
- Do not automatically assume that the latest document is the most authoritative.
- Distinguish missing evidence from confirmed failure to meet a requirement.
- Avoid introducing unnecessary intermediate LLM agents or profile-merging pipelines.

### 7. Current Limitations

- Requirement retrieval has not yet been validated against a representative collection of real candidate documents.
- Similar or outdated resumes may introduce repeated or conflicting evidence.
- Source diversity does not guarantee evidence relevance or correctness.
- The final Matching Analysis module has not yet been implemented.
- The standalone GUI and JD preview interface remain pending.
- Automatic JD completeness detection remains limited.

### Next Steps

1. Index real candidate documents, including resumes, academic records, language certificates, and research materials.
2. Ensure that personal documents and generated local data are excluded from Git.
3. Keep temporary test documents separate from real candidate evidence where practical.
4. Re-run requirement-based retrieval using the Sony JD.
5. Evaluate retrieval quality, cross-language retrieval, missing evidence, and conflicting document versions.
6. Implement LLM-based Matching Analysis using the original JD, structured requirements, and retrieved candidate evidence.
7. Develop a standalone GUI with readable, editable JD preview and confirmation.
8. Add application recommendations and skill-gap analysis.

### Development Status

Completed initial implementations:

- Multi-format document extraction
- Document chunking
- Chroma indexing
- Multi-document indexing with change detection
- Basic semantic retrieval
- Job description URL extraction
- Structured JD extraction
- Requirement-based RAG retrieval

Next priority:

Validate RAG evidence quality using real candidate documents before implementing final matching evaluation.


----------------------------------------------------------------


## 2026-11-03

### Development Focus

Re-evaluated the existing JobMatch retrieval and evidence selection architecture after observing repeated, weakly relevant, and potentially misleading evidence in previous matching experiments.

The main objective was to identify the root causes before proceeding with further LLM matching development.

No major changes were made to the production RAG or matching architecture today. Development focused on diagnostic experiments and architectural evaluation.

### 1. Evidence Retrieval Architecture Review

Reviewed the existing pipeline:

`Documents → Parsing → Chunking → ChromaDB → Vector Retrieval → CrossEncoder Reranking → Evidence Selection → LLM Matching`

Identified several architectural concerns:

- Retrieved chunks were treated as evidence before their actual evidential value had been established.
- The retrieval pipeline selected a fixed number of chunks even when no directly supporting evidence existed.
- Multiple resumes in different languages could contain repeated descriptions of the same underlying experience.
- Chunk-level semantic deduplication did not reliably identify fact-level duplication.
- CrossEncoder reranking improved relevance ordering but did not independently solve evidence duplication or qualification verification.
- Retrieval and reranking could not recover information missing from the indexed content.

Decided not to proceed immediately with the proposed `validated_analyzer.py` implementation, as stricter LLM matching alone would not resolve upstream data quality and retrieval problems.

### 2. Document Inventory Experiment

Created and executed:

`tests/test_document_scope.py`

The script was corrected to use the existing ChromaDB collection named `jobmatch_documents` rather than relying on an unavailable indexing helper or assuming that only one collection existed.

Inventory results:

- Local documents: 11
- Indexed chunks: 89
- Resume and resume-related documents: 31 chunks
- Certificates and academic records: 43 chunks
- Career history: 12 chunks
- Test sample: 3 chunks

Key findings:

- Four multilingual or alternative-format resumes accounted for 30 chunks.
- One Japanese resume spreadsheet contributed another chunk.
- The academic transcript document alone generated 31 chunks.
- The TOEFL report generated six chunks.
- Multiple resume versions were present, creating opportunities for repeated retrieval of the same underlying qualifications.
- The inventory alone did not demonstrate a parsing failure or prove that multilingual duplication was the primary source of retrieval errors.

### 3. Document Scope and Deduplication Comparison

Used `test_document_scope.py` to compare:

- A: Retrieval using all indexed personal documents, excluding the known sample document.
- B: Retrieval using a curated document subset.
- C: Curated retrieval with the existing semantic deduplication logic.

Initial requirements tested:

- R1: Master's degree
- R7: Problem-solving skills
- R8: English communication
- R15: Interest in Japanese culture, anime, or entertainment industries

Key findings:

- Reducing the number of resume versions did not consistently improve evidence quality.
- Removing some resume sources sometimes increased the proportion of academic transcript chunks in the results.
- Relevant evidence from the Japanese career history document remained retrievable in the curated experiment.
- The existing `is_duplicate()` function produced no changes to the final Top-5 results for the four tested requirements.
- Cross-language and cross-document duplication could not be reliably addressed by the current chunk-level similarity checks.

Conclusion:

Simple document filtering and the current semantic deduplication method were insufficient to resolve the observed evidence problems.

### 4. Retrieval Recall Experiment

Created and executed:

`tests/test_recall_diagnostics.py`

Compared four experimental strategies:

- A: Vector Top-15 followed by CrossEncoder reranking.
- B: Vector Top-30 followed by CrossEncoder reranking.
- C: Source-balanced candidate selection followed by reranking.
- D: Document-category-routed candidate selection followed by reranking.

Initial requirements:

- R1: Master's degree
- R8: English communication
- R15: Japanese culture, anime, or entertainment interest

Key findings:

- R1 produced identical final Top-5 results with Vector Top-15 and Top-30.
- R8 returned different TOEFL chunks when the candidate pool expanded.
- Source balancing did not consistently improve the relevance of retrieved content.
- The experimental category routing excluded TOEFL evidence from the final R8 Top-5.
- R15 continued to return weakly relevant chunks despite having no identified direct supporting evidence.
- Increasing candidate pool size changed retrieval results but did not necessarily improve factual correctness.

Conclusion:

Retrieval quality could not be evaluated by similarity scores, candidate diversity, or ranking order alone. Direct factual relevance and evidence completeness were necessary evaluation criteria.

### 5. TOEFL Document Extraction Investigation

Investigated the indexed chunks from:

`外国語（英語）試験成績証明書.pdf`

The six indexed chunks contained:

- Candidate identification information
- General TOEFL score-range descriptions
- Test information
- Institution codes
- Administrative and verification notes

However, the indexed chunks did not contain the candidate's actual TOEFL total score or individual section scores.

The original PDF was subsequently inspected.

The original document contained:

- TOEFL iBT total score: 99/120
- Reading: 24
- Listening: 29
- Speaking: 23
- Writing: 23
- Test date: May 20, 2023

These values were visible in the original document and available in its text layer, but were absent from the indexed ChromaDB chunks.

This established a concrete case of information loss somewhere between source document extraction and the final indexed representation.

The exact failure point within parsing, chunking, or indexing has not yet been isolated.

Conclusion:

Improving retrieval or reranking alone cannot recover facts absent from the indexed content.

### 6. Architectural Conclusions

The experiments identified three distinct classes of problems:

**Document-level problems**

- Multiple document versions and languages may describe the same underlying facts.
- Source documents contain both useful facts and irrelevant administrative or explanatory information.
- Some important information is not preserved in the final indexed chunks.

**Retrieval-level problems**

- Vector similarity and CrossEncoder relevance scores do not establish qualification validity.
- Fixed Top-K selection may return irrelevant candidates when direct evidence is unavailable.
- Source balancing and category routing do not automatically improve evidence quality.
- The current deduplication function does not provide reliable fact-level deduplication.

**Matching-level problems**

- Retrieved chunks should be treated as candidate context rather than verified evidence.
- Multiple sources describing one experience should not be counted as independent experiences.
- Matching should distinguish supported, partially supported, unsupported, and unknown qualifications.
- Evidence citations must remain traceable to original documents.

### 7. Proposed Architecture Revision

Proposed direction:

`Documents → Document Preprocessing → Fact Extraction → Chunking / Indexing → RAG Retrieval → LLM Matching → Recommendations`

Planned preprocessing responsibilities:

- Identify document types and languages.
- Extract source content using appropriate parsers.
- Improve preservation of important factual information.
- Use a single LLM extraction pass where semantic interpretation is needed.
- Represent extracted facts with source references.
- Associate repeated facts across languages and document versions.
- Preserve original document content for verification.
- Cache preprocessing results using file hashes.

The preprocessing stage should use a hybrid approach:

- Standard parsing and validation for deterministic tasks.
- LLM-based structured extraction for semantic understanding.
- No additional multi-agent architecture.
- No mandatory multi-stage Evidence → Merge → Profile pipeline.

This architecture is proposed but has not yet been implemented.

### 8. Diagnostic Outputs

Generated local diagnostic reports:

- `data/diagnostics/01_index_inventory.csv`
- `data/diagnostics/02_evidence_comparison.csv`
- `data/diagnostics/03_comparison_summary.csv`
- `data/diagnostics/04_recall_detail.csv`
- `data/diagnostics/05_recall_summary.csv`
- `data/diagnostics/06_toefl_chunks.csv`

These files may contain personal information and document text and must remain excluded from Git version control.

### 9. Lessons Learned

- Successful execution does not establish retrieval correctness.
- Better reranking does not necessarily mean better evidence quality.
- Chunk-level deduplication does not solve fact-level duplication.
- Document preprocessing quality should be validated before retrieval optimization.
- Increasing architectural complexity without clear evaluation criteria can produce limited practical benefits.
- Development decisions should prioritize the usefulness and factual reliability of final matching results rather than intermediate similarity metrics.

### Next Steps

1. Design a lightweight Document Preprocessing module.
2. Define a structured fact representation with source references.
3. Determine how to preserve important information from complex PDF layouts.
4. Integrate LLM-based fact extraction with file-hash caching.
5. Update ChromaDB indexing to support useful structured facts.
6. Revise evidence retrieval to avoid forced Top-K evidence selection.
7. Adapt the matching analyzer to use factual evidence rather than unverified chunks.
8. Continue toward the JobMatch MVP GUI after the core matching pipeline becomes reliable.

The immediate next development priority is Document Preprocessing, not additional reranker or deduplication tuning.


----------------------------------------------------------------


## 2026-11-05

### Architecture Reconsideration: Full-Context + RAG Augmentation

Reconsidered the proposed November 3 fact-extraction-first architecture in light of the original product goals and the history of failed multi-stage Profile extraction experiments. This was an architectural discussion, not an implementation or testing session.

**Previous proposal (November 3):**

`Documents -> Preprocessing -> Structured Facts -> Fact Index -> RAG -> LLM Matching`

The concern was that making an extracted Fact Store the mandatory information gateway could discard important source details, reproduce earlier multi-stage extraction errors, and delay a usable MVP. Retrieval-score tuning also cannot recover facts missing upstream.

**Accepted target direction:** Full-Context + RAG Augmentation, rather than RAG-only or fact-only indexing.

- Supply selected, complete, relevant core candidate materials to the matching LLM when feasible and within context constraints.
- Retain ChromaDB-based RAG as a mandatory complementary evidence-retrieval step with source traceability.
- Combine the confirmed original JD, structured JD requirements, selected core candidate context, and retrieved supplementary evidence in matching.
- Do not require a generated Candidate Profile or structured Fact Store to access original document information.
- Apply targeted preprocessing/fact extraction only where directly justified by observed failures (e.g. TOEFL information lost from indexed chunks).
- Avoid the previously abandoned mandatory `Evidence -> Merge -> Profile` process without separate justification and user approval.
- Preserve `matched`, `partial`, `missing`, and `unknown`, and distinguish unsupported evidence from a confirmed unmet qualification.
- Avoid counting several multilingual resume versions as independent qualifications.

**Status:** The Full-Context + RAG architecture is a target design. No new source-code implementation, integration test, index migration, or GUI completion has been verified during this discussion. The November 3 fact-extraction-first plan remains historical rather than a required next step.

### Agent Governance Discussion

Discussed separate project requirements (`GOALS.md`), repository development instructions (`AGENTS.md`), and personal global Codex instructions. The desired workflow includes: low-frequency architecture reviews with fresh context; repeated-failure analysis; proposals before rule changes; and explicit user approval before modifying rules or broad architecture. These governance decisions do not establish an automated review service by themselves.

### Privacy and Data Handling Considerations

Personal documents and derived diagnostic data should remain excluded from Git tracking. However, Git ignores do not prevent model API calls, IDE-agent context transmission, or command outputs from reaching remote services. Review permission settings, outbound transmissions, and Git staged files separately. Do not assume the local repository has been audited solely because documentation contains these safeguards.

### Next Steps

1. Inspect current source interfaces and plan the smallest working Full-Context + RAG prototype.
2. Test source-context completeness and requirement-level matching semantics using authorized data handling.
3. Validate the target design before changing production Chroma data or performing a broad refactor.
4. Continue to the user-facing JD confirmation, matching report, and Windows GUI.
