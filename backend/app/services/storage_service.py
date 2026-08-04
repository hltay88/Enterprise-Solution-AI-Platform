"""Local filesystem storage for uploads (ATLAS-013 / ATLAS-027)."""

import hashlib
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationAppError


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "upload.bin"


class StorageService:
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.storage_path)
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def max_bytes(self) -> int:
        return settings.max_upload_mb * 1024 * 1024

    async def save_upload(
        self,
        *,
        project_id: uuid.UUID,
        upload: UploadFile,
        max_bytes: int | None = None,
    ) -> tuple[str, int, str]:
        """Save upload; returns (relative_path, size_bytes, sha256_hex)."""
        if not upload.filename:
            raise ValidationAppError("Filename is required")

        limit = max_bytes if max_bytes is not None else self.max_bytes
        safe_name = _safe_filename(upload.filename)
        project_dir = self.root / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        absolute_path = project_dir / stored_name

        digest = hashlib.sha256()
        size = 0
        with absolute_path.open("wb") as output:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    output.close()
                    absolute_path.unlink(missing_ok=True)
                    limit_mb = max(1, limit // (1024 * 1024))
                    raise ValidationAppError(f"File exceeds maximum size of {limit_mb} MB")
                digest.update(chunk)
                output.write(chunk)

        if size == 0:
            absolute_path.unlink(missing_ok=True)
            raise ValidationAppError("Uploaded file is empty")

        relative_path = str(Path(str(project_id)) / stored_name)
        return relative_path, size, digest.hexdigest()

    def absolute_path(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        root = self.root.resolve()
        if not str(path).startswith(str(root)):
            raise ValidationAppError("Invalid storage path")
        return path

    def delete_file(self, relative_path: str) -> None:
        path = self.absolute_path(relative_path)
        path.unlink(missing_ok=True)
