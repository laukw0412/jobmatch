import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.rag.indexing import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)


def main():
    """Test semantic retrieval across indexed documents."""

    # Load the OpenAI API key.
    load_dotenv()

    openai_client = OpenAI()

    # Connect to the existing Chroma collection.
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = chroma_client.get_collection(
        name=COLLECTION_NAME
    )

    # Define the search query.
    query = "Experience with computer vision and image generation"

    # Generate an embedding for the query.
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    query_embedding = response.data[0].embedding

    # Search across all indexed documents.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(2, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Display the retrieval results.
    for i, text in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        print(f"\n=== Result {i + 1} ===")
        print(f"Source: {metadata['source_file']}")
        print(f"Distance: {distance:.4f}")
        print(f"Text: {text}")


if __name__ == "__main__":
    main()
