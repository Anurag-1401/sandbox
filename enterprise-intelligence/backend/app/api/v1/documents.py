import logging
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.organization import Organization
from app.db.session import get_db
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
from app.schemas.documents import DocumentUploadResponse
from app.storage.local_storage import LocalFileStorage
from app.modules.search.chunking import DocumentChunker
from app.modules.search.embeddings import EmbeddingService
from app.modules.search.embedding_service import (
    DocumentEmbeddingService,
)

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
def get_development_organization(db: Session) -> Organization:
    """
    Resolve the configured single development organization.

    This is temporary until authentication and organization
    membership authorization are implemented.
    """

    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The unauthenticated development upload endpoint "
                "is disabled outside development mode."
            ),
        )

    organization = db.execute(
        select(Organization).where(
            Organization.id == settings.default_organization_id
        )
    ).scalar_one_or_none()

    if organization is None:
        organization = Organization(
            id=settings.default_organization_id,
            name=settings.default_organization_name,
        )
        db.add(organization)
        db.flush()

    return organization


async def write_upload_to_temp_file(
    upload: UploadFile,
) -> Path:
    """
    Stream the uploaded file to a temporary file while enforcing
    the maximum upload size.
    """

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


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    temp_path: Path | None = None
    stored_key: str | None = None

    try:
        # 1. Validate the original filename.
        original_filename = (
            Path((file.filename or "").replace("\\", "/")).name
        )

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

        # 2. Stream to a temporary file with a size limit.
        temp_path = await write_upload_to_temp_file(file)

        # 3. Reuse the existing M1 file validator.
        validation = validator.validate(temp_path)

        if not validation["valid"]:
            raise HTTPException(
                status_code=422,
                detail="File validation failed.",
            )

        # 4. Validate the actual PDF structure.
        pdf_structure = validate_pdf_structure(temp_path)

        # 5. Calculate SHA-256.
        content_hash = generate_file_hash(str(temp_path))

        # 6. Parse the PDF using the existing M1 parser.
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
                    "Scanned PDFs require OCR, which is not "
                    "implemented in this upload pipeline yet."
                ),
            )

        # 7. Resolve the development organization.
        organization = get_development_organization(db)

        # 8. Create document and version identifiers.
        document_id = uuid4()
        version_id = uuid4()

        title = (
            (parsed.get("metadata") or {}).get("title")
            or Path(original_filename).stem
        )

        # 9. Save the original file in local development storage.
        stored_key = storage.store(
            source_path=temp_path,
            organization_id=organization.id,
            document_id=document_id,
            version_id=version_id,
        )

        # 10. Create database records.
        document = Document(
            id=document_id,
            organization_id=organization.id,
            title=title[:500],
            source_filename=original_filename[:500],
            # content_hash=content_hash,
            status="processing",
        )

        version = DocumentVersion(
            id=version_id,
            document_id=document_id,
            organization_id=organization.id,
            version_number=1,
            content_hash=content_hash,
            storage_key=stored_key,
            status="processing",
        )

        db.add_all([document, version])
        db.flush()

        indexing_result = indexing_service.index_pages(
    db=db,
    organization_id=organization.id,
    version_id=version_id,
    pages=pages,
)

        chunks_indexed = indexing_result.chunks_indexed

        # 12. Mark processing as complete.
        document.status = "indexed"
        version.status = "indexed"

        db.commit()

        return DocumentUploadResponse(
            document_id=document_id,
            version_id=version_id,
            title=title,
            filename=original_filename,
            sha256=content_hash,
            pages_extracted=pdf_structure["page_count"],
            chunks_indexed=chunks_indexed,
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
                logger.exception(
                    "Failed to remove uploaded file after ingestion error"
                )

        logger.exception("Document ingestion failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Document ingestion failed. "
                "Check backend logs for the underlying error."
            ),
        ) from exc

    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

        await file.close()