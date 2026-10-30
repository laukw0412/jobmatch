from pathlib import Path

from jobmatch.rag.indexing import index_directory


def main():
    """Test multi-document indexing with sample files."""

    test_dir = Path("data/test_index_documents")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create two small sample documents.
    file_a = test_dir / "research.txt"
    file_b = test_dir / "skills.txt"

    file_a.write_text(
        "Research in computer vision and image generation "
        "using PyTorch and transformer models.",
        encoding="utf-8",
    )

    file_b.write_text(
        "Programming skills include Python, machine learning, "
        "deep learning, and data analysis.",
        encoding="utf-8",
    )

    # First indexing run.
    print("\n=== First run ===")
    first_result = index_directory(test_dir)
    print(first_result)

    # Second indexing run.
    print("\n=== Second run ===")
    second_result = index_directory(test_dir)
    print(second_result)

    # Modify only one document.
    file_a.write_text(
        "Research in computer vision, generative AI, "
        "and omnidirectional image generation using PyTorch.",
        encoding="utf-8",
    )

    # Third indexing run.
    print("\n=== Third run: modified document ===")
    third_result = index_directory(test_dir)
    print(third_result)


if __name__ == "__main__":
    main()
