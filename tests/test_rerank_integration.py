
import json
from pathlib import Path

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.retriever import retrieve_job_requirements


INPUT_PATH = Path("data/test_structured_job.json")
OUTPUT_PATH = Path("data/test_requirement_evidence_reranked.json")


def main() -> None:
    """Test reranking integration for all job requirements."""

    job = JobDescription.model_validate_json(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    results = retrieve_job_requirements(
        job=job,
        top_k=5,
        candidate_multiplier=3,
        strategy="rerank",
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    for item in results:
        print("=" * 65)
        print(f"Requirement {item['requirement_id']}")
        print(item["requirement"])
        print(f"Evidence count: {len(item['evidence'])}")

        for index, evidence in enumerate(
            item["evidence"],
            start=1,
        ):
            print(
                f"  {index}. "
                f"{evidence.get('source_file', 'Unknown')}"
            )

            score = evidence.get("rerank_score")

            if score is not None:
                print(f"     Rerank score: {score:.6f}")

    print("\nTotal requirements:", len(results))
    print(
        "Total evidence:",
        sum(len(item["evidence"]) for item in results),
    )
    print("Saved to:", OUTPUT_PATH) 


if __name__ == "__main__":
    main()
