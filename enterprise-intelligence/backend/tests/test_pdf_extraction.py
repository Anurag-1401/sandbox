from pathlib import Path

from app.modules.document_intelligence.parsers.pdf_parser import (
    extract_pdf
)


pdf_path = Path("data/sample_documents/regulation.pdf")

result = extract_pdf(pdf_path)

print("\nDOCUMENT INFORMATION")
print("====================")

print("Filename:", result["filename"])
print("Total pages:", result["total_pages"])

print("\nMETADATA")
print("========")

for key, value in result["metadata"].items():
    print(f"{key}: {value}")

print("\nEXTRACTED CONTENT")
print("=================")

for page in result["pages"]:

    print(f"\nPAGE {page['page_number']}")
    print("-" * 40)

    print(page["text"])

    print("\nNumber of text blocks:", len(page["blocks"]))