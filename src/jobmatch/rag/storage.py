import chromadb
from chromadb.config import Settings


def create_chroma_client(path: str):
    """Use fresh, consistent settings for every local persistent client."""
    return chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
