"""Collector contracts for legacy feeds and official venue sources."""

from .audit import audit_collector_coverage
from .base import (
    BaseCollector,
    CollectionResult,
    CollectorContext,
    CollectorContractError,
    CollectorError,
    CollectorRecord,
    CollectorRunReport,
    CollectorSource,
    RawEvent,
    SourceKind,
)
from .http import CollectorHttpClient, CollectorHttpError
from .registry import (
    CollectorRegistration,
    CollectorRegistry,
    collector_registry,
)
from .runner import (
    CollectorBatchResult,
    CollectorRunner,
    run_collectors,
)

__all__ = [
    "BaseCollector",
    "CollectionResult",
    "CollectorBatchResult",
    "CollectorContext",
    "CollectorContractError",
    "CollectorError",
    "CollectorHttpClient",
    "CollectorHttpError",
    "CollectorRecord",
    "CollectorRegistration",
    "CollectorRegistry",
    "CollectorRunReport",
    "CollectorRunner",
    "CollectorSource",
    "RawEvent",
    "SourceKind",
    "audit_collector_coverage",
    "collector_registry",
    "run_collectors",
]
