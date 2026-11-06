# JobMatch Architecture

Last reviewed: November 6, 2026

## Scope and status terminology

JobMatch aims to provide a standalone Windows application for evidence-based candidate–job matching. Its product baseline is [GOALS.md](../GOALS.md): reusable candidate documents, a confirmable JD, requirement-level evidence and uncertainty, recommendations, explicit document-read failures, manual JD fallback, and recovery of at least five prior profile/document versions.

This document describes the current source and the accepted development direction. A minimal Full-Context + RAG function workflow now has offline mocked verification; the complete application has not been validated with real documents, production retrieval, or live LLM calls.

- **Implemented:** present in source code; not necessarily executed or validated during this review.
- **Experimentally verified (historical):** execution or observations reported in the development log or README; not independently reproduced here.
- **Planned / accepted target:** approved direction or product requirement that is not fully implemented.
- **Proposed:** an option requiring evaluation or approval, not a completed feature or mandatory design.

Sources are [AGENTS.md](../AGENTS.md), [README.md](../README.md), [development-log.md](../develop_log/development-log.md), and the source/test files linked below. Code determines implemented behavior; the latest accepted decision determines the target. Verification evolved from mocked boundaries to temporary real Chroma and, with separate authorization, bounded real scenarios recorded below. The latest desktop milestone used only synthetic documents and mocked APIs; no real candidate data or production storage was accessed in that milestone.

## 1. Implemented Architecture

### 1.1 Current data flows

```text
Indexing:
caller-selected directory
  -> index_directory()
  -> file hashing / unchanged-file check
  -> chunk_document()
  -> OpenAI embeddings
  -> persistent Chroma chunks and metadata

Matching experiments:
JD text or URL
  -> URL text extraction when needed
  -> external text-file review and terminal confirmation in a test script
  -> extract_job_description()
  -> JobDescription / JobRequirement
  -> retrieve_job_requirements()
  -> retrieve_chunks() for each requirement
  -> evidence selection
  -> analyze_matches()
  -> MatchingResult

Minimal combined workflow (implemented, offline verification only):
confirmed JD text + explicitly selected core document paths
  -> match_job()
  -> load_core_documents() from data/documents/
  -> structured JD extraction
  -> mandatory requirement RAG excluding selected core paths
  -> analyze_matches(core_documents, confirmed_jd_text, requirement_evidence)
  -> MatchingResult with resolved source text and quotes
```

`matching/workflow.py` connects the combined function workflow. It expects already confirmed JD text; callers remain responsible for confirmation and authorization for API transmission. It does not index documents and optionally saves a report through `report_path`. Older experiments still use intermediate JSON files. Desktop orchestration now connects these backend components to a GUI, as described below.

### 1.2 Document parsing and chunking

| Source | Actual interface and responsibility |
|---|---|
| [document/models.py](../src/jobmatch/document/models.py) | `DocumentContent` contains `source_file`, `file_type`, and `text` |
| [document/loader.py](../src/jobmatch/document/loader.py) | `load_document(file_path)` dispatches PDF, DOCX, XLSX, XLS, and PNG/JPG/JPEG; unsupported extensions raise an error |
| [document/extraction.py](../src/jobmatch/document/extraction.py) | PDF/DOCX use Docling first; PDF fallback uses PyMuPDF and OCR for pages without text; DOCX fallback reads paragraphs; spreadsheets use openpyxl/xlrd; images use Tesseract |
| [rag/chunking.py](../src/jobmatch/rag/chunking.py) | `chunk_document(file_path)` supports all the above plus TXT/Markdown; `chunk_plain_text(text, source_file, max_chars=1500)` uses a recursive text splitter |

TXT/Markdown are read directly by the chunking entry point, not by `load_document()`. XLS uses the loader and text splitter. Other supported formats first attempt Docling conversion and `HybridChunker`; failure or no chunks triggers loader-based fallback.

For complete-document PDF/DOCX extraction, [document/markdown.py](../src/jobmatch/document/markdown.py) now provides `export_markdown(document)`. It creates export-only table copies, keeps each spanned cell's text at its origin, and leaves covered Markdown grid positions empty. Source cell objects and their spans remain unchanged. Compact table formatting removes padding. This is span-aware rendering, not general text deduplication: distinct cells with identical text remain distinct. This merged-cell correction does not alter HybridChunker's table serialization; the later picture-traversal update is described below. Existing vectors have not been rebuilt.

The later picture-text preservation repair also enables `traverse_pictures=True` for complete export. `PictureTextSerializerProvider` in `rag/chunking.py` sets the same option in a fresh Docling chunking serializer. It retains the existing HybridChunker/table behavior while including recognized figure text. This corrects a demonstrated traversal omission; it does not add OCR, an external extraction call, a Fact Store, or invented score facts. Existing vector collections remain unchanged.

