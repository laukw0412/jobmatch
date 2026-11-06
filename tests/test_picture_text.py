"""Keep recognized figure text in complete context and RAG without network access."""

from functools import partial
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from docling_core.types.doc import DocItemLabel
from docling_core.types.doc import DoclingDocument

from jobmatch.document.markdown import export_markdown
from jobmatch.rag import chunking


class CharacterTokenizer(BaseTokenizer):
    def count_tokens(self, text):
        return len(text)

    def get_max_tokens(self):
        return 10_000

    def get_tokenizer(self):
        return self


def score_document():
    document = DoclingDocument(name="synthetic_score_report")
    document.add_text(label=DocItemLabel.TEXT, text="Synthetic score report")
    picture = document.add_picture()
    for text in ["Reading:", "Score is", "18", "Score range 0 to 30.", "Listening:", "Score is", "22", "Total Score", "0", "74", "120"]:
        document.add_text(label=DocItemLabel.TEXT, text=text, parent=picture)
    return document


class PictureTextTests(unittest.TestCase):
    def test_complete_export_recovers_picture_text_and_preserves_source(self):
        document = score_document()
        original = document.model_dump()
        self.assertNotIn("Score is", document.export_to_markdown())
        text = export_markdown(document)
        self.assertIn("Reading:\n\nScore is\n\n18", text)
        self.assertIn("Listening:\n\nScore is\n\n22", text)
        self.assertIn("Total Score\n\n0\n\n74\n\n120", text)
        self.assertEqual(document.model_dump(), original)

    def test_hybrid_chunks_keep_score_labels_and_values_together(self):
        document = score_document()
        chunker = HybridChunker(
            tokenizer=CharacterTokenizer(), serializer_provider=chunking.PictureTextSerializerProvider(),
        )
        texts = [" ".join(chunker.contextualize(chunk=item).split()) for item in chunker.chunk(dl_doc=document)]
        self.assertTrue(any("Reading: Score is 18" in text for text in texts))
        self.assertTrue(any("Listening: Score is 22" in text for text in texts))
        self.assertTrue(any("Total Score 0 74 120" in text for text in texts))

    def test_actual_chunk_document_entry_uses_picture_aware_provider(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic converter input")
            with (
                patch.object(chunking._converter, "convert", return_value=SimpleNamespace(document=score_document())),
                patch.object(chunking, "HybridChunker", partial(HybridChunker, tokenizer=CharacterTokenizer())),
                patch.object(chunking, "load_document", side_effect=AssertionError("Unexpected fallback")),
                patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
            ):
                chunks = chunking.chunk_document(path)
                self.assertTrue(any("Reading: Score is 18" in " ".join(item["text"].split()) for item in chunks))
                self.assertTrue(all(item["source_file"] == "synthetic.pdf" for item in chunks))
                self.assertTrue(all(item["method"] == "hybrid" for item in chunks))

    def test_picture_without_recognized_text_does_not_invent_scores(self):
        document = DoclingDocument(name="empty_picture")
        document.add_picture()
        text = export_markdown(document)
        self.assertNotIn("Score", text)
        self.assertNotIn("74", text)


if __name__ == "__main__":
    unittest.main()
