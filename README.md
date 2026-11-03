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

**Development Phase: RAG Evaluation and Architecture Revision**

The project currently includes working implementations of document parsing, chunking, persistent vector indexing, structured job requirement extraction, candidate information retrieval, CrossEncoder reranking, and experimental LLM-based matching.

These components have been implemented and tested individually or through integration experiments.

However, the complete application is not yet considered a reliable end-to-end MVP.

Retrieval experiments conducted on November 3, 2026, identified limitations in document information preservation, fact-level duplication, retrieval relevance, and evidence reliability.

The current development priority is introducing a lightweight document preprocessing and fact extraction stage before proceeding with the final matching workflow and graphical interface.

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

Structured Requirements + Retrieved Candidate Context → LLM Matching → Matching Results and Recommendations

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

## Planned Architecture Revision

The next development stage will introduce document preprocessing before retrieval.

**Document Processing**

Documents → Format Identification → Content Extraction → LLM Structured Fact Extraction → Source Validation → Cached Fact Records

**Knowledge Base**

Validated Fact Records → Embeddings → ChromaDB

**Job Matching**

Job Description → Structured Requirements → RAG Retrieval → Evidence-Aware LLM Matching → Recommendations

The planned approach will combine deterministic document processing with LLM-based semantic extraction.

### Design Principles

- Preserve original documents and their source references.
- Improve extraction of important facts from complex layouts.
- Represent qualifications as structured, retrievable information.
- Support multilingual documents and multiple resume versions.
- Identify repeated underlying facts without discarding useful source information.
- Cache document preprocessing results using file hashes.
- Avoid unnecessary multi-stage LLM pipelines.
- Keep the application architecture simple and practical.
- Prioritize factual reliability over similarity scores alone.

**Note:** Document preprocessing, structured fact indexing, and the revised matching pipeline are planned features and have not yet been implemented.

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

- The standalone GUI is not yet implemented.
- Structured document preprocessing is not yet implemented.
- Some important information may be lost before indexing.
- Multiple document versions may create repeated factual content.
- Existing chunk-level deduplication does not reliably solve fact-level redundancy.
- Retrieval relevance scores do not independently establish evidence validity.
- The matching analyzer requires stronger factual grounding.
- Local LLM inference is not yet integrated.

## Next Development Priorities

1. Implement lightweight document preprocessing.
2. Introduce LLM-based structured fact extraction.
3. Improve preservation of important information from complex PDF documents.
4. Add source verification and document-hash-based preprocessing caching.
5. Update indexing to support structured fact retrieval.
6. Revise evidence selection and LLM matching.
7. Develop the standalone graphical user interface.
8. Add an optional local LLM provider after the primary workflow is functional.

## Development Documentation

Detailed development history, experiments, and architecture decisions are documented in:

`develop_log/development-log.md`

## Privacy

Personal documents, local vector databases, extracted candidate information, and diagnostic outputs are excluded from version control.

When OpenAI API processing is enabled, selected document content or extracted information may be transmitted to the API.

API credentials and private candidate data must not be committed to public repositories.