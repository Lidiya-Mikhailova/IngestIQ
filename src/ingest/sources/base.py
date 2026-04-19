from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from src.ingest.http_client import HttpClient
from src.ingest.state import IngestState


@dataclass(frozen=True)
class SourceSpec:
    source: str
    dataset: str
    state_key: str
    enabled: bool = True
    reason_disabled: str | None = None


class Source(Protocol):
    def spec(self) -> SourceSpec: ...
    def extract(self, client: HttpClient, state: IngestState) -> Iterable[dict[str, Any]]: ...
    def next_state(self, state: IngestState, records: list[dict[str, Any]]) -> IngestState: ...
