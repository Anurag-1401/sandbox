import pytest
import fitz


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a valid two-page PDF for testing."""

    pdf_path = tmp_path / "sample.pdf"

    document = fitz.open()

    page1 = document.new_page()
    page1.insert_text(
        (72, 72),
        "Enterprise Intelligence Platform - Page 1"
    )

    page2 = document.new_page()
    page2.insert_text(
        (72, 72),
        "Document Intelligence - Page 2"
    )

    document.save(pdf_path)
    document.close()

    return pdf_path


@pytest.fixture
def corrupted_pdf(tmp_path):
    """Create a file containing invalid PDF data."""

    pdf_path = tmp_path / "corrupted.pdf"

    pdf_path.write_bytes(
        b"This is not a valid PDF document"
    )

    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Create a valid PDF containing no pages."""

    pdf_path = tmp_path / "empty.pdf"

    document = fitz.open()
    document.save(pdf_path)
    document.close()

    return pdf_path