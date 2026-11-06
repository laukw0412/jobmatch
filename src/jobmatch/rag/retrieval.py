import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.rag.indexing import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)
from jobmatch.rag.storage import create_chroma_client


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    include_embeddings: bool = False,
    excluded_source_paths: set[str] | None = None,
    chroma_path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    included_source_paths: set[str] | None = None,
    client: OpenAI | None = None,
) -> list[dict]:
    """Retrieve relevant chunks from the existing Chroma collection."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be positive.")

    if included_source_paths is not None and not included_source_paths:
        return []

    with create_chroma_client(path=chroma_path) as chroma_client:
        collection = chroma_client.get_collection(name=collection_name)
        count = collection.count()
        if count == 0:
            return []

        if client is None:
            load_dotenv()
            client = OpenAI()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
        query_embedding = np.asarray(response.data[0].embedding, dtype=float)

        include_fields = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include_fields.append("embeddings")

        filters = []
        if included_source_paths is not None:
            filters.append({"source_path": {"$in": sorted(included_source_paths)}})
        if excluded_source_paths:
            filters.append({"source_path": {"$nin": sorted(excluded_source_paths)}})
        query_options = {}
        if len(filters) == 1:
            query_options["where"] = filters[0]
        elif filters:
            query_options["where"] = {"$and": filters}

        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, count),
            include=include_fields,
            **query_options,
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
