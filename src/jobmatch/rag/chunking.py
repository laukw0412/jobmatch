
from pathlib import Path

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from jobmatch.document.loader import load_document


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".md",
}

_converter = DocumentConverter()


def chunk_plain_text(
    text: str,
    source_file: str,
    max_chars: int = 1500,
) -> list[dict]:
    """Split plain text using LangChain's recursive text splitter."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=min(100, max_chars // 5),
    )

    texts = splitter.split_text(text)

    return [
        {
            "chunk_id": f"{source_file}::{i}",
            "source_file": source_file,
            "chunk_index": i,
            "text": content,
            "method": "recursive_text",
        }
        for i, content in enumerate(texts)
    ]


def chunk_document(file_path: str | Path) -> list[dict]:
    """
    Extract and chunk a document for RAG indexing.

    Prefer Docling HybridChunker for structured documents.
    Use direct text loading or the existing document loader as fallback.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(path)

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    # Plain text files do not require document conversion.
    if extension in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8-sig")
        return chunk_plain_text(text, path.name)

    # Use the legacy Excel loader for .xls files.
    if extension == ".xls":

        document = load_document(path)
        return chunk_plain_text(
            text=document.text,
            source_file=document.source_file,
        )

    # Prefer Docling for structured documents and images.
    try:
        result = _converter.convert(str(path))
        chunker = HybridChunker()
        chunks = []

        for item in chunker.chunk(dl_doc=result.document):
            text = chunker.contextualize(chunk=item).strip()

            if not text:
                continue

            chunks.append({
                "chunk_id": f"{path.name}::{len(chunks)}",
                "source_file": path.name,
                "chunk_index": len(chunks),
                "text": text,
                "method": "hybrid",
            })

        if chunks:
            return chunks

        print(f"Docling produced no chunks: {path.name}")

    except Exception as exc:
        print(f"Docling processing failed: {path.name}: {exc}")

    # Fall back to the existing document loader.
    document = load_document(path)

    return chunk_plain_text(
        text=document.text,
        source_file=document.source_file,
    )
