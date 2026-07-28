"""Collector contracts for legacy feeds and official venue sources."""

from .audit import audit_collector_coverage
from .batches import (
    BatchExecutionPolicy,
    CollectorBatchExecutor,
    RegionGroup,
    SourceBatch,
    SourceBatchRegistry,
    SourceBatchRunReport,
    load_source_batch_registry,
)
from .batch_runtime import (
    SubprocessCollectorRunner,
    collector_report_from_mapping,
)
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
from .huashan import Huashan1914Collector
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
    "BatchExecutionPolicy",
    "CollectorBatchExecutor",
    "CollectionResult",
    "CollectorBatchResult",
    "CollectorContext",
    "CollectorContractError",
    "CollectorError",
    "CollectorHttpClient",
    "CollectorHttpError",
    "Huashan1914Collector",
    "CollectorRecord",
    "CollectorRegistration",
    "CollectorRegistry",
    "CollectorRunReport",
    "CollectorRunner",
    "CollectorSource",
    "RawEvent",
    "RegionGroup",
    "SourceBatch",
    "SourceBatchRegistry",
    "SourceBatchRunReport",
    "SubprocessCollectorRunner",
    "SourceKind",
    "audit_collector_coverage",
    "collector_registry",
    "collector_report_from_mapping",
    "load_source_batch_registry",
    "run_collectors",
]


# Planned sources are registered for explicit dry runs. They remain disabled in source_registry.json.
if collector_registry.get(Huashan1914Collector.source_id) is None:
    collector_registry.register(
        Huashan1914Collector,
        priority=90,
        enabled=False,
    )
