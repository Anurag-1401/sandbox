import os
import uuid

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.modules.search.repository import (
    ChunkRecord,
    SearchRepository,
)


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def db():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not configured")

    engine = create_engine(TEST_DATABASE_URL)

    with Session(engine) as session:
        transaction = session.begin()

        try:
            yield session
        finally:
            transaction.rollback()

    engine.dispose()


def unit_vector(index: int) -> list[float]:
    vector = np.zeros(384, dtype=np.float32)
    vector[index] = 1.0
    return vector.tolist()


def create_document_version(db, organization_id):
    document = Document(
        id=uuid.uuid4(),
        organization_id=organization_id,
        title="Certification Regulation",
        source_filename="regulation.pdf",
    )

    version = DocumentVersion(
        id=uuid.uuid4(),
        document_id=document.id,
        organization_id=organization_id,
        version_number=1,
        content_hash="a" * 64,
        storage_key=f"test/{uuid.uuid4()}.pdf",
    )

    db.add_all([document, version])
    db.flush()

    return document, version


def test_semantic_search_respects_organization_scope(db):
    org_a = Organization(id=uuid.uuid4(), name="Test Org A")
    org_b = Organization(id=uuid.uuid4(), name="Test Org B")

    db.add_all([org_a, org_b])
    db.flush()

    doc_a, version_a = create_document_version(db, org_a.id)
    doc_b, version_b = create_document_version(db, org_b.id)

    repository = SearchRepository(db)

    repository.replace_version_chunks(
        organization_id=org_a.id,
        version_id=version_a.id,
        chunks=[
            ChunkRecord(
                chunk_index=0,
                content="Certification must be renewed annually.",
                token_count=6,
                page_start=2,
                page_end=2,
                embedding=unit_vector(0),
            )
        ],
    )

    repository.replace_version_chunks(
        organization_id=org_b.id,
        version_id=version_b.id,
        chunks=[
            ChunkRecord(
                chunk_index=0,
                content="Confidential organization B information.",
                token_count=5,
                page_start=4,
                page_end=4,
                embedding=unit_vector(0),
            )
        ],
    )

    results = repository.semantic_search(
        organization_id=org_a.id,
        query_embedding=unit_vector(0),
        top_k=10,
    )

    assert len(results) == 1
    assert results[0].document_id == doc_a.id
    assert results[0].document_id != doc_b.id
    assert results[0].page_start == 2
    assert results[0].similarity == pytest.approx(1.0)