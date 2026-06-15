"""Fetch App Store customer reviews via public iTunes RSS (1–2 star = high-SNR pain).

Uses legacy RSS endpoint (no API key):
  https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/json

Note: Apple has deprecated richer RSS variants; many apps return empty feeds.
Use `search_terms` + `app_ids` and verify with a single-app fetch first.

Usage:
    python3 helpers/fetch_app_store.py <pipeline_id> [--config configs/radar.app_store.example.yaml]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import urllib.parse

from radar_common import (
    ROOT,
    created_after_iso,
    effective_keywords,
    filter_posts,
    global_filters,
    http_get_json,
    limits,
    load_yaml,
    source_enabled,
)

DEFAULT_CONFIG = ROOT / "configs" / "radar.app_store.example.yaml"
RSS_URL = "https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/json"
LOOKUP_URL = "https://itunes.apple.com/lookup?id={app_id}"
SEARCH_URL = "https://itunes.apple.com/search?term={term}&entity=software&limit=10"
USER_AGENT = "pain-radar/0.7 (app store rss)"


def _label(node: dict | None) -> str:
    if not node:
        return ""
    if isinstance(node, dict):
        return str(node.get("label") or "")
    return str(node)


def parse_apple_datetime(raw: str) -> str | None:
    if not raw:
        return None
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def parse_app_store_source(config: dict) -> dict | None:
    sources = config.get("sources") or []
    entry = next((s for s in sources if s.get("type") == "app_store"), None)
    if not entry or not source_enabled(entry):
        return None
    return {
        "app_ids": [str(i) for i in (entry.get("app_ids") or [])],
        "search_terms": list(entry.get("search_terms") or []),
        "max_stars": int(entry.get("max_stars", 2)),
        "max_pages": int(entry.get("max_pages", 2)),
        "min_points": int(entry.get("min_points", 10)),
        "keywords": entry.get("keywords") or [],
        "date_range": (config.get("filters") or {}).get("date_range", "last_7_days"),
    }


def lookup_app_name(app_id: str) -> str:
    try:
        payload = http_get_json(
            LOOKUP_URL.format(app_id=app_id),
            headers={"User-Agent": USER_AGENT},
        )
        results = payload.get("results") or []
        if results:
            return results[0].get("trackName") or app_id
    except Exception as e:
        print(f"WARN app_store lookup {app_id}: {e}", file=sys.stderr)
    return app_id


def resolve_app_ids(cfg: dict) -> list[str]:
    ids: list[str] = list(cfg["app_ids"])
    for term in cfg["search_terms"]:
        q = urllib.parse.quote(term)
        try:
            payload = http_get_json(
                SEARCH_URL.format(term=q),
                headers={"User-Agent": USER_AGENT},
            )
        except Exception as e:
            print(f"WARN app_store search {term!r}: {e}", file=sys.stderr)
            continue
        for row in payload.get("results") or []:
            track_id = row.get("trackId")
            if track_id is not None:
                ids.append(str(track_id))
    seen: set[str] = set()
    out: list[str] = []
    for app_id in ids:
        if app_id not in seen:
            seen.add(app_id)
            out.append(app_id)
    return out


def _normalize_feed_entries(feed: object) -> list[dict]:
    """Apple RSS returns a single review as dict; iterating that dict yields key strings."""
    if not isinstance(feed, dict):
        return []
    raw = feed.get("entry")
    if not raw:
        return []
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [e for e in raw if isinstance(e, dict)]
    return []


def extract_review(entry: dict, *, app_id: str, app_name: str) -> dict | None:
    if "im:rating" not in entry:
        return None
    try:
        rating = int(_label(entry.get("im:rating")) or 0)
    except ValueError:
        return None
    review_id = _label(entry.get("id"))
    if not review_id:
        return None
    title = _label(entry.get("title")) or "(no title)"
    content = _label(entry.get("content"))
    vote_count = 0
    try:
        vote_count = int(_label(entry.get("im:voteCount")) or 0)
    except ValueError:
        pass
    ups = max((5 - rating) * 10, vote_count)
    return {
        "source": "app_store",
        "source_label": app_name,
        "object_id": review_id,
        "title": title,
        "selftext": content,
        "ups": ups,
        "num_comments": 0,
        "star_rating": rating,
        "app_id": app_id,
        "source_url": f"https://apps.apple.com/app/id{app_id}",
        "permalink": f"app_store:{app_id}/review/{review_id}",
        "created_at": parse_apple_datetime(_label(entry.get("updated"))),
    }


def fetch_reviews_for_app(app_id: str, app_name: str, *, max_pages: int) -> list[dict]:
    reviews: list[dict] = []
    for page in range(1, max_pages + 1):
        url = RSS_URL.format(page=page, app_id=app_id)
        try:
            payload = http_get_json(url, headers={"User-Agent": USER_AGENT})
        except Exception as e:
            print(f"WARN app_store rss {app_id} page={page}: {e}", file=sys.stderr)
            break
        entries = _normalize_feed_entries(payload.get("feed"))
        if not entries:
            break
        for entry in entries:
            post = extract_review(entry, app_id=app_id, app_name=app_name)
            if post:
                reviews.append(post)
    return reviews


def collect(config: dict, raw_dir: pathlib.Path) -> list[dict]:
    cfg = parse_app_store_source(config)
    if not cfg:
        return []

    app_ids = resolve_app_ids(cfg)
    if not app_ids:
        print("WARN app_store: no app_ids or search_terms configured", file=sys.stderr)
        return []

    fetch_limit, top_n = limits(config)
    created_after = created_after_iso(cfg["date_range"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"✓ App Store (apps={len(app_ids)}, max_stars={cfg['max_stars']}, "
        f"date_range={cfg['date_range']})"
    )

    all_reviews: list[dict] = []
    app_payloads: dict[str, list[dict]] = {}

    for app_id in app_ids:
        app_name = lookup_app_name(app_id)
        try:
            reviews = fetch_reviews_for_app(
                app_id, app_name, max_pages=cfg["max_pages"]
            )
        except Exception as e:
            print(f"WARN app_store reviews {app_id} ({app_name}): {e}", file=sys.stderr)
            continue
        app_payloads[app_id] = reviews
        all_reviews.extend(reviews)
        if reviews:
            low = sum(1 for r in reviews if r["star_rating"] <= cfg["max_stars"])
            print(f"  · {app_name} ({app_id}): {len(reviews)} reviews, {low} ≤{cfg['max_stars']}★")

    (raw_dir / "app_store.json").write_text(
        json.dumps(app_payloads, indent=2, ensure_ascii=False) + "\n"
    )

    max_stars = cfg["max_stars"]
    starred = [r for r in all_reviews if r.get("star_rating", 5) <= max_stars]

    if created_after:
        starred = [r for r in starred if (r.get("created_at") or "") >= created_after]

    gf = global_filters(config)
    as_keywords = effective_keywords(cfg["keywords"], config)
    filtered = filter_posts(
        starred,
        min_score=cfg["min_points"],
        keywords=as_keywords,
        exclude_keywords=gf["exclude_keywords"],
        config=config,
    )[:top_n]

    top_path = raw_dir / "app_store_top.json"
    top_path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False) + "\n")
    print(
        f"✓ app_store: fetched {len(all_reviews)}, kept {len(starred)} ≤{max_stars}★, "
        f"top {len(filtered)} → {top_path.name}"
    )
    return filtered


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    config = load_yaml(config_path)
    raw_dir = ROOT / "runs" / pipeline_id / "_raw"
    merged = collect(config, raw_dir)
    if not merged and parse_app_store_source(config):
        raise SystemExit("App Store fetch produced no posts")
    top50_path = raw_dir / "top50.json"
    top50_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {top50_path.relative_to(ROOT)} ({len(merged)} posts)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    run(args.pipeline_id, args.config)


if __name__ == "__main__":
    main()
