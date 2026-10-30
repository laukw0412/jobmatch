# JobMatch

**JobMatch** is an AI-assisted job matching application that retrieves evidence from a candidate's documents and compares it with job descriptions to support informed application decisions.

The project is also a hands-on portfolio project focused on building a practical Retrieval-Augmented Generation (RAG) workflow, integrating LLM APIs, and learning software engineering through an end-to-end application.

## Project Goals

- Import multiple candidate documents (resumes, transcripts, certificates, research materials, etc.).
- Retrieve relevant evidence from those documents using semantic search.
- Analyze job descriptions and evaluate requirements against retrieved evidence.
- Present concise matching results, evidence, gaps, and actionable application recommendations.
- Provide a standalone desktop GUI in a later phase.
- Support additional JD input formats, such as PDF and URLs, later.
- Keep an interface that can accommodate a local LLM provider in the future.

## Architecture

The **current MVP direction is RAG-first**. A consolidated candidate Profile is *not* required before retrieval.

```text
Candidate documents (PDF / DOCX / XLSX / XLS / images / TXT / MD)
    -> Document parsing + Chunking
    -> OpenAI Embeddings
    -> Chroma (persistent vector collection)

Job description / query
    -> Query Embedding
    -> Chroma Top-K Retrieval
    -> Source-grounded chunks
    -> [Planned] JD requirement extraction + LLM matching
    -> [Planned] Match report and recommendations
```

### Document Processing and Chunking

- `src/jobmatch/document/` contains the existing document-loading utilities.
- `src/jobmatch/rag/chunking.py` provides `chunk_document()` and `chunk_plain_text()`.
- TXT and Markdown are read as text and split with LangChain's `RecursiveCharacterTextSplitter`.
- Legacy XLS is processed through the existing loader and the recursive text splitter.
- PDF, DOCX, XLSX, and image files are routed through Docling and `HybridChunker`, with a fallback to the existing loader and recursive splitter if Docling processing fails or produces no chunks.
- Chunk metadata includes a source filename, index, text, and chunking method.

Supported file extensions in the current chunker: `.pdf`, `.docx`, `.xlsx`, `.xls`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.md`. **Legacy `.doc` is not in the current chunker whitelist.** Format support does not guarantee perfect OCR or extraction for every document.

### Multi-Document Indexing

`src/jobmatch/rag/indexing.py` implements:

- `calculate_file_hash()` — SHA-256 content fingerprinting.
- `index_document()` — chunk, embed, and store one document.
- `index_directory()` — recursively index supported files from a directory.
- OpenAI `text-embedding-3-small` embeddings.
- A persistent Chroma collection for multiple files.
- Detection of unchanged files to skip unnecessary parsing and API calls.
- Replacement of the indexed chunks for a modified file.
- Source-path and content-hash metadata for indexed records.

Known MVP limitations: deleted source files are not automatically removed from the collection; indexing is not transactional; embedding requests are not yet batched for very large documents; and a change to the embedding model or chunking configuration does not automatically invalidate an unchanged file's stored index.

### Retrieval

Cross-document semantic retrieval has been tested using a query embedding and Chroma's vector search. Retrieved results include the source file, text, and vector distance. **Distance is not a matching percentage.**

A reusable `retrieve_chunks(query, top_k=5)` function has been drafted in `src/jobmatch/rag/retrieval.py`, but its standalone test result has not yet been confirmed. The immediate next task is to verify this reusable interface, then connect it to JD analysis.

## Previous Profile Experiments

The project previously explored a structured `ProfileContent` schema and an experimental pipeline:

```text
DocumentContent -> EvidenceSet -> MergedEvidenceSet -> ProfileContent
```

This approach was found to add repeated LLM transformations, latency, and risks of information loss, duplication, category drift, and multilingual inconsistencies. A simpler direct document-to-Profile extraction was also prototyped.

**Neither Profile consolidation nor the Evidence/Merge pipeline is a prerequisite for the current RAG MVP.** Existing Profile-related code is historical/experimental and may be revisited later for editable candidate information, version history, or GUI features.

## LLM Integration

- OpenAI API integration and structured-output experiments are already part of the project.
- Model configuration and API usage tracking are implemented under `src/jobmatch/llm/`.
- Usage tracking includes tokens and estimated cost where supported.
- The current indexing flow uses OpenAI Embeddings and reads credentials from the local environment / `.env` file.
- Local LLM integration is deferred until the main MVP works, with a provider abstraction planned for later.

## Development Status (October 30, 2026)

| Component | Status |
| --- | --- |
| Development environment and GitHub | Implemented |
| Multi-format document loading | Implemented; coverage varies by format |
| Recursive and Docling hybrid chunking | Implemented |
| OpenAI embeddings | Tested |
| Chroma multi-document indexing | Tested with two TXT files |
| SHA-256 unchanged-file skipping | Tested |
| Modified-file reindexing | Tested |
| Cross-document semantic retrieval | Tested with two TXT files |
| Reusable retrieval interface | Drafted; standalone test unconfirmed |
| JD requirement extraction | Planned next |
| Requirement-wise RAG + matching analysis | Planned |
| Matching report and recommendations | Planned |
| Standalone desktop GUI | Planned |
| Local LLM provider | Deferred |

### Recent Test Results

A two-file indexing test showed unchanged files being skipped and only the modified file being updated, with two stored chunks remaining. A retrieval query for computer vision and image generation ranked `research.txt` (distance `0.7455`) ahead of `skills.txt` (distance `1.4661`) and returned the updated research text.

These are small functional checks, **not** a comprehensive benchmark of retrieval accuracy or multi-format document quality.

## Project Structure (Relevant Components)

```text
jobmatch/
├── src/jobmatch/
│   ├── document/       # Document loading and extraction
│   ├── rag/
│   │   ├── chunking.py
│   │   ├── indexing.py
│   │   └── retrieval.py  # Drafted; test unconfirmed
│   ├── profile/        # Previous Profile experiments
│   ├── llm/            # LLM configuration and usage tracking
│   ├── matching/       # Planned JD matching logic
│   └── main.py
├── data/                # Local documents and vector data (do not commit private content)
├── docs/
│   └── development-log.md
├── tests/
│   ├── test_multi_index.py
│   └── test_multi_retrieval.py
├── pyproject.toml
├── README.md
└── .gitignore
```

The diagram summarizes relevant modules discussed during development; it is not intended as a verified inventory of every file in the local working tree.

## Next Steps

1. Run and verify `retrieve_chunks()` as a reusable module.
2. Implement a minimal JD requirement extractor.
3. Retrieve supporting candidate evidence separately for each requirement.
4. Use an LLM to produce evidence-based matching assessments that distinguish unmet requirements from insufficient evidence.
5. Add a compact matching report, then a standalone GUI.
6. Add larger-document batching, index lifecycle controls, improved source traceability, and local LLM support as follow-up improvements.

## Privacy

Candidate documents, vector databases, `.env` credentials, and local API-usage records should remain local and excluded from version control. Review `git status` before committing; do not publish private documents or API keys.
