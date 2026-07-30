from __future__ import annotations

from typing import Iterable

from .base import CollectorSource
from .registry import CollectorRegistry


EXTERNALLY_MANAGED_SOURCE_IDS = {"culture-ministry"}


def audit_collector_coverage(
    sources: Iterable[CollectorSource],
    registry: CollectorRegistry,
) -> dict:
    source_list = list(sources)
    registered = set(registry.ids())
    source_ids = {source.id for source in source_list}

    implemented = sorted(source_ids & registered)
    external = sorted(source_ids & EXTERNALLY_MANAGED_SOURCE_IDS)
    active_missing = sorted(
        source.id
        for source in source_list
        if source.enabled
        and source.id not in registered
        and source.id not in EXTERNALLY_MANAGED_SOURCE_IDS
    )
    planned_missing = sorted(
        source.id
        for source in source_list
        if not source.enabled and source.id not in registered
    )
    orphan_collectors = sorted(registered - source_ids)

    return {
        "mode": "collector-framework-audit",
        "sourceCount": len(source_list),
        "activeSourceCount": sum(1 for source in source_list if source.enabled),
        "implementedCollectorIds": implemented,
        "externalManagedSourceIds": external,
        "activeSourcesMissingCollectors": active_missing,
        "plannedSourcesMissingCollectors": planned_missing,
        "orphanCollectorIds": orphan_collectors,
        "frameworkReady": not active_missing and not orphan_collectors,
        "nextPilotSourceId": "songshan-cultural-park",
    }
