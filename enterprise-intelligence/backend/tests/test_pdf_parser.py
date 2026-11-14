import fitz
import pytest

from app.modules.document_intelligence.parsers.pdf_parser import (
    extract_pdf,
    PDFParsingError
)


@pytest.fixture
def sample_pdf(tmp_path):

    pdf_path = tmp_path / "sample_regulation.pdf"

    document = fitz.open()

    # Create page 1
    page1 = document.new_page()

    page1.insert_text(
        (72, 72),
        "Enterprise Intelligence Platform"
    )

    page1.insert_text(
        (72, 110),
        "Document Processing and Analysis"
    )

    # Create page 2
    page2 = document.new_page()

    page2.insert_text(
        (72, 72),
        "Regulatory Compliance Requirements"
    )

    page2.insert_text(
        (72, 110),
        "Organizations must maintain audit records."
    )

    document.save(pdf_path)
    document.close()

    return pdf_path


def test_pdf_page_count(sample_pdf):

    result = extract_pdf(sample_pdf)

    assert result["total_pages"] == 2


def test_pdf_filename(sample_pdf):

    result = extract_pdf(sample_pdf)

    assert result["filename"] == "sample_regulation.pdf"


def test_pdf_text_extraction(sample_pdf):

    result = extract_pdf(sample_pdf)

    first_page = result["pages"][0]["text"]

    assert "Enterprise Intelligence Platform" in first_page


def test_pdf_page_numbers(sample_pdf):

    result = extract_pdf(sample_pdf)

    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][1]["page_number"] == 2


def test_pdf_second_page_content(sample_pdf):

    result = extract_pdf(sample_pdf)

    second_page = result["pages"][1]["text"]

    assert "audit records" in second_page


def test_pdf_blocks_extraction(sample_pdf):

    result = extract_pdf(sample_pdf)

    assert len(result["pages"][0]["blocks"]) > 0


def test_missing_pdf():

    with pytest.raises(PDFParsingError):

        extract_pdf("missing_document.pdf")


def test_invalid_pdf(tmp_path):

    invalid_file = tmp_path / "corrupted.pdf"

    invalid_file.write_bytes(
        b"This is not a valid PDF file"
    )

    with pytest.raises(PDFParsingError):

        extract_pdf(invalid_file)


def test_wrong_extension(tmp_path):

    invalid_file = tmp_path / "document.txt"

    invalid_file.write_text(
        "This is a text document"
    )

    with pytest.raises(PDFParsingError):

        extract_pdf(invalid_file)