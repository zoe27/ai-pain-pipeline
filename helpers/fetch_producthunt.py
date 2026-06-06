"""Fetch Product Hunt posts via GraphQL API.

Requires PRODUCTHUNT_TOKEN in .env — https://www.producthunt.com/v2/oauth/applications

Usage:
    python3 helpers/fetch_producthunt.py <pipeline_id> [--config configs/radar.example.yaml]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

from radar_common import (
    ROOT,
    created_after_iso,
    effective_keywords,
    filter_posts,
    http_post_json,
    limits,
    load_dotenv,
    load_yaml,
    source_enabled,
)

DEFAULT_CONFIG = ROOT / "configs" / "radar.example.yaml"
PH_API = "https://api.producthunt.com/v2/api/graphql"

POSTS_QUERY = """
query Posts($first: Int!) {
  posts(order: VOTES, first: $first) {
    edges {
      node {
        id
        name
        tagline
        description
        votesCount
        commentsCount
        url
        createdAt
        topics {
          edges {
            node { name }
          }
        }
      }
    }
  }
}
"""


def parse_ph_source(config: dict) -> dict | None:
    sources = config.get("sources") or []
    ph = next((s for s in sources if s.get("type") == "producthunt"), None)
    if not ph or not source_enabled(ph):
        return None
    return {
        "topics": {t.lower() for t in (ph.get("topics") or ph.get("categories") or [])},
        "min_votes": int(ph.get("min_votes", ph.get("min_upvotes", 10))),
        "keywords": ph.get("keywords") or [],
        "date_range": (config.get("filters") or {}).get("date_range", "last_7_days"),
    }


def ph_token() -> str:
    import os

    load_dotenv(ROOT / ".env")
    token = os.environ.get("PRODUCTHUNT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Missing PRODUCTHUNT_TOKEN. Create an app at "
            "https://www.producthunt.com/v2/oauth/applications"
        )
    return token


def extract_post(node: dict) -> dict:
    oid = str(node.get("id", ""))
    topics = [
        e["node"]["name"]
        for e in (node.get("topics") or {}).get("edges") or []
        if e.get("node")
    ]
    description = node.get("description") or ""
    tagline = node.get("tagline") or ""
    selftext = description if description else tagline
    return {
        "source": "producthunt",
        "source_label": topics[0] if topics else "producthunt",
        "object_id": oid,
        "title": node.get("name") or "",
        "selftext": selftext,
        "ups": int(node.get("votesCount") or 0),
        "num_comments": int(node.get("commentsCount") or 0),
        "permalink": f"/posts/{oid}",
        "source_url": node.get("url") or f"https://www.producthunt.com/posts/{oid}",
        "author": "",
        "url": node.get("url"),
        "topics": topics,
        "created_at": node.get("createdAt"),
    }


def fetch_posts(fetch_limit: int) -> tuple[dict, list[dict]]:
    payload = http_post_json(
        PH_API,
        {"query": POSTS_QUERY, "variables": {"first": min(fetch_limit, 50)}},
        headers={
            "Authorization": f"Bearer {ph_token()}",
            "User-Agent": "pain-radar/0.1",
        },
    )
    if payload.get("errors"):
        raise RuntimeError(f"Product Hunt API errors: {payload['errors']}")
    edges = payload.get("data", {}).get("posts", {}).get("edges") or []
    posts = [extract_post(e["node"]) for e in edges if e.get("node")]
    return payload, posts


def collect(config: dict, raw_dir: pathlib.Path) -> list[dict]:
    ph = parse_ph_source(config)
    if not ph:
        return []

    fetch_limit, top_n = limits(config)
    created_after = created_after_iso(ph["date_range"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"✓ Product Hunt (topics={ph['topics'] or 'all'}, min_votes={ph['min_votes']}, "
        f"date_range={ph['date_range']})"
    )

    try:
        payload, posts = fetch_posts(fetch_limit)
    except Exception as e:
        print(f"WARN producthunt: {e}", file=sys.stderr)
        return []

    (raw_dir / "producthunt.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")

    if created_after:
        posts = [p for p in posts if (p.get("created_at") or "") >= created_after]

    if ph["topics"]:
        posts = [
            p
            for p in posts
            if ph["topics"].intersection({t.lower() for t in p.get("topics") or []})
        ]

    ph_keywords = effective_keywords(ph["keywords"], config)
    filtered = filter_posts(
        posts,
        min_score=ph["min_votes"],
        keywords=ph_keywords,
        config=config,
    )[:top_n]
    if ph_keywords and not filtered and posts:
        print(
            f"WARN producthunt: no keyword matches after quality filter; "
            f"skipping fallback (PH launches excluded by default)",
            file=sys.stderr,
        )

    top_path = raw_dir / "producthunt_top.json"
    top_path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ producthunt: fetched {len(posts)}, kept top {len(filtered)} → {top_path.name}")
    return filtered


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    config = load_yaml(config_path)
    raw_dir = ROOT / "runs" / pipeline_id / "_raw"
    merged = collect(config, raw_dir)
    if not merged and parse_ph_source(config):
        raise SystemExit("Product Hunt fetch produced no posts")
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
