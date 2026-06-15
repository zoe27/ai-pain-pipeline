"""Assemble Chinese (zh) reading sidecars from Agent i18n judgments.

Inputs (per stage, under runs/{pipeline_id}/):
    Stage 1: 1_pain_points.json + _judgments/stage1_i18n.json
    Stage 2: 2_scored_pain_points.json + _judgments/stage2_i18n.json
    Stage 3: 3_opportunity.json + _judgments/stage3_i18n.json

Outputs:
    1_pain_points.i18n.json
    2_scored_pain_points.i18n.json
    3_opportunity.i18n.json

Usage:
    python3 helpers/build_i18n.py <pipeline_id> --stage 1|2|3
    python3 helpers/build_i18n.py <pipeline_id> --all
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _len_ok(text: str, lo: int, hi: int, field: str) -> None:
    n = len(text)
    if not (lo <= n <= hi):
        raise ValueError(f"{field} length {n} out of [{lo},{hi}]")


def build_stage1(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    src_path = run_dir / "1_pain_points.json"
    judg_path = run_dir / "_judgments" / "stage1_i18n.json"
    out_path = run_dir / "1_pain_points.i18n.json"

    if not src_path.exists():
        raise FileNotFoundError(f"missing {src_path}")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing {judg_path}")

    src = json.loads(src_path.read_text())
    rows = json.loads(judg_path.read_text())
    points = src["pain_points"]

    if len(rows) != len(points):
        raise ValueError(f"stage1_i18n length {len(rows)} != pain_points {len(points)}")

    items = []
    for pp, j in zip(points, rows):
        title_zh = j["title_zh"].strip()
        summary_zh = j["summary_zh"].strip()
        _len_ok(title_zh, 1, 200, "title_zh")
        _len_ok(summary_zh, 10, 500, "summary_zh")
        kws = j.get("keywords_zh") or []
        if not kws:
            raise ValueError(f"keywords_zh empty for {pp['id']}")
        if len(kws) > 10:
            raise ValueError(f"too many keywords_zh for {pp['id']}")
        for kw in kws:
            if not kw.strip():
                raise ValueError(f"empty keyword in keywords_zh for {pp['id']}")

        items.append(
            {
                "id": pp["id"],
                "title_zh": title_zh,
                "summary_zh": summary_zh,
                "keywords_zh": kws,
            }
        )

    batch = {
        "pipeline_id": pipeline_id,
        "locale": "zh",
        "generated_at": _now(),
        "source_file": str(src_path.relative_to(ROOT)),
        "count": len(items),
        "items": items,
    }
    out_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)} ({batch['count']} items)")
    return batch


def build_stage2(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    src_path = run_dir / "2_scored_pain_points.json"
    judg_path = run_dir / "_judgments" / "stage2_i18n.json"
    out_path = run_dir / "2_scored_pain_points.i18n.json"

    if not src_path.exists():
        raise FileNotFoundError(f"missing {src_path}")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing {judg_path}")

    src = json.loads(src_path.read_text())
    rows = json.loads(judg_path.read_text())
    by_id = {j["pain_point_id"]: j for j in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate pain_point_id in stage2_i18n.json")

    missing = [s["pain_point_id"] for s in src["scored"] if s["pain_point_id"] not in by_id]
    if missing:
        raise ValueError(f"missing i18n for {len(missing)} scored items (first: {missing[0]})")

    items = []
    for s in src["scored"]:
        j = by_id[s["pain_point_id"]]
        title_zh = j["title_zh"].strip()
        reasoning_zh = j["ai_reasoning_zh"].strip()
        _len_ok(title_zh, 1, 200, "title_zh")
        _len_ok(reasoning_zh, 20, 500, "ai_reasoning_zh")
        flags = j.get("red_flags_zh") or []
        if len(flags) > 10:
            raise ValueError(f"too many red_flags_zh for {s['pain_point_id']}")
        for r in flags:
            _len_ok(r.strip(), 3, 80, "red_flag_zh")

        items.append(
            {
                "pain_point_id": s["pain_point_id"],
                "title_zh": title_zh,
                "ai_reasoning_zh": reasoning_zh,
                "red_flags_zh": flags,
            }
        )

    batch = {
        "pipeline_id": pipeline_id,
        "locale": "zh",
        "generated_at": _now(),
        "source_file": str(src_path.relative_to(ROOT)),
        "count": len(items),
        "items": items,
    }
    out_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)} ({batch['count']} items)")
    return batch


def build_stage3(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    src_path = run_dir / "3_opportunity.json"
    judg_path = run_dir / "_judgments" / "stage3_i18n.json"
    out_path = run_dir / "3_opportunity.i18n.json"

    if not src_path.exists():
        raise FileNotFoundError(f"missing {src_path}")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing {judg_path}")

    src = json.loads(src_path.read_text())
    j = json.loads(judg_path.read_text())

    _len_ok(j["title_zh"].strip(), 1, 200, "title_zh")
    _len_ok(j["one_liner_zh"].strip(), 10, 200, "one_liner_zh")
    _len_ok(j["product_hypothesis_zh"].strip(), 50, 1000, "product_hypothesis_zh")
    _len_ok(j["research_notes_zh"].strip(), 50, 2000, "research_notes_zh")

    personas = j.get("target_personas") or []
    if not personas:
        raise ValueError("target_personas required in stage3_i18n.json")
    for p in personas:
        _len_ok(p["name_zh"].strip(), 1, 80, "name_zh")
        quotes = p.get("quotes_zh") or []
        if not quotes:
            raise ValueError(f"quotes_zh empty for persona {p.get('name_zh')}")

    solutions = j.get("existing_solutions") or []
    if not solutions:
        raise ValueError("existing_solutions required in stage3_i18n.json")
    for s in solutions:
        _len_ok(s["name_zh"].strip(), 1, 80, "name_zh")
        weak = s.get("weaknesses_zh") or []
        if not weak:
            raise ValueError(f"weaknesses_zh empty for {s.get('name_zh')}")

    rec_map = {"build": "建议做", "skip": "建议跳过", "partner": "建议合作", "validate": "建议验证"}
    conf_map = {"high": "高", "medium": "中", "low": "低"}

    batch = {
        "pipeline_id": pipeline_id,
        "locale": "zh",
        "generated_at": _now(),
        "source_file": str(src_path.relative_to(ROOT)),
        "pain_point_id": src["pain_point_id"],
        "title_zh": j["title_zh"].strip(),
        "one_liner_zh": j["one_liner_zh"].strip(),
        "recommendation_zh": rec_map.get(src["recommendation"], src["recommendation"]),
        "confidence_zh": conf_map.get(src["confidence"], src["confidence"]),
        "target_personas": personas,
        "existing_solutions": solutions,
        "product_hypothesis_zh": j["product_hypothesis_zh"].strip(),
        "research_notes_zh": j["research_notes_zh"].strip(),
    }
    if "confidence_basis_rationale_zh" in j:
        _len_ok(j["confidence_basis_rationale_zh"].strip(), 20, 500, "confidence_basis_rationale_zh")
        batch["confidence_basis_rationale_zh"] = j["confidence_basis_rationale_zh"].strip()
    if "unsupported_assumptions_zh" in j:
        assumptions = [a.strip() for a in j["unsupported_assumptions_zh"]]
        for a in assumptions:
            _len_ok(a, 10, 200, "unsupported_assumptions_zh")
        batch["unsupported_assumptions_zh"] = assumptions
    if "validation_required" in j:
        validations = j["validation_required"]
        for v in validations:
            _len_ok(v["experiment_zh"].strip(), 10, 200, "experiment_zh")
            _len_ok(v["success_criterion_zh"].strip(), 10, 200, "success_criterion_zh")
        batch["validation_required"] = validations
    if "evidence_ledger" in j:
        evidence_ledger = j["evidence_ledger"]
        for entry in evidence_ledger:
            _len_ok(entry["claim_zh"].strip(), 10, 200, "claim_zh")
            for assumption in entry.get("assumptions_zh") or []:
                _len_ok(assumption.strip(), 10, 200, "assumptions_zh")
        batch["evidence_ledger"] = evidence_ledger
    out_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)}")
    return batch


BUILDERS = {1: build_stage1, 2: build_stage2, 3: build_stage3}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        for n in (1, 2, 3):
            BUILDERS[n](args.pipeline_id)
    elif args.stage:
        BUILDERS[args.stage](args.pipeline_id)
    else:
        parser.error("specify --stage 1|2|3 or --all")


if __name__ == "__main__":
    main()
