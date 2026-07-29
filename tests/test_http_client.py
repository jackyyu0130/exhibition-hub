import json
import sys
import unittest
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    CollectorContext,
)
from exhibition_hub.http_client import (  # noqa: E402
    HttpClient,
    HttpClientError,
)


def build_response(
    *,
    url: str = "https://example.com/events",
    status_code: int = 200,
    content: bytes = b"",
    headers: dict[str, str] | None = None,
    encoding: str = "utf-8",
) -> requests.Response:
    """Create a requests response without using the internet."""

    response = requests.Response()
    response.url = url
    response.status_code = status_code
    response._content = content
    response.headers.update(headers or {})
    response.encoding = encoding

    return response


class FakeSession:
    """Minimal requests-like session for isolated unit tests."""

    def __init__(
        self,
        response: requests.Response,
    ) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> requests.Response:
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )

        return self.response

    def close(self) -> None:
        self.closed = True


class HttpClientTests(unittest.TestCase):
    def setUp(self):
        self.context = CollectorContext.create(
            timeout_seconds=18,
            user_agent="ExhibitionHub-Test/1.0",
        )

    def create_client(
        self,
        response: requests.Response,
        *,
        max_response_bytes: int = 1024,
    ) -> tuple[HttpClient, FakeSession]:
        session = FakeSession(response)

        client = HttpClient(
            self.context,
            session=session,
            retry_count=0,
            max_response_bytes=max_response_bytes,
        )

        return client, session

    def test_invalid_constructor_values_are_rejected(self):
        with self.assertRaises(ValueError):
            HttpClient(
                self.context,
                retry_count=-1,
            )

        with self.assertRaises(ValueError):
            HttpClient(
                self.context,
                backoff_factor=-0.1,
            )

        with self.assertRaises(ValueError):
            HttpClient(
                self.context,
                max_response_bytes=0,
            )

    def test_default_headers_are_added_to_session(self):
        response = build_response(content=b"ok")
        client, session = self.create_client(response)

        self.assertEqual(
            session.headers["User-Agent"],
            "ExhibitionHub-Test/1.0",
        )
        self.assertIn(
            "zh-TW",
            session.headers["Accept-Language"],
        )

        client.close()

        # Externally supplied sessions are not owned by the client.
        self.assertFalse(session.closed)

    def test_get_uses_context_timeout_and_request_options(self):
        response = build_response(content=b"ok")
        client, session = self.create_client(response)

        result = client.get(
            "https://example.com/events",
            params={"page": 2},
            headers={"X-Test": "yes"},
        )

        self.assertIs(result, response)
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(
            session.calls[0]["timeout"],
            18,
        )
        self.assertEqual(
            session.calls[0]["params"],
            {"page": 2},
        )
        self.assertEqual(
            session.calls[0]["headers"],
            {"X-Test": "yes"},
        )

    def test_custom_timeout_is_supported(self):
        response = build_response(content=b"ok")
        client, session = self.create_client(response)

        client.get(
            "https://example.com/events",
            timeout_seconds=5,
        )

        self.assertEqual(
            session.calls[0]["timeout"],
            5,
        )

        with self.assertRaises(ValueError):
            client.get(
                "https://example.com/events",
                timeout_seconds=0,
            )

    def test_get_text_returns_decoded_content(self):
        response = build_response(
            content="展覽資料".encode("utf-8"),
        )
        client, _ = self.create_client(response)

        text = client.get_text(
            "https://example.com/events"
        )

        self.assertEqual(text, "展覽資料")

    def test_get_json_returns_expected_payload(self):
        payload = {
            "events": [
                {
                    "title": "測試展覽",
                }
            ]
        }
        response = build_response(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
        )
        client, _ = self.create_client(response)

        result = client.get_json(
            "https://example.com/events",
            expected_type=dict,
        )

        self.assertEqual(result, payload)

    def test_unexpected_json_structure_is_rejected(self):
        response = build_response(
            content=b"[]",
            headers={
                "Content-Type": "application/json",
            },
        )
        client, _ = self.create_client(response)

        with self.assertRaises(HttpClientError) as error:
            client.get_json(
                "https://example.com/events",
                expected_type=dict,
            )

        self.assertIn(
            "unexpected JSON structure",
            str(error.exception),
        )

    def test_invalid_json_is_rejected(self):
        response = build_response(
            content=b"not-json",
            headers={
                "Content-Type": "application/json",
            },
        )
        client, _ = self.create_client(response)

        with self.assertRaises(HttpClientError) as error:
            client.get_json(
                "https://example.com/events"
            )

        self.assertIn(
            "returned invalid JSON",
            str(error.exception),
        )

    def test_http_error_hides_query_parameters(self):
        response = build_response(
            url=(
                "https://example.com/events"
                "?access_token=secret"
            ),
            status_code=503,
            content=b"Service unavailable",
        )
        client, _ = self.create_client(response)

        with self.assertRaises(HttpClientError) as error:
            client.get(
                "https://example.com/events"
                "?access_token=secret"
            )

        message = str(error.exception)

        self.assertIn("HTTP 503", message)
        self.assertNotIn("secret", message)
        self.assertNotIn("access_token", message)

    def test_declared_response_size_limit_is_enforced(self):
        response = build_response(
            content=b"small",
            headers={
                "Content-Length": "5000",
            },
        )
        client, _ = self.create_client(
            response,
            max_response_bytes=100,
        )

        with self.assertRaises(HttpClientError) as error:
            client.get(
                "https://example.com/events"
            )

        self.assertIn(
            "response is too large",
            str(error.exception),
        )

    def test_actual_response_size_limit_is_enforced(self):
        response = build_response(
            content=b"x" * 101,
        )
        client, _ = self.create_client(
            response,
            max_response_bytes=100,
        )

        with self.assertRaises(HttpClientError):
            client.get(
                "https://example.com/events"
            )

    def test_invalid_urls_are_rejected(self):
        response = build_response(content=b"ok")
        client, session = self.create_client(response)

        invalid_urls = [
            "",
            "example.com/events",
            "file:///tmp/events.json",
            "javascript:alert(1)",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    client.get(url)

        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
