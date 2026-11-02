from jobmatch.jobs.models import JobDescription
from jobmatch.rag.retrieval import retrieve_chunks


def select_evidence(
    chunks: list[dict],
    top_k: int,
) -> list[dict]:
    """Select relevant chunks with diverse document sources."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Sort chunks by semantic distance
    ranked_chunks = sorted(
        chunks,
        key=lambda chunk: chunk.get("distance", float("inf")),
    )

    selected = []
    used_sources = set()
    remaining = []

    # First pass: select one chunk from each source
    for chunk in ranked_chunks:
        source = (
            chunk.get("source_path")
            or chunk.get("source_file")
            or "unknown"
        )

        if source not in used_sources and len(selected) < top_k:
            selected.append(chunk)
            used_sources.add(source)
        else:
            remaining.append(chunk)

    # Second pass: fill remaining slots by relevance
    for chunk in remaining:
        if len(selected) >= top_k:
            break

        selected.append(chunk)

    return selected


def retrieve_job_requirements(
    job: JobDescription,
    top_k: int = 5,
    candidate_multiplier: int = 3,
) -> list[dict]:
    """Retrieve candidate evidence for each job requirement."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if candidate_multiplier < 1:
        raise ValueError(
            "candidate_multiplier must be at least 1."
        )

    results = []

    for index, requirement in enumerate(job.requirements):
        candidates = retrieve_chunks(
            query=requirement.description,
            top_k=top_k * candidate_multiplier,
        )

        evidence = select_evidence(
            chunks=candidates,
            top_k=top_k,
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
