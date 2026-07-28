from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any
from urllib.parse import urlparse

import requests


class CollectorHttpError(RuntimeError):
    pass


@dataclass(frozen=True)
class CollectorHttpResponse:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]


class CollectorHttpClient:
    def __init__(
        self,
        *,
        timeout: float = 25,
        retries: int = 2,
        backoff_seconds: float = 0.6,
        user_agent: str = "TaiwanExhibitionJournal-Collector/1.0",
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = max(0, retries)
        self.backoff_seconds = max(0, backoff_seconds)
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.6",
        })

    @staticmethod
    def validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise CollectorHttpError("Collector URL must be absolute HTTP(S)")

    def get(self, url: str) -> CollectorHttpResponse:
        self.validate_url(url)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 429 or response.status_code >= 500:
                    raise CollectorHttpError(
                        f"Transient HTTP {response.status_code} for {url}"
                    )
                response.raise_for_status()
                return CollectorHttpResponse(
                    url=str(response.url),
                    status_code=response.status_code,
                    text=response.text,
                    headers=dict(response.headers),
                )
            except (requests.RequestException, CollectorHttpError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(self.backoff_seconds * (2 ** attempt))
        raise CollectorHttpError(str(last_error) if last_error else f"Failed to fetch {url}")

    def get_json(self, url: str) -> Any:
        response = self.get(url)
        try:
            return requests.models.complexjson.loads(response.text)
        except ValueError as exc:
            raise CollectorHttpError(f"Invalid JSON from {url}") from exc
