
from pathlib import Path

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.retriever import select_evidence
from jobmatch.rag.retrieval import retrieve_chunks


INPUT_PATH = Path("data/test_structured_job.json")
TEST_REQUIREMENT_IDS = [1, 7, 15]


def print_evidence(title: str, evidence: list[dict]) -> None:
    """Display evidence sources and text previews."""

    print(f"\n  {title}")

    for index, item in enumerate(evidence, start=1):
        print(f"    Evidence {index}")
        print(f"    Source: {item.get('source_file')}")
        print(f"    Distance: {item.get('distance'):.4f}")

        preview = " ".join(
            item.get("text", "").split()
        )[:160]

        print(f"    Text: {preview}")
        print()


def main() -> None:
    """Compare source diversity against MMR selection."""

    job = JobDescription.model_validate_json(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    for requirement_id in TEST_REQUIREMENT_IDS:
        requirement = job.requirements[requirement_id - 1]

        print("=" * 75)
        print(f"Requirement {requirement_id}")
        print(requirement.description)

        # Retrieve candidates once for a fair comparison
        candidates = retrieve_chunks(
            query=requirement.description,
            top_k=15,
            include_embeddings=True,
        )

        original = select_evidence(
            chunks=candidates,
            top_k=5,
            strategy="source",
        )

        mmr = select_evidence(
            chunks=candidates,
            top_k=5,
            strategy="mmr",
            lambda_mult=0.7,
        )

        print_evidence("Original Source Diversity", original)
        print_evidence("MMR Selection", mmr)

    print("\nMMR comparison completed.")


if __name__ == "__main__":
    main()
