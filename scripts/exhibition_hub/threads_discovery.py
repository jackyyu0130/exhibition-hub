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
        if len(title) < 4 or len(title) > 64 or GENERIC_TITLE.fullmatch(title):
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
        for query in rotated(config.get("staticQueries") or [], static_limit, seed)
    ]
    plan.extend(
        {
            "q": query,
            "searchType": "RECENT",
            "searchMode": "KEYWORD",
            "kind": "event_title",
        }
        for query in dynamic_queries(events, today=now.date(), limit=dynamic_limit)
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


def response_error_details(response: requests.Response | None) -> dict[str, Any]:
    if response is None:
        return {}
    details: dict[str, Any] = {"httpStatus": int(response.status_code or 0)}
    try:
        payload = response.json()
    except Exception:
        text = clean(getattr(response, "text", ""))
        if text:
            details["message"] = text[:300]
        return details

    error = payload.get("error") if isinstance(payload, Mapping) else None
    if isinstance(error, Mapping):
        for source, target in (
            ("message", "message"),
            ("type", "metaType"),
            ("code", "metaCode"),
            ("error_subcode", "metaSubcode"),
            ("is_transient", "isTransient"),
            ("fbtrace_id", "fbtraceId"),
        ):
            value = error.get(source)
            if value not in (None, ""):
                details[target] = value
    return details


def classify_http_error(response: requests.Response | None) -> str:
    details = response_error_details(response)
    status = int(details.get("httpStatus") or 0)
    code = int(details.get("metaCode") or 0)
    if status in {401, 403} or code in {10, 190, 200}:
        return "permission_denied"
    if status == 429 or code in {4, 17, 32, 613}:
        return "rate_limited"
    if status >= 500 or bool(details.get("isTransient")):
        return "server_error"
    return "http_error"


def request_json(
    session: requests.Session,
    endpoint: str,
    *,
    params: Mapping[str, Any],
    token: str,
    use_query_token: bool = False,
) -> Mapping[str, Any]:
    request_params = dict(params)
    headers = {
        "User-Agent": "TaiwanExhibitionJournal-T1Threads/1.1 (+https://twexhibition.com/)",
        "Accept": "application/json",
    }
    if use_query_token:
        request_params["access_token"] = token
    else:
        headers["Authorization"] = f"Bearer {token}"

    response = session.get(
        endpoint,
        params=request_params,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, Mapping) else {}


def api_preflight(
    session: requests.Session,
    *,
    token: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    host = clean(config.get("apiHost") or "https://graph.threads.net").rstrip("/")
    try:
        payload = request_json(
            session,
            f"{host}/me",
            params={"fields": "id,username"},
            token=token,
        )
        return {
            "status": "success",
            "userIdAvailable": bool(payload.get("id")),
            "usernameAvailable": bool(payload.get("username")),
        }
    except requests.HTTPError as exc:
        details = response_error_details(exc.response)
        return {"status": classify_http_error(exc.response), **details}
    except Exception as exc:
        return {"status": "error", "message": f"{type(exc).__name__}: {exc}"}


def api_search(
    session: requests.Session,
    *,
    token: str,
    config: Mapping[str, Any],
    query: Mapping[str, str],
    now: datetime,
) -> tuple[list[dict[str, Any]], str]:
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

    raw_retries = limits.get("serverErrorRetries")
    retry_count = 1 if raw_retries is None else max(0, int(raw_retries))
    last_error: requests.HTTPError | None = None
    for attempt in range(retry_count + 1):
        try:
            payload = request_json(
                session,
                endpoint,
                params=params,
                token=token,
            )
            rows = [
                item for item in payload.get("data") or []
                if isinstance(item, Mapping)
            ]
            return rows, "full"
        except requests.HTTPError as exc:
            last_error = exc
            if classify_http_error(exc.response) != "server_error" or attempt >= retry_count:
                break
            time.sleep(1.0 * (attempt + 1))

    # Meta's keyword endpoint can occasionally return an opaque HTTP 500 for
    # otherwise valid requests. Retry once using the smallest request shown in
    # Meta's official example: no time window, no explicit search_mode, and a
    # conservative field list. The access token is still never logged.
    if last_error is not None and classify_http_error(last_error.response) == "server_error":
        compatibility_fields = ",".join(
            str(item)
            for item in (
                config.get("compatibilityFields")
                or [
                    "id",
                    "permalink",
                    "username",
                    "text",
                    "timestamp",
                    "shortcode",
                    "is_quote_post",
                    "has_replies",
                ]
            )
        )
        compatibility_params = {
            "q": query["q"],
            "search_type": query["searchType"],
            "limit": min(int(limits.get("maxResultsPerQuery") or 25), 25),
            "fields": compatibility_fields,
        }
        payload = request_json(
            session,
            endpoint,
            params=compatibility_params,
            token=token,
            use_query_token=True,
        )
        rows = [
            item for item in payload.get("data") or []
            if isinstance(item, Mapping)
        ]
        return rows, "compatibility"

    assert last_error is not None
    raise last_error


@dataclass
class QueryResult:
    query: str
    searchType: str
    status: str
    returnedCount: int
    acceptedCount: int
    attemptMode: str = ""
    error: str = ""
    errorDetails: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "query": self.query,
            "searchType": self.searchType,
            "status": self.status,
            "returnedCount": self.returnedCount,
            "acceptedCount": self.acceptedCount,
            "attemptMode": self.attemptMode,
            "error": self.error,
        }
        if self.errorDetails:
            payload["errorDetails"] = self.errorDetails
        return payload


def overall_status(results: Sequence[QueryResult], preflight: Mapping[str, Any]) -> str:
    preflight_status = clean(preflight.get("status"))
    if preflight_status and preflight_status != "success":
        return preflight_status
    successful = sum(1 for item in results if item.status == "success")
    if successful == len(results) and results:
        return "success"
    if successful > 0:
        return "partial_success"
    if any(item.status == "permission_denied" for item in results):
        return "permission_denied"
    if any(item.status == "rate_limited" for item in results):
        return "rate_limited"
    return "api_error" if results else "success"


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
    preflight = {"status": "skipped_for_test"} if search_fn else api_preflight(
        session,
        token=token,
        config=config,
    )

    if not search_fn and preflight.get("status") != "success":
        report = {
            "schemaVersion": 2,
            "generatedAt": now.isoformat(),
            "status": overall_status(results, preflight),
            "reviewRequired": True,
            "publishAllowed": False,
            "preflight": preflight,
            "queryCount": 0,
            "successfulQueryCount": 0,
            "candidateCount": 0,
            "queries": [],
            "privacy": {
                "fullTextStored": False,
                "authorIdentityPublished": False,
                "usernameStored": False,
            },
        }
        return [], report

    for query in plan:
        try:
            if search_fn:
                posts = list(search_fn(query))
                attempt_mode = "test"
            else:
                posts, attempt_mode = api_search(
                    session,
                    token=token,
                    config=config,
                    query=query,
                    now=now,
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
                    attemptMode=attempt_mode,
                )
            )
        except requests.HTTPError as exc:
            status = classify_http_error(exc.response)
            details = response_error_details(exc.response)
            results.append(
                QueryResult(
                    query=query["q"],
                    searchType=query["searchType"],
                    status=status,
                    returnedCount=0,
                    acceptedCount=0,
                    error=f"HTTP {details.get('httpStatus', 0)}",
                    errorDetails=details,
                )
            )
            if status == "permission_denied":
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
    status = "success" if search_fn else overall_status(results, preflight)
    report = {
        "schemaVersion": 2,
        "generatedAt": now.isoformat(),
        "status": status,
        "reviewRequired": True,
        "publishAllowed": False,
        "preflight": preflight,
        "queryCount": len(results),
        "successfulQueryCount": sum(1 for item in results if item.status == "success"),
        "candidateCount": len(candidates),
        "queries": [item.to_dict() for item in results],
        "privacy": {
            "fullTextStored": False,
            "authorIdentityPublished": False,
            "usernameStored": False,
        },
    }
    return candidates, report