Chunk dictionaries contain `chunk_id`, `source_file`, `chunk_index`, `text`, and `method`. This representation does not expose a general page/bounding-box citation interface. Parsing success is not a guarantee of factual completeness.

[document/context.py](../src/jobmatch/document/context.py) adds `load_core_documents(file_paths, max_chars=60000)`. Only explicitly selected files are read, duplicate resolved paths are skipped, and resolved paths must stay inside the repository's `data/documents/`. TXT/Markdown are read directly; other formats reuse `load_document()`. `CoreDocument` retains the filename, resolved path, and complete parsed text. Empty, unreadable, missing, and over-budget input raises an error; there is no automatic selection, summarization, or truncation.

### 1.3 Persistent indexing and retrieval

[rag/indexing.py](../src/jobmatch/rag/indexing.py) implements:

- `calculate_file_hash(file_path)`: SHA-256 content hashing.
- `index_document(file_path, collection, client)`: skips unchanged files, chunks changed files, generates embeddings, and replaces their stored chunks.
- `index_directory(directory, chroma_path=CHROMA_PATH)`: recursively processes supported files and returns counts for `indexed`, `updated`, `skipped`, `empty`, and `failed`; errors are printed per file.

Defaults are `data/chroma`, collection `jobmatch_documents`, and embedding model `text-embedding-3-small`. Real candidate input is restricted by repository policy to `data/documents/`; the function itself accepts arbitrary directories. Metadata includes filename, resolved source path, file hash, chunk index, and chunking method. Stored IDs derive from the source path and chunk index.

Embeddings are generated before old chunks are deleted, but deletion and upsert are separate operations. There is no implemented rollback or historical-version recovery. Directory indexing also does not synchronize removal of deleted source files. An empty reprocessed document returns `empty` without replacing existing chunks.

[rag/retrieval.py](../src/jobmatch/rag/retrieval.py) exposes `retrieve_chunks(query, top_k=5, include_embeddings=False, excluded_source_paths=None, chroma_path=CHROMA_PATH, collection_name=COLLECTION_NAME, included_source_paths=None)`. It embeds a query, queries the selected existing collection, and returns text, source filename/path, chunk index, and distance. Core exclusions and an optional source allowlist are applied before Top-K selection. An explicitly empty allowlist returns no results without opening storage or calling an API. Collection lookup now uses `get_collection()` rather than creating a missing collection. However, constructing a persistent client can still initialize or modify database files; experiments must use isolated storage. Optional stored embeddings and query cosine similarity support evidence selection. Parsing dependencies load only when indexing is invoked.

### 1.4 JD acquisition and structure

[jobs/web_extractor.py](../src/jobmatch/jobs/web_extractor.py) exposes `extract_job_text_from_url(url)`. It validates HTTPS URLs, attempts Requests plus Trafilatura, and falls back to Playwright-rendered content. Length, job markers, and blocking markers provide basic checks. Failure raises an error asking for manual pasted text. This is a failure message, not a complete manual-entry UI.

[jobs/extractor.py](../src/jobmatch/jobs/extractor.py) exposes `extract_job_description(jd_text, model="gpt-4.1-mini")`, calling OpenAI structured chat output. [jobs/models.py](../src/jobmatch/jobs/models.py) defines:

- `JobDescription`: title, company, location, responsibilities, and requirements.
- `JobRequirement`: description, category, and `required`/`preferred` priority.

[test_job_extraction.py](../tests/test_job_extraction.py) provides an experimental confirmation workflow: save or load JD text, ask the user to review/edit the file, request terminal confirmation, reload the text, and then extract requirements. It is not a GUI, and confirmation is not enforced across every possible caller. No completed JD file-upload pipeline is present.

### 1.5 Requirement retrieval and matching

[matching/retriever.py](../src/jobmatch/matching/retriever.py) implements:

- `retrieve_job_requirements(job, top_k=5, candidate_multiplier=3, strategy="source", lambda_mult=0.7, excluded_files=None, excluded_source_paths=None, chroma_path=CHROMA_PATH, collection_name=COLLECTION_NAME, included_source_paths=None)`.
- `select_evidence(chunks, top_k=5, strategy="source", lambda_mult=0.7, query=None)`.
- `is_duplicate(candidate, selected)` for normalized exact matches and conservative embedding-based duplicates with matching extracted number sequences.

Each requirement description becomes a query. Source-path exclusions are applied inside the database query; excluded filenames are filtered afterward. Evidence is selected by source diversity, MMR, or reranking. The combined workflow excludes its core paths so supplementary materials can occupy retrieval slots. The default filename exclusion covers one known sample, not a general production/test-data boundary. Selection does not establish a factual relevance threshold or guarantee support. Embedding vectors are removed before evidence is passed onward.

