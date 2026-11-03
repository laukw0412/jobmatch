
from pathlib import Path

import torch
from sentence_transformers import CrossEncoder

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.retriever import select_evidence
from jobmatch.rag.retrieval import retrieve_chunks


MODEL_NAME = "BAAI/bge-reranker-v2-m3"
INPUT_PATH = Path("data/test_structured_job.json")

TEST_REQUIREMENT_IDS = [1, 7, 15]
EXCLUDED_FILES = {"two_column_resume_sample.docx"}


def rerank_chunks(
    model: CrossEncoder,
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank retrieved chunks using a multilingual CrossEncoder."""

    if not chunks:
        return []

    pairs = [
        (query, chunk["text"])
        for chunk in chunks
    ]

    scores = model.predict(
        pairs,
        batch_size=4,
        show_progress_bar=False,
    )

    ranked = []

    for chunk, score in zip(chunks, scores):
        item = chunk.copy()
        item["rerank_score"] = float(score)
        ranked.append(item)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return ranked[:top_k]


def print_evidence(
    title: str,
    evidence: list[dict],
) -> None:
    """Print evidence sources, scores, and previews."""

    print(f"\n{title}")

    for index, item in enumerate(evidence, start=1):
        print(f"  Evidence {index}")
        print(f"  Source: {item.get('source_file', 'Unknown')}")
        print(f"  Distance: {item['distance']:.4f}")

        if "rerank_score" in item:
            print(f"  Rerank score: {item['rerank_score']:.4f}")

        preview = " ".join(
            item.get("text", "").split()
        )[:200]

        print(f"  Text: {preview}")
        print()


def main() -> None:
    """Compare source diversity with multilingual reranking."""

    job = JobDescription.model_validate_json(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model = CrossEncoder(
        MODEL_NAME,
        device=device,
        max_length=512,
    ) 

    for requirement_id in TEST_REQUIREMENT_IDS:
        requirement = job.requirements[requirement_id - 1]
        query = requirement.description

        print("=" * 75)
        print(f"Requirement {requirement_id}")
        print(query)

        # Retrieve the same candidate pool for both methods.
        candidates = retrieve_chunks(
            query=query,
            top_k=15,
        )

        # Exclude known sample documents from this comparison.
        candidates = [
            chunk
            for chunk in candidates
            if chunk.get("source_file") not in EXCLUDED_FILES
        ]

        original = select_evidence(
            chunks=candidates,
            top_k=5,
            strategy="source",
        )

        reranked = rerank_chunks(
            model=model,
            query=query,
            chunks=candidates,
            top_k=5,
        )

        print_evidence(
            "Source Diversity (Baseline)",
            original,
        )

        print_evidence(
            "Multilingual CrossEncoder",
            reranked,
        )

    print("\nReranker comparison completed.")


if __name__ == "__main__":
    main()
