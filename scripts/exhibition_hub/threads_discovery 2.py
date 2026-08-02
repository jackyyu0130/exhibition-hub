from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import re
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

SPACE = re.compile(r"\s+")
GENERIC_TITLE = re.compile(
    r"^(?:活動|展覽|最新消息|節目|更多|首頁|展演資訊)$",
    re.I,
)


def clean(value: Any) -> str:
    return SPACE.sub(" ", str(value or "")).strip()


def normalize_url(value: Any) -> str:
    parsed = urlparse(clean(value))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    query = urlencode(
        [
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith(("utm_", "fbclid", "gclid", "xmt"))
        ]
    )
    return urlunparse(
        (parsed.scheme, parsed.netloc.lower(), parsed.path, "", query, "")
    )


def is_threads_permalink(value: Any) -> bool:
    parsed = urlparse(normalize_url(value))
    host = (parsed.hostname or "").lower()
    return host.endswith("threads.net") or host.endswith("threads.com")


def parse_date(value: Any) -> date | None:
    text = clean(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def current_events(
    events: Sequence[Mapping[str, Any]],
    *,
    today: date,
) -> list[Mapping[str, Any]]:
    rows = []
    for event in events:
        if not isinstance(event, Mapping):
            continue
        end = parse_date(event.get("endDate") or event.get("startDate"))
        if end and end < today - timedelta(days=2):
            continue
        rows.append(event)
    rows.sort(
        key=lambda event: (
            str(event.get("startDate") or "9999-12-31"),
            str(event.get("title") or ""),
        )
    )
    return rows


def rotated(values: Sequence[str], count: int, seed: int) -> list[str]:
    cleaned = [clean(value) for value in values if clean(value)]
    if not cleaned or count <= 0:
        return []
    count = min(count, len(cleaned))
    start = seed % len(cleaned)
    return [cleaned[(start + index) % len(cleaned)] for index in range(count)]


def dynamic_queries(
    events: Sequence[Mapping[str, Any]],
    *,
    today: date,
    limit: int,
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for event in current_events(events, today=today):
        title = clean(event.get("title"))
        title = re.sub(r"^[【\[].*?[】\]]\s*", "", title)
        if (
            len(title) < 4
            or len(title) > 64
            or GENERIC_TITLE.fullmatch(title)
        ):
            continue
        key = re.sub(r"\W+", "", title.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(title)
        if len(result) >= limit:
            break
    return result


def build_query_plan(
    config: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
    include_top: bool = False,
) -> list[dict[str, str]]:
    limits = config.get("limits") or {}
    static_limit = int(limits.get("maxStaticQueriesPerRun") or 12)
    dynamic_limit = int(limits.get("maxDynamicQueriesPerRun") or 8)
    seed = int(now.strftime("%j")) + (12 if now.hour >= 12 else 0)

    plan = [
        {
            "q": query,
            "searchType": "RECENT",
            "searchMode": "KEYWORD",
            "kind": "static",
        }
        for query in rotated(
            config.get("staticQueries") or [],
            static_limit,
            seed,
        )
    ]
    plan.extend(
        {
            "q": query,
            "searchType": "RECENT",
            "searchMode": "KEYWORD",
            "kind": "event_title",
        }
        for query in dynamic_queries(
            events,
            today=now.date(),
            limit=dynamic_limit,
        )
    )
    if include_top:
        plan.extend(
            {
                "q": clean(query),
                "searchType": "TOP",
                "searchMode": "KEYWORD",
                "kind": "top",
            }
            for query in (config.get("topQueries") or [])
            if clean(query)
        )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in plan:
        key = (item["q"].lower(), item["searchType"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def account_hash(username: Any) -> str:
    value = clean(username).lower().lstrip("@")
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def has_any(text: str, values: Sequence[Any]) -> bool:
    lower = text.lower()
    return any(clean(value).lower() in lower for value in values if clean(value))


def normalize_post(
    post: Mapping[str, Any],
    query: Mapping[str, str],
    config: Mapping[str, Any],
) -> dict[str, Any] | None:
    text = clean(post.get("text"))
    permalink = normalize_url(post.get("permalink"))
    if not text or not is_threads_permalink(permalink):
        return None

    if has_any(text, config.get("excludedTerms") or []):
        return None
    if query.get("kind") != "event_title" and not has_any(
        text,
        config.get("eventSignalTerms") or [],
    ):
        return None

    username = clean(post.get("username")).lower().lstrip("@")
    priority = {
        clean(item).lower().lstrip("@")
        for item in config.get("priorityAccountSignals") or []
    }
    editor_weight = 0.35 if username and username in priority else 0.0
    privacy = config.get("privacy") or {}
    maximum = int(privacy.get("maximumExcerptCharacters") or 240)

    keywords = [query.get("q", "")]
    topic_tag = clean(post.get("topic_tag"))
    if topic_tag:
        keywords.append(topic_tag)

    return {
        "source": "threads",
        "postUrl": permalink,
        "publishedAt": clean(post.get("timestamp")),
        "shortExcerpt": text[:maximum],
        "keywords": [item for item in keywords if clean(item)],
        "candidatePurpose": "social_or_event_signal",
        "discoveryQuery": query.get("q", ""),
        "sourceAccountHash": account_hash(username),
        "verifiedAccount": bool(post.get("is_verified")),
        "topicTag": topic_tag,
        "editorWeight": editor_weight,
        "engagementSnapshot": {},
    }


@dataclass
class QueryResult:
    query: str
    searchType: str
    status: str
    returnedCount: int
    acceptedCount: int
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "searchType": self.searchType,
            "status": self.status,
            "returnedCount": self.returnedCount,
            "acceptedCount": self.acceptedCount,
            "error": self.error,
        }


def api_search(
    session: requests.Session,
    *,
    token: str,
    config: Mapping[str, Any],
    query: Mapping[str, str],
    now: datetime,
) -> list[dict[str, Any]]:
    limits = config.get("limits") or {}
    lookback = int(limits.get("lookbackHours") or 72)
    endpoint = (
        clean(config.get("apiHost") or "https://graph.threads.net").rstrip("/")
        + clean(config.get("endpoint") or "/keyword_search")
    )
    fields = ",".join(str(item) for item in config.get("fields") or [])
    params = {
        "q": query["q"],
        "search_type": query["searchType"],
        "search_mode": query.get("searchMode") or "KEYWORD",
        "limit": int(limits.get("maxResultsPerQuery") or 25),
        "fields": fields,
        "since": int((now - timedelta(hours=lookback)).timestamp()),
        "until": int(now.timestamp()),
    }
    response = session.get(
        endpoint,
        params=params,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "TaiwanExhibitionJournal-T1Threads/1.0 (+https://twexhibition.com/)",
            "Accept": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, Mapping):
        return []
    return [
        item for item in payload.get("data") or []
        if isinstance(item, Mapping)
    ]


def discover_threads(
    config: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    token: str,
    now: datetime | None = None,
    include_top: bool = False,
    search_fn: Callable[[Mapping[str, str]], Sequence[Mapping[str, Any]]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    plan = build_query_plan(config, events, now=now, include_top=include_top)
    session = requests.Session()
    delay = float((config.get("limits") or {}).get("requestDelaySeconds") or 0.35)

    rows: dict[str, dict[str, Any]] = {}
    results: list[QueryResult] = []
    permission_denied = False

    for query in plan:
        try:
            posts = list(
                search_fn(query)
                if search_fn
                else api_search(
                    session,
                    token=token,
                    config=config,
                    query=query,
                    now=now,
                )
            )
            accepted = 0
            for post in posts:
                candidate = normalize_post(post, query, config)
                if not candidate:
                    continue
                key = candidate["postUrl"]
                if key not in rows:
                    rows[key] = candidate
                    accepted += 1
                else:
                    existing = rows[key]
                    merged_keywords = [
                        *existing.get("keywords", []),
                        *candidate.get("keywords", []),
                    ]
                    existing["keywords"] = list(dict.fromkeys(merged_keywords))
                    existing["editorWeight"] = max(
                        float(existing.get("editorWeight") or 0),
                        float(candidate.get("editorWeight") or 0),
                    )
            results.append(
                QueryResult(
                    query=query["q"],
                    searchType=query["searchType"],
                    status="success",
                    returnedCount=len(posts),
                    acceptedCount=accepted,
                )
            )
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", 0)
            if status_code in {401, 403}:
                permission_denied = True
            results.append(
                QueryResult(
                    query=query["q"],
                    searchType=query["searchType"],
                    status="permission_denied" if permission_denied else "http_error",
                    returnedCount=0,
                    acceptedCount=0,
                    error=f"HTTP {status_code}" if status_code else type(exc).__name__,
                )
            )
            if permission_denied:
                break
        except Exception as exc:
            results.append(
                QueryResult(
                    query=query["q"],
                    searchType=query["searchType"],
                    status="error",
                    returnedCount=0,
                    acceptedCount=0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
        if not search_fn:
            time.sleep(max(0.0, delay))

    candidates = sorted(
        rows.values(),
        key=lambda item: str(item.get("publishedAt") or ""),
        reverse=True,
    )
    report = {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(),
        "status": "permission_denied" if permission_denied else "success",
        "reviewRequired": True,
        "publishAllowed": False,
        "queryCount": len(results),
        "successfulQueryCount": sum(
            1 for item in results if item.status == "success"
        ),
        "candidateCount": len(candidates),
        "queries": [item.to_dict() for item in results],
        "privacy": {
            "fullTextStored": False,
            "authorIdentityPublished": False,
            "usernameStored": False,
        },
    }
    return candidates, report
