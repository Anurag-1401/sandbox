from app.modules.document_intelligence.fingerprinting.hasher import (
    generate_file_hash
)


def find_duplicate(
    file_path: str,
    existing_hashes: dict[str, str]
) -> str | None:

    new_hash = generate_file_hash(file_path)

    for document_id, existing_hash in existing_hashes.items():

        if new_hash == existing_hash:

            return document_id

    return None