[matching/reranker.py](../src/jobmatch/matching/reranker.py) lazily caches a `BAAI/bge-reranker-v2-m3` CrossEncoder, selects CUDA when available, and reorders query/chunk pairs by score. Its module is now imported only for the reranking strategy. Relevance scores are not qualification judgments.

[matching/analyzer.py](../src/jobmatch/matching/analyzer.py) exposes `analyze_matches(requirement_evidence, model="gpt-4.1-mini", *, core_documents=None, confirmed_jd_text="", max_input_chars=60000)`. It sends complete selected core text once as numbered lines, confirmed JD text, and per-requirement RAG evidence in the same form. Joining each source's supplied lines reproduces its original text; there is no summarization or truncation. Core IDs (`core:N`) are available to all requirements; RAG IDs (`rag:REQUIREMENT_ID:N`) remain requirement-local. Model output now requests source IDs and line ranges only; trusted metadata and quote text are resolved locally. The RAG-only function call remains supported, but new model responses use the line-reference schema rather than the old quote schema.

[matching/models.py](../src/jobmatch/matching/models.py) defines citation models, `RequirementMatch`, and `MatchingResult`: requirement judgments and reasons, resolved `supporting_evidence`, legacy RAG-only indices, summary, strengths, gaps, recommendation, and validation warnings. Every resolved citation retains source type, ID, filename, path when available, source text, exact quote, and optional chunk index. The four statuses are:

- `matched`: direct support for all essential parts.
- `partial`: direct support for some essential parts.
- `missing`: direct evidence of non-fulfillment.
- `unknown`: insufficient evidence to determine fulfillment.

The analyzer checks requirement coverage, source IDs, RAG requirement scope, inclusive line bounds, and nonempty selected text. Exact quote strings are sliced from unchanged source lines, not copied or normalized from model output. Unknown sources, cross-requirement references, invalid ranges, and unsupported uncited judgments become requirement-level review issues. Affected judgments become `unknown`, with the original model status/reason recorded separately and valid excerpts retained for inspection. Other requirements remain available. Narrow excerpt-coverage warnings mark review without mechanically changing a qualification status. Duplicate/missing requirement rows or a missing parsed response still fail the analysis because they violate the overall response contract. These checks establish provenance, not semantic entailment.

The character guard checks the serialized matching payload plus system prompt before the matching API call. It is not token counting or a guaranteed model context limit and does not include output-token budgeting. The workflow checks raw JD/core size before any API calls, but expanded requirements and retrieval may push the final payload over the cap after those earlier API calls. The caller must reduce inputs or explicitly raise the cap; nothing is silently truncated.

`match_job()` also accepts `chroma_path`, `collection_name`, and optional `supplementary_document_paths`, passing the selected storage and resolved source allowlist into retrieval. Defaults preserve existing production locations; scenario callers must explicitly select isolated storage. An optional `report_path` writes a local Markdown result and rejects an already existing destination before initiating paid work.

### 1.6 LLM integration, legacy modules, and application shell

OpenAI clients are constructed directly in default indexing, retrieval, JD extraction, matching, and legacy Profile operations. Retrieval, JD extraction, and matching also accept an optional shared client for desktop orchestration and offline verification. A replaceable provider interface is not implemented. [llm/config.py](../src/jobmatch/llm/config.py) configures legacy Profile model selection; JD extraction and matching have their own defaults. [llm/openai_usage.py](../src/jobmatch/llm/openai_usage.py) contains legacy cost tracking, not a verified current pricing source or integrated desktop budget mechanism.

The retained [profile/](../src/jobmatch/profile/) code includes evidence extraction, merge, Profile generation, models, and loading/validation. These are historical experiments, not mandatory matching stages. Legacy validation imports `src.jobmatch.profile.schema`, which is absent from the inspected source tree; this path should not be assumed runnable.

[main.py](../src/jobmatch/main.py) now lazily launches the PySide6 desktop prototype; `python -m jobmatch` uses [__main__.py](../src/jobmatch/__main__.py). The old hard-coded private-document parsing demonstration was removed. `recommendations/` and `enrichment/` remain package placeholders; recommendation text comes from the matching analyzer. The GUI is runnable from Python, not a packaged standalone Windows executable.

### 1.6.1 Desktop orchestration (implemented, offline integrated verification)

[ui/app.py](../src/jobmatch/ui/app.py) provides `MainWindow`, background `TaskThread`, and a text-only report browser. Startup scans supported filenames under `data/documents/` without parsing content, opening Chroma, or calling APIs. Core and supplementary roles are explicit and mutually exclusive per file. JD editing resets confirmation and transmission consent; document/model changes reset consent. URL extraction runs in the background, and failures retain manual JD input. Requirement results expose exact source lines, uncertainty, and review warnings. Report rendering blocks embedded resources and links, and export refuses overwrites.

