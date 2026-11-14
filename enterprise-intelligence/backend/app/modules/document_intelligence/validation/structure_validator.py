from pathlib import Path
import fitz

from app.modules.document_intelligence.validation.exceptions import (
    CorruptedDocumentError,
    EncryptedDocumentError,
)


def validate_pdf_structure(file_path: Path):

    try:

        with fitz.open(file_path) as document:

            if document.needs_pass:
                raise EncryptedDocumentError(
                    "PDF requires a password."
                )

            if document.page_count == 0:
                raise CorruptedDocumentError(
                    "PDF contains no pages."
                )

            return {
                "valid": True,
                "page_count": document.page_count,
                "encrypted": document.is_encrypted,
            }

    except (EncryptedDocumentError, CorruptedDocumentError):
        raise

    except Exception as error:

        raise CorruptedDocumentError(
            f"Unable to parse PDF: {error}"
        ) from error