from app.modules.document_intelligence.fingerprinting.hasher import generate_hash


def test_same_content_produces_same_hash():

    file_a = b"Enterprise Policy 2026"
    file_b = b"Enterprise Policy 2026"

    hash_a = generate_hash(file_a)
    hash_b = generate_hash(file_b)

    assert hash_a == hash_b


def test_different_content_produces_different_hash():

    file_a = b"Enterprise Policy 2026"
    file_b = b"Enterprise Policy 2027"

    hash_a = generate_hash(file_a)
    hash_b = generate_hash(file_b)

    assert hash_a != hash_b


def test_hash_length_is_64():

    content = b"Enterprise Intelligence"

    result = generate_hash(content)

    assert len(result) == 64