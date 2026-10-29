
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.rag.chunking import chunk_document


DOCUMENT = Path("data/documents/KA WANG LAU Resume (EN).pdf")
DB_PATH = "data/chroma"
COLLECTION_NAME = "jobmatch_demo"
EMBEDDING_MODEL = "text-embedding-3-small"


def main():
    load_dotenv()
    openai_client = OpenAI()

    # Step 1: Extract document chunks.
    chunks = chunk_document(DOCUMENT)
    texts = [chunk["text"] for chunk in chunks]
    print(f"Chunks: {len(texts)}")

    if not texts:
        raise RuntimeError("No chunks found.")

    # Step 2: Generate embeddings using OpenAI.
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    embeddings = [item.embedding for item in response.data]
    print(f"Embedding dimensions: {len(embeddings[0])}")

    # Step 3: Store embeddings and text in Chroma.
    db = chromadb.PersistentClient(path=DB_PATH)
    collection = db.get_or_create_collection(COLLECTION_NAME)

    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {"source_file": chunk["source_file"]}
            for chunk in chunks
        ],
    )

    print(f"Stored chunks: {collection.count()}")

    # Step 4: Embed a search query.
    query = "Experience with transformer-based AI models"

    query_response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )

    query_embedding = query_response.data[0].embedding

    # Step 5: Search for the most relevant chunks.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(3, collection.count()),
    )

    print("\nSEARCH RESULTS")

    for index, text in enumerate(results["documents"][0]):
        distance = results["distances"][0][index]
        print(f"\nResult {index + 1}")
        print(f"Distance: {distance:.4f}")
        print(text)


if __name__ == "__main__":
    main()
