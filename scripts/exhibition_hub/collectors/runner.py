from __future__ import annotations

from .base import CollectorRunReport, CollectorSource
from .http import CollectorHttpClient
from .registry import CollectorRegistry


class CollectorRunner:
    def __init__(
        self,
        registry: CollectorRegistry,
        client: CollectorHttpClient | None = None,
    ) -> None:
        self.registry = registry
        self.client = client or CollectorHttpClient()

    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
    ) -> CollectorRunReport:
        if not source.enabled and not allow_planned:
            return CollectorRunReport(
                source_id=source.id,
                status="skipped",
                warnings=["Source is disabled or planned"],
            )

        collector = self.registry.create(source.id)
        if collector is None:
            return CollectorRunReport(
                source_id=source.id,
                status="failed",
                errors=[f"Collector not implemented: {source.id}"],
            )

        return collector.run(source, self.client)
