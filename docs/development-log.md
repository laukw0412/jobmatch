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