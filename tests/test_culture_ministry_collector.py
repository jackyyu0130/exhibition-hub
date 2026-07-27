import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    CollectorContext,
    CollectorError,
)
from exhibition_hub.collectors.culture_ministry import (  # noqa: E402
    CULTURE_API_METHODS,
    CultureMinistryCollector,
)
from exhibition_hub.http_client import (  # noqa: E402
    HttpClientError,
)


class FakeHttpClient:
    """Scripted HTTP client that never connects to the internet."""

    responses: dict[
        tuple[str, str],
        Any,
    ] = {}
    instances: list["FakeHttpClient"] = []

    def __init__(self, context):
        self.context = context
        self.calls: list[dict[str, Any]] = []
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return None

    def get_json(
        self,
        url,
        *,
        params,
        expected_type=None,
        **kwargs,
    ):
        call = {
            "url": url,
            "params": dict(params),
            "expected_type": expected_type,
        }
        self.calls.append(call)

        key = (
            str(params["category"]),
            str(params["method"]),
        )

        response = type(self).responses.get(
            key,
            HttpClientError(
                f"No scripted response for {key}"
            ),
        )

        if isinstance(response, Exception):
            raise response

        return response


class CultureMinistryCollectorTests(unittest.TestCase):
    def setUp(self):
        FakeHttpClient.responses = {}
        FakeHttpClient.instances = []
        self.context = CollectorContext.create()

    def collect_with_fake_http(
        self,
        collector,
    ):
        with patch(
            (
                "exhibition_hub.collectors."
                "culture_ministry.HttpClient"
            ),
            FakeHttpClient,
        ):
            return collector.collect(self.context)

    def test_successful_category_adds_source_metadata(self):
        primary_method = CULTURE_API_METHODS[0]

        FakeHttpClient.responses[
            ("6", primary_method)
        ] = [
            {
                "title": "測試展覽",
                "startDate": "2026/07/01",
            }
        ]

        result = self.collect_with_fake_http(
            CultureMinistryCollector(
                categories=["6"]
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(result.event_count, 1)

        event = result.events[0]

        self.assertEqual(event["title"], "測試展覽")
        self.assertEqual(event["_feedCategory"], "6")
        self.assertEqual(
            event["_collectorSource"],
            "culture-ministry",
        )
        self.assertEqual(result.errors, [])

    def test_fallback_method_is_used_when_primary_fails(self):
        primary_method = CULTURE_API_METHODS[0]
        fallback_method = CULTURE_API_METHODS[1]

        FakeHttpClient.responses[
            ("6", primary_method)
        ] = HttpClientError(
            "Primary API temporarily unavailable"
        )
        FakeHttpClient.responses[
            ("6", fallback_method)
        ] = [
            {
                "title": "備援 API 展覽",
            }
        ]

        result = self.collect_with_fake_http(
            CultureMinistryCollector(
                categories=["6"]
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(result.event_count, 1)
        self.assertTrue(
            any(
                fallback_method in warning
                for warning in result.warnings
            )
        )

        calls = FakeHttpClient.instances[0].calls

        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0]["params"]["method"],
            primary_method,
        )
        self.assertEqual(
            calls[1]["params"]["method"],
            fallback_method,
        )

    def test_one_failed_category_does_not_block_successful_one(
        self,
    ):
        primary_method = CULTURE_API_METHODS[0]
        fallback_method = CULTURE_API_METHODS[1]

        FakeHttpClient.responses[
            ("6", primary_method)
        ] = [
            {
                "title": "成功取得的展覽",
            }
        ]

        FakeHttpClient.responses[
            ("7", primary_method)
        ] = HttpClientError("HTTP 503")
        FakeHttpClient.responses[
            ("7", fallback_method)
        ] = HttpClientError("HTTP 503")

        result = self.collect_with_fake_http(
            CultureMinistryCollector(
                categories=["6", "7"]
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(result.event_count, 1)
        self.assertEqual(
            result.events[0]["title"],
            "成功取得的展覽",
        )
        self.assertTrue(
            any(
                "category=7 failed" in warning
                for warning in result.warnings
            )
        )
        self.assertTrue(
            any(
                "Unavailable Culture categories: 7"
                in warning
                for warning in result.warnings
            )
        )

    def test_all_failed_categories_return_failed_result(self):
        for category in ("6", "7"):
            for method in CULTURE_API_METHODS:
                FakeHttpClient.responses[
                    (category, method)
                ] = HttpClientError(
                    "Culture API unavailable"
                )

        result = self.collect_with_fake_http(
            CultureMinistryCollector(
                categories=["6", "7"]
            )
        )

        self.assertFalse(result.succeeded)
        self.assertEqual(result.event_count, 0)
        self.assertEqual(
            result.errors,
            ["All Culture Ministry feeds failed"],
        )

    def test_empty_api_result_uses_fallback_method(self):
        primary_method = CULTURE_API_METHODS[0]
        fallback_method = CULTURE_API_METHODS[1]

        FakeHttpClient.responses[
            ("6", primary_method)
        ] = []
        FakeHttpClient.responses[
            ("6", fallback_method)
        ] = [
            {
                "title": "Fallback after empty result",
            }
        ]

        result = self.collect_with_fake_http(
            CultureMinistryCollector(
                categories=["6"]
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(result.event_count, 1)
        self.assertEqual(
            result.events[0]["title"],
            "Fallback after empty result",
        )

    def test_dictionary_payload_wrappers_are_supported(self):
        supported_payloads = [
            {
                "events": [
                    {
                        "title": "Events wrapper",
                    }
                ]
            },
            {
                "data": [
                    {
                        "title": "Data wrapper",
                    }
                ]
            },
            {
                "result": [
                    {
                        "title": "Result wrapper",
                    }
                ]
            },
        ]

        for payload in supported_payloads:
            with self.subTest(payload=payload):
                records = (
                    CultureMinistryCollector
                    ._extract_records(payload)
                )

                self.assertEqual(len(records), 1)
                self.assertIn(
                    "title",
                    records[0],
                )

    def test_non_dictionary_items_are_ignored(self):
        records = (
            CultureMinistryCollector
            ._extract_records(
                [
                    {
                        "title": "有效展覽",
                    },
                    "invalid",
                    123,
                    None,
                ]
            )
        )

        self.assertEqual(
            records,
            [
                {
                    "title": "有效展覽",
                }
            ],
        )

    def test_empty_or_invalid_payload_is_rejected(self):
        invalid_payloads = [
            [],
            {},
            {
                "events": [],
            },
            "not-a-list",
            None,
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(
                    CollectorError
                ):
                    (
                        CultureMinistryCollector
                        ._extract_records(payload)
                    )

    def test_collector_requires_at_least_one_category(self):
        with self.assertRaises(ValueError):
            CultureMinistryCollector(
                categories=[]
            )

        with self.assertRaises(ValueError):
            CultureMinistryCollector(
                categories=["", "   "]
            )


if __name__ == "__main__":
    unittest.main()
