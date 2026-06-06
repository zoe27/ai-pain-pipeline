"""Stage 0 assembler: validate and write domain_context.json from _judgments/stage0.json.

Usage:
    python3 helpers/build_domain_context.py <pipeline_id>
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "domain_context.schema.json"


def build(pipeline_id: str) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    judg_path = run_dir / "_judgments" / "stage0.json"
    out_path = run_dir / "domain_context.json"

    if not judg_path.exists():
        raise FileNotFoundError(f"missing judgments: {judg_path}")

    data = json.loads(judg_path.read_text())
    data["pipeline_id"] = pipeline_id

    import jsonschema

    jsonschema.validate(data, json.loads(SCHEMA_PATH.read_text()))

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)}")
    return data


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    build(sys.argv[1])


if __name__ == "__main__":
    main()
