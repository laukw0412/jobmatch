
from jobmatch.jobs.web_extractor import extract_job_text_from_url


def main():
    url = input("Enter job posting URL: ").strip()

    try:
        text = extract_job_text_from_url(url)

        print("\n=== Extracted Content ===\n")
        print(text)

        print("\n=== Extraction Summary ===")
        print(f"Character count: {len(text)}")

    except ValueError as exc:
        print(f"Extraction failed: {exc}")


if __name__ == "__main__":
    main()
