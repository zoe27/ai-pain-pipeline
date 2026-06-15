"""Cluster stage-1 pain points by theme + product for Stage 2/3 commercial pre-screen.

Writes runs/{pipeline_id}/_raw/pain_clusters.json with cluster sizes, member IDs,
and aggregated commercial_hints (switch intent, platform bug, workaround signals).

Usage:
    python3 helpers/compute_pain_clusters.py <pipeline_id>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))

from commercial_signals import cluster_key, scan_commercial_hints  # noqa: E402


def compute(pain_points: list[dict]) -> dict:
    buckets: dict[str, dict] = {}

    for pp in pain_points:
        title = pp.get("title") or ""
        body = pp.get("raw_content") or ""
        source = pp.get("source") or "unknown"
        label = pp.get("source_label")
        key = cluster_key(title, body, source, label)
        hints = scan_commercial_hints(title, body)

        if key not in buckets:
            buckets[key] = {
                "cluster_id": key,
                "theme": key.split("@", 1)[0],
                "product": key.split("@", 1)[-1],
                "pain_point_ids": [],
                "sources": set(),
                "switch_intent_count": 0,
                "platform_bug_count": 0,
                "workaround_count": 0,
            }
        bucket = buckets[key]
        bucket["pain_point_ids"].append(pp["id"])
        bucket["sources"].add(source)
        if hints["switch_intent"]:
            bucket["switch_intent_count"] += 1
        if hints["platform_bug_signal"]:
            bucket["platform_bug_count"] += 1
        if hints["workaround_signal"]:
            bucket["workaround_count"] += 1

    clusters = []
    by_id: dict[str, str] = {}
    for bucket in sorted(buckets.values(), key=lambda b: -len(b["pain_point_ids"])):
        size = len(bucket["pain_point_ids"])
        source_count = len(bucket["sources"])
        commercial_hints = {
            "switch_intent_ratio": round(bucket["switch_intent_count"] / size, 2),
            "platform_bug_ratio": round(bucket["platform_bug_count"] / size, 2),
            "workaround_ratio": round(bucket["workaround_count"] / size, 2),
            "single_source_echo": size >= 3 and source_count == 1,
            "persistence_hint": (
                "platform_bug"
                if bucket["platform_bug_count"] / size >= 0.5
                else "structural"
                if bucket["switch_intent_count"] / size < 0.2 and size >= 2
                else "unknown"
            ),
        }
        cluster = {
            "cluster_id": bucket["cluster_id"],
            "theme": bucket["theme"],
            "product": bucket["product"],
            "size": size,
            "source_count": source_count,
            "pain_point_ids": bucket["pain_point_ids"],
            "commercial_hints": commercial_hints,
        }
        clusters.append(cluster)
        for pid in bucket["pain_point_ids"]:
            by_id[pid] = bucket["cluster_id"]

    multi = [c for c in clusters if c["size"] >= 2]
    return {
        "pain_point_count": len(pain_points),
        "cluster_count": len(clusters),
        "multi_member_clusters": len(multi),
        "by_pain_point_id": by_id,
        "clusters": clusters,
    }


def run(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    inp = run_dir / "1_pain_points.json"
    if not inp.is_file():
        raise SystemExit(f"Missing {inp} (run pain-radar first)")

    batch = json.loads(inp.read_text())
    payload = compute(batch["pain_points"])
    out = run_dir / "_raw" / "pain_clusters.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(
        f"✓ wrote {out.relative_to(ROOT)} "
        f"({payload['cluster_count']} clusters, {payload['multi_member_clusters']} multi-member)"
    )
    if multi := [c for c in payload["clusters"] if c["size"] >= 2][:5]:
        print(f"  top clusters: {[(c['cluster_id'], c['size']) for c in multi]}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    args = parser.parse_args()
    run(args.pipeline_id)


if __name__ == "__main__":
    main()
