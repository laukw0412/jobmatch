from pathlib import Path

from jobmatch.document.models import CoreDocument


DOCUMENTS_DIR = Path(__file__).resolve().parents[3] / "data" / "documents"
DEFAULT_MAX_INPUT_CHARS = 60_000


def load_core_documents(file_paths: list[str | Path], max_chars: int = DEFAULT_MAX_INPUT_CHARS) -> list[CoreDocument]:
    """Read only explicitly selected core files without truncating their parsed text."""
    if not file_paths:
        raise ValueError("Select at least one core document.")
    if max_chars < 1:
        raise ValueError("max_chars must be positive.")

    documents = []
    seen = set()
    total_chars = 0
    root = DOCUMENTS_DIR.resolve()

    for file_path in file_paths:
        path = Path(file_path).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Core documents must be inside data/documents/.")
        if path in seen:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"Core document not found: {path.name}")

        try:
            if path.suffix.lower() in {".txt", ".md"}:
                text = path.read_text(encoding="utf-8-sig")
            else:
                # load document parsers only when a selected file requires them
                from jobmatch.document.loader import load_document

                text = load_document(path).text
        except Exception as exc:
            raise ValueError(f"Could not read core document: {path.name}") from exc

        if not text.strip():
            raise ValueError(f"Core document has no readable text: {path.name}")
        total_chars += len(text)
        if total_chars > max_chars:
            raise ValueError("Core documents exceed the character budget; select fewer files or raise the limit.")

        documents.append(CoreDocument(source_file=path.name, source_path=str(path), text=text))
        seen.add(path)

    return documents
