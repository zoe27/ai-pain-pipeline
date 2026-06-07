"""Smoke test GitHub Issues product_pain filtering (#10).

Fetches issues from configured repos, reports kept vs rejected ratio,
and writes docs/github_issues_smoke.json for regression reference.

Usage:
    python3 helpers/smoke_github_issues.py
    python3 helpers/smoke_github_issues.py --config configs/radar.github_smoke.yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "radar.github_smoke.yaml"
REPORT_PATH = ROOT / "docs" / "github_issues_smoke.json"


def run_smoke(config_path: pathlib.Path) -> dict:
    sys.path.insert(0, str(ROOT / "helpers"))
    from fetch_github_issues import fetch_repo_issues, parse_github_source
    from radar_common import (
        created_after_iso,
        filter_posts,
        global_filters,
        limits,
        load_yaml,
        looks_like_framework_bug_issue,
    )

    config = load_yaml(config_path)
    gh = parse_github_source(config)
    if not gh:
        raise SystemExit("github_issues not enabled in config")

    fetch_limit, top_n = limits(config)
    created_after = created_after_iso(gh["date_range"])
    exclude = global_filters(config)["exclude_keywords"]
    product_pain = gh["mode"] == "product_pain"

    report: dict = {
        "config": str(config_path.relative_to(ROOT)),
        "mode": gh["mode"],
        "repos": gh["repos"],
        "pain_keywords": gh["pain_keywords"],
        "repos_detail": [],
        "totals": {
            "fetched": 0,
            "after_min_comments": 0,
            "kept_product_pain": 0,
            "rejected_framework_bug": 0,
            "rejected_no_pain_keyword": 0,
        },
        "kept_titles": [],
    }

    for repo in gh["repos"]:
        posts, _raw = fetch_repo_issues(
            repo,
            fetch_limit=fetch_limit,
            created_after=created_after,
            label_filter=gh["labels"],
        )
        min_ok = [p for p in posts if p["ups"] >= gh["min_comments"]]
        kept = filter_posts(
            min_ok,
            min_score=gh["min_comments"],
            exclude_keywords=exclude,
            github_product_pain=product_pain,
            pain_keywords=gh["pain_keywords"],
            config=config,
        )[:top_n]

        rejected_bug = 0
        rejected_kw = 0
        if product_pain:
            for p in min_ok:
                if looks_like_framework_bug_issue(p):
                    rejected_bug += 1
                elif not any(
                    k.lower() in f"{p.get('title','')} {p.get('selftext','')}".lower()
                    for k in gh["pain_keywords"]
                ):
                    rejected_kw += 1

        detail = {
            "repo": repo,
            "fetched": len(posts),
            "after_min_comments": len(min_ok),
            "kept": len(kept),
            "rejected_framework_bug_heuristic": rejected_bug,
            "rejected_no_pain_keyword": rejected_kw,
            "kept_titles": [p["title"][:120] for p in kept],
        }
        report["repos_detail"].append(detail)
        report["totals"]["fetched"] += len(posts)
        report["totals"]["after_min_comments"] += len(min_ok)
        report["totals"]["kept_product_pain"] += len(kept)
        report["totals"]["rejected_framework_bug"] += rejected_bug
        report["totals"]["rejected_no_pain_keyword"] += rejected_kw
        report["kept_titles"].extend(detail["kept_titles"])

    t = report["totals"]
    denom = t["after_min_comments"] or 1
    t["keep_rate"] = round(t["kept_product_pain"] / denom, 3)
    t["pass"] = t["kept_product_pain"] >= 1
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=pathlib.Path, default=REPORT_PATH)
    args = parser.parse_args()

    report = run_smoke(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    t = report["totals"]
    print(f"# GitHub Issues smoke — {report['config']}")
    print(f"mode: {report['mode']}")
    for d in report["repos_detail"]:
        print(
            f"  {d['repo']}: fetched={d['fetched']} "
            f"kept={d['kept']} bug_rejected≈{d['rejected_framework_bug_heuristic']}"
        )
    print(
        f"TOTAL kept={t['kept_product_pain']}/{t['after_min_comments']} "
        f"(keep_rate={t['keep_rate']:.1%}) PASS={t['pass']}"
    )
    print(f"→ wrote {args.output.relative_to(ROOT)}")

    if not t["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
