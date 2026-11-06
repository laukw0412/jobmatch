"""Check source filters against an isolated in-memory Chroma collection."""

import socket
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

import chromadb
from chromadb.config import Settings

from jobmatch.rag import retrieval
from jobmatch.rag.storage import create_chroma_client


class RetrievalScopeTests(unittest.TestCase):
    def test_real_chroma_filters_sources_before_ranking(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
            client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
            name = f"scope_{uuid4().hex}"
            collection = client.create_collection(name, embedding_function=None)
            try:
                collection.add(
                    ids=["core", "allowed", "unapproved"],
                    embeddings=[[1.0, 0.0], [0.8, 0.2], [0.99, 0.01]],
                    documents=["Synthetic core", "Synthetic approved certificate", "Synthetic other file"],
                    metadatas=[
                        {"source_file": "core.txt", "source_path": "synthetic/core.txt"},
                        {"source_file": "certificate.txt", "source_path": "synthetic/certificate.txt"},
                        {"source_file": "other.txt", "source_path": "synthetic/other.txt"},
                    ],
                )
                with (
                    patch.object(retrieval, "create_chroma_client") as storage,
                    patch.object(retrieval, "load_dotenv"),
                    patch.object(retrieval, "OpenAI") as cloud,
                ):
                    storage.return_value.__enter__.return_value = client
                    cloud.return_value.embeddings.create.return_value = SimpleNamespace(
                        data=[SimpleNamespace(embedding=[1.0, 0.0])],
                    )
                    chunks = retrieval.retrieve_chunks(
                        "Synthetic query", top_k=1,
                        chroma_path="synthetic-isolated-storage", collection_name=name,
                        included_source_paths={"synthetic/core.txt", "synthetic/certificate.txt"},
                        excluded_source_paths={"synthetic/core.txt"},
                    )
                    storage.assert_called_once_with(path="synthetic-isolated-storage")
                    self.assertEqual([item["source_file"] for item in chunks], ["certificate.txt"])
            finally:
                client.delete_collection(name)

    def test_empty_allowlist_does_not_open_storage_or_call_api(self):
        with patch.object(retrieval, "create_chroma_client") as storage, patch.object(retrieval, "OpenAI") as cloud:
            self.assertEqual(retrieval.retrieve_chunks("Synthetic query", included_source_paths=set()), [])
            storage.assert_not_called()
            cloud.assert_not_called()

    def test_missing_collection_is_not_created(self):
        with patch.object(retrieval, "create_chroma_client") as storage, patch.object(retrieval, "OpenAI") as cloud:
            storage.return_value.__enter__.return_value = storage.return_value
            storage.return_value.get_collection.side_effect = ValueError("Missing isolated collection")
            with self.assertRaisesRegex(ValueError, "Missing isolated collection"):
                retrieval.retrieve_chunks("Synthetic query", chroma_path="synthetic-only", collection_name="missing")
            storage.return_value.get_or_create_collection.assert_not_called()
            cloud.assert_not_called()

    def test_real_persistent_clients_share_settings_and_survive_reopening(self):
        with TemporaryDirectory() as directory, patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
            path = str(Path(directory) / "isolated_chroma")
            with create_chroma_client(path=path) as writer:
                collection = writer.create_collection("persistent_scope", embedding_function=None)
                collection.add(
                    ids=["approved", "other"], embeddings=[[1.0, 0.0], [0.9, 0.1]],
                    documents=["Synthetic approved evidence", "Synthetic excluded evidence"],
                    metadatas=[
                        {"source_file": "certificate.txt", "source_path": "synthetic/certificate.txt"},
                        {"source_file": "other.txt", "source_path": "synthetic/other.txt"},
                    ],
                )
                with patch.object(retrieval, "load_dotenv"), patch.object(retrieval, "OpenAI") as cloud:
                    cloud.return_value.embeddings.create.return_value = SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])])
                    for _ in range(2):
                        chunks = retrieval.retrieve_chunks(
                            "Synthetic query", chroma_path=path, collection_name="persistent_scope",
                            included_source_paths={"synthetic/certificate.txt"},
                        )
                        self.assertEqual([item["source_file"] for item in chunks], ["certificate.txt"])
                self.assertEqual(collection.count(), 2)
            with create_chroma_client(path=path) as reopened:
                self.assertEqual(reopened.get_collection("persistent_scope").count(), 2)


if __name__ == "__main__":
    unittest.main()
