from pathlib import Path

from jobmatch.document.context import DEFAULT_MAX_INPUT_CHARS
from jobmatch.document.context import load_core_documents
from jobmatch.jobs.extractor import extract_job_description
from jobmatch.matching.analyzer import analyze_matches
from jobmatch.matching.analyzer import SYSTEM_PROMPT
from jobmatch.matching.models import MatchingResult
from jobmatch.matching.report import write_matching_report
from jobmatch.matching.retriever import retrieve_job_requirements
from jobmatch.rag.indexing import CHROMA_PATH
from jobmatch.rag.indexing import COLLECTION_NAME


def match_job(
    confirmed_jd_text: str,
    core_document_paths: list[str | Path],
    *,
    model: str = "gpt-4.1-mini",
    top_k: int = 5,
    strategy: str = "source",
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
    chroma_path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    supplementary_document_paths: list[str | Path] | None = None,
    report_path: str | Path | None = None,
) -> MatchingResult:
    """Match a confirmed JD using user-selected core files and mandatory RAG.

    The caller must obtain JD confirmation and authorization for cloud API
    processing. This function reads selected core files and queries the existing
    index; it does not index files. An optional report path saves the result
    without overwriting an existing file. The character cap is a local
    input guard, not an exact model-token or price estimate.
    """
    if not confirmed_jd_text.strip():
        raise ValueError("Confirmed job description cannot be empty.")
    if top_k < 1:
        raise ValueError("top_k must be positive.")
    if strategy not in {"source", "mmr", "rerank"}:
        raise ValueError("Strategy must be 'source', 'mmr', or 'rerank'.")
    if report_path is not None and Path(report_path).exists():
        raise FileExistsError("The report path already exists; select a new output path.")

    core_documents = load_core_documents(core_document_paths, max_chars=max_input_chars)
    if len(SYSTEM_PROMPT) + len(confirmed_jd_text) + sum(len(item.text) for item in core_documents) > max_input_chars:
        raise ValueError("JD and core documents exceed the character budget.")

    job = extract_job_description(confirmed_jd_text, model=model)
    if not job.requirements:
        raise ValueError("No job requirements were extracted; review the confirmed JD.")

    evidence = retrieve_job_requirements(
        job,
        top_k=top_k,
        strategy=strategy,
        excluded_source_paths={item.source_path for item in core_documents},
        chroma_path=chroma_path,
        collection_name=collection_name,
        included_source_paths=(
            {str(Path(path).resolve()) for path in supplementary_document_paths}
            if supplementary_document_paths is not None else None
        ),
    )
    result = analyze_matches(
        evidence,
        model=model,
        core_documents=core_documents,
        confirmed_jd_text=confirmed_jd_text,
        max_input_chars=max_input_chars,
    )
    if report_path is not None:
        write_matching_report(result, report_path)
    return result
