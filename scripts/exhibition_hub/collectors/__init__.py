"""Collector framework for official venue and ticketing sources."""

from .audit import audit_collector_coverage
from .base import BaseCollector, CollectorRecord, CollectorRunReport, CollectorSource
from .http import CollectorHttpClient, CollectorHttpError
from .registry import CollectorRegistry, collector_registry
from .runner import CollectorRunner

__all__ = [
    "BaseCollector",
    "CollectorHttpClient",
    "CollectorHttpError",
    "CollectorRecord",
    "CollectorRegistry",
    "CollectorRunReport",
    "CollectorRunner",
    "CollectorSource",
    "audit_collector_coverage",
    "collector_registry",
]
