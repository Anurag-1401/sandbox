
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import mimetypes

from app.modules.document_intelligence.ingestion.file_detector import (
    detect_file_format
)


@dataclass
class DocumentMetadata:
    filename: str
    extension: str
    declared_mime_type: str | None
    detected_format: str
    detected_mime_type: str | None
    size_bytes: int
    size_kb: float
    size_mb: float
    modified_at: str
    is_empty: bool
    extension_matches_format: bool


SUPPORTED_FORMATS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".txt": "txt",
    ".html": "html",
    ".csv": "csv_candidate",
}


DETECTED_MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    "txt": "text/plain",
    "html": "text/html",
    "csv_candidate": "text/csv",
}


def inspect_document(
    file_path: str,
    declared_mime_type: str | None = None
) -> DocumentMetadata:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError("Provided path is not a regular file")

    stats = path.stat()

    extension = path.suffix.lower()

    detected_format = detect_file_format(str(path))

    detected_mime = DETECTED_MIME_TYPES.get(detected_format)

    if detected_mime is None:
        detected_mime = mimetypes.guess_type(path.name)[0]

    expected_format = SUPPORTED_FORMATS.get(extension)

    extension_matches = (
        expected_format == detected_format
        if expected_format is not None
        else False
    )

    size_bytes = stats.st_size

    return DocumentMetadata(
        filename=path.name,
        extension=extension,
        declared_mime_type=declared_mime_type,
        detected_format=detected_format,
        detected_mime_type=detected_mime,
        size_bytes=size_bytes,
        size_kb=round(size_bytes / 1024, 2),
        size_mb=round(size_bytes / (1024 ** 2), 4),
        modified_at=datetime.fromtimestamp(
            stats.st_mtime,
            tz=timezone.utc
        ).isoformat(),
        is_empty=size_bytes == 0,
        extension_matches_format=extension_matches
    )


if __name__ == "__main__":
    metadata = inspect_document(
        "sample_documents/regulation_2026.pdf",
        declared_mime_type="application/pdf"
    )

    print(asdict(metadata))
