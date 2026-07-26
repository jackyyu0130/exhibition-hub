"""Load and validate nationwide source and venue registries."""

from .loader import (
    build_venue_alias_index,
    load_source_registry,
    load_venue_registry,
    resolve_venue,
    source_registry_summary,
)
from .event_enricher import (
    enrich_event_with_registry,
    normalize_region,
    resolve_event_venue,
)
from .validator import (
    validate_all_registries,
    validate_source_registry,
    validate_venue_registry,
)

__all__ = [
    "build_venue_alias_index",
    "enrich_event_with_registry",
    "load_source_registry",
    "load_venue_registry",
    "normalize_region",
    "resolve_event_venue",
    "resolve_venue",
    "source_registry_summary",
    "validate_all_registries",
    "validate_source_registry",
    "validate_venue_registry",
]
