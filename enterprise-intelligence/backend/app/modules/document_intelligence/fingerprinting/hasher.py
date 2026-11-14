import hashlib
from pathlib import Path


def generate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def generate_file_hash(file_path: str) -> str:
    """
    Generate SHA-256 fingerprint of a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(lambda: file.read(1024 * 1024), b""):

            sha256.update(chunk)

    return sha256.hexdigest()