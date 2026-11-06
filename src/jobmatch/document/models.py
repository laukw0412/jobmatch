from pydantic import BaseModel
from pydantic import Field


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".txt", ".md"}


class DocumentContent(BaseModel):
    source_file: str
    file_type: str
    text: str


class CoreDocument(BaseModel):
    source_file: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    text: str = Field(min_length=1)
