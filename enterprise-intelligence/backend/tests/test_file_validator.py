import pytest

from pathlib import Path

from app.modules.document_intelligence.validation.file_validator import (
    FileValidator,
)

from app.modules.document_intelligence.validation.exceptions import (
    EmptyFileError,
    InvalidFileSignatureError,
    UnsupportedFileTypeError,
    FileSizeExceededError,
)


@pytest.fixture
def validator():
    return FileValidator(max_file_size_mb=1)


def test_empty_file(tmp_path, validator):

    file = tmp_path / "empty.pdf"
    file.write_bytes(b"")

    with pytest.raises(EmptyFileError):
        validator.validate(file)


def test_invalid_signature(tmp_path, validator):

    file = tmp_path / "fake.pdf"
    file.write_bytes(b"Hello World")

    with pytest.raises(InvalidFileSignatureError):
        validator.validate(file)


def test_unsupported_extension(tmp_path, validator):

    file = tmp_path / "program.exe"
    file.write_bytes(b"MZ")

    with pytest.raises(UnsupportedFileTypeError):
        validator.validate(file)


def test_oversized_file(tmp_path, validator):

    file = tmp_path / "large.txt"
    file.write_bytes(b"A" * (2 * 1024 * 1024))

    with pytest.raises(FileSizeExceededError):
        validator.validate(file)


def test_valid_pdf(tmp_path, validator):

    import fitz

    file = tmp_path / "valid.pdf"

    with fitz.open() as document:
        document.new_page()
        document.save(file)

    result = validator.validate(file)

    assert result["valid"] is True
    assert result["extension"] == ".pdf"