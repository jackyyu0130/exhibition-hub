from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

import requests

from scripts.exhibition_hub.threads_discovery import (
    QueryResult,
    api_search,
    overall_status,
    response_error_details,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, endpoint, *, params, headers, timeout):
        self.calls.append({"endpoint": endpoint, "params": dict(params), "headers": dict(headers)})
        return self.responses.pop(0)


class T1ThreadsHTTP500HotfixTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "data/threads_search_config.json").read_text(encoding="utf-8")
        )
        self.query = {
            "q": "展覽推薦",
            "searchType": "RECENT",
            "searchMode": "KEYWORD",
            "kind": "static",
        }
        self.now = datetime(2026, 8, 2, 15, tzinfo=timezone.utc)

    def test_all_failed_queries_are_not_reported_as_success(self):
        results = [
            QueryResult("展覽", "RECENT", "server_error", 0, 0),
            QueryResult("音樂祭", "RECENT", "server_error", 0, 0),
        ]
        self.assertEqual(overall_status(results, {"status": "success"}), "api_error")

    def test_partial_query_success_is_explicit(self):
        results = [
            QueryResult("展覽", "RECENT", "success", 2, 1),
            QueryResult("音樂祭", "RECENT", "server_error", 0, 0),
        ]
        self.assertEqual(overall_status(results, {"status": "success"}), "partial_success")

    def test_meta_error_body_is_preserved_without_token(self):
        response = FakeResponse(
            500,
            {
                "error": {
                    "message": "An unexpected error has occurred.",
                    "type": "OAuthException",
                    "code": 2,
                    "is_transient": True,
                    "fbtrace_id": "TRACE123",
                }
            },
        )
        details = response_error_details(response)
        self.assertEqual(details["httpStatus"], 500)
        self.assertEqual(details["metaCode"], 2)
        self.assertTrue(details["isTransient"])
        self.assertNotIn("access_token", json.dumps(details))

    def test_http_500_uses_minimal_compatibility_request(self):
        self.config["limits"]["serverErrorRetries"] = 0
        session = FakeSession(
            [
                FakeResponse(
                    500,
                    {
                        "error": {
                            "message": "temporary",
                            "type": "OAuthException",
                            "code": 2,
                            "is_transient": True,
                        }
                    },
                ),
                FakeResponse(
                    200,
                    {
                        "data": [
                            {
                                "id": "1",
                                "permalink": "https://www.threads.com/@demo/post/ABC",
                                "username": "demo",
                                "text": "展覽推薦",
                                "timestamp": "2026-08-02T10:00:00+0000",
                            }
                        ]
                    },
                ),
            ]
        )
        rows, mode = api_search(
            session,
            token="secret-token",
            config=self.config,
            query=self.query,
            now=self.now,
        )
        self.assertEqual(mode, "compatibility")
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(session.calls), 2)
        second = session.calls[1]
        self.assertNotIn("since", second["params"])
        self.assertNotIn("until", second["params"])
        self.assertNotIn("search_mode", second["params"])
        self.assertEqual(second["params"]["access_token"], "secret-token")
        self.assertNotIn("Authorization", second["headers"])

    def test_workflow_fails_false_green_api_reports_but_still_uploads(self):
        workflow = (
            ROOT / ".github/workflows/social-discovery-review.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("Validate Threads API result", workflow)
        self.assertIn("api_error", workflow)
        self.assertIn("if: always()", workflow)


if __name__ == "__main__":
    unittest.main()
