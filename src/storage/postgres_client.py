from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _get_db_url() -> str:
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "mypassword")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    db = os.environ.get("POSTGRES_DB", "ingestiq_db")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


@dataclass(frozen=True)
class PostgresClient:
    engine: Engine

    @classmethod
    def from_env(cls) -> "PostgresClient":
        db_url = _get_db_url()
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=5)
        return cls(engine=engine)

    def execute(self, query: str, params: Optional[dict] = None) -> Any:
        with self.engine.begin() as conn:
            result = conn.execute(text(query), params or {})
            if result.returns_rows:
                return result.fetchall()
            return None

    def execute_df(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        conn = self.engine.raw_connection()
        try:
            return pd.read_sql(query, conn, params=params)
        finally:
            conn.close()

    def executemany(self, query: str, rows: list[tuple]) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(text(query), rows)
            return result.rowcount

    def execute_scalar(self, query: str, params: Optional[dict] = None) -> Any:
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.fetchone()
            return row[0] if row else None

    def table_exists(self, table_name: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table
            )
        """
        return self.execute_scalar(query, {"table": table_name}) is True

    def close(self) -> None:
        self.engine.dispose()
