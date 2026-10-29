from pathlib import Path
from jobmatch.rag.chunking import chunk_document

file_path = Path("data/documents/KA WANG LAU Resume (EN).pdf")

chunks = chunk_document(file_path)

print(f"Total chunks: {len(chunks)}")

for chunk in chunks:
    print(f"\nChunk {chunk['chunk_index']}")
    print(chunk["text"][:500])