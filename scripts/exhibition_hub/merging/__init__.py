from .candidate import (
    build_source_merge_candidate,
    load_source_priority,
)
from .dedupe import MatchDecision, MatchResult, find_best_match
from .source_adapter import collector_record_to_event

__all__ = [
    "MatchDecision",
    "MatchResult",
    "build_source_merge_candidate",
    "collector_record_to_event",
    "find_best_match",
    "load_source_priority",
]