[ui/service.py](../src/jobmatch/ui/service.py) defines immutable `AnalysisRequest`, `DesktopResult`, `validate_request()`, and `run_analysis(request, progress, ...)`. It validates selected files and consent, loads complete selected core text, checks a preliminary character budget, indexes only selected supplements into a separate reusable cache, extracts JD requirements, performs mandatory per-requirement RAG, calls combined matching, and saves JSON/Markdown. The analyzer still enforces the final serialized-input budget. An early core/JD check does not guarantee that later retrieved evidence fits; failure may occur after earlier paid steps.

The cache is `data/cache/desktop_evidence/<corpus-hash>/chroma`, using collection `jobmatch_desktop_evidence`; its key includes selected source paths, file hashes, and `CACHE_VERSION`. Unchanged supplements reuse embeddings. This desktop path does not access production storage. Each run creates a new directory under `data/test_outputs/desktop_runs/`. Cache and outputs are ignored, potentially sensitive local data; they are not five-version recovery or encrypted storage. Older corpus caches have no automatic cleanup.

One shared OpenAI client uses the official endpoint, `max_retries=0`, a 60-second request timeout, and `trust_env=False`; structured chat calls set `store=False`, which is not a claim of zero provider retention. The UI explicitly requires transmission/cost consent, but has no hard spending cap, complete usage display, or cancellation. Closing during a task waits for completion. Document errors identify the selected filename without displaying raw API error bodies. Parser assets may require downloads when absent locally.

Two synthetic offscreen GUI tests passed with real temporary Chroma, actual TXT processing, mocked API responses, and blocked Python socket connections. They cover background responsiveness, cached embedding reuse, source-line display, invalid citations becoming `unknown`, suppression of unsafe aggregates, sanitized failures, and URL fallback. Screenshots were reviewed for Chinese rendering and evidence display. Twenty-six related backend regressions also passed (17 context/workflow, 3 runner, 4 retrieval/storage, 2 reports). No real candidate documents, production records, or paid APIs were used for this desktop milestone. Real GUI matching, parser performance across all formats, live line selection, packaged distribution, and recovery remain unverified or planned.

### 1.7 Verification evidence and its limits

The development log reports historical experiments for multiformat chunking and vector search (October 29), incremental indexing and cross-document retrieval (October 30), and web JD extraction and requirement retrieval (November 2). README also reports successful reranking integration and experimental matching. November 3 diagnostics found weak evidence, duplicate content, and missing information in indexed representations. These reports are historical evidence, not newly executed checks or proof of end-to-end reliability.

Most files under `tests/` are manual experiments or diagnostics rather than isolated assertion-based unit tests. Some legacy files perform document reads and paid calls at import time. Test collection is therefore not assumed safe. `test_multi_index.py` calls `index_directory(test_dir)` without overriding production storage: running it would index test documents into the production collection and violates the current repository safeguard. It must use isolated storage before future execution.

[test_full_context_matching.py](../tests/test_full_context_matching.py) adds focused standard-library `unittest` checks. Seventeen offline tests passed in the `jobmatch` environment on November 6: selected text loading, combined inputs, source/quote validation, unknown handling, budget rejection, mandatory retrieval wiring, and query-filter propagation. OpenAI and Chroma were mocked; real parser quality, Chroma filtering behavior, and live model judgments remain unverified. Run only this focused file, not unrestricted test discovery.

A subsequent user-authorized local smoke check used [validate_core_documents.py](../tests/validate_core_documents.py) on two explicitly selected real PDFs. Both parsed through Docling, with no numeric-token omissions detected against native PDF text; initial word differences were recoverable after formatting normalization. This is a heuristic comparison, not semantic completeness validation. The English resume's longer parsed representation remains a manual-review item. Sensitive outputs stayed in ignored local storage; Python network calls were blocked during parsing, with no attempts observed. No production database or live matching was exercised.

Follow-up local inspection resolved the English resume expansion: its native text has 2,297 characters and its original Markdown export 4,445. Three cells spanning two columns were repeated in both grid positions during Markdown serialization. The repeated text added 360 characters (302 word characters); the remaining net increase of 1,788 characters was formatting. Re-conversion reproduced the cached Markdown exactly, and the two positions were verified to reference the same cell object with `col_span=2`.

The targeted span-aware export correction is now implemented. Six synthetic regression tests passed, including row/column spans, preservation of legitimate repeated values, source immutability, numeric precision, and pipe escaping. The original seventeen offline matching checks also passed. A network-blocked rerun of the authorized English resume through the actual loader produced 2,372 characters; the three affected passages each occur once, normalized word-character counts and multisets match native text, and no numeric-token omissions were detected. This does not establish semantic order, validate other formats, or correct production RAG chunks. Private rerun artifacts remain in ignored local storage.

### 1.8 Bounded real-scenario attempt

