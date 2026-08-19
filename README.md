# JobMatch

JobMatch is an AI-assisted job matching and career analysis application designed to compare structured candidate profiles with job descriptions and provide actionable application recommendations.

## Goals

JobMatch aims to combine:

- Personal profile management
- Job description analysis
- Candidate-job matching
- Application recommendations
- Job and company information enrichment
- Career growth and skill-gap analysis

The project is also being developed as a practical software engineering and AI application portfolio project.

## Planned Workflow

### Personal Profile

Multiple candidate documents will eventually be consolidated into a structured Personal Profile:

`CV / Resume / Transcript / Certificates / Research / Projects -> Personal Profile`

The Profile will support:

- Machine-readable JSON representation
- Human-readable Markdown representation
- Profile editing
- Version history and rollback

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

**Personal Profile v1 — In Development**

Completed so far:

- Development environment setup
- Git and GitHub integration
- Initial modular project structure
- Python package configuration using `pyproject.toml`
- Editable package installation
- Initial `profile.json`
- Profile JSON loader
- Basic manual Profile validation
- Initial Pydantic Profile model design

Currently working on:

- Finalizing the Personal Profile v1 schema
- Migrating nested Profile validation to Pydantic
- Testing Profile models and validation

## Project Structure

```text
jobmatch/
├── src/
│   └── jobmatch/
│       ├── profile/
│       │   ├── models.py
│       │   ├── loader.py
│       │   └── validator.py
│       └── main.py
├── data/
│   └── profile/
├── prompts/
├── tests/
├── docs/
├── pyproject.toml
├── requirements.txt
├── README.md
└── .gitignore