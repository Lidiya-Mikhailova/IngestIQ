from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.config.settings import app_settings as settings


from src.ingest.http_client import HttpClient
from src.ingest.raw_writer import RawWriter
from src.ingest.registry import build_sources
from src.ingest.state import StateStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OneSourceResult:
    source: str
    dataset: str
    status: str
    rows: int
    raw_path: str | None
    reason: str | None


def _is_asset_record(r: Any) -> bool:
    return isinstance(r, dict) and r.get("__asset__") is True


def run_all(*, full_refresh: bool = False) -> list[OneSourceResult]:
    settings.paths.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.state_dir.mkdir(parents=True, exist_ok=True)

    state_store = StateStore(settings.paths.state_dir)
    writer = RawWriter(settings.paths.raw_dir)

    client = HttpClient(
        timeout_s=settings.api.timeout_s,
        max_retries=settings.api.max_retries,
        backoff_min_s=settings.api.backoff_min_s,
        backoff_max_s=settings.api.backoff_max_s,
    )

    results: list[OneSourceResult] = []

    try:
        for src in build_sources():
            spec = src.spec()

            if not spec.enabled:
                results.append(
                    OneSourceResult(
                        source=spec.source,
                        dataset=spec.dataset,
                        status="skipped",
                        rows=0,
                        raw_path=None,
                        reason=spec.reason_disabled,
                    )
                )
                continue

            try:
                state = state_store.load(spec.state_key)

                if full_refresh:
                    state.since = None
                    state.cursor = None

                records = list(src.extract(client, state))

                if len(records) == 0:
                    results.append(
                        OneSourceResult(
                            source=spec.source,
                            dataset=spec.dataset,
                            status="ok",
                            rows=0,
                            raw_path=None,
                            reason="no new data",
                        )
                    )
                    continue

                asset_records = [r for r in records if _is_asset_record(r)]
                json_records = [r for r in records if not _is_asset_record(r)]

                raw_paths: list[str] = []
                rows_written = 0

                if json_records:
                    write_res = writer.write_ndjson(
                        source=spec.source,
                        dataset=spec.dataset,
                        records=json_records,
                    )
                    rows_written += write_res.rows
                    raw_paths.append(str(write_res.path))

                for ar in asset_records:
                    filename = ar.get("filename")
                    content = ar.get("bytes")
                    if not isinstance(filename, str) or not isinstance(content, (bytes, bytearray)):
                        raise ValueError(
                            f"Bad asset record for {spec.source}/{spec.dataset}: expected filename:str and bytes:bytes"
                        )

                    run_ts = ar.get("run_ts")
                    if run_ts is not None and not isinstance(run_ts, str):
                        run_ts = None

                    p = writer.write_bytes(
                        source=spec.source,
                        dataset=f"{spec.dataset}_assets",
                        filename=filename,
                        content=bytes(content),
                        run_ts=run_ts,
                    )
                    raw_paths.append(str(p))

                new_state = src.next_state(state, records)
                state_store.save(spec.state_key, new_state)

                results.append(
                    OneSourceResult(
                        source=spec.source,
                        dataset=spec.dataset,
                        status="ok",
                        rows=rows_written,
                        raw_path=", ".join(raw_paths) if raw_paths else None,
                        reason=None,
                    )
                )

            except Exception as e:
                logger.exception(
                    "Failed to ingest %s/%s: %s: %s",
                    spec.source,
                    spec.dataset,
                    type(e).__name__,
                    e,
                )
                results.append(
                    OneSourceResult(
                        source=spec.source,
                        dataset=spec.dataset,
                        status="failed",
                        rows=0,
                        raw_path=None,
                        reason=f"{type(e).__name__}: {e}",
                    )
                )
                raise

        return results

    finally:
        client.close()
