"""Collector for Ministry of Culture arts and exhibition feeds."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..http_client import HttpClient, HttpClientError
from .base import (
    BaseCollector,
    CollectionResult,
    CollectorContext,
    CollectorError,
    RawEvent,
    SourceKind,
)


CULTURE_API_URL = (
    "https://cloud.culture.tw/frontsite/trans/"
    "SearchShowAction.do"
)

# Use the current Open API first and retain the older method
# only as a compatibility fallback.
CULTURE_API_METHODS = (
    "doFindTypeJOpenApi",
    "doFindTypeJ",
)

# Keep the same feed coverage as the existing production scraper
# during the gradual migration.
CULTURE_FEED_CATEGORIES = (
    "all",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "11",
    "13",
    "14",
    "15",
    "17",
    "19",
)


class CultureMinistryCollector(BaseCollector):
    """Retrieve raw activity records from official Culture feeds."""

    source_id = "culture-ministry"
    source_name = "文化部文化資料開放服務網"
    source_kind = SourceKind.API

    def __init__(
        self,
        categories: Iterable[str] | None = None,
    ) -> None:
        selected_categories = (
            categories
            if categories is not None
            else CULTURE_FEED_CATEGORIES
        )

        self.categories = tuple(
            category.strip()
            for category in selected_categories
            if category.strip()
        )

        if not self.categories:
            raise ValueError(
                "At least one Culture Ministry category "
                "must be configured"
            )

    def _collect(
        self,
        context: CollectorContext,
        result: CollectionResult,
    ) -> None:
        successful_feeds = 0
        failed_categories: list[str] = []

        with HttpClient(context) as client:
            for category in self.categories:
                try:
                    records, method = self._fetch_category(
                        client,
                        category,
                    )

                except CollectorError as exc:
                    failed_categories.append(category)
                    result.add_warning(
                        f"category={category} failed: {exc}"
                    )
                    continue

                successful_feeds += 1

                if method != CULTURE_API_METHODS[0]:
                    result.add_warning(
                        f"category={category} used "
                        f"fallback method {method}"
                    )

                for record in records:
                    prepared_record = dict(record)
                    prepared_record.setdefault(
                        "_feedCategory",
                        category,
                    )
                    prepared_record.setdefault(
                        "_collectorSource",
                        self.source_id,
                    )

                    result.add_event(prepared_record)

        if successful_feeds == 0:
            raise CollectorError(
                "All Culture Ministry feeds failed"
            )

        if not result.events:
            raise CollectorError(
                "Culture Ministry feeds returned no records"
            )

        if failed_categories:
            result.add_warning(
                "Unavailable Culture categories: "
                + ", ".join(failed_categories)
            )

    def _fetch_category(
        self,
        client: HttpClient,
        category: str,
    ) -> tuple[list[RawEvent], str]:
        errors: list[str] = []

        for method in CULTURE_API_METHODS:
            try:
                payload = client.get_json(
                    CULTURE_API_URL,
                    params={
                        "method": method,
                        "category": category,
                    },
                    expected_type=(list, dict),
                )
                records = self._extract_records(payload)

            except (
                HttpClientError,
                CollectorError,
            ) as exc:
                errors.append(
                    f"{method}: {exc}"
                )
                continue

            return records, method

        raise CollectorError(
            f"No usable response for category={category}; "
            + " | ".join(errors)
        )

    @staticmethod
    def _extract_records(
        payload: Any,
    ) -> list[RawEvent]:
        if isinstance(payload, dict):
            payload = (
                payload.get("events")
                or payload.get("data")
                or payload.get("result")
                or []
            )

        if not isinstance(payload, list):
            raise CollectorError(
                "API response is not a JSON array"
            )

        records = [
            dict(item)
            for item in payload
            if isinstance(item, dict)
        ]

        if not records:
            raise CollectorError(
                "API returned an empty record list"
            )

        return records
