from pathlib import Path

from app.modules.document_intelligence.validation.exceptions import (
    UnsupportedFileTypeError,
    FileSizeExceededError,
    EmptyFileError,
    InvalidFileSignatureError,
)

from app.modules.document_intelligence.validation.signatures import (
    FILE_SIGNATURES,
    SUPPORTED_EXTENSIONS,
)


class FileValidator:

    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size = max_file_size_mb * 1024 * 1024

    def validate_extension(self, file_path: Path):

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension: {extension}"
            )

        return extension

    def validate_size(self, file_path: Path):

        size = file_path.stat().st_size

        if size == 0:
            raise EmptyFileError("Uploaded file is empty.")

        if size > self.max_file_size:
            raise FileSizeExceededError(
                "File exceeds the maximum allowed size."
            )

    def validate_signature(self, file_path: Path, extension: str):

        expected_signatures = FILE_SIGNATURES.get(extension)

        if not expected_signatures:
            return

        with file_path.open("rb") as file:
            header = file.read(16)

        if not any(
            header.startswith(signature)
            for signature in expected_signatures
        ):
            raise InvalidFileSignatureError(
                "File signature does not match its extension."
            )

    def validate(self, file_path: Path):

        extension = self.validate_extension(file_path)

        self.validate_size(file_path)

        self.validate_signature(file_path, extension)

        return {
            "valid": True,
            "filename": file_path.name,
            "extension": extension,
            "size_bytes": file_path.stat().st_size,
        }