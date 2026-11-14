from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


class ModelRegistry:
    """File-based model manifest registry.

    Model files are immutable versioned artifacts. The latest.json pointer
    is updated only after a model has been evaluated and registered.
    """

    def __init__(self, root: Path | None = None):
        self.root = Path(root or settings.ml_model_root)

    def _model_dir(self, name: str) -> Path:
        safe_name = "".join(
            c for c in name if c.isalnum() or c in "-_"
        )
        if not safe_name:
            raise ValueError("Invalid model name.")
        return self.root / safe_name

    @staticmethod
    def checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def register(
        self,
        *,
        name: str,
        version: str,
        artifact_path: str | Path,
        task: str,
        labels: list[str],
        metrics: dict[str, Any],
        dataset_version: str,
    ) -> dict[str, Any]:
        artifact = Path(artifact_path).resolve()

        if not artifact.exists() or not artifact.is_file():
            raise FileNotFoundError(artifact)

        directory = self._model_dir(name)
        directory.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": name,
            "version": version,
            "task": task,
            "artifact": str(artifact),
            "sha256": self.checksum(artifact),
            "labels": labels,
            "metrics": metrics,
            "dataset_version": dataset_version,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        version_file = directory / f"{version}.json"
        version_file.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        latest_file = directory / "latest.json"
        latest_file.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        return manifest

    def get_latest(self, name: str) -> dict[str, Any] | None:
        path = self._model_dir(name) / "latest.json"
        if not path.exists():
            return None

        manifest = json.loads(path.read_text(encoding="utf-8"))
        artifact = Path(manifest["artifact"])

        if not artifact.exists():
            raise FileNotFoundError(
                f"Registered artifact is missing: {artifact}"
            )

        if self.checksum(artifact) != manifest["sha256"]:
            raise RuntimeError("Model artifact checksum mismatch.")

        return manifest