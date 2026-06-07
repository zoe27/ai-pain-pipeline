"""Merge Stage 0 domain_context.json into a run-specific radar config YAML.

Reads runs/{pipeline_id}/domain_context.json and a base config (default
configs/radar.example.yaml), writes runs/{pipeline_id}/radar.config.yaml.

Usage:
    python3 helpers/merge_radar_config.py <pipeline_id>
    python3 helpers/merge_radar_config.py pipe_2026-06-07_001 --base configs/radar.indie_gtm.example.yaml

Then fetch with:
    python3 helpers/fetch_radar.py <pipeline_id> --config runs/<pipeline_id>/radar.config.yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from radar_common import ROOT, load_yaml

DEFAULT_BASE = ROOT / "configs" / "radar.example.yaml"

DOMAIN_CONTEXT_KEYS = (
    "domain",
    "target_user",
    "hypothesis",
    "known_competitors",
    "search_keywords",
    "ice_priority",
    "notes",
)


def merge_domain_into_config(base: dict, domain_ctx: dict) -> dict:
    out = json.loads(json.dumps(base))  # deep copy via JSON
    merged_dc = dict(out.get("domain_context") or {})
    for key in DOMAIN_CONTEXT_KEYS:
        val = domain_ctx.get(key)
        if val is None:
            continue
        if key in ("known_competitors", "search_keywords") and not val:
            continue
        merged_dc[key] = val
    out["domain_context"] = merged_dc
    return out


def write_yaml(data: dict, path: pathlib.Path) -> None:
    try:
        import yaml
    except ImportError as e:
        raise SystemExit("PyYAML required: pip install -r requirements.txt") from e
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def merge(
    pipeline_id: str,
    *,
    base_path: pathlib.Path = DEFAULT_BASE,
    out_path: pathlib.Path | None = None,
) -> pathlib.Path:
    run_dir = ROOT / "runs" / pipeline_id
    ctx_path = run_dir / "domain_context.json"
    if not ctx_path.is_file():
        raise FileNotFoundError(
            f"missing {ctx_path} — run domain-focus + build_domain_context.py first"
        )
    if not base_path.is_file():
        raise FileNotFoundError(f"missing base config: {base_path}")

    domain_ctx = json.loads(ctx_path.read_text())
    base = load_yaml(base_path)
    merged = merge_domain_into_config(base, domain_ctx)

    dest = out_path or (run_dir / "radar.config.yaml")
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(merged, dest)

    kw = (merged.get("domain_context") or {}).get("search_keywords") or []
    print(f"✓ wrote {dest.relative_to(ROOT)}")
    print(f"  domain: {(merged.get('domain_context') or {}).get('domain', '')}")
    print(f"  search_keywords ({len(kw)}): {', '.join(kw[:8])}{'…' if len(kw) > 8 else ''}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=DEFAULT_BASE,
        help="Base radar YAML to merge into (default: configs/radar.example.yaml)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Output path (default: runs/{pid}/radar.config.yaml)",
    )
    args = parser.parse_args()
    merge(args.pipeline_id, base_path=args.base, out_path=args.output)


if __name__ == "__main__":
    main()
