
import hashlib
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.rag.chunking import (
    SUPPORTED_EXTENSIONS,
    chunk_document,
)


DOCUMENTS_DIR = Path("data/documents")
DB_PATH = "data/chroma"
COLLECTION_NAME = "jobmatch_documents_v1"
EMBEDDING_MODEL = "text-embedding-3-small"


def hash_file(path: Path) -> str:
    """Calculate a stable hash for document change detection."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def index_documents() -> None:
    """Index new or modified documents into Chroma."""
    load_dotenv()
    openai_client = OpenAI()

    db = chromadb.PersistentClient(path=DB_PATH)
    collection = db.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"embedding_model": EMBEDDING_MODEL},
    )

    files = sorted(
        path
        for path in DOCUMENTS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith("~$")
    )

    print(f"Found {len(files)} supported documents.")

    for path in files:
        source = path.relative_to(DOCUMENTS_DIR).as_posix()
        source_id = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        file_hash = hash_file(path)

        existing = collection.get(
            where={"source_id": source_id},
            include=["metadatas"],
        )

        old_metadata = existing["metadatas"] or []

        if (
            old_metadata
            and all(
                item["file_hash"] == file_hash
                for item in old_metadata
            )
        ):
            print(f"SKIP: {source}")
            continue

        try:
            chunks = chunk_document(path)
            if not chunks:
                print(f"EMPTY: {source}")
                continue

            texts = [chunk["text"] for chunk in chunks]

            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )

            embeddings = [
                item.embedding
                for item in sorted(
                    response.data,
                    key=lambda item: item.index,
                )
            ]

            ids = [
                f"{source_id}::{i}"
                for i in range(len(chunks))
            ]

            metadatas = [
                {
                    "source_file": source,
                    "source_id": source_id,
                    "file_hash": file_hash,
                    "chunk_index": i,
                    "method": chunk["method"],
                }
                for i, chunk in enumerate(chunks)
            ]

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            # Remove obsolete chunks after a successful update.
            obsolete_ids = set(existing["ids"]) - set(ids)

            if obsolete_ids:
                collection.delete(ids=list(obsolete_ids))

            print(f"INDEXED: {source} ({len(chunks)} chunks)")

        except Exception as exc:
            print(f"FAILED: {source}: {exc}")

    print(f"\nTotal indexed chunks: {collection.count()}")


if __name__ == "__main__":
    index_documents()
