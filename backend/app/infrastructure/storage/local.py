import os
import tempfile
from pathlib import Path

from app.core.config import settings


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Résout un chemin en empêchant de sortir du stockage."""

        relative = Path(key)

        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("Chemin de stockage invalide")

        path = (self.root / relative).resolve()

        if not path.is_relative_to(self.root):
            raise ValueError("Chemin hors du stockage autorisé")

        return path

    def read_bytes(self, key: str) -> bytes:
        return self._get_path(key).read_bytes()

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=path.parent,
                delete=False,
            ) as temporary_file:
                temporary_file.write(data)
                temporary_path = Path(temporary_file.name)

            os.replace(temporary_path, path)

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def read_text(self, key: str) -> str:
        return self.read_bytes(key).decode("utf-8")

    def write_text(self, key: str, content: str) -> None:
        self.write_bytes(key, content.encode("utf-8"))


storage = LocalStorage(settings.storage_root)
