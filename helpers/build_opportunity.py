"""Stage 3 assembler: validate and write Opportunity from _judgments/stage3.json.

Inputs (read from runs/{pipeline_id}/):
    - 2_scored_pain_points.json   stage 2 output (existence check)
    - _judgments/stage3.json        Opportunity fields (minus pipeline metadata)

Output:
    - 3_opportunity.json            valid Opportunity per contracts/opportunity.schema.json

Usage:
    python3 helpers/build_opportunity.py <pipeline_id>
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "opportunity.schema.json"


def _validate_evidence_ids(judgment: dict, scored_ids: set[str]) -> None:
    for entry in judgment.get("evidence_ledger") or []:
        for item in entry.get("evidence") or []:
            evidence_id = item.get("pain_point_id")
            if evidence_id not in scored_ids:
                raise ValueError(
                    f"evidence pain_point_id {evidence_id!r} not found in stage 2 output"
                )


def build(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    scored_path = run_dir / "2_scored_pain_points.json"
    judg_path = run_dir / "_judgments" / "stage3.json"
    out_path = run_dir / "3_opportunity.json"

    if not scored_path.exists():
        raise FileNotFoundError(f"missing stage 2 output: {scored_path} (run score-pain first)")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing judgments: {judg_path}")

    scored = json.loads(scored_path.read_text())
    judgment = json.loads(judg_path.read_text())

    pain_point_id = judgment["pain_point_id"]
    scored_ids = {s["pain_point_id"] for s in scored["scored"]}
    if pain_point_id not in scored_ids:
        raise ValueError(f"pain_point_id {pain_point_id!r} not found in stage 2 output")
    for rid in judgment.get("related_pain_point_ids") or []:
        if rid not in scored_ids:
            raise ValueError(f"related_pain_point_id {rid!r} not found in stage 2 output")
    _validate_evidence_ids(judgment, scored_ids)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    opportunity = {
        "pipeline_id": pipeline_id,
        "researched_at": now,
        "input_file": str(scored_path.relative_to(ROOT)),
        **judgment,
    }

    import jsonschema

    jsonschema.validate(opportunity, json.loads(SCHEMA_PATH.read_text()))
    print("✓ jsonschema validation passed")
    if opportunity["recommendation"] == "validate" and opportunity["confidence"] == "high":
        print("WARN validate recommendation usually should not use high confidence")

    out_path.write_text(json.dumps(opportunity, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)} ({out_path.stat().st_size} bytes)")
    print(f"  recommendation: {opportunity['recommendation']} (confidence: {opportunity['confidence']})")

    return opportunity


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    build(sys.argv[1])


if __name__ == "__main__":
    main()
