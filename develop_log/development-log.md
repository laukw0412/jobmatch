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