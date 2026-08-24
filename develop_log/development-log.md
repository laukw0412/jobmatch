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

