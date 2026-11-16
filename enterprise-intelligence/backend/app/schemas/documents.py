
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
    id: UUID
    title: str
    source_filename: str
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    latest_version_number: int | None
    latest_version_status: str | None
    version_count: int
    chunk_count: int


class DocumentDetailResponse(BaseModel):
    id: UUID
    title: str
    source_filename: str
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    latest_version_number: int | None
    latest_version_status: str | None
    version_count: int
    chunk_count: int


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    content_hash: str
    status: str
    created_at: datetime
    chunk_count: int


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int
    limit: int
    offset: int


class DocumentVersionListResponse(BaseModel):
    items: list[DocumentVersionResponse]
    total: int


class DocumentProcessingSummary(BaseModel):
    total_documents: int
    indexed_documents: int
    processing_documents: int
    failed_documents: int
    total_versions: int
    total_chunks: int
