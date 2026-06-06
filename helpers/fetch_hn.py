"""Fetch Hacker News posts via Algolia API and build runs/{pipeline_id}/_raw/top50.json.

No API key required. https://hn.algolia.com/api

Usage:
    python3 helpers/fetch_hn.py <pipeline_id> [--config configs/radar.example.yaml]
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "radar.example.yaml"
ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
TOP_PER_SOURCE = 10
DATE_RANGE_SECONDS = {
    "last_24_hours": 86400,
    "last_7_days": 7 * 86400,
    "last_month": 30 * 86400,
}


def load_yaml(path: pathlib.Path) -> dict:
    try:
        import yaml
    except ImportError as e:
        raise SystemExit(
            "PyYAML required: pip install -r requirements.txt (in .venv)"
        ) from e
    return yaml.safe_load(path.read_text()) or {}


def http_get(url: str, *, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "pain-radar/0.1 (hackernews algolia)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


def clean_story_text(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<p>\s*", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def created_after_ts(date_range: str) -> int | None:
    import datetime

    seconds = DATE_RANGE_SECONDS.get(date_range)
    if seconds is None:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    return int(now.timestamp()) - seconds


def parse_hn_source(config: dict) -> tuple[list[str], list[str], int, str, int, int, list[str]] | None:
    from radar_common import source_enabled

    sources = config.get("sources") or []
    hn = next((s for s in sources if s.get("type") == "hackernews"), None)
    if not hn or not source_enabled(hn):
        return None
    from radar_common import effective_keywords

    tags = hn.get("tags") or ["ask_hn"]
    keywords = effective_keywords(hn.get("keywords") or [], config)
    min_points = int(hn.get("min_points", hn.get("min_upvotes", 10)))
    date_range = (config.get("filters") or {}).get("date_range", "last_7_days")
    fetch_limit = int(config.get("limit_per_source", 50))
    top_n = int(config.get("top_per_source", TOP_PER_SOURCE))
    from radar_common import global_filters

    exclude = global_filters(config)["exclude_keywords"]
    return tags, keywords, min_points, date_range, fetch_limit, top_n, exclude


def build_algolia_url(
    tag: str,
    *,
    created_after: int | None,
    min_points: int,
    limit: int,
    query: str | None = None,
) -> str:
    numeric = [f"points>{min_points}"]
    if created_after is not None:
        numeric.append(f"created_at_i>{created_after}")

    params: dict[str, str | int] = {
        "tags": tag,
        "numericFilters": ",".join(numeric),
        "hitsPerPage": limit,
    }
    if query:
        params["query"] = query

    qs = urllib.parse.urlencode(params)
    return f"{ALGOLIA_BASE}/search_by_date?{qs}"


def filter_posts(
    posts: list[dict],
    min_points: int,
    keywords: list[str],
    *,
    exclude_keywords: list[str] | None = None,
    config: dict | None = None,
) -> list[dict]:
    from radar_common import filter_posts as common_filter

    return common_filter(
        posts,
        min_score=min_points,
        keywords=keywords,
        exclude_keywords=exclude_keywords or [],
        config=config,
    )


def extract_hit(hit: dict, tag: str) -> dict:
    object_id = str(hit.get("objectID", ""))
    return {
        "source": "hackernews",
        "source_label": tag,
        "object_id": object_id,
        "title": hit.get("title") or "",
        "selftext": clean_story_text(hit.get("story_text")),
        "ups": int(hit.get("points") or 0),
        "num_comments": int(hit.get("num_comments") or 0),
        "permalink": f"/item?id={object_id}",
        "author": hit.get("author") or "",
        "url": hit.get("url"),
    }


def fetch_tag(
    tag: str,
    keywords: list[str],
    *,
    created_after: int | None,
    min_points: int,
    limit: int,
) -> tuple[dict, list[dict]]:
    query = " ".join(keywords) if keywords else None
    url = build_algolia_url(
        tag,
        created_after=created_after,
        min_points=min_points,
        limit=limit,
        query=query,
    )
    payload = http_get(url)
    hits = payload.get("hits") or []
    posts = [extract_hit(h, tag) for h in hits]

    if keywords and not posts:
        # Algolia query + date window can return 0; retry recent posts, filter locally.
        url = build_algolia_url(
            tag,
            created_after=created_after,
            min_points=min_points,
            limit=limit,
        )
        payload = http_get(url)
        hits = payload.get("hits") or []
        posts = [extract_hit(h, tag) for h in hits]

    return payload, posts


def collect(config: dict, raw_dir: pathlib.Path) -> list[dict]:
    parsed = parse_hn_source(config)
    if not parsed:
        return []
    tags, keywords, min_points, date_range, fetch_limit, top_n, exclude = parsed
    created_after = created_after_ts(date_range)
    raw_dir.mkdir(parents=True, exist_ok=True)

    kw_display = " ".join(keywords) if keywords else "(recent, no keyword filter)"
    print(
        f"✓ HN Algolia fetch (tags={tags}, keywords={kw_display}, "
        f"date_range={date_range})"
    )

    ok, failed = 0, []
    merged: list[dict] = []
    seen_global: set[str] = set()

    for tag in tags:
        out_path = raw_dir / f"{tag}.json"
        try:
            payload, posts = fetch_tag(
                tag,
                keywords,
                created_after=created_after,
                min_points=min_points,
                limit=fetch_limit,
            )
            out_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
            filtered = filter_posts(
                posts,
                min_points,
                keywords,
                exclude_keywords=exclude,
                config=config,
            )[:top_n]
            if keywords and not filtered and posts:
                print(
                    f"WARN {tag}: no internet/SaaS keyword matches; "
                    f"keeping top {top_n} recent (exclude + quality filter)",
                    file=sys.stderr,
                )
                filtered = filter_posts(
                    posts,
                    min_points,
                    [],
                    exclude_keywords=exclude,
                    config=config,
                )[:top_n]
            from hn_comments import enrich_comment_resonance

            for post in filtered:
                enrich_comment_resonance(post, config)
            top_path = raw_dir / f"{tag}_top.json"
            top_path.write_text(
                json.dumps(filtered, indent=2, ensure_ascii=False) + "\n"
            )
            for post in filtered:
                oid = post["object_id"]
                if oid not in seen_global:
                    seen_global.add(oid)
                    merged.append(post)
            print(
                f"✓ {tag}: fetched {len(posts)}, kept top {len(filtered)} → {top_path.name}"
            )
            ok += 1
        except Exception as e:
            failed.append((tag, str(e)))
            print(f"WARN {tag}: {e}", file=sys.stderr)
        time.sleep(1)

    if ok == 0:
        print(
            "warning: all HN tags failed — "
            + "; ".join(f"{tag}: {err}" for tag, err in failed),
            file=sys.stderr,
        )
    elif failed:
        print(f"warning: {len(failed)} HN tag(s) skipped", file=sys.stderr)
    return merged


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    config = load_yaml(config_path)
    if not parse_hn_source(config):
        raise SystemExit("config has no enabled sources[].type: hackernews")
    raw_dir = ROOT / "runs" / pipeline_id / "_raw"
    merged = collect(config, raw_dir)
    if not merged:
        raise SystemExit("Hacker News fetch produced no posts")
    top50_path = raw_dir / "top50.json"
    top50_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {top50_path.relative_to(ROOT)} ({len(merged)} posts)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id", help="e.g. pipe_2026-05-31_001")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=DEFAULT_CONFIG,
        help="RadarConfig YAML path",
    )
    args = parser.parse_args()
    if not re.match(r"^pipe_\d{4}-\d{2}-\d{2}_\d{3}$", args.pipeline_id):
        print(
            f"warning: pipeline_id {args.pipeline_id!r} does not match pipe_YYYY-MM-DD_NNN"
        )
    run(args.pipeline_id, args.config)


if __name__ == "__main__":
    main()
