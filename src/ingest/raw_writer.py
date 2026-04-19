from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WriteResult:
    path: Path
    rows: int


class RawWriter:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def _run_ts(self) -> str:
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    def _date_part(self, run_ts: str) -> str:
        return run_ts[:8]

    def _dataset_dir(self, *, source: str, dataset: str, run_ts: str) -> Path:
        date = self._date_part(run_ts)
        out_dir = self.base_dir / f"source={source}" / f"dataset={dataset}" / f"date={date}"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def write_ndjson(
        self,
        *,
        source: str,
        dataset: str,
        records: Iterable[dict[str, Any]],
        run_ts: str | None = None,
    ) -> WriteResult:
        if run_ts is None:
            run_ts = self._run_ts()

        out_dir = self._dataset_dir(source=source, dataset=dataset, run_ts=run_ts)
        out_path = out_dir / f"{run_ts}.ndjson"

        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(out_dir), prefix=".tmp_", suffix=".ndjson")
        rows = 0
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False))
                    f.write("\n")
                    rows += 1
            os.replace(tmp_path, out_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return WriteResult(path=out_path, rows=rows)

    def write_bytes(
        self,
        *,
        source: str,
        dataset: str,
        filename: str,
        content: bytes,
        run_ts: str | None = None,
    ) -> Path:
        if run_ts is None:
            run_ts = self._run_ts()

        out_dir = self._dataset_dir(source=source, dataset=dataset, run_ts=run_ts)
        out_path = out_dir / f"{run_ts}_{filename}"

        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(out_dir), prefix=".tmp_", suffix=".bin")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(content)
            os.replace(tmp_path, out_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return out_path