[validate_real_matching.py](../tests/validate_real_matching.py) prepares explicitly selected source text offline and supports one separately authorized live attempt. The pilot uses six requirement groups from the confirmed Sony JD, two selected complete core PDFs, and chunks from only the English/Japanese certificates. It reuses extraction, requirement retrieval, and matching functions rather than exercising the GUI or the complete `match_job()` entry point. A new database under ignored `data/test_outputs/scenario_validation/` avoids production access. Its guard allows at most nine API requests, limits each chat output to 4,096 tokens, uses a conservative USD 0.10 reservation check, disables SDK retries, and retains a run marker to prevent accidental paid reruns. This is not a provider-enforced billing cap.

Three offline source-scope checks passed, including a real in-memory Chroma query. Two runner checks also passed after correcting an erroneous test expectation about repeated client construction. Together with the seventeen matching and six export checks, 28 focused offline tests passed. The runner test replaced the persistent-client constructor and did not cover persistent-client settings identity.

The authorized November 6 live attempt stopped after two successful API requests: embedding eleven certificate chunks and extracting sixteen JD requirements. The pilot selected six requirements, but before query embedding or retrieval, Chroma rejected reopening the same isolated path with different settings. The runner created its client with `anonymized_telemetry=False`; retrieval created another client with defaults (`True`). Installed Chroma requires settings equality for clients sharing a persistent path. No matching result was generated and no retry occurred. Usage-based estimated cost was USD 0.00146452; this is not an invoice. Core text was not transmitted in this attempt. Certificate text and JD text were transmitted under the user's explicit authorization.

The local preparation also reproduced the historical English-score issue: native PDF text contained the previously documented score values, but Docling complete text and its six HybridChunker outputs did not retain the full set. This lexical check does not establish label/value associations, but places the loss before final matching. No scores were inserted or parser fixes added as part of this pilot. Both core PDFs had matching normalized word-character multisets and no detected native-number omissions, which still does not prove semantic associations or current qualification status.

That first attempt stopped as authorized, without an automatic retry. The subsequent user-selected continuation is recorded below.

### 1.9 Consistent storage clients and verified continuation

[rag/storage.py](../src/jobmatch/rag/storage.py) now provides `create_chroma_client(path)`, constructing fresh settings with anonymized telemetry disabled for each client. Indexing, retrieval, and the validation runner share this function. Retrieval closes its own client after database operations. This avoids the demonstrated same-path settings conflict; it does not normalize arbitrary third-party client settings or guarantee compatibility with clients constructed outside this helper.

The regression suite now uses real temporary persistent databases, not a mocked Chroma constructor, for concurrent open/query/close/reopen and the synthetic full runner. The first revised runner test exposed an obsolete mock that reused one client and therefore closed it prematurely; replacing that mock with actual persistent clients resolved the test issue. Thirty focused offline checks passed: seventeen matching, six export, four retrieval-scope, and three runner checks. The continuation test verifies cached reuse, preserved failure artifacts, seven new simulated requests, and refusal of duplicate execution.

The runner adds offline `inspect-resume` and an explicit `resume` mode. It checks prepared/source hashes, cached certificate documents and metadata, and selected requirements against the successful JD response. Continuation requires the known two-request stopping point, never recreates a missing cache, uses a new `continuation/` output directory, and retains the original failure and usage records. Original call reservations count toward the same nine-request / USD 0.10 guard. The telemetry-free client check opened only the authorized isolated database.

After the user selected the continuation scope, one live resume completed on November 6 within the previously explicitly authorized data scope and cumulative limits. It reused eleven certificate vectors and six selected requirements. Six new query-embedding requests and one matching request succeeded, without repeating document embeddings or JD extraction. The six assessments were master's degree `partial`, Python/frameworks `matched`, English `matched`, Japanese `matched`, publication record `unknown`, and distributed/cloud training `unknown`. Six resolved citations came from core text and one from retrieved N1 evidence. All cited paths were approved and quotes occurred in their source text; no analyzer validation warnings were produced.

This establishes a bounded real retrieval-plus-matching flow for selected requirements, not full product acceptance. The English assessment relies on core sources and does not resolve certificate score loss. The Python/framework assessment's selected excerpts show framework use but omit explicit Python wording even though both complete core sources contain it; quote coverage remains an improvement item. Citation validity does not prove semantic entailment, current degree status, or the correctness of every generated recommendation. Unknown judgments are not confirmed qualification gaps.

New usage-based estimated cost was USD 0.00379268, cumulative USD 0.00525720 including the first attempt; actual invoices were not inspected. The core and retrieved text was transmitted only within the authorized official API workflow; original files were not uploaded. All private reports remain in ignored local storage. No production data, vector rebuild, additional parser repair, or further paid run was performed. The requested continuation stopping point has been reached.

### 1.10 Offline score-text and citation-excerpt repair

