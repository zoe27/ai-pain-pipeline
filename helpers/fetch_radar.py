"""Fetch all enabled radar sources and merge into runs/{pipeline_id}/_raw/top50.json.

Runs collectors in order: hackernews → github_issues → producthunt → app_store → reddit.
Each source is skipped when disabled in config or when credentials are missing.

Usage:
    python3 helpers/fetch_radar.py <pipeline_id> [--config configs/radar.example.yaml]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from radar_common import ROOT, load_yaml, merge_posts

DEFAULT_CONFIG = ROOT / "configs" / "radar.example.yaml"


def collect_all(config: dict, raw_dir: pathlib.Path) -> list[dict]:
    from fetch_app_store import collect as collect_app_store
    from fetch_github_issues import collect as collect_github
    from fetch_hn import collect as collect_hn
    from fetch_producthunt import collect as collect_ph
    from fetch_reddit import collect as collect_reddit

    merged: list[dict] = []
    collectors = [
        ("hackernews", collect_hn),
        ("github_issues", collect_github),
        ("producthunt", collect_ph),
        ("app_store", collect_app_store),
        ("reddit", collect_reddit),
    ]
    for name, fn in collectors:
        try:
            posts = fn(config, raw_dir)
            if posts:
                merge_posts(merged, posts)
                print(f"✓ merged {len(posts)} from {name} (total {len(merged)})")
        except Exception as e:
            print(f"WARN {name}: {e}", file=sys.stderr)
    return merged


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    config = load_yaml(config_path)
    raw_dir = ROOT / "runs" / pipeline_id / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    merged = collect_all(config, raw_dir)
    if not merged:
        raise SystemExit(
            "No posts from any source. Enable at least one source in config "
            "and check credentials / network."
        )

    top50_path = raw_dir / "top50.json"
    top50_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {top50_path.relative_to(ROOT)} ({len(merged)} posts)")

    from compute_radar_signals import compute

    signals = compute(merged)
    signals_path = raw_dir / "radar_signals.json"
    signals_path.write_text(json.dumps(signals, indent=2, ensure_ascii=False) + "\n")
    if signals.get("multi_post_themes"):
        print(f"✓ cross-post themes: {signals['multi_post_themes']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    if not re.match(r"^pipe_\d{4}-\d{2}-\d{2}_\d{3}$", args.pipeline_id):
        print(
            f"warning: pipeline_id {args.pipeline_id!r} does not match pipe_YYYY-MM-DD_NNN"
        )
    run(args.pipeline_id, args.config)


if __name__ == "__main__":
    main()
