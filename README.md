# JobMatch

JobMatch is an AI-assisted job matching and career analysis application designed to evaluate candidate qualifications against job descriptions and provide evidence-based application recommendations.

The project is also developed as a practical software engineering and AI application portfolio project, focusing on document processing, Retrieval-Augmented Generation (RAG), LLM integration, and information retrieval evaluation.

## Project Goals

JobMatch aims to provide:

- Multi-format candidate document ingestion
- Personal document management
- Job description extraction from text, PDF, and web sources
- Structured job requirement analysis
- RAG-based candidate information retrieval
- Evidence-based candidate-job matching
- Qualification and skill-gap analysis
- Actionable application recommendations
- A standalone graphical user interface
- Optional local LLM support in a later development stage

The intended user workflow is:

**Upload Documents → Build Candidate Knowledge Base → Enter Job Description → Analyze Matching → Review Results and Recommendations**

## Current Status

**Development Phase: Desktop MVP Integration**

The project currently includes working implementations of document parsing, chunking, persistent vector indexing, structured job requirement extraction, candidate information retrieval, CrossEncoder reranking, and experimental LLM-based matching.

These components have been implemented and tested individually or through integration experiments.

However, the complete application is not yet considered a reliable end-to-end MVP.

Retrieval experiments conducted on November 3, 2026, identified limitations in document information preservation, fact-level duplication, retrieval relevance, and evidence reliability.

Following a subsequent architecture reconsideration on November 5, 2026, the **accepted target direction** is **Full-Context + RAG Augmentation**. Selected complete core candidate materials should be available to the matching LLM when feasible, while RAG remains mandatory for supplementary, traceable evidence retrieval. Structured fact extraction is an optional technique to address demonstrated extraction failures, **not a mandatory gateway** to candidate information. On November 6, a minimal function workflow was implemented and verified with seventeen offline tests using synthetic documents and mocked OpenAI/Chroma interfaces. Real-document parsing quality, live retrieval, and LLM matching have not been validated for this combined workflow.

The MVP uses **user-selected core files**, not automatic selection. `jobmatch.matching.workflow.match_job(confirmed_jd_text, core_document_paths, ...)` loads complete parsed text from explicitly selected files inside `data/documents/`, extracts requirements, retrieves supplementary evidence excluding core paths, and runs combined matching. The caller must first obtain JD confirmation and authorization for API transmission. This function interface is now complemented by the desktop prototype described below.

Both core and RAG citations retain source type, filename/path, corresponding text, and an exact quote checked against that text. IDs use separate namespaces (`core:N` and `rag:REQUIREMENT_ID:N`); old RAG-only numeric indices remain for compatibility. A configurable character cap (60,000 by default, including the final serialized matching payload and system prompt) rejects oversized input without truncation. It is not an exact token/cost budget. Uncited judgments become `unknown`, with validation warnings when model summaries have not been revalidated.

Complete-document Docling export now renders merged-cell text once and uses compact Markdown tables. Six synthetic export regression checks and the seventeen matching checks passed. A local, network-blocked rerun of the selected English resume reduced its exported text from 4,445 to 2,372 characters while retaining the native text's normalized word-character counts. This corrects a demonstrated export duplication issue; it does not establish semantic completeness or change existing RAG vectors.

