
from __future__ import annotations

import logging
import tempfile

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.rbac import (
    Permission,
    require_permission,
)
from app.core.security.principal import UserPrincipal

from app.db.session import get_db

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.document_chunk import DocumentChunk

from app.modules.document_intelligence.fingerprinting.hasher import (
    generate_file_hash,
)
from app.modules.document_intelligence.parsers.pdf_parser import (
    extract_pdf,
    PDFParsingError,
)
from app.modules.document_intelligence.validation.exceptions import (
    DocumentValidationError,
)
from app.modules.document_intelligence.validation.file_validator import (
    FileValidator,
)
from app.modules.document_intelligence.validation.structure_validator import (
    validate_pdf_structure,
)

from app.modules.search.indexing import DocumentIndexingService
from app.modules.search.chunking import DocumentChunker
from app.modules.search.embeddings import EmbeddingService
from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)

from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentProcessingSummary,
    DocumentUploadResponse,
    DocumentVersionListResponse,
    DocumentVersionResponse,
)

from app.storage.local_storage import LocalFileStorage


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

storage = LocalFileStorage()

validator = FileValidator(
    max_file_size_mb=settings.max_upload_size_mb
)

chunker = DocumentChunker()

embedding_service = DocumentEmbeddingService(
    embedding_service=EmbeddingService(),
)

indexing_service = DocumentIndexingService(
    chunker=chunker,
    embedding_service=embedding_service,
)


def get_document_or_404(
    db: Session,
    principal: UserPrincipal,
    document_id: UUID,
) -> Document:
    document = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == principal.organization_id,
            Document.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


def get_storage_path(storage_key: str) -> Path:
    root = storage.root.resolve()
    path = (root / storage_key).resolve()

    if root not in path.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid storage reference.",
        )

    return path


async def write_upload_to_temp_file(
    upload: UploadFile,
) -> Path:
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    total_bytes = 0

    temporary = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        prefix="enterprise-upload-",
        delete=False,
    )

    temp_path = Path(temporary.name)

    try:
        with temporary:
            while True:
                content = await upload.read(1024 * 1024)

                if not content:
                    break

                total_bytes += len(content)

                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded file exceeds the size limit.",
                    )

                temporary.write(content)

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        return temp_path

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def get_document_counts(
    db: Session,
    document_id: UUID,
    organization_id: UUID,
) -> tuple[int, int, int | None, str | None]:
    version_count = db.execute(
        select(func.count())
        .select_from(DocumentVersion)
        .where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.organization_id == organization_id,
        )
    ).scalar_one()

    latest = db.execute(
        select(
            DocumentVersion.version_number,
            DocumentVersion.status,
        )
        .where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.organization_id == organization_id,
        )
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    ).first()

    chunk_count = db.execute(
        select(func.count())
        .select_from(DocumentChunk)
        .join(
            DocumentVersion,
            DocumentVersion.id == DocumentChunk.version_id,
        )
        .where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.organization_id == organization_id,
            DocumentChunk.organization_id == organization_id,
        )
    ).scalar_one()

    return (
        version_count,
        chunk_count,
        latest.version_number if latest else None,
        latest.status if latest else None,
    )


def build_document_list_item(
    db: Session,
    document: Document,
    organization_id: UUID,
) -> DocumentListItem:
    version_count, chunk_count, latest_number, latest_status = (
        get_document_counts(
            db,
            document.id,
            organization_id,
        )
    )

    return DocumentListItem(
        id=document.id,
        title=document.title,
        source_filename=document.source_filename,
        status=document.status,
        visibility=document.visibility,
        created_at=document.created_at,
        updated_at=document.updated_at,
        latest_version_number=latest_number,
        latest_version_status=latest_status,
        version_count=version_count,
        chunk_count=chunk_count,
    )


