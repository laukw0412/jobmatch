from pathlib import Path

from jobmatch.jobs.extractor import extract_job_description
from jobmatch.jobs.web_extractor import extract_job_text_from_url


DATA_DIR = Path("data")
JD_PATH = DATA_DIR / "test_extracted_job.txt"
OUTPUT_PATH = DATA_DIR / "test_structured_job.json"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=== JobMatch JD Extraction ===")
    print("1. Extract JD from URL")
    print("2. Use existing JD text file")

    choice = input("Select input (1/2): ").strip()

    if choice == "1":
        url = input("Enter job URL: ").strip()

        try:
            jd_text = extract_job_text_from_url(url)
        except ValueError as exc:
            print(f"URL extraction failed: {exc}")
            print("Please provide JD text manually.")
            return

        JD_PATH.write_text(jd_text, encoding="utf-8")

    elif choice == "2":
        if not JD_PATH.exists():
            print(f"JD file not found: {JD_PATH}")
            return

    else:
        print("Invalid selection.")
        return

    print(f"\nReview the JD text in: {JD_PATH}")
    print("Check that all requirements are included.")
    print("Edit and save the file if necessary.")

    confirmation = input(
        "\nHave you reviewed and confirmed the JD? (y/n): "
    ).strip().lower()

    if confirmation != "y":
        print("Extraction cancelled.")
        return

    # Reload the text to include any manual edits.
    jd_text = JD_PATH.read_text(encoding="utf-8")

    if not jd_text.strip():
        print("JD text is empty.")
        return

    result = extract_job_description(jd_text)

    OUTPUT_PATH.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print("\n=== Structured Job Description ===")
    print(result.model_dump_json(indent=2))
    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