The user selected scope B: repair and locally verify score preservation and excerpt coverage, then stop without paid calls or production mutation. Inspection of the selected English certificate established that the missing values already existed in Docling's structured text, under `PictureItem` parents. Default Markdown and chunk serialization skipped those descendants. Export with picture traversal recovered the full set; an additional parser, native-text fallback, or LLM fact extraction was unnecessary.

The production extraction and chunking paths now include recognized picture descendants. A network-blocked local check found the total and all four section label/value combinations in complete text and in individual chunks. The certificate produced eight hybrid chunks. The test compared specific label/value spans against the retained structure, not merely the presence of numbers. This establishes preservation for the observed case, not general OCR accuracy or correct interpretation of every score/date type. Earlier private outputs and vector collections were not overwritten.

Matching instructions now require quoted passages to cover essential AND conditions, allow multiple noncontiguous quotes from the same source, and require one applicable OR alternative. Exact-quote, source, and requirement-scope validation remains in place. `quote_coverage_warnings()` is a deliberately narrow advisory check for the observed English Python-and-framework pattern; it can flag omitted Python or requested-framework wording. It does not parse arbitrary requirements, establish semantic support, or change statuses. Multiple framework names connected by AND are outside that narrow check. On the cached six-requirement result, it flagged only the known Python excerpt gap without calling an API or altering the old result.

Forty focused offline tests passed, including four picture-text and six citation-coverage cases in addition to the existing thirty checks. The new cases use synthetic data, a local tokenizer, and mocked LLM responses. Live LLM adherence to the revised instructions and retrieval over refreshed embeddings remain unverified. Existing hash-based indexing may skip unchanged files even after parser behavior changes; updating old stored vectors requires a separately authorized refresh. Including previously skipped picture text can also expose more source information to future cloud matching, so authorized transmission scope must be reviewed for any new live run.

### 1.11 Consolidated two-requirement live check

The user selected a targeted live check and requested fewer small tests and faster product progress. One combined run reused confirmed core text and JD, embedded the eight repaired English-certificate chunks in a new isolated database, issued two requirement queries, and made one matching request. No additional unit-test suite or application changes were introduced for this run; its one-off driver and sensitive artifacts remain in ignored local storage.

All four API requests succeeded, with usage-based estimated cost USD 0.00306172. Retrieved English evidence contained the total and four section score-label/value combinations. The Python/framework response included two valid verbatim passages that together explicitly mention Python and a requested framework. However, two additional model citations failed strict source checks: one core quote matched only after removing punctuation/case differences, and one retrieved certificate quote did not match even after whitespace, Unicode, punctuation, and case normalization. Analyzer validation stopped at the first invalid quote, so no validated `MatchingResult` was returned. Raw model judgments must not be presented as accepted results.

This live run verifies refreshed score retrieval and demonstrates improved excerpt coverage, but not reliable verbatim quoting or a successful final report. An initial total-score diagnostic regex assumed a particular scale order and missed a valid total-score sentence; local inspection corrected that diagnostic without changing retrieval output. No paid retry, production index update, new document parsing, or automatic quotation repair followed. A source-position-based quotation mechanism and user-reviewable report handling are proposed next, not implemented by this validation.

### 1.12 Position citations and reviewable local reports

The user subsequently authorized implementing position references, local failure handling, and report presentation together. `EvidenceReference` contains `evidence_id`, `start_line`, and `end_line`; the model no longer supplies quote text. Source-local line numbers are one-based and inclusive, refer to the supplied parsed-text snapshot or RAG chunk, and are not PDF page coordinates. `SupportingEvidence` retains original text/file metadata plus the resolved line positions and exact extracted quote. Existing stored result JSON without line fields can still load through defaulted output fields; old raw model responses require an explicitly identified offline adaptation and are not accepted as new line-reference responses.

`prepare_matching_input()` builds the numbered payload and untouched local source registry. `resolve_matching_result()` checks and resolves references without a model call. Invalid citations are recorded in `CitationIssue`; corresponding requirements become `unknown` with `review_required`, while valid excerpts survive for inspection and unrelated results remain unchanged. These review excerpts are not evidence that an unknown requirement is fulfilled. Lexical Python/framework warnings remain advisory but mark the result for review. A result requiring review uses a deterministic cautious summary, clears aggregate strengths/gaps, and substitutes a review recommendation, rather than forwarding the original model aggregates.

[matching/report.py](../src/jobmatch/matching/report.py) renders readable Markdown, displays effective status separately from an unconfirmed model proposal, lists issues and source/line references, and fences excerpts verbatim. It independently suppresses aggregate claims when review flags or validation warnings exist. The writer uses UTF-8 without newline translation and exclusive creation; an existing report is never overwritten. The module CLI accepts `--input`/`--output` and performs no database/API operation. `match_job(..., report_path=...)` integrates the writer; no GUI was added.

