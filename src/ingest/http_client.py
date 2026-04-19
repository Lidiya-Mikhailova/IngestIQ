from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class JsonResponse:
    status_code: int
    headers: dict[str, str]
    json: Any


class HttpClient:
    def __init__(
        self,
        *,
        timeout_s: float = 15.0,
        max_retries: int = 3,
        backoff_min_s: float = 0.5,
        backoff_max_s: float = 5.0,
        user_agent: str = "IngestIQ/1.0",
    ):
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.backoff_min_s = backoff_min_s
        self.backoff_max_s = backoff_max_s

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonResponse:
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout_s,
                )

                if resp.status_code in (429, 500, 502, 503, 504):
                    self._sleep_backoff(attempt, resp)
                    continue

                resp.raise_for_status()

                return JsonResponse(
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    json=resp.json(),
                )

            except Exception as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise
                self._sleep_backoff(attempt, None)

        raise RuntimeError("HttpClient.get_json failed") from last_exc

    def _sleep_backoff(self, attempt: int, resp: requests.Response | None) -> None:
        base = min(self.backoff_max_s, self.backoff_min_s * (2**attempt))
        sleep_s = base + random.random() * 0.25

        if resp is not None:
            ra = resp.headers.get("Retry-After")
            if ra and ra.isdigit():
                sleep_s = max(sleep_s, float(ra))

        time.sleep(sleep_s)

    def close(self) -> None:
        self._session.close()
