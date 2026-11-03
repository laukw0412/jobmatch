import json
from pathlib import Path

from jobmatch.matching.analyzer import analyze_matches


INPUT_PATH = Path("data/test_requirement_evidence.json")
OUTPUT_PATH = Path("data/test_matching_result.json")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        requirement_evidence = json.load(file)

    result = analyze_matches(requirement_evidence)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        file.write(result.model_dump_json(indent=2))

    for match in result.matches:
        print(
            f"[{match.requirement_id}] "
            f"{match.status.upper()}: {match.reason}"
        )

    print()
    print("Overall summary:", result.overall_summary)
    print("Recommendation:", result.application_recommendation)
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()