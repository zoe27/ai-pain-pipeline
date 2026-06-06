"""Compute cross-post theme counts and per-post signals after radar fetch.

Usage:
    python3 helpers/compute_radar_signals.py <pipeline_id>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))

from radar_common import detect_pain_themes  # noqa: E402


def compute(posts: list[dict]) -> dict:
    theme_counts: dict[str, int] = {}
    per_post: list[dict] = []
    for post in posts:
        themes = detect_pain_themes(post)
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        per_post.append(
            {
                "source": post.get("source"),
                "object_id": post.get("object_id"),
                "title": post.get("title"),
                "themes": themes,
                "comment_resonance": int(post.get("comment_resonance") or 0),
                "ups": int(post.get("ups") or 0),
            }
        )
    multi = {t: c for t, c in theme_counts.items() if c >= 2}
    return {
        "post_count": len(posts),
        "theme_counts": theme_counts,
        "multi_post_themes": multi,
        "posts": per_post,
    }


def run(pipeline_id: str) -> dict:
    top50 = ROOT / "runs" / pipeline_id / "_raw" / "top50.json"
    if not top50.is_file():
        raise SystemExit(f"Missing {top50}")
    posts = json.loads(top50.read_text())
    payload = compute(posts)
    out = ROOT / "runs" / pipeline_id / "_raw" / "radar_signals.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(
        f"✓ wrote {out.relative_to(ROOT)} "
        f"({payload['post_count']} posts, themes={payload['theme_counts']})"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    args = parser.parse_args()
    run(args.pipeline_id)


if __name__ == "__main__":
    main()
