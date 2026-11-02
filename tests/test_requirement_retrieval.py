import json
from pathlib import Path

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.retriever import retrieve_job_requirements


INPUT_PATH = Path("data/test_structured_job.json")
OUTPUT_PATH = Path("data/test_requirement_evidence.json")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Structured JD not found: {INPUT_PATH}"
        )

    job = JobDescription.model_validate_json(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    print("=== Requirement-based RAG Retrieval ===")
    print(f"Job: {job.job_title}")
    print(f"Requirements: {len(job.requirements)}")

    results = retrieve_job_requirements(
        job=job,
        top_k=5,
        candidate_multiplier=3,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for result in results:
        print(
            f"\n[{result['requirement_id']}] "
            f"{result['priority'].upper()} - "
            f"{result['requirement']}"
        )

        for evidence in result["evidence"]:
            print(
                f"  Source: {evidence.get('source_file')}"
                f" | Distance: {evidence.get('distance')}"
            )

            preview = evidence.get("text", "")
            print(f"  Text: {preview[:180]}...")

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
