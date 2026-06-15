"""Stage 2 assembler: combine PainPoints + Claude ICE judgments into ScoredPainPointBatch.

Inputs (read from runs/{pipeline_id}/):
    - 1_pain_points.json         stage 1 output
    - _judgments/stage2.json     list of {pain_point_id, impact, confidence, ease, ai_reasoning, red_flags}
    - domain_context.json        optional ice_priority multipliers (Stage 0)
    - _raw/radar_signals.json    theme cluster + comment_resonance
    - _raw/top50.json              HN object_id lookup for 48h comment enrich

Output:
    - 2_scored_pain_points.json  valid ScoredPainPointBatch per contracts/scored_pain_point.schema.json

Judgments are matched by pain_point_id (not order), so the judgment file order doesn't matter
and dropping/adding pain points later is safe.

Usage:
    python3 helpers/build_scored_batch.py <pipeline_id>
"""
import json
import datetime
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "scored_pain_point.schema.json"


def build(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    inp_path = run_dir / "1_pain_points.json"
    judg_path = run_dir / "_judgments" / "stage2.json"
    out_path = run_dir / "2_scored_pain_points.json"

    if not inp_path.exists():
        raise FileNotFoundError(f"missing stage 1 output: {inp_path} (run pain-radar first)")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing judgments: {judg_path}")

    from market_signals_enrich import (
        apply_cluster_dampening,
        apply_confidence_boosts,
        apply_ice_priority,
        enrich_for_pain_point,
        load_top50_object_ids,
    )

    inp = json.loads(inp_path.read_text())
    judgments = json.loads(judg_path.read_text())

    if inp["count"] != len(inp["pain_points"]):
        raise ValueError(f"stage 1 output corrupt: count={inp['count']} but {len(inp['pain_points'])} items")

    judg_by_id = {j["pain_point_id"]: j for j in judgments}
    if len(judg_by_id) != len(judgments):
        raise ValueError("duplicate pain_point_id in judgments")

    missing = [p["id"] for p in inp["pain_points"] if p["id"] not in judg_by_id]
    if missing:
        raise ValueError(f"missing judgments for {len(missing)} pain points (first: {missing[0]})")

    ice_priority = None
    ctx_path = run_dir / "domain_context.json"
    if ctx_path.is_file():
        ice_priority = json.loads(ctx_path.read_text()).get("ice_priority")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    signals_path = run_dir / "_raw" / "radar_signals.json"
    sig_by_title: dict[str, dict] = {}
    multi_themes: dict[str, int] = {}
    if signals_path.exists():
        sig = json.loads(signals_path.read_text())
        multi_themes = sig.get("multi_post_themes") or {}
        for row in sig.get("posts") or []:
            if row.get("title"):
                sig_by_title[row["title"]] = row

    hn_ids = load_top50_object_ids(run_dir)

    cluster_by_id: dict[str, dict] = {}
    clusters_path = run_dir / "_raw" / "pain_clusters.json"
    if clusters_path.exists():
        cluster_payload = json.loads(clusters_path.read_text())
        for cluster in cluster_payload.get("clusters") or []:
            for pid in cluster.get("pain_point_ids") or []:
                cluster_by_id[pid] = cluster

    ext_by_id: dict[str, dict] = {}
    ext_path = run_dir / "_raw" / "external_signals.json"
    if ext_path.exists():
        ext_by_id = json.loads(ext_path.read_text()).get("by_pain_point_id") or {}

    scored = []
    for pp in inp["pain_points"]:
        j = judg_by_id[pp["id"]]
        i, c, e = int(j["impact"]), int(j["confidence"]), int(j["ease"])
        if not (1 <= i <= 10 and 1 <= c <= 10 and 1 <= e <= 10):
            raise ValueError(f"ICE out of range for {pp['id']}: I={i} C={c} E={e}")
        if not (20 <= len(j["ai_reasoning"]) <= 500):
            raise ValueError(f"reasoning length {len(j['ai_reasoning'])} out of [20,500] for {pp['title']!r}")
        if len(j["red_flags"]) > 10:
            raise ValueError(f"too many red_flags ({len(j['red_flags'])}) for {pp['title']!r}")
        for r in j["red_flags"]:
            if not (3 <= len(r) <= 80):
                raise ValueError(f"red_flag length out of [3,80]: {r!r}")

        i, c, e = apply_ice_priority(i, c, e, ice_priority)

        market_signals: dict | None = None
        row = sig_by_title.get(pp["title"])
        if row:
            themes = row.get("themes") or []
            theme_mentions = max(
                (multi_themes.get(t, 1) for t in themes),
                default=0,
            )
            resonance = int(row.get("comment_resonance") or 0)
            market_signals = {
                "comment_resonance": resonance,
                "theme_mentions": max(theme_mentions, 1) if themes else 1,
            }

        object_id = hn_ids.get(pp["title"])
        if not object_id and pp.get("source") == "hackernews":
            # Fallback: parse from source_url
            url = pp.get("source_url", "")
            if "id=" in url:
                object_id = url.split("id=")[-1].split("&")[0]

        extra = enrich_for_pain_point(
            source=pp.get("source", ""),
            object_id=object_id,
            title=pp["title"],
            keywords=pp.get("extracted_keywords") or [],
        )
        if extra or market_signals:
            market_signals = {**(market_signals or {}), **extra}

        cluster = cluster_by_id.get(pp["id"])
        if cluster:
            market_signals = {
                **(market_signals or {}),
                "cluster_id": cluster["cluster_id"],
                "cluster_size": cluster["size"],
                "cluster_source_count": cluster["source_count"],
                "commercial_hints": cluster["commercial_hints"],
            }

        ext = ext_by_id.get(pp["id"])
        if ext:
            ext_out: dict = {
                "switch_intent_score": ext["switch_intent"]["score"],
                "workaround_score": ext["workaround"]["score"],
            }
            if ext.get("switch_intent", {}).get("phrases"):
                ext_out["switch_phrases"] = ext["switch_intent"]["phrases"][:5]
            if ext.get("github"):
                gh = ext["github"]
                ext_out["github_issue_state"] = gh.get("state")
                pref = gh.get("persistence_prefill") or {}
                if pref.get("score"):
                    ext_out["persistence_prefill_score"] = pref["score"]
            if ext.get("competitor_mentions"):
                ext_out["competitor_mentions"] = ext["competitor_mentions"]
            market_signals = {**(market_signals or {}), "external_signals": ext_out}

        c = apply_confidence_boosts(c, market_signals)
        c = apply_cluster_dampening(c, market_signals)

        scored.append({
            "pain_point_id": pp["id"],
            "title": pp["title"],
            "ice_score": {
                "impact": i,
                "confidence": c,
                "ease": e,
                "total": i * c * e,
            },
            "market_signals": market_signals if market_signals else None,
            "ai_reasoning": j["ai_reasoning"],
            "red_flags": j["red_flags"],
        })

    batch = {
        "pipeline_id": pipeline_id,
        "scored_at": now,
        "input_file": str(inp_path.relative_to(ROOT)),
        "count": len(scored),
        "scored": scored,
    }

    out_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)} ({out_path.stat().st_size} bytes, {batch['count']} scored)")

    import jsonschema
    jsonschema.validate(batch, json.loads(SCHEMA_PATH.read_text()))
    print("✓ jsonschema validation passed")

    enriched = sum(1 for s in scored if s.get("market_signals"))
    print(f"✓ market_signals enriched: {enriched}/{len(scored)}")

    try:
        from build_commercial_prefill import build as build_prefill

        build_prefill(pipeline_id)
    except Exception as e:
        print(f"WARN commercial_prefill: {e}", file=sys.stderr)

    return batch


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    build(sys.argv[1])


if __name__ == "__main__":
    main()