def ingest_pdf(
    *,
    db: Session,
    principal: UserPrincipal,
    temp_path: Path,
    original_filename: str,
    existing_document: Document | None = None,
) -> DocumentUploadResponse:
    stored_key: str | None = None

    try:
        validation = validator.validate(temp_path)

        if not validation["valid"]:
            raise HTTPException(
                status_code=422,
                detail="File validation failed.",
            )

        pdf_structure = validate_pdf_structure(temp_path)
        content_hash = generate_file_hash(str(temp_path))
        parsed = extract_pdf(temp_path)
        pages = parsed["pages"]

        if not any(
            (page.get("text") or "").strip()
            for page in pages
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "This PDF contains no extractable text. "
                    "Scanned PDFs require OCR, which is not implemented."
                ),
            )

        document_id = (
            existing_document.id
            if existing_document is not None
            else uuid4()
        )

        if existing_document is None:
            title = (
                (parsed.get("metadata") or {}).get("title")
                or Path(original_filename).stem
            )

            document = Document(
                id=document_id,
                organization_id=principal.organization_id,
                owner_user_id=principal.user_id,
                title=title[:500],
                source_filename=original_filename[:500],
                visibility="organization",
                is_active=True,
                status="processing",
            )

            db.add(document)
            db.flush()

            version_number = 1

        else:
            document = existing_document

            latest_number = db.execute(
                select(func.max(DocumentVersion.version_number))
                .where(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.organization_id
                    == principal.organization_id,
                )
            ).scalar_one()

            version_number = (latest_number or 0) + 1
            document.status = "processing"

        version_id = uuid4()

        stored_key = storage.store(
            source_path=temp_path,
            organization_id=principal.organization_id,
            document_id=document.id,
            version_id=version_id,
        )

        version = DocumentVersion(
            id=version_id,
            document_id=document.id,
            organization_id=principal.organization_id,
            version_number=version_number,
            content_hash=content_hash,
            storage_key=stored_key,
            status="processing",
        )

        db.add(version)
        db.flush()

        indexing_result = indexing_service.index_pages(
            db=db,
            organization_id=principal.organization_id,
            version_id=version_id,
            pages=pages,
        )

        version.status = "indexed"
        document.status = "indexed"

        db.commit()

        return DocumentUploadResponse(
            document_id=document.id,
            version_id=version_id,
            title=document.title,
            filename=original_filename,
            sha256=content_hash,
            pages_extracted=pdf_structure["page_count"],
            chunks_indexed=indexing_result.chunks_indexed,
            embedding_dimension=settings.embedding_dimension,
            status="indexed",
            message="PDF uploaded, parsed, and indexed successfully.",
        )

    except HTTPException:
        db.rollback()

        if stored_key:
            storage.delete(stored_key)

        raise

    except (
        DocumentValidationError,
        PDFParsingError,
        ValueError,
    ) as exc:
        db.rollback()

        if stored_key:
            storage.delete(stored_key)

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        if stored_key:
            try:
                storage.delete(stored_key)
            except Exception:
                logger.exception("Failed to remove stored upload.")

        logger.exception(
            "Document ingestion failed",
            extra={
                "organization_id": str(principal.organization_id),
                "user_id": str(principal.user_id),
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Check backend logs.",
        ) from exc


@router.get(
    "",
    response_model=DocumentListResponse,
)
def list_documents(
    q: str | None = Query(default=None, max_length=200),
    document_status: str | None = Query(
        default=None,
        alias="status",
        max_length=30,
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_READ)
    ),
):
    statement = select(Document).where(
        Document.organization_id == principal.organization_id,
        Document.is_active.is_(True),
    )

    if q:
        search = f"%{q.strip()}%"
        statement = statement.where(
            Document.title.ilike(search)
            | Document.source_filename.ilike(search)
        )

    if document_status:
        statement = statement.where(
            Document.status == document_status
        )

    total = db.execute(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ).scalar_one()

    documents = db.execute(
        statement
        .order_by(Document.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    items = [
        build_document_list_item(
            db,
            document,
            principal.organization_id,
        )
        for document in documents
    ]

    return DocumentListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/summary",
    response_model=DocumentProcessingSummary,
)
def document_summary(
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_READ)
    ),
):
    total_documents = db.execute(
        select(func.count())
        .select_from(Document)
        .where(
            Document.organization_id == principal.organization_id,
            Document.is_active.is_(True),
        )
    ).scalar_one()

    indexed_documents = db.execute(
        select(func.count())
        .select_from(Document)
        .where(
            Document.organization_id == principal.organization_id,
            Document.is_active.is_(True),
            Document.status == "indexed",
        )
    ).scalar_one()

    processing_documents = db.execute(
        select(func.count())
        .select_from(Document)
        .where(
            Document.organization_id == principal.organization_id,
            Document.is_active.is_(True),
            Document.status == "processing",
        )
    ).scalar_one()

    failed_documents = db.execute(
        select(func.count())
        .select_from(Document)
        .where(
            Document.organization_id == principal.organization_id,
            Document.is_active.is_(True),
            Document.status == "failed",
        )
    ).scalar_one()

    total_versions = db.execute(
        select(func.count())
        .select_from(DocumentVersion)
        .where(
            DocumentVersion.organization_id == principal.organization_id,
        )
    ).scalar_one()

    total_chunks = db.execute(
        select(func.count())
        .select_from(DocumentChunk)
        .where(
            DocumentChunk.organization_id == principal.organization_id,
        )
    ).scalar_one()

    return DocumentProcessingSummary(
        total_documents=total_documents,
        indexed_documents=indexed_documents,
        processing_documents=processing_documents,
        failed_documents=failed_documents,
        total_versions=total_versions,
        total_chunks=total_chunks,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_MANAGE)
    ),
):
    temp_path: Path | None = None

    try:
        original_filename = Path(
            (file.filename or "").replace("\\", "/")
        ).name

        if not original_filename:
            raise HTTPException(
                status_code=400,
                detail="A valid filename is required.",
            )

        if Path(original_filename).suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=415,
                detail="Only PDF files are currently supported.",
            )

        temp_path = await write_upload_to_temp_file(file)

        return ingest_pdf(
            db=db,
            principal=principal,
            temp_path=temp_path,
            original_filename=original_filename,
        )

    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

        await file.close()


