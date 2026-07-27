"""Reliable HTTP requests shared by all exhibition collectors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .collectors.base import (
    CollectorContext,
    CollectorError,
)


DEFAULT_RETRY_STATUS_CODES = frozenset(
    {
        429,
        500,
        502,
        503,
        504,
    }
)

DEFAULT_MAX_RESPONSE_BYTES = 12 * 1024 * 1024


class HttpClientError(CollectorError):
    """Expected network failure from an external data source."""


class HttpClient:
    """HTTP client with timeouts, retries, and response safeguards."""

    def __init__(
        self,
        context: CollectorContext,
        *,
        retry_count: int = 3,
        backoff_factor: float = 0.5,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        session: requests.Session | None = None,
    ) -> None:
        if retry_count < 0:
            raise ValueError(
                "retry_count must be zero or greater"
            )

        if backoff_factor < 0:
            raise ValueError(
                "backoff_factor must be zero or greater"
            )

        if max_response_bytes <= 0:
            raise ValueError(
                "max_response_bytes must be greater than zero"
            )

        self.context = context
        self.retry_count = retry_count
        self.backoff_factor = backoff_factor
        self.max_response_bytes = max_response_bytes

        self._owns_session = session is None
        self._session = session or self._create_session()

        self._session.headers.update(
            {
                "User-Agent": context.user_agent,
                "Accept": "*/*",
                "Accept-Language": (
                    "zh-TW,zh;q=0.9,en;q=0.7"
                ),
            }
        )

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retry_policy = Retry(
            total=self.retry_count,
            connect=self.retry_count,
            read=self.retry_count,
            status=self.retry_count,
            backoff_factor=self.backoff_factor,
            status_forcelist=DEFAULT_RETRY_STATUS_CODES,
            allowed_methods=frozenset(
                {
                    "GET",
                    "HEAD",
                }
            ),
            respect_retry_after_header=True,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_policy,
            pool_connections=20,
            pool_maxsize=20,
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> requests.Response:
        """Perform a protected HTTP GET request."""

        self._validate_url(url)

        safe_url = self._safe_url(url)
        active_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.context.timeout_seconds
        )

        if active_timeout <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )

        try:
            response = self._session.get(
                url,
                params=dict(params or {}),
                headers=dict(headers or {}),
                timeout=active_timeout,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )
            status_text = (
                f" HTTP {status_code}"
                if status_code is not None
                else ""
            )

            raise HttpClientError(
                f"GET {safe_url} failed:"
                f"{status_text} "
                f"{type(exc).__name__}"
            ) from exc

        self._validate_url(response.url)
        self._validate_response_size(
            response,
            safe_url=safe_url,
        )

        return response

    def get_text(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> str:
        """Download a text or HTML response."""

        response = self.get(
            url,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if not response.encoding:
            response.encoding = (
                response.apparent_encoding or "utf-8"
            )

        return response.text

    def get_json(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
        expected_type: (
            type
            | tuple[type, ...]
            | None
        ) = None,
    ) -> Any:
        """Download and decode a JSON response."""

        response = self.get(
            url,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        try:
            payload = response.json()

        except ValueError as exc:
            raise HttpClientError(
                f"GET {self._safe_url(url)} "
                "returned invalid JSON"
            ) from exc

        if (
            expected_type is not None
            and not isinstance(payload, expected_type)
        ):
            raise HttpClientError(
                f"GET {self._safe_url(url)} "
                "returned an unexpected JSON structure"
            )

        return payload

    def _validate_response_size(
        self,
        response: requests.Response,
        *,
        safe_url: str,
    ) -> None:
        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            try:
                declared_size = int(content_length)

            except ValueError:
                declared_size = None

            if (
                declared_size is not None
                and declared_size
                > self.max_response_bytes
            ):
                raise HttpClientError(
                    f"GET {safe_url} response is too large: "
                    f"{declared_size} bytes"
                )

        actual_size = len(response.content)

        if actual_size > self.max_response_bytes:
            raise HttpClientError(
                f"GET {safe_url} response is too large: "
                f"{actual_size} bytes"
            )

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlsplit(url)

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
        ):
            raise ValueError(
                "Only valid HTTP and HTTPS URLs are allowed"
            )

    @staticmethod
    def _safe_url(url: str) -> str:
        """Remove query strings and fragments from error messages."""

        parsed = urlsplit(url)

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",
                "",
            )
        )

    def close(self) -> None:
        """Close internally created network resources."""

        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.close()
