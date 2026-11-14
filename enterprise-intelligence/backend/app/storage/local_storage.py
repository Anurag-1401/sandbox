from pathlib import Path
from shutil import copyfile
from uuid import UUID

from app.core.config import settings


class LocalFileStorage:
    def __init__(self) -> None:
        self.root = settings.storage_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        source_path: Path,
        organization_id: UUID,
        document_id: UUID,
        version_id: UUID,
    ) -> str:
        relative_key = (
            Path(str(organization_id))
            / str(document_id)
            / str(version_id)
            / "original.pdf"
        )

        destination = self.root / relative_key
        destination.parent.mkdir(parents=True, exist_ok=True)

        copyfile(source_path, destination)

        return relative_key.as_posix()

    def delete(self, storage_key: str) -> None:
        candidate = (self.root / storage_key).resolve()

        # Prevent paths escaping the storage directory.
        if self.root not in candidate.parents:
            raise ValueError("Invalid storage key")

        if candidate.exists() and candidate.is_file():
            candidate.unlink()