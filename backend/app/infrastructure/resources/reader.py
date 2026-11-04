import json
from pathlib import Path
from typing import Any

from app.core.config import settings


class ResourceReader:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _get_path(self, key: str) -> Path:
        relative = Path(key)

        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative.parts
        ):
            raise ValueError("Chemin de ressource invalide")

        path = (self.root / relative).resolve()

        if not path.is_relative_to(self.root):
            raise ValueError("Chemin hors des ressources")

        return path

    def read_bytes(self, key: str) -> bytes:
        return self._get_path(key).read_bytes()

    def read_text(self, key: str) -> str:
        return self.read_bytes(key).decode("utf-8")

    def read_json(self, key: str) -> Any:
        return json.loads(self.read_text(key))


resources = ResourceReader(settings.resources_root)
