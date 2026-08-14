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
from .songshan import SongshanCulturalParkCollector
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
    "SongshanCulturalParkCollector",
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


if collector_registry.get(SongshanCulturalParkCollector.source_id) is None:
    collector_registry.register(
        SongshanCulturalParkCollector,
        priority=90,
        enabled=True,
    )

# R11.0 official-site collectors. Source-level enabled/status remains governed
# by data/source_registry.json; registry entries only expose implemented classes.
from .official_sites import (
    OFFICIAL_SITE_COLLECTORS,
    ConfiguredOfficialSiteCollector,
    KaohsiungMusicCenterCollector,
    Pier2ArtCenterCollector,
    TainanArtMuseumCollector,
    TaipeiExpoParkExpoDomeCollector,
    TaipeiMusicCenterCollector,
    TaipeiPerformingArtsCenterCollector,
    TwtcHall1Collector,
)

__all__.extend([
    "ConfiguredOfficialSiteCollector",
    "TaipeiMusicCenterCollector",
    "KaohsiungMusicCenterCollector",
    "TainanArtMuseumCollector",
    "TaipeiPerformingArtsCenterCollector",
    "Pier2ArtCenterCollector",
    "TwtcHall1Collector",
    "TaipeiExpoParkExpoDomeCollector",
])

for _official_collector_type in OFFICIAL_SITE_COLLECTORS:
    if collector_registry.get(_official_collector_type.source_id) is None:
        collector_registry.register(
            _official_collector_type,
            priority=90,
            enabled=True,
        )
