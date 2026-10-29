
import sys
from pathlib import Path

from jobmatch.rag.chunking import chunk_document


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/test_multiformat_chunking.py <file_path>")
        return

    path = Path(sys.argv[1])
    chunks = chunk_document(path)

    print(f"\nFile: {path.name}")
    print(f"Total chunks: {len(chunks)}")

    for chunk in chunks:
        print(f"\n--- Chunk {chunk['chunk_index']} ---")
        print(f"Method: {chunk['method']}")
        print(f"Length: {len(chunk['text'])}")
        print(chunk["text"])


if __name__ == "__main__":
    main()
