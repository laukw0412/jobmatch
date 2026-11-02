from pathlib import Path

from jobmatch.jobs.web_extractor import extract_job_text_from_url


def main():
    url = input("Enter job URL: ").strip()

    try:
        text = extract_job_text_from_url(url)

        print("\n=== Extracted Job Description ===\n")
        print(text)

        print("\n=== Summary ===")
        print(f"Characters: {len(text)}")

        output = Path("data/test_extracted_job.txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")

        print(f"Saved to: {output}")

    except ValueError as exc:
        print(f"Extraction failed: {exc}")


if __name__ == "__main__":
    main()