Twenty-eight relevant offline tests passed: seventeen existing context/workflow checks, six coverage checks, three runner checks, and two new integrated range/report checks. The new tests cover preserved CRLF/spacing, multiple ranges, mixed valid and invalid references, source scope, empty/reversed/out-of-bounds ranges, missing citations, unaffected requirements, safe aggregate handling, and file overwrite refusal. The first file-level test exposed Windows newline translation; disabling translation fixed that implementation issue. Unrelated parser/storage tests were not rerun for this matching/report change.

A local replay adapted the prior rejected quote response: only exact old quotes were mapped to source line ranges; unresolvable quotes were represented by invalid ranges, not fuzzily repaired. It produced a readable review report, retained two valid excerpts, and withheld both affected model judgments and aggregate claims. This is an offline compatibility replay, not evidence that a live model selected the new line ranges. No API call, original-document read, production database operation, dependency change, or index refresh occurred in this implementation task. Correct line references still cannot prove semantic support, and live response-schema adherence remains to be verified.

## 2. Accepted Target Architecture

**Status: approved direction from November 5, refined by user instruction on November 6; a minimal function workflow is implemented with offline mocked verification, not live end-to-end validation.**

```text
Candidate documents -> parsing and quality checks -> selected complete core context --+
                    -> chunking / embeddings / Chroma -> requirement RAG evidence ---+
JD text or URL -> user review and correction -> confirmed JD + structured requirements-+
                                                                                    |
                                                                                    v
                                                               evidence-aware matching
                                                                                    |
                                                                                    v
                                                          results, sources, recommendations
```

The arrows describe target responsibilities, not new existing modules or agreed function signatures.

- Provide selected complete, relevant core materials when feasible within context limits. Full context does not mean sending every file without selection.
- For the MVP, the user selects core files such as one resume and one career history. Automatic document selection is deferred; RAG retrieves other supplementary material. Both core and RAG evidence must retain file provenance and corresponding text.
- Keep meaningful requirement-specific Chroma retrieval mandatory as supplementary evidence.
- Combine confirmed original JD, structured requirements, core context, and retrieved evidence in the main analysis.
- Preserve original information and traceable sources; a generated Candidate Profile or Fact Store is not a prerequisite.
- Preserve all four match states, distinguish research from professional experience, and avoid counting repeated multilingual descriptions as separate qualifications.
- Evaluate lightweight preprocessing only for demonstrated information-preservation failures. Mandatory extraction/merge/judge stages are not part of the accepted direction.

The product also requires user-facing JD confirmation, manual text entry, readable results, explicit read failures, Windows GUI delivery, document updates, and at least five recoverable prior versions. The PySide6 prototype now provides selection, confirmation, read failures, and results; packaged delivery and recoverable versions remain planned, along with provider replacement and local inference.

## 3. Architecture Gaps

| Gap | Existing basis | Still required / status |
|---|---|---|
| Complete core context | Explicit selection, full parsed text, file sources, and character cap implemented | User-facing selection is implemented; broader real-format completeness remains unverified. Automatic selection is deferred |
| Combined matching input | `match_job()` connects confirmed JD, core context, and mandatory supplementary RAG | Bounded historical live checks and a desktop prototype exist; live GUI matching with position references remains unverified |
| Information preservation | Parsers and fallback chunking | Validate important source facts through parsing, chunking, and final model input; target specific failures rather than impose a Fact Store |
| Evidence quality | Selection, reranking, citation checks | Validate factual support, unsupported requirements, duplicate qualifications, and summary consistency; selection/abstention policy remains undecided |
| Traceable reports | Both source types resolve to file metadata, text, and checked quotes | Markdown and desktop evidence display implemented; page-level references and version-aware citations remain absent |
| User workflow | Runnable PySide6 selection, JD review/fallback, background matching, and evidence/report display | Authorized real GUI validation, usability review, and packaged Windows delivery |
| Updates and recovery | Hash-based replacement | Implement at least five recoverable historical versions and safe update/recovery behavior; incremental indexing alone is insufficient |
| Failure reporting | Exceptions and printed indexing failures | Desktop names failed selected files; semantic detection of incomplete extraction remains incomplete |
| Provider and cost control | Direct OpenAI calls, legacy usage helper | Future provider replacement; consistent usage visibility and transmission control are not connected to the current matching workflow |
| Safe verification | Seventeen isolated offline checks plus older experimental scripts | Repair older unsafe experiments before running them; verify actual database/provider integration only with authorization |

**Proposed next milestone:** review the runnable desktop prototype, then validate one bounded real GUI scenario with explicit authorization. Safe updates and at least five recoverable versions remain a separate required milestone. Offline checks do not authorize personal-data transmission or production migrations.

## 4. Historical Decisions

