import chromadb
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.rag.indexing import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    include_embeddings: bool = False,
) -> list[dict]:
    """Retrieve relevant chunks from the existing Chroma collection."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be positive.")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    count = collection.count()

    if count == 0:
        return []

    load_dotenv()
    openai_client = OpenAI()

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    query_embedding = np.asarray(
        response.data[0].embedding,
        dtype=float,
    )

    include_fields = [
        "documents",
        "metadatas",
        "distances",
    ]

    if include_embeddings:
        include_fields.append("embeddings")

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=min(top_k, count),
        include=include_fields,
    )

    retrieved_chunks = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    stored_embeddings = results.get("embeddings")

    for index, text in enumerate(documents):
        metadata = metadatas[index]

        chunk = {
            "text": text,
            "source_file": metadata.get("source_file", ""),
            "source_path": metadata.get("source_path", ""),
            "chunk_index": metadata.get("chunk_index", 0),
            "distance": float(distances[index]),
        }

        if include_embeddings:
            if stored_embeddings is None:
                raise ValueError(
                    "Chroma did not return stored embeddings."
                )

            embedding = np.asarray(
                stored_embeddings[0][index],
                dtype=float,
            )

            denominator = (
                np.linalg.norm(query_embedding)
                * np.linalg.norm(embedding)
            )

            similarity = (
                float(np.dot(query_embedding, embedding) / denominator)
                if denominator > 0
                else 0.0
            )

            chunk["embedding"] = embedding.tolist()
            chunk["query_similarity"] = similarity

        retrieved_chunks.append(chunk)

    return retrieved_chunks