@router.post(
    "/{document_id}/versions",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_version(
    document_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_MANAGE)
    ),
):
    temp_path: Path | None = None

    try:
        document = get_document_or_404(
            db,
            principal,
            document_id,
        )

        if Path((file.filename or "").replace("\\", "/")).suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=415,
                detail="Only PDF files are currently supported.",
            )

        temp_path = await write_upload_to_temp_file(file)

        return ingest_pdf(
            db=db,
            principal=principal,
            temp_path=temp_path,
            original_filename=Path(file.filename or "document.pdf").name,
            existing_document=document,
        )

    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

        await file.close()


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_READ)
    ),
):
    document = get_document_or_404(
        db,
        principal,
        document_id,
    )

    version_count, chunk_count, latest_number, latest_status = (
        get_document_counts(
            db,
            document.id,
            principal.organization_id,
        )
    )

    return DocumentDetailResponse(
        id=document.id,
        title=document.title,
        source_filename=document.source_filename,
        status=document.status,
        visibility=document.visibility,
        created_at=document.created_at,
        updated_at=document.updated_at,
        latest_version_number=latest_number,
        latest_version_status=latest_status,
        version_count=version_count,
        chunk_count=chunk_count,
    )


@router.get(
    "/{document_id}/versions",
    response_model=DocumentVersionListResponse,
)
def list_document_versions(
    document_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_READ)
    ),
):
    get_document_or_404(
        db,
        principal,
        document_id,
    )

    versions = db.execute(
        select(DocumentVersion)
        .where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.organization_id == principal.organization_id,
        )
        .order_by(DocumentVersion.version_number.desc())
    ).scalars().all()

    items = []

    for version in versions:
        count = db.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(
                DocumentChunk.version_id == version.id,
                DocumentChunk.organization_id
                == principal.organization_id,
            )
        ).scalar_one()

        items.append(
            DocumentVersionResponse(
                id=version.id,
                document_id=version.document_id,
                version_number=version.version_number,
                content_hash=version.content_hash,
                status=version.status,
                created_at=version.created_at,
                chunk_count=count,
            )
        )

    return DocumentVersionListResponse(
        items=items,
        total=len(items),
    )


@router.get(
    "/{document_id}/versions/{version_id}/download",
)
def download_document_version(
    document_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(
        require_permission(Permission.DOCUMENTS_READ)
    ),
):
    get_document_or_404(
        db,
        principal,
        document_id,
    )

    version = db.execute(
        select(DocumentVersion)
        .where(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == document_id,
            DocumentVersion.organization_id == principal.organization_id,
        )
    ).scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Document version not found.",
        )

    path = get_storage_path(version.storage_key)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Original document file is unavailable.",
        )

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"{document_id}-v{version.version_number}.pdf",
    )
