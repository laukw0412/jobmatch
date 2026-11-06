# JobMatch Repository Instructions

These instructions apply to the JobMatch repository. Follow global personal Codex instructions for communication, Python formatting, and general workflow; this file contains JobMatch-specific requirements.

## Project goals

JobMatch is a Python desktop application for evidence-based candidate–job matching and a practical AI/software engineering portfolio project.

The intended product includes:

- Candidate document ingestion from PDF, DOCX, XLS/XLSX, images, TXT, and Markdown
- Job-description input by pasted text and web URL, with file input as a planned extension
- A readable, editable JD confirmation step before matching
- Requirement-level matching results, evidence references, uncertainties, skill gaps, and application recommendations
- A standalone Windows GUI
- Document updates and recovery of at least five historical knowledge-base versions
- A replaceable LLM provider interface for future local LLM support

**RAG is mandatory.** It must perform meaningful evidence retrieval in the matching workflow. Do not remove it or reduce it to a decorative step.

## Accepted target architecture

The current direction is **Full-Context + RAG Augmentation**, not RAG-only and not fact-only indexing.

- Supply selected complete core candidate materials to the matching LLM when feasible and within context limits
- Use ChromaDB RAG for supplementary evidence retrieval with traceable sources
- Combine core context, JD requirements, and retrieved evidence in the main matching analysis
- Preserve original information and references; do not require a generated Candidate Profile or Fact Store as a gateway to source information
- Prefer a simple, usable pipeline over extra mandatory extraction, merge, or judge stages
- Preserve `matched`, `partial`, `missing`, and `unknown`; absence of evidence does not prove a requirement is unmet
- Distinguish academic research from professional experience and related skills from fully satisfied requirements
- Treat this as a **target design**, not a statement that the code already implements it

The accepted target architecture applies to normal development tasks.

During independent architecture reviews, the Agent may challenge the accepted design and propose alternatives based on `GOALS.md` and verifiable implementation evidence.

Such proposals do not authorize architectural changes. The current accepted design remains in effect until the user approves a replacement.

Do not reintroduce the abandoned multi-stage `Evidence → Merge → Profile` pipeline during normal development without concrete justification and user approval.

Lightweight document preprocessing or fact extraction may be evaluated when supported by observed data-quality problems. Do not assume such preprocessing must become a mandatory gateway to original source information.

## Historical engineering lessons

- The earlier multi-stage Profile architecture was complex and caused information loss
- OCR, spreadsheet layout, and document-to-index processing sometimes lost or scrambled important details, including TOEFL score information
- Multiple English, Japanese, and Chinese resume versions produced repeated retrieval evidence
- High embedding similarity or CrossEncoder scores do not prove that a JD requirement is satisfied
- The current personal document corpus is small enough that full relevant context can sometimes be preferable to strict Top-K filtering
- Judge architectural changes against these concrete problems instead of adding complexity for its own sake

Detailed history belongs in `develop_log/development-log.md` and, when available, `docs/architecture.md`.

## Repository onboarding and source of truth

Before substantial edits:

1. Inspect the relevant source files and their actual interfaces
2. Read `README.md`
3. Read `docs/architecture.md` if it exists
4. Read recent relevant entries in `develop_log/development-log.md` and older entries when needed
5. Identify disagreements between documentation, code, and the most recent accepted decisions

Source code is the authority on **what is implemented**. The latest accepted architecture decision is the authority on **what should be built**.

Existing technologies include Python 3.12, Pydantic, Docling, ChromaDB, OpenAI API, and an optional CrossEncoder reranker. PySide6 is planned for the GUI. Check installed dependencies rather than assuming a new library is needed.

## Data and indexing safeguards

- Use `data/documents/` as the only real candidate-document input directory unless the user changes this rule
- Do not create another candidate input directory by default
- Production Chroma path: `data/chroma`
- Production collection: `jobmatch_documents`
- Never index `data/test_index_documents/` into the production collection
- Before proposing or running a command or script that could index those test files into `data/chroma` / `jobmatch_documents`, warn explicitly and use isolated test storage instead
- Use temporary or separate databases and collections for indexing experiments
- Never delete, rebuild, reset, or overwrite production documents, vectors, or history without approval
- Do not commit source documents, extracted personal data, secrets, local databases, or API keys
- Do not send sensitive identity documents to external LLMs without the user's informed authorization

