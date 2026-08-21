from pydantic import BaseModel


class DocumentContent(BaseModel):
    source_file: str
    file_type: str
    text: str