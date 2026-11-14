import pytest

from app.modules.search.chunking import DocumentChunker


class FakeTokenizer:
    model_max_length = 256

    def encode(self, text, add_special_tokens=False):
        return text.split()

    def decode(self, token_ids, skip_special_tokens=True):
        return " ".join(token_ids)


@pytest.fixture
def chunker():
    return DocumentChunker(
        chunk_size=5,
        overlap=2,
        tokenizer=FakeTokenizer(),
    )


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=0,
            tokenizer=FakeTokenizer(),
        )


def test_invalid_overlap():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=5,
            overlap=5,
            tokenizer=FakeTokenizer(),
        )


def test_negative_overlap():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=5,
            overlap=-1,
            tokenizer=FakeTokenizer(),
        )


def test_empty_text_returns_no_chunks(chunker):
    assert chunker.chunk_text("") == []
    assert chunker.chunk_text("   ") == []


def test_single_chunk(chunker):
    chunks = chunker.chunk_text("one two three")

    assert len(chunks) == 1
    assert chunks[0].content == "one two three"
    assert chunks[0].token_count == 3


def test_multiple_chunks(chunker):
    chunks = chunker.chunk_text(
        "one two three four five six seven eight"
    )

    assert len(chunks) == 2
    assert chunks[0].content == "one two three four five"
    assert chunks[1].content == "four five six seven eight"


def test_chunk_indices_are_sequential(chunker):
    chunks = chunker.chunk_text(
        "one two three four five six seven eight nine"
    )

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_page_provenance(chunker):
    chunks = chunker.chunk_text(
        "one two three four five six",
        page_number=7,
    )

    assert all(chunk.page_start == 7 for chunk in chunks)
    assert all(chunk.page_end == 7 for chunk in chunks)


def test_chunk_pages_preserves_page_numbers(chunker):
    pages = [
        {"page_number": 1, "text": "one two three four five six"},
        {"page_number": 2, "text": "seven eight nine"},
    ]

    chunks = chunker.chunk_pages(pages)

    assert chunks
    assert all(chunk.index == i for i, chunk in enumerate(chunks))
    assert {chunk.page_start for chunk in chunks} == {1, 2}


def test_chunk_size_respects_model_limit():
    with pytest.raises(ValueError):
        DocumentChunker(
            chunk_size=300,
            overlap=20,
            tokenizer=FakeTokenizer(),
        )