Retrieval now accepts an explicit database path, collection, and source allowlist for isolated experiments. A first real attempt stopped before retrieval because persistent Chroma client settings differed. Clients now share one creation helper, and thirty focused offline checks passed, including real temporary persistent-storage tests. A user-authorized continuation reused the successful artifacts and completed six selected requirements: three matched, one partial, and two unknown, with both core and RAG citations. This validated a bounded function-level scenario, not the complete MVP; certificate score loss and citation quality issues motivated the subsequent offline repair below. See [architecture notes](docs/architecture.md#19-consistent-storage-clients-and-verified-continuation).

Subsequent local repair located the English score values in recognized text nested under Docling picture nodes. Complete Markdown export and HybridChunker serialization now traverse that text. Local checks preserved all five score-label/value combinations in complete text and in individual chunks; the English report now produces eight chunks. Citation instructions also request quotes covering every essential condition, allow multiple passages from one source, and add an advisory check for the observed Python/framework excerpt gap. Forty focused offline checks passed. At that offline milestone, the repairs had not been re-indexed into existing databases or retested with a live LLM; lexical quote warnings do not determine qualification fulfillment.

A later combined live check embedded the repaired certificate chunks in a new isolated database and evaluated English and Python/frameworks with four API requests. Score evidence was retrieved and valid Python/framework excerpts were returned, but additional nonverbatim citations caused strict validation to reject the final result. No paid retry occurred. Existing production vectors remain unchanged; position references and reviewable reporting were subsequently implemented as described below, while live-model line selection remains unverified. See [targeted check details](docs/architecture.md#111-consolidated-two-requirement-live-check).

Position-based citations and reviewable reporting are now implemented. Model citations contain only a source ID and inclusive, one-based line range; the application extracts the untouched original lines. Invalid references affect their requirement rather than aborting the whole result. Citation failures produce `unknown` with explicit review issues while retaining valid excerpts; narrow lexical coverage warnings remain advisory. Aggregate strengths, gaps, and recommendations are suppressed whenever review is required. `match_job(..., report_path=...)` optionally writes a Markdown report without overwriting files, and `python -m jobmatch.matching.report --input <result.json> --output <report.md>` renders existing results without API calls. Twenty-eight relevant offline checks passed, including two integrated report checks and adaptation of existing tests; a legacy-cache replay generated a review report. New live-model line selection has not been verified; the desktop prototype described below has offline integrated verification.

## Run the Desktop Prototype

The PySide6 desktop prototype connects explicit core/supplementary selection, editable JD confirmation, mandatory RAG, background matching, requirement-level evidence, review warnings, and local reports. Two integrated offscreen tests passed using synthetic documents, real temporary Chroma storage, and mocked APIs; twenty-six related backend checks also passed. Real GUI matching quality and complete MVP acceptance remain unverified.

Use the `jobmatch` Conda environment. PySide6 6.12.0 was installed there with user approval; the base environment was not changed. From the repository root in PowerShell:

```powershell
& 'E:\Anaconda\envs\jobmatch\python.exe' -m jobmatch
```

1. Place candidate files in `data/documents/`. Startup lists supported filenames only; it does not parse documents or call APIs.
2. Select at least one **core** document and one **supplementary** document. No files are selected automatically, and a file cannot serve both roles.
3. Paste the JD, or fetch an HTTPS job URL, then review/edit and confirm the text. Failed URL extraction preserves manual input.
4. Confirm transmission of selected material text and JD to the official OpenAI API, then start analysis. Configure `OPENAI_API_KEY` locally; never commit it. Calls incur costs, have no hard spending cap, and disable automatic SDK retries. The desktop client bypasses environment proxy settings.
5. Review each requirement, source lines, and any `unknown`/review warnings. Full reports are saved locally; Markdown export refuses to overwrite an existing file.

The selected supplementary corpus uses a reusable cache under `data/cache/desktop_evidence/`, keyed by paths, file hashes, and a parser revision marker. Unchanged files reuse embeddings; JD extraction, query embeddings, and matching still incur calls each run. The desktop workflow does not open or modify production `data/chroma` / `jobmatch_documents`. Results are written under `data/test_outputs/desktop_runs/`. Both locations are Git-ignored but may contain personal data; they are not encrypted or a version-recovery system.

Parsing and API work run in a background thread. Wait for an active task to finish before closing; cancellation is not implemented. PDF/image parsing can require locally cached parser assets. No standalone `.exe` has been built. The declared `jobmatch` launcher requires package installation/refresh; the module command above does not rely on it. Live GUI matching, five-version recovery, and Windows packaging remain planned.

## Implemented Features

### 1. Multi-Format Document Processing

Supported formats:

- PDF (`.pdf`)
- Word (`.docx`)
- Excel (`.xlsx`, `.xls`)
- Images (`.png`, `.jpg`, `.jpeg`)
- Plain text (`.txt`)
- Markdown (`.md`)

Docling is used as the primary layout-aware parser for supported documents, with format-specific extraction and fallback mechanisms where appropriate.

### 2. Document Chunking

Implemented capabilities include:

- Docling HybridChunker
- Text-based fallback chunking
- LangChain RecursiveCharacterTextSplitter
- Source filename and path tracking
- Chunk index metadata

Documents are converted into chunks for embedding and retrieval.

### 3. Persistent RAG Indexing

Implemented using:

- OpenAI Embeddings
- ChromaDB
- Persistent local vector storage
- File-hash-based change detection
- Incremental indexing
- Skipping unchanged documents
- Updating modified documents

The indexing pipeline supports processing multiple documents without rebuilding the complete index on every execution.

### 4. Job Description Processing

LLM-based structured job description extraction is implemented.

Extracted requirements include:

- Requirement description
- Requirement category
- Requirement priority (`required` or `preferred`)

The structured requirements serve as queries for candidate information retrieval.

### 5. Requirement-Based Retrieval

The retrieval system supports:

- Vector similarity search
- Source-aware candidate selection
- Maximal Marginal Relevance (MMR)
- CrossEncoder reranking
- Chunk-level semantic deduplication
- Source metadata tracking

These methods have been implemented or evaluated experimentally.

The current evidence selection pipeline remains under review due to redundancy and relevance limitations.

### 6. CrossEncoder Reranking

The project integrates:

`BAAI/bge-reranker-v2-m3`

CrossEncoder reranking evaluates the relevance between a job requirement and retrieved document chunks.

Integration testing confirmed that candidates can be reordered according to CrossEncoder scores.

However, reranking does not independently verify qualifications or resolve repeated underlying facts across different documents.

### 7. Experimental LLM Matching

An experimental matching analyzer uses structured LLM outputs to generate:

- Requirement-level matching judgments
- Matching explanations
- Supporting evidence references
- Candidate strengths
- Qualification gaps
- Overall matching summaries
- Application recommendations

The analyzer requires further revision to ensure that judgments are grounded in complete and reliable candidate information.

## Current Architecture

The existing pipeline consists of document indexing and requirement-based matching.

**Document Indexing**

Documents → Extraction → Chunking → OpenAI Embeddings → ChromaDB

**Job Analysis and Retrieval**

Job Description → LLM Requirement Extraction → Vector Retrieval → CrossEncoder Reranking → Evidence Selection

**Matching Analysis**

Confirmed JD + Structured Requirements + User-Selected Complete Core Text + Supplementary RAG → LLM Matching → Results with Resolved Citations

Some components are currently executed through development and integration tests rather than a completed standalone application.

## Retrieval Evaluation

Diagnostic experiments were conducted on November 3, 2026, using the existing local candidate document collection.

### Experiment 1: Document Inventory

The local dataset contained 11 documents and 89 indexed chunks.

| Document Category | Indexed Chunks |
|---|---:|
| Resumes and resume-related documents | 31 |
| Certificates and academic records | 43 |
| Career history | 12 |
| Test sample | 3 |
| **Total** | **89** |

**Findings**

- Multiple resumes in different languages and formats were indexed.
- Four major resume files accounted for 30 chunks.
- One academic transcript document generated 31 chunks.
- The inventory suggested potential document redundancy but did not establish that multilingual duplication was the primary retrieval problem.

### Experiment 2: Document Scope and Deduplication

Compared three retrieval configurations:

- **A — All Documents:** Retrieve from all indexed personal documents, excluding the known sample.
- **B — Curated Documents:** Restrict retrieval to a selected set of candidate documents.
- **C — Curated + Deduplication:** Apply the existing semantic deduplication method to curated retrieval results.

Requirements tested:

- R1: Master's degree
- R7: Problem-solving skills
- R8: English communication
- R15: Japanese culture, anime, or entertainment interest

**Findings**

- Restricting document versions did not consistently improve evidence quality.
- Removing certain resume sources sometimes increased the proportion of academic transcript chunks.
- Relevant career history information remained retrievable in the curated experiment.
- The current semantic deduplication function produced no changes to the final Top-5 results for these four requirements.
- Fact-level duplication could not be reliably addressed through chunk-level similarity checks alone.

**Conclusion:** Simple document filtering and semantic deduplication are insufficient to resolve the current evidence retrieval problems.

### Experiment 3: Retrieval Recall Comparison

Compared four strategies:

1. Vector Top-15 + CrossEncoder
2. Vector Top-30 + CrossEncoder
3. Source-balanced candidate selection
4. Document-category-routed candidate selection

Requirements tested:

- R1: Master's degree
- R8: English communication
- R15: Japanese culture, anime, or entertainment interest

**Findings**

- Expanding the candidate pool changed some reranked results.
- R1 produced identical final Top-5 results with Vector Top-15 and Top-30.
- R8 retrieved different TOEFL document chunks when the candidate pool increased.
- Source balancing did not consistently improve factual relevance.
- Experimental document-category routing could exclude important documents.
- R15 continued to return weakly relevant candidates despite having no identified direct supporting evidence.

**Conclusion:** Increasing Top-K, balancing sources, or routing document categories does not necessarily improve factual evidence quality.

### Experiment 4: TOEFL Document Information Loss

Investigated the retrieval results and original content of a TOEFL iBT score report.

The original PDF contained:

| Field | Original Document |
|---|---:|
| Total Score | 99/120 |
| Reading | 24 |
| Listening | 29 |
| Speaking | 23 |
| Writing | 23 |

However, the six indexed chunks contained general score-range explanations, administrative information, and candidate identification details without preserving these actual scores.

The information loss occurred somewhere between source document processing and the final indexed representation. The exact stage has not yet been isolated.

**Conclusion:** Retrieval and reranking cannot recover important facts that are absent from the index. Improving document preprocessing and information preservation is therefore a higher priority than additional similarity-based optimization.

## Architectural Findings

The experiments identified three main problem areas.

### 1. Document Representation

Multiple resume versions may describe the same underlying qualifications, while important information from complex PDF layouts may be absent from indexed content.

A document should not be considered successfully processed solely because text extraction and chunk generation completed without errors.

### 2. Retrieval and Evidence Quality

Vector similarity and CrossEncoder relevance scores do not establish whether a job requirement is satisfied.

The existing fixed Top-K selection can return irrelevant candidate chunks when no direct evidence is available.

Chunk-level semantic deduplication also does not reliably identify different descriptions of the same underlying experience.

### 3. Matching Reliability

Retrieved document chunks should be treated as candidate context rather than verified evidence.

Matching analysis must distinguish between:

- Directly supported qualifications
- Partially supported qualifications
- Explicitly unmet requirements
- Unknown or insufficiently documented qualifications

Repeated descriptions of the same experience should not be treated as independent evidence of multiple experiences.

## Architecture Reconsideration (November 5, 2026)

After the November 3 diagnostic experiments, a fact-only indexing direction was proposed. A later design review reconsidered whether enforcing structured fact extraction as the sole route into the knowledge base would repeat earlier multi-stage Profile pipeline problems, including information loss and unnecessary transformations.

**Accepted target direction: Full-Context + RAG Augmentation**

- Retain original candidate documents and traceable source references.
- When feasible within the model context budget, select complete, relevant core candidate materials for the main matching analysis instead of requiring everything to pass through a fact store.
- Keep RAG as a meaningful, mandatory supplementary retrieval path for requirement-specific evidence.
- Combine the original JD, structured requirements, selected core candidate context, and retrieved supporting evidence in matching analysis.
- Use lightweight document-specific preprocessing only where necessary to preserve important information (such as the missing TOEFL scores).
- Do not require an LLM-generated Candidate Profile or Fact Store as a prerequisite to access original source information.
- Preserve `matched`, `partial`, `missing`, and `unknown`, with explicit distinctions between absent evidence and evidence of unmet requirements.
- Avoid double-counting repeated descriptions of the same qualification across resume versions.

**Target flow (Python workflow and desktop prototype implemented; quality checks, GUI live validation, version recovery, and packaging remain incomplete):**

```text
Candidate Documents ──> Source Parsing / Quality Checks ──> Selected Complete Core Context ─┐
                    └─> Chunking / Embeddings / ChromaDB ──> Requirement-based RAG Evidence ─┤
JD Text / URL ──> User Confirmation ──> Structured JD Requirements ───────────────────────────┤
                                                                                                v
                                                                                  Evidence-aware LLM Matching
                                                                                                |
                                                                                                v
                                                                                   Results and Recommendations
```

The earlier November 3 fact-extraction-first proposal is retained in the development log as a historical design proposal, **not the current approved implementation mandate**. The exact selection and retrieval policy, context limits, performance, and privacy safeguards require implementation and testing.

### Immediate Development Direction

1. Inspect current code and confirm the actual interfaces before implementing a revised pipeline.
2. Prototype the Full-Context + RAG matching inputs with existing source material and retrieval interfaces.
3. Verify that the most important source facts survive parsing and reach the LLM context; test the TOEFL failure case.
4. Reassess evidence selection, duplicate qualifications, and unknown-versus-missing decisions.
5. Continue to a usable end-to-end MVP and standalone GUI before adding extensive infrastructure.
6. Defer optional local LLM provider work until the primary matching flow is functional.

## Development Principles

- Product-level requirements belong in `GOALS.md`; the accepted engineering direction and operating constraints are described in `AGENTS.md`.
- Treat the existing architecture as revisable during independent reviews, not as an immutable requirement.
- Keep real candidate documents and generated sensitive artifacts outside Git and explicitly review cloud-model transmissions.
- Separate implemented/verified features from approved but unimplemented designs.

## Technology Stack

- **Language:** Python 3.12
- **Data Validation:** Pydantic
- **LLM and Embeddings:** OpenAI API
- **Document Processing:** Docling
- **Text Chunking:** LangChain
- **Vector Database:** ChromaDB
- **Reranking:** Sentence Transformers
- **Machine Learning:** PyTorch, NumPy
- **Development Environment:** Windows 11, Conda, Visual Studio Code
- **Version Control:** Git and GitHub

## Development Tests

Representative test scripts include:

- `tests/test_chunking.py`
- `tests/test_multiformat_chunking.py`
- `tests/test_vector_search.py`
- `tests/test_multi_index.py`
- `tests/test_multi_retrieval.py`
- `tests/test_reranker.py`
- `tests/test_rerank_integration.py`
- `tests/test_document_scope.py`
- `tests/test_recall_diagnostics.py`

The diagnostic tests are designed to examine indexing, retrieval behavior, candidate redundancy, source distribution, and document information preservation.

Local experimental results are stored separately from source code.

## Current Limitations

- The PySide6 desktop prototype is implemented; live GUI matching and standalone Windows packaging remain unverified/unimplemented.
- Structured document preprocessing is not yet implemented.
- Some important information may be lost before indexing.
- Multiple document versions may create repeated factual content.
- Existing chunk-level deduplication does not reliably solve fact-level redundancy.
- Retrieval relevance scores do not independently establish evidence validity.
- The matching analyzer requires stronger factual grounding.
- Local LLM inference is not yet integrated.

## Next Development Priorities

1. Review the desktop prototype locally; perform a bounded real GUI scenario only after explicit data-transmission and cost authorization.
2. Verify live source-line selection and semantic support, including `unknown` / `missing` behavior; offline provenance checks do not establish qualification correctness.
3. Implement safe document updates and at least five recoverable historical versions as required by the MVP.
4. Improve demonstrated parsing/retrieval failures and multilingual duplication without mandatory intermediate LLM stages.
5. Package the Windows application and later integrate a replaceable LLM provider.

## Development Documentation

Detailed development history, experiments, and architecture decisions are documented in:

`develop_log/development-log.md`

Current module interfaces, target architecture, gaps, and risks are recorded in [docs/architecture.md](docs/architecture.md).

The focused offline checks can be run without paid API calls or production data access:

```powershell
conda run -n jobmatch python -B tests/test_full_context_matching.py -v
```

Do not use unrestricted test discovery: some older experimental files read private documents or call APIs at import time. The combined workflow itself does make cloud calls when invoked normally and may transmit selected candidate text; running the offline checks does not invoke that live processing.

## Privacy

Personal documents, local vector databases, extracted candidate information, and diagnostic outputs must be excluded from version control. The repository `.gitignore` and tracked-file status must be verified before any commit; this README does not verify the local Git state.

When OpenAI API processing is enabled, selected document text, embeddings input, or extracted information may be transmitted to the API. `.gitignore` does not prevent API transmission or Codex model context transfer.

API credentials and private candidate data must not be committed to public repositories.
