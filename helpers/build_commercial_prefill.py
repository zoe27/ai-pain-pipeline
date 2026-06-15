"""Build Stage 3 commercial prefill from external signals + clusters + stage 2 ICE.

Output: runs/{pipeline_id}/_raw/commercial_prefill.json

Agent reads this before writing _judgments/stage3.json. Supports focus mode via
--pain-point-id or auto-select top ICE ≥ 200.

Usage:
    python3 helpers/build_commercial_prefill.py <pipeline_id>
    python3 helpers/build_commercial_prefill.py <pipeline_id> --pain-point-id <uuid>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))


def _avg(values: list[int]) -> int:
    if not values:
        return 5
    return max(1, min(10, round(sum(values) / len(values))))


def _pick_focus(scored: list[dict], pain_point_id: str | None) -> dict:
    if pain_point_id:
        for s in scored:
            if s["pain_point_id"] == pain_point_id:
                return s
        raise ValueError(f"pain_point_id {pain_point_id!r} not in stage 2 output")
    ranked = sorted(scored, key=lambda x: -x["ice_score"]["total"])
    high = [s for s in ranked if s["ice_score"]["total"] >= 200]
    return high[0] if high else ranked[0]


def build(pipeline_id: str, pain_point_id: str | None = None) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    scored_path = run_dir / "2_scored_pain_points.json"
    ext_path = run_dir / "_raw" / "external_signals.json"
    cluster_path = run_dir / "_raw" / "pain_clusters.json"

    if not scored_path.is_file():
        raise FileNotFoundError(f"missing {scored_path}")
    if not ext_path.is_file():
        raise FileNotFoundError(
            f"missing {ext_path} — run enrich_external_signals after stage 1"
        )

    scored_batch = json.loads(scored_path.read_text())
    external = json.loads(ext_path.read_text())
    clusters = json.loads(cluster_path.read_text()) if cluster_path.is_file() else {}

    focus = _pick_focus(scored_batch["scored"], pain_point_id)
    focus_id = focus["pain_point_id"]
    related_ids = [focus_id]
    cluster_id = (focus.get("market_signals") or {}).get("cluster_id")
    cluster_row = None
    for c in clusters.get("clusters") or []:
        if c.get("cluster_id") == cluster_id:
            cluster_row = c
            related_ids = list(c.get("pain_point_ids") or [focus_id])
            break

    ext_by_id = external.get("by_pain_point_id") or {}
    member_ext = [ext_by_id[pid] for pid in related_ids if pid in ext_by_id]
    if not member_ext and focus_id in ext_by_id:
        member_ext = [ext_by_id[focus_id]]

    switch_scores = [e["switch_intent"]["score"] for e in member_ext]
    workaround_scores = [e["workaround"]["score"] for e in member_ext]
    persistence_rows = [
        e["github"]["persistence_prefill"]
        for e in member_ext
        if e.get("github", {}).get("persistence_prefill")
    ]

    switching_willingness = _avg(switch_scores)
    workaround_quality = _avg(workaround_scores)
    if persistence_rows:
        persistence = persistence_rows[0]
        persistence_score = persistence["score"]
    else:
        hints = (cluster_row or {}).get("commercial_hints") or {}
        ph = hints.get("persistence_hint", "unknown")
        persistence_score = 4 if ph == "platform_bug" else 7 if ph == "structural" else 5
        persistence = {
            "root_cause_type": "platform_bug" if ph == "platform_bug" else "unknown",
            "owner": "platform",
            "score": persistence_score,
            "rationale": f"Cluster persistence_hint={ph}; no GitHub lifecycle data.",
        }

    competitor_mentions: list[str] = []
    pricing_snippets: list[str] = []
    for e in member_ext:
        competitor_mentions.extend(e.get("competitor_mentions") or [])
        pricing_snippets.extend(e.get("pricing_snippets") or [])

    prefill = {
        "pipeline_id": pipeline_id,
        "focus_pain_point_id": focus_id,
        "focus_title": focus["title"],
        "ice_total": focus["ice_score"]["total"],
        "cluster_id": cluster_id,
        "cluster_size": (cluster_row or {}).get("size", 1),
        "related_pain_point_ids": [pid for pid in related_ids if pid != focus_id],
        "suggested_scores": {
            "pain_score": min(10, max(1, focus["ice_score"]["impact"])),
            "switching_willingness": switching_willingness,
            "workaround_quality_score": workaround_quality,
            "persistence_score": persistence_score,
            "competition_score": min(10, 5 + len(set(competitor_mentions))),
        },
        "persistence_prefill": persistence,
        "switch_phrases": sorted(
            {p for e in member_ext for p in e.get("switch_intent", {}).get("phrases", [])}
        )[:10],
        "workaround_phrases": sorted(
            {p for e in member_ext for p in e.get("workaround", {}).get("phrases", [])}
        )[:10],
        "competitor_mentions": sorted(set(competitor_mentions)),
        "pricing_snippets": sorted(set(pricing_snippets))[:8],
        "data_sources": {
            "external_signals": True,
            "pain_clusters": cluster_path.is_file(),
            "domain_focus": (run_dir / "domain_context.json").is_file(),
            "mode": external.get("mode", "broad"),
        },
        "agent_notes": (
            "Prefill is heuristic — Agent must override with judgment and cite evidence_ledger. "
            "In focus mode, known_competitors from domain_context drive competitor_mentions."
        ),
    }

    out = run_dir / "_raw" / "commercial_prefill.json"
    out.write_text(json.dumps(prefill, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out.relative_to(ROOT)} (focus={focus['title'][:50]!r})")
    return prefill


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--pain-point-id")
    args = parser.parse_args()
    build(args.pipeline_id, args.pain_point_id)


if __name__ == "__main__":
    main()
