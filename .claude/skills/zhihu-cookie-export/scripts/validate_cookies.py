#!/usr/bin/env python3
"""Validate Zhihu cookie file without printing secret values."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("z_c0",)
RECOMMENDED = ("_xsrf", "d_c0")


def extract_names(data) -> set[str]:
    if isinstance(data, dict) and "cookies" in data and isinstance(data["cookies"], dict):
        data = data["cookies"]

    if isinstance(data, list):
        names = set()
        for item in data:
            if isinstance(item, dict) and item.get("name"):
                names.add(str(item["name"]))
        return names

    if isinstance(data, dict):
        # ignore meta keys
        return {k for k in data.keys() if not str(k).startswith("_") and k != "cookies"}

    raise ValueError("Cookie file must be a JSON object or array")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Zhihu cookies JSON (no secrets printed)")
    parser.add_argument("path", nargs="?", default="configs/zhihu.cookies.json")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"MISSING: {path}")
        print("Create it from browser export. See .claude/skills/zhihu-cookie-export/SKILL.md")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"INVALID_JSON: {e}")
        return 1

    try:
        names = extract_names(data)
    except ValueError as e:
        print(f"INVALID_FORMAT: {e}")
        return 1

    missing_required = [k for k in REQUIRED if k not in names]
    if missing_required:
        print(f"FAIL: missing required keys: {', '.join(missing_required)}")
        print(f"Found keys: {', '.join(sorted(names)) or '(none)'}")
        return 1

    missing_recommended = [k for k in RECOMMENDED if k not in names]
    found_req = [k for k in REQUIRED if k in names]
    found_rec = [k for k in RECOMMENDED if k in names]

    print(f"OK: found required keys: {', '.join(found_req)}")
    if found_rec:
        print(f"OK: found recommended keys: {', '.join(found_rec)}")
    if missing_recommended:
        print(f"WARN: missing recommended keys: {', '.join(missing_recommended)}")
    print(f"Total cookie keys: {len(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
