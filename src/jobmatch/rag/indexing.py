from dotenv import load_dotenv
import hashlib
from pathlib import Path

import chromadb
from openai import OpenAI

from jobmatch.rag.chunking import (
    SUPPORTED_EXTENSIONS,
    chunk_document,
)


EMBEDDING_MODEL = "text-embedding-3-small"
CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "jobmatch_documents"


def calculate_file_hash(file_path: str | Path) -> str:
    """Calculate a SHA-256 hash from the file contents."""
    path = Path(file_path)

    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)

    return hasher.hexdigest()


def index_document(
    file_path: str | Path,
    collection,
    client: OpenAI,
) -> str:
    """Index a document, skipping files that have not changed."""

    path = Path(file_path).resolve()

    # Identify the document and its current contents
    source_path = str(path)
    file_hash = calculate_file_hash(path)

    # Find chunks previously indexed from this file
    existing = collection.get(
        where={"source_path": source_path},
        include=["metadatas"],
    )

    existing_ids = existing["ids"]
    existing_metadata = existing["metadatas"]

    # Skip indexing if the file is unchanged
    if existing_ids and all(
        item["file_hash"] == file_hash
        for item in existing_metadata
    ):
        return "skipped"

    # Chunk the document using the existing RAG module
    chunks = chunk_document(path)

    if not chunks:
        return "empty"

    # Only executed if chunks are not empty
    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings for all chunks
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    embeddings = [item.embedding for item in response.data]

    # Create stable, unique IDs for this document
    document_id = hashlib.sha256(
        source_path.encode("utf-8")
    ).hexdigest()

    ids = []
    metadatas = []

    for chunk in chunks:
        chunk_index = chunk["chunk_index"]
        chunk_id = f"{document_id}::{chunk_index}"

        ids.append(chunk_id)

        metadatas.append({
            "source_file": path.name,
            "source_path": source_path,
            "file_hash": file_hash,
            "chunk_index": chunk_index,
            "method": chunk["method"],
        })

    # Replace old chunks only after new embeddings are ready
    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return "updated" if existing_ids else "indexed"


def index_directory(
    directory: str | Path,
    chroma_path: str = CHROMA_PATH,
) -> dict:
    """Index supported documents in a directory recursively."""

    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(directory)

    # Load environment variables from .env
    load_dotenv()
    # Initialize the OpenAI client
    openai_client = OpenAI()

    chroma_client = chromadb.PersistentClient(path=chroma_path)

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    results = {
        "indexed": 0,
        "updated": 0,
        "skipped": 0,
        "empty": 0,
        "failed": 0,
    }

    # Find and index all supported files
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            status = index_document(
                path,
                collection,
                openai_client,
            )

        except Exception as exc:
            print(f"Indexing failed: {path.name}: {exc}")
            results["failed"] += 1
            continue

        results[status] += 1
        print(f"{status}: {path.name}")

    print(f"Total stored chunks: {collection.count()}")

    return results
