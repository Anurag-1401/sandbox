from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    title: str
    filename: str
    sha256: str
    pages_extracted: int
    chunks_indexed: int
    embedding_dimension: int
    status: str
    message: str


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source_filename: str
    status: str
    created_at: datetime