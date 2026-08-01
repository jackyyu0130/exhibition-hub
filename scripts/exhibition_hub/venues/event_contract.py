from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


_SPLIT_RE = re.compile(r"[、,，|｜;；]+")


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _strings(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    output: list[str] = []
    for raw in values:
        for item in _SPLIT_RE.split(_clean(raw)):
            item = _clean(item)
            if item and item not in output:
                output.append(item)
    return output


def normalize_event_venue_contract(event: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one event to the R12 main-venue/subspace contract.

    Public filtering fields (`venueName`, `venueNames`, `venueId`, `venueIds`)
    represent canonical parent venues only. Child halls, floors and galleries
    are carried by `subVenueName`, `subVenueNames`, and `venueDetail`.

    Older collector records sometimes stored child spaces in `venueNames`.
    When an explicit parent `venueName` exists, those legacy names are safely
    migrated to `subVenueNames`.
    """

    result = deepcopy(dict(event))
    legacy_names = _strings(result.get("venueNames"))
    main_name = _clean(
        result.get("venueName")
        or result.get("parentVenueName")
        or result.get("venueGroup")
        or result.get("locationName")
        or result.get("location")
    )

    explicit_sub = _strings(result.get("subVenueNames"))
    if result.get("subVenueName"):
        explicit_sub = _strings([result.get("subVenueName"), *explicit_sub])

    # Legacy configured collectors used venueName for the parent and placed
    # only child halls in venueNames. Detect that shape only when the parent is
    # missing from venueNames. Canonical multi-venue records keep every parent.
    legacy_sub = []
    if main_name and legacy_names and main_name not in legacy_names and not explicit_sub:
        legacy_sub = list(legacy_names)
    sub_names = []
    for name in [*explicit_sub, *legacy_sub]:
        if name and name != main_name and name not in sub_names:
            sub_names.append(name)

    if not main_name and legacy_names:
        main_name = legacy_names[0]

    parent_id = _clean(
        result.get("parentVenueId")
        or result.get("venueId")
        or result.get("publicVenueId")
    )
    parent_ids = _strings(result.get("venueIds"))
    if parent_id and parent_id not in parent_ids:
        parent_ids.insert(0, parent_id)

    if main_name:
        top_level_names = []
        for name in [main_name, *legacy_names]:
            if name and name not in sub_names and name not in top_level_names:
                top_level_names.append(name)
        result.update({
            "venueName": main_name,
            "venueNames": top_level_names,
            "venueGroup": main_name,
            "parentVenueName": main_name,
            "locationName": main_name,
            "location": main_name,
        })
    else:
        result["venueNames"] = []

    if parent_id:
        result["venueId"] = parent_id
        result["parentVenueId"] = parent_id
    result["venueIds"] = parent_ids

    result["subVenueNames"] = sub_names
    result["subVenueName"] = sub_names[0] if sub_names else ""
    result["venueDetail"] = _clean(
        result.get("venueDetail") or "／".join(sub_names)
    )
    return result


def validate_event_venue_contract(event: Mapping[str, Any]) -> list[str]:
    """Return contract violations without mutating the event."""

    errors: list[str] = []
    main_name = _clean(event.get("venueName") or event.get("parentVenueName"))
    venue_names = _strings(event.get("venueNames"))
    sub_names = _strings(event.get("subVenueNames"))

    if main_name and (not venue_names or venue_names[0] != main_name):
        errors.append("venueNames must start with the canonical main venue")
    overlap = sorted(set(venue_names).intersection(sub_names))
    if overlap:
        errors.append(
            "main venue and subVenueNames overlap: " + ", ".join(overlap)
        )
    if sub_names and not main_name:
        errors.append("subVenueNames requires venueName/parentVenueName")
    if event.get("subVenueName") and _clean(event.get("subVenueName")) not in sub_names:
        errors.append("subVenueName must be included in subVenueNames")
    if event.get("venueDetail") and sub_names:
        detail = _clean(event.get("venueDetail"))
        missing = [name for name in sub_names if name not in detail]
        if missing:
            errors.append("venueDetail does not include every subVenueName")
    return errors
