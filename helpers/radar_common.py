"""Shared helpers for pain-radar fetch scripts."""
from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOP_PER_SOURCE = 10
DATE_RANGE_SECONDS = {
    "last_24_hours": 86400,
    "last_7_days": 7 * 86400,
    "last_month": 30 * 86400,
}


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


def matches_keywords(post: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    haystack = f"{post['title']} {post['selftext']}".lower()
    return any(kw.lower() in haystack for kw in keywords)


def filter_posts(
    posts: list[dict],
    *,
    min_score: int,
    keywords: list[str] | None = None,
) -> list[dict]:
    keywords = keywords or []
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
        if keywords and not matches_keywords(post, keywords):
            continue
        out.append(post)
    out.sort(key=lambda p: p["ups"], reverse=True)
    return out


def merge_posts(merged: list[dict], new_posts: list[dict]) -> None:
    seen = {f"{p['source']}:{p.get('object_id', p.get('permalink', ''))}" for p in merged}
    for post in new_posts:
        key = f"{post['source']}:{post.get('object_id', post.get('permalink', ''))}"
        if key not in seen:
            seen.add(key)
            merged.append(post)
