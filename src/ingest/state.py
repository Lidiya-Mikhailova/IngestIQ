from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class IngestState:
    cursor: str | None = None
    since: str | None = None
    extra: dict | None = None


class StateStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def _path(self, state_key: str) -> Path:
        return self.base_dir / f"{state_key}.json"

    def load(self, state_key: str) -> IngestState:
        path = self._path(state_key)
        if not path.exists():
            return IngestState()

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return IngestState(**data)

    def save(self, state_key: str, state: IngestState) -> None:
        path = self._path(state_key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(state), f, ensure_ascii=False, indent=2)
