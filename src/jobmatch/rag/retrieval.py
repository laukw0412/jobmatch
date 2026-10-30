from dotenv import load_dotenv
from openai import OpenAI
import chromadb

from jobmatch.rag.indexing import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)


def retrieve_chunks(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve the most relevant chunks from Chroma."""

    # Validate the input
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    # Connect to the existing Chroma collection
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    # Return an empty list if no documents are indexed
    count = collection.count()

    if count == 0:
        return []

    # Initialize the OpenAI client
    load_dotenv()
    openai_client = OpenAI()

    # Generate an embedding for the query
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    query_embedding = response.data[0].embedding

    # Search for the most relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    # Convert the Chroma results into a list of dictionaries
    retrieved_chunks = []

    for i, text in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        retrieved_chunks.append({
            "text": text,
            "source_file": metadata["source_file"],
            "source_path": metadata["source_path"],
            "chunk_index": metadata["chunk_index"],
            "distance": distance,
        })

    return retrieved_chunks
