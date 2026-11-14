from pathlib import Path
from typing import Any

import fitz


class PDFParsingError(Exception):
    """Raised when a PDF cannot be processed."""


def extract_pdf(path: str | Path) -> dict[str, Any]:
    """
    Extract text, page information and metadata from a PDF.

    Args:
        path: Path to the PDF file.

    Returns:
        Structured dictionary containing extracted content.

    Raises:
        PDFParsingError: If the PDF cannot be opened or processed.
    """

    file_path = Path(path)

    # 1. Verify file existence
    if not file_path.exists():
        raise PDFParsingError(
            f"File not found: {file_path}"
        )

    if not file_path.is_file():
        raise PDFParsingError(
            f"Path is not a file: {file_path}"
        )

    # 2. Verify extension
    if file_path.suffix.lower() != ".pdf":
        raise PDFParsingError(
            "Unsupported file extension. Expected PDF."
        )

    try:
        # 3. Open PDF
        with fitz.open(file_path) as document:

            # 4. Check password protection
            if document.needs_pass:
                raise PDFParsingError(
                    "PDF is password protected."
                )

            # 5. Check empty document
            if document.page_count == 0:
                raise PDFParsingError(
                    "PDF contains no pages."
                )

            extracted_pages = []

            # 6. Extract every page
            for page_index in range(document.page_count):

                page = document.load_page(page_index)

                # Extract text in approximately reading order
                text = page.get_text(
                    "text",
                    sort=True
                )

                # Extract individual text blocks
                raw_blocks = page.get_text(
                    "blocks",
                    sort=True
                )

                blocks = []

                for block in raw_blocks:

                    # Text blocks contain text at index 4.
                    # Image blocks and other blocks are ignored here.
                    if len(block) >= 7 and block[6] == 0:

                        block_text = block[4].strip()

                        if block_text:
                            blocks.append({
                                "text": block_text,
                                "bbox": [
                                    block[0],
                                    block[1],
                                    block[2],
                                    block[3]
                                ]
                            })

                extracted_pages.append({
                    "page_number": page_index + 1,
                    "text": text.strip(),
                    "blocks": blocks
                })

            # 7. Extract metadata
            metadata = document.metadata or {}

            # 8. Return structured output
            return {
                "filename": file_path.name,
                "total_pages": document.page_count,
                "metadata": metadata,
                "pages": extracted_pages
            }

    except PDFParsingError:
        raise

    except (fitz.FileDataError, RuntimeError, ValueError, OSError) as error:

        raise PDFParsingError(
            f"Unable to process PDF: {error}"
        ) from error