## Implementation priorities

- Focus on getting a usable end-to-end MVP before complex optimization
- Retain and adapt working ingestion, RAG, JD extraction, and matching code where justified
- Do not assume the old design is optimal; explain concrete benefits before broad architectural changes
- Avoid introducing mandatory intermediate fact extraction, profile merging, multi-agent orchestration, or manually labeled benchmark datasets without a demonstrated need
- Use focused real-document and real-JD scenario tests rather than building a research benchmark
- For paid API calls or indexing tests, state whether they operate on production or isolated data, and avoid unnecessary repeated requests
- Integrate document selection, matching, and report output into a Windows GUI without sacrificing RAG functionality
- Keep a clear distinction between implemented features and planned features
- Update `develop_log/development-log.md` and architecture notes when requested or when approved architectural changes are completed

## Collaboration

The user primarily reviews decisions, downloads or saves files, runs tests on a local Windows 11 machine, and reports errors or results. Handle inspection, implementation, and safe testing directly whenever the available environment allows. Do not state that local files, tests, Git commits, or GitHub were changed unless they actually were.

## Agent self-improvement

- Do not treat repeated failures as automatic evidence
  that repository instructions are incorrect
- When the same root cause causes two failed attempts,
  investigate whether the problem comes from code,
  requirements, architecture, tools, or instructions
- When the user rejects the same type of approach twice,
  reconsider the underlying assumptions
- Propose AGENTS.md updates only when an instruction-level
  improvement has a clear and reusable benefit
- Never modify AGENTS.md without explicit user approval
- Consolidate noncritical improvement proposals
- Do not repeatedly suggest previously rejected changes
  unless meaningful new evidence is available
- Prefer refining or removing obsolete rules over
  continuously accumulating additional restrictions

## Independent architecture review

- Suggest a fresh architecture review after approximately
  three completed functional modules when meaningful
  architectural changes have accumulated
- Suggest an earlier review before substantial changes to
  core data models, persistence, or system architecture
- Do not trigger a review solely because a fixed number
  of files, commits, or messages has been reached
- Avoid repeated reviews when the architecture has not
  materially changed
- Keep routine development reviews lightweight

### Review scheduling and repetition

- A completed functional module must have verifiable behavior or focused test results
- Do not count files, commits, or conversation turns as completed functional modules
- Suggest reviews rather than launching them automatically
- Do not repeat an architecture review unless material implementation changes or new evidence justify it
- Group nonurgent review opportunities at milestone boundaries
- Keep review findings concise and prioritize actionable risks
- The user decides whether to initiate a fresh review session

### Review independence

- Use a fresh Agent session without inheriting the
  development conversation or its prior conclusions
- Read GOALS.md and the current implementation
- Inspect relevant tests and observable behavior
- Treat previous architecture decisions as hypotheses,
  not as requirements
- Product requirements remain authoritative, but
  implementation choices may be challenged
- Evaluate reasonable alternative architectures
  without being constrained by the current technology
  stack or abandoned implementation approaches
- Do not equate passing tests with architectural quality
- Identify concrete benefits, migration costs, and risks

### Review permissions

- Independent reviews are read-only by default
- Do not modify source code during an architecture review
- Do not modify AGENTS.md or GOALS.md without approval
- Return one of:
  KEEP / INCREMENTAL IMPROVEMENT / REDESIGN
- Explain whether the expected improvement justifies
  the implementation and migration costs
- Prefer keeping the current architecture when
  alternatives have no meaningful demonstrated advantage
- Ask for approval before implementing recommendations

## Instruction hierarchy and maintenance

- GOALS.md defines approved product requirements
- AGENTS.md defines operational and development rules
- docs/architecture.md records the current accepted design
- Source code and tests describe actual implementation
- Historical decisions are informative but not immutable
- Architectural alternatives may be proposed during review
- Approved architectural changes should update the
  architecture documentation
- Never silently reinterpret product requirements
  to justify an implementation decision
