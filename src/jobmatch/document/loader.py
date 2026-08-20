from pathlib import Path
from jobmatch.document.extractor import (
    extract_pdf,
    extract_docx,
    extract_xlsx,
    extract_xls,
    extract_image,
)


def load_document(file_path):
    path = Path(file_path)

    # path = Path("data/documents/resume.pdf")

    # path.name
    # File name, e.g. "resume.pdf"

    # path.suffix
    # File extension, e.g. ".pdf"

    # path.suffix.lower
    # Get the file extension and normalize it to lowercase
    # (e.g. ".PDF" -> ".pdf")

    if path.suffix.lower() == ".pdf":
        return extract_pdf(path)

    if path.suffix.lower() == ".docx":
        return extract_docx(path)

    if path.suffix.lower() == ".xlsx":
        return extract_xlsx(path)

    if path.suffix.lower() == ".xls":
        return extract_xls(path)

    if path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        return extract_image(path)

    raise ValueError(f"Unsupported file type: {path.suffix}")