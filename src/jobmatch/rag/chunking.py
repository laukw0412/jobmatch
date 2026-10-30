
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

    # Use LangChain's splitter to set the rule for chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=min(100, max_chars // 5),
    )

    # Use the splitter to split text into chunks
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
    """Extract and chunk a document for RAG indexing."""

    path = Path(file_path)

    # Validate the input file
    if not path.is_file():
        raise FileNotFoundError(path)

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    # Select the chunking method based on the file type
    if extension in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8-sig")
        return chunk_plain_text(text, path.name)

    elif extension == ".xls":
        document = load_document(path)
        text = document.text
        source_file = document.source_file

        return chunk_plain_text(text, source_file)

    else:
        # =====================================================
        # Try Docling HybridChunker for other supported formats
        try:
            result = _converter.convert(str(path))
            chunker = HybridChunker()
            chunks = []

            for item in chunker.chunk(dl_doc=result.document):
                text = chunker.contextualize(chunk=item).strip()

                # Skip empty chunks ("")
                if not text:
                    continue

                chunks.append({
                    "chunk_id": f"{path.name}::{len(chunks)}",
                    "source_file": path.name,
                    "chunk_index": len(chunks),
                    "text": text,
                    "method": "hybrid",
                })
            # -------------------------------------------------
            # Return chunks if the list is not empty
            if chunks:
                return chunks
            else:
                print(f"Docling produced no chunks: {path.name}")
            # -------------------------------------------------
        # =====================================================
        except Exception as exc:
            print(f"Docling processing failed: {path.name}: {exc}")

        # Fallback if Docling fails or produces no chunks
        document = load_document(path)
        text = document.text
        source_file = document.source_file

        return chunk_plain_text(text,source_file)
