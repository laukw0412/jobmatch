import re

import numpy as np

from jobmatch.jobs.models import JobDescription
from jobmatch.rag.indexing import CHROMA_PATH
from jobmatch.rag.indexing import COLLECTION_NAME
from jobmatch.rag.retrieval import retrieve_chunks


DEFAULT_EXCLUDED_FILES = {
    "two_column_resume_sample.docx",
}

SEMANTIC_DUPLICATE_THRESHOLD = 0.97


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""

    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def normalize_text(text: str) -> str:
    """Normalize text for exact duplicate detection."""

    return " ".join(text.casefold().split())


def is_duplicate(
    candidate: dict,
    selected: list[dict],
) -> bool:
    """Detect exact or conservative semantic duplicates."""

    candidate_text = normalize_text(
        candidate.get("text", "")
    )

    for existing in selected:
        existing_text = normalize_text(
            existing.get("text", "")
        )

        if candidate_text == existing_text:
            return True

        first = candidate.get("embedding")
        second = existing.get("embedding")

        if first is None or second is None:
            continue

        # Avoid merging records with different explicit numbers
        first_numbers = re.findall(r"\d+", candidate_text)
        second_numbers = re.findall(r"\d+", existing_text)

        if first_numbers != second_numbers:
            continue

        similarity = cosine_similarity(first, second)

        if similarity >= SEMANTIC_DUPLICATE_THRESHOLD:
            return True

    return False



def select_evidence(
    chunks: list[dict],
    top_k: int = 5,
    strategy: str = "source",
    lambda_mult: float = 0.7,
    query: str | None = None,
) -> list[dict]:
    """Select evidence using source diversity, MMR, or reranking."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if strategy not in ("source", "mmr", "rerank"):
        raise ValueError(
            "Strategy must be 'source', 'mmr', or 'rerank'."
        )

    if not 0 <= lambda_mult <= 1:
        raise ValueError(
            "lambda_mult must be between 0 and 1."
        )

    if not chunks:
        return []

    ranked_chunks = sorted(
        chunks,
        key=lambda item: item.get(
            "distance",
            float("inf"),
        ),
    )

    if strategy == "source":
        selected = []
        remaining = []
        used_sources = set()

        for chunk in ranked_chunks:
            source = (
                chunk.get("source_path")
                or chunk.get("source_file")
                or "unknown"
            )

            if (
                source not in used_sources
                and len(selected) < top_k
            ):
                selected.append(chunk)
                used_sources.add(source)
            else:
                remaining.append(chunk)

        for chunk in remaining:
            if len(selected) >= top_k:
                break

            selected.append(chunk)

    elif strategy == "mmr":
        if any(
            "embedding" not in chunk
            or "query_similarity" not in chunk
            for chunk in ranked_chunks
        ):
            raise ValueError(
                "MMR requires embeddings and query similarities."
            )

        selected = []
        remaining = ranked_chunks.copy()

        while remaining and len(selected) < top_k:
            best_chunk = None
            best_score = float("-inf")

            for chunk in remaining:
                relevance = chunk["query_similarity"]

                redundancy = (
                    max(
                        0.0,
                        max(
                            cosine_similarity(
                                chunk["embedding"],
                                item["embedding"],
                            )
                            for item in selected
                        ),
                    )
                    if selected
                    else 0.0
                )

                score = (
                    lambda_mult * relevance
                    - (1 - lambda_mult) * redundancy
                )

                if score > best_score:
                    best_score = score
                    best_chunk = chunk

            selected.append(best_chunk)
            remaining.remove(best_chunk)

    else:
        from jobmatch.matching.reranker import rerank_chunks

        if query is None or not query.strip():
            raise ValueError(
                "Reranking requires a nonempty query."
            )

        if any(
            "embedding" not in chunk
            for chunk in ranked_chunks
        ):
            raise ValueError(
                "Reranking requires stored embeddings for deduplication."
            )

        ranked_chunks = rerank_chunks(
            query=query,
            chunks=ranked_chunks,
        )

        selected = []

        # Preserve reranker order while removing duplicates
        for chunk in ranked_chunks:
            if len(selected) >= top_k:
                break

            if is_duplicate(chunk, selected):
                continue

            selected.append(chunk)

    # Do not pass large embedding vectors into the LLM.
    return [
        {
            key: value
            for key, value in chunk.items()
            if key not in (
                "embedding",
                "query_similarity",
            )
        }
        for chunk in selected
    ]



def retrieve_job_requirements(
    job: JobDescription,
    top_k: int = 5,
    candidate_multiplier: int = 3,
    strategy: str = "source",
    lambda_mult: float = 0.7,
    excluded_files: set[str] | None = None,
    excluded_source_paths: set[str] | None = None,
    chroma_path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    included_source_paths: set[str] | None = None,
    client=None,
    progress=None,
) -> list[dict]:
    """Retrieve candidate evidence for every job requirement."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if candidate_multiplier < 1:
        raise ValueError(
            "candidate_multiplier must be at least 1."
        )

    if strategy not in ("source", "mmr", "rerank"):
        raise ValueError(
            "Strategy must be 'source', 'mmr', or 'rerank'."
        )

    if excluded_files is None:
        excluded_files = DEFAULT_EXCLUDED_FILES

    results = []

    for index, requirement in enumerate(job.requirements):
        if progress is not None:
            progress("检索补充证据 {}/{}".format(index + 1, len(job.requirements)))
        candidates = retrieve_chunks(
            query=requirement.description,
            top_k=top_k * candidate_multiplier,
            include_embeddings=(
                strategy in ("mmr", "rerank")
            ),
            excluded_source_paths=excluded_source_paths,
            chroma_path=chroma_path,
            collection_name=collection_name,
            included_source_paths=included_source_paths,
            client=client,
        )

        candidates = [
            chunk
            for chunk in candidates
            if chunk.get("source_file") not in excluded_files
        ]

        evidence = select_evidence(
            chunks=candidates,
            top_k=top_k,
            strategy=strategy,
            lambda_mult=lambda_mult,
            query=requirement.description,
        )

        results.append(
            {
                "requirement_id": index + 1,
                "requirement": requirement.description,
                "category": requirement.category,
                "priority": requirement.priority,
                "evidence": evidence,
            }
        )

    return results
