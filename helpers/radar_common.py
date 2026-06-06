"""Shared helpers for pain-radar fetch scripts."""
from __future__ import annotations

import json
import os
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOP_PER_SOURCE = 10
DATE_RANGE_SECONDS = {
    "last_24_hours": 86400,
    "last_7_days": 7 * 86400,
    "last_month": 30 * 86400,
}

# Default noise for internet/SaaS focus (overridable via config filters.exclude_keywords)
DEFAULT_EXCLUDE_KEYWORDS = [
    "lego",
    "parenting",
    "renewable",
    "solar power",
    "wind power",
    "energy transition",
    "geopolitics",
    "nytimes",
    "journalism",
    "climate",
]

# GitHub issue titles that are usually framework bugs, not product pains
TECH_ISSUE_TITLE_RE = re.compile(
    r"(^fix[\(:]|^bug[\(:]|regression|typo|valueerror|typeerror|"
    r"doesn'?t work|fails when|broken test|ci fail|enum|"
    r"structured.?output|checkpoint|text-splitter|lint rule)",
    re.I,
)

BUG_REPORT_BODY_MARKERS = (
    "bug report",
    "### checked other resources",
    "### submission checklist",
    "### verify canary release",
    "### link to the code that reproduces",
)


def global_filters(config: dict) -> dict:
    """Shared filter knobs from config.filters."""
    flt = config.get("filters") or {}
    exclude = list(flt.get("exclude_keywords") or DEFAULT_EXCLUDE_KEYWORDS)
    return {
        "focus": flt.get("focus", "internet_saas"),
        "exclude_keywords": [k.lower() for k in exclude],
    }


def haystack(post: dict) -> str:
    return f"{post.get('title', '')} {post.get('selftext', '')}".lower()


def matches_keywords(post: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = haystack(post)
    return any(kw.lower() in text for kw in keywords)


def matches_exclude(post: dict, exclude_keywords: list[str]) -> bool:
    if not exclude_keywords:
        return False
    text = haystack(post)
    return any(kw in text for kw in exclude_keywords)


def looks_like_framework_bug_issue(post: dict) -> bool:
    """GitHub issues that read as bug reports / DX fixes, not user/business pains."""
    if post.get("source") != "github_issues":
        return False
    title = post.get("title", "")
    body = (post.get("selftext") or "")[:800].lower()
    if TECH_ISSUE_TITLE_RE.search(title):
        return True
    if any(m in body for m in BUG_REPORT_BODY_MARKERS):
        return True
    return False


def filter_posts(
    posts: list[dict],
    *,
    min_score: int,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    source: str | None = None,
    github_product_pain: bool = False,
    pain_keywords: list[str] | None = None,
) -> list[dict]:
    keywords = keywords or []
    exclude_keywords = exclude_keywords or []
    pain_keywords = pain_keywords or []

    out = []
    seen: set[str] = set()
    for post in posts:
        key = f"{post['source']}:{post.get('object_id', post.get('permalink', ''))}"
        if key in seen:
            continue
        seen.add(key)
        if post["ups"] < min_score:
            continue
        if not post["title"].strip():
            continue
        if matches_exclude(post, exclude_keywords):
            continue
        if source and post.get("source") != source:
            continue
        if github_product_pain and looks_like_framework_bug_issue(post):
            if not matches_keywords(post, pain_keywords):
                continue
        elif github_product_pain and pain_keywords:
            if not matches_keywords(post, pain_keywords):
                continue
        elif keywords and not matches_keywords(post, keywords):
            continue
        out.append(post)
    out.sort(key=lambda p: p["ups"], reverse=True)
    return out


def load_dotenv(path: pathlib.Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def load_yaml(path: pathlib.Path) -> dict:
    try:
        import yaml
    except ImportError as e:
        raise SystemExit(
            "PyYAML required: pip install -r requirements.txt (in .venv)"
        ) from e
    return yaml.safe_load(path.read_text()) or {}


def source_enabled(entry: dict) -> bool:
    return entry.get("enabled", True) is not False


def limits(config: dict) -> tuple[int, int]:
    fetch_limit = int(config.get("limit_per_source", 50))
    top_n = int(config.get("top_per_source", TOP_PER_SOURCE))
    return fetch_limit, top_n


def created_after_iso(date_range: str) -> str | None:
    import datetime

    seconds = DATE_RANGE_SECONDS.get(date_range)
    if seconds is None:
        return None
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get_json(
    url: str,
    *,
    headers: dict | None = None,
    timeout: int = 30,
) -> dict | list:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


def http_post_json(
    url: str,
    payload: dict,
    *,
    headers: dict | None = None,
    timeout: int = 30,
) -> dict:
    data = json.dumps(payload).encode()
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


def merge_posts(merged: list[dict], new_posts: list[dict]) -> None:
    seen = {f"{p['source']}:{p.get('object_id', p.get('permalink', ''))}" for p in merged}
    for post in new_posts:
        key = f"{post['source']}:{post.get('object_id', post.get('permalink', ''))}"
        if key not in seen:
            seen.add(key)
            merged.append(post)
