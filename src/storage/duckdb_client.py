from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import duckdb


def get_default_db_path() -> Path:
    return Path(os.environ.get("DUCKDB_PATH", "data/warehouse.duckdb"))


@dataclass(frozen=True)
class DuckDBClient:
    db_path: Path

    @classmethod
    def from_env(cls) -> "DuckDBClient":
        return cls(db_path=get_default_db_path())

    def connect(self, read_only: bool = False) -> duckdb.DuckDBPyConnection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(self.db_path), read_only=read_only)
        con.execute("PRAGMA threads=4;")
        return con
