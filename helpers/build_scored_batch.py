"""Stage 2 assembler: combine PainPoints + Claude ICE judgments into ScoredPainPointBatch.

Inputs (read from runs/{pipeline_id}/):
    - 1_pain_points.json         stage 1 output
    - _judgments/stage2.json     list of {pain_point_id, impact, confidence, ease, ai_reasoning, red_flags}

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

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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

        scored.append({
            "pain_point_id": pp["id"],
            "title": pp["title"],
            "ice_score": {
                "impact": i,
                "confidence": c,
                "ease": e,
                "total": i * c * e,
            },
            "market_signals": None,
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

    return batch


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    build(sys.argv[1])


if __name__ == "__main__":
    main()