| Period | Approach and outcome |
|---|---|
| August 2026 | `DocumentContent -> EvidenceSet -> MergedEvidenceSet -> ProfileContent` experiments sought consolidation and provenance. The August 24 review recorded repeated transformations, information loss, category drift, duplication, latency, and cost. A simpler direct multi-document extraction alternative was proposed; it is not the current required gateway |
| October 29–30, 2026 | RAG-first MVP direction made original documents and metadata primary sources, removed Profile generation as a prerequisite, and added chunking, persistent indexing, and retrieval experiments |
| November 2, 2026 | JD acquisition and requirement retrieval were connected experimentally; user confirmation was added to the text-file/terminal workflow because extraction success did not establish JD completeness |
| November 3, 2026 | Diagnostics showed that source filtering, larger candidate pools, routing, and chunk deduplication did not consistently improve factual evidence. A TOEFL information-loss case motivated a preprocessing/fact-index proposal; the loss stage remained unresolved |
| November 5, 2026 | Full-Context + RAG Augmentation replaced the fact-extraction-first proposal as the accepted target, to preserve source detail and avoid another mandatory transformation gateway. This was a design decision, not an implementation or migration |
| November 6, 2026 | User selected a simple MVP policy: explicitly chosen core files, RAG over other materials, and traceable citations for both. A function workflow and seventeen offline tests were implemented; no live API or production-data verification occurred |

Older log statements such as “incremental indexing is not yet implemented” describe their date, not current code. November 3 fact-first next steps are historical. README references to JD PDF input describe an aspiration, not a completed file-input workflow. This document does not authorize a replacement architecture.

## 5. Known Risks and Trade-offs

### Information loss and context limits

OCR, table layouts, merged spreadsheet cells, DOCX paragraph fallback, and chunk boundaries can omit or misassociate important facts. The historical TOEFL case establishes a reported loss between source processing and indexed output, not a proven root cause. Supplying complete parsed materials can reduce Top-K omissions, but cannot restore facts already lost during parsing. Larger context increases latency, cost, and irrelevant content. Manual selection and a character cap now provide simple controls; automatic selection and model-specific token budgets remain unimplemented.

### Weak evidence and duplicate facts

Nearest-neighbor and CrossEncoder scores measure relevance, not qualification fulfillment. Fixed-size selection can return weak candidates when direct support is absent. Structural citation checks do not validate entailment. Chunk-level deduplication can miss cross-language paraphrases or merge useful repeated context; repeated sources must not be treated as independent experience. Current prompts help express these rules but do not prove compliance.

### Persistence and reproducibility

Deletion followed by upsert can lose the previous indexed state if writing fails. Source removal is not synchronized, and file-hash skipping does not detect changes in parsing/chunking configuration. Chunk indices can change after updates; there is no version-aware citation or recovery mechanism. Production mutation and index experiments require separate treatment and explicit approval where required by repository policy.

### Privacy and external transmission

Production input is `data/documents/`; production vectors are `data/chroma` / `jobmatch_documents`. Source text, embeddings, paths, reports, prompts, and derived results can contain personal information. `.gitignore` covers principal local-data locations but neither protects already tracked files nor blocks network transmission. Tracking and staged content must be reviewed before publication.

The existing application sends candidate chunk text for OpenAI embeddings, requirement text for query embeddings, JD text for extraction, and retrieved candidate evidence for matching. The implemented combined path also sends selected core text when using a cloud model. Its matching payload omits local absolute source paths; paths remain available in locally resolved results. Filenames and candidate text are still transmitted. Sensitive identity documents require informed authorization. Document review, logs, and diagnostic exports must avoid unnecessary disclosure. A local Chroma database does not make the complete workflow local-only.

### API costs and dependencies

Changed documents require embedding calls; each requirement currently triggers a query embedding, followed by separate JD extraction and matching calls. Unchanged-file skipping reduces repeated document embedding costs but is not a general cache or budget mechanism. Full-context inputs trade broader information coverage for potentially higher token costs. Reranking avoids an LLM call but uses local compute and may require a model download.

The repository requires the `jobmatch` Conda environment rather than assuming the shell's default Python. Most `requirements.txt` entries are unpinned and not all reranking dependencies are declared directly. PySide6 is constrained to `>=6.8,<7`, declared in requirements and as an optional `gui` dependency; other runtime dependencies remain outside `pyproject.toml`. With explicit approval, PySide6 6.12.0 was installed only in the jobmatch environment. Package availability does not prove all runtime compatibility. Current API prices were not reverified for the desktop milestone.

### JD completeness and URL handling

Keyword/length checks can accept incomplete or unrelated job text; user confirmation remains essential. HTTPS and literal-IP validation provide some protection, but do not establish comprehensive destination isolation: DNS resolution and browser subresource requests are not constrained by those checks. Website behavior and extraction failures still require a usable manual-entry path.
