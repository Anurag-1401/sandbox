
from pathlib import Path
import zipfile


def detect_file_format(file_path: str) -> str:
    """
    Detect a file's likely format using its binary signature
    and, where needed, its internal structure.
    """

    path = Path(file_path)

    with path.open("rb") as file:
        header = file.read(8192)

    if not header:
        return "empty"

    # PDF signature
    if header.startswith(b"%PDF-"):
        return "pdf"

    # PNG signature
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    # JPEG signature
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    # ZIP-based formats: DOCX and XLSX
    if zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())

                if (
                    "[Content_Types].xml" in names
                    and "word/document.xml" in names
                ):
                    return "docx"

                if (
                    "[Content_Types].xml" in names
                    and "xl/workbook.xml" in names
                ):
                    return "xlsx"

                return "zip"

        except (zipfile.BadZipFile, OSError):
            return "invalid_zip"

    # HTML detection
    stripped = header.lstrip().lower()

    if (
        stripped.startswith(b"<!doctype html")
        or stripped.startswith(b"<html")
    ):
        return "html"

    # Text-based detection
    try:
        text = header.decode("utf-8")
    except UnicodeDecodeError:
        return "unknown"

    if "\x00" in text:
        return "unknown"

    if "," in text or ";" in text or "\t" in text:
        return "csv_candidate"

    return "txt"
