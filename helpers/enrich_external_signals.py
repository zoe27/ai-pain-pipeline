"""Phase 2c: external signal enrichment for commercial judgment.

Reads stage-1 pain points + raw fetch metadata, writes:
    runs/{pipeline_id}/_raw/external_signals.json

Signals per pain point:
    - switch_intent (phrases + score)
    - workaround (phrases + score)
    - github_persistence (issue state, labels, persistence prefill)
    - competitor_mentions + pricing_snippets (from domain_context.known_competitors)

Works with both full-market scans and Stage 0 focus runs (domain_context optional).

Usage:
    python3 helpers/enrich_external_signals.py <pipeline_id>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))

from commercial_signals import (  # noqa: E402
    extract_pricing_mentions,
    extract_switch_intent,
    extract_workarounds,
    haystack,
    match_competitors_in_text,
    persistence_score_from_github,
    scan_commercial_hints,
)
from radar_common import http_get_json, load_dotenv  # noqa: E402

GITHUB_ISSUE_RE = re.compile(r"github\.com/([^/]+/[^/]+)/issues/(\d+)")


def _github_headers() -> dict:
    import os

    load_dotenv(ROOT / ".env")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    hdrs = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pain-radar/0.9 (external-signals)",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def _parse_github_url(source_url: str) -> tuple[str, str] | None:
    m = GITHUB_ISSUE_RE.search(source_url or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def fetch_github_issue(repo: str, number: str) -> dict | None:
    try:
        return http_get_json(
            f"https://api.github.com/repos/{repo}/issues/{number}",
            headers=_github_headers(),
        )
    except Exception as e:
        print(f"WARN github issue {repo}#{number}: {e}", file=sys.stderr)
        return None


def load_competitors(run_dir: pathlib.Path) -> list[str]:
    ctx_path = run_dir / "domain_context.json"
    if not ctx_path.is_file():
        return []
    ctx = json.loads(ctx_path.read_text())
    return list(ctx.get("known_competitors") or [])


def enrich_pain_point(pp: dict, *, competitors: list[str], throttle: bool) -> dict:
    title = pp.get("title") or ""
    body = pp.get("raw_content") or ""
    hints = scan_commercial_hints(title, body)
    out: dict = {
        "switch_intent": extract_switch_intent(title, body),
        "workaround": extract_workarounds(title, body),
        "platform_bug_signal": hints["platform_bug_signal"],
    }

    if competitors:
        text = f"{title}\n{body}"
        mentioned = match_competitors_in_text(text, competitors)
        if mentioned:
            out["competitor_mentions"] = mentioned
        prices = extract_pricing_mentions(text)
        if prices:
            out["pricing_snippets"] = prices

    source = pp.get("source")
    if source == "github_issues":
        parsed = _parse_github_url(pp.get("source_url", ""))
        if parsed:
            repo, number = parsed
            issue = fetch_github_issue(repo, number)
            if throttle:
                time.sleep(0.3)
            if issue and not issue.get("pull_request"):
                labels = [lb.get("name", "") for lb in issue.get("labels") or []]
                state = issue.get("state") or "open"
                persistence = persistence_score_from_github(
                    state=state,
                    closed_at=issue.get("closed_at"),
                    created_at=issue.get("created_at"),
                    labels=labels,
                    platform_bug_signal=hints["platform_bug_signal"],
                )
                out["github"] = {
                    "repo": repo,
                    "number": int(number),
                    "state": state,
                    "closed_at": issue.get("closed_at"),
                    "labels": labels[:10],
                    "comments": int(issue.get("comments") or 0),
                    "persistence_prefill": persistence,
                }

    return out


def run(pipeline_id: str, *, throttle: bool = True) -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    inp = run_dir / "1_pain_points.json"
    if not inp.is_file():
        raise SystemExit(f"Missing {inp}")

    batch = json.loads(inp.read_text())
    competitors = load_competitors(run_dir)
    mode = "focus" if competitors or (run_dir / "domain_context.json").is_file() else "broad"

    by_id: dict[str, dict] = {}
    for pp in batch["pain_points"]:
        by_id[pp["id"]] = enrich_pain_point(pp, competitors=competitors, throttle=throttle)

    switch_hits = sum(1 for v in by_id.values() if v["switch_intent"]["detected"])
    gh_enriched = sum(1 for v in by_id.values() if "github" in v)

    payload = {
        "pipeline_id": pipeline_id,
        "mode": mode,
        "known_competitors": competitors,
        "pain_point_count": len(by_id),
        "switch_intent_hits": switch_hits,
        "github_enriched": gh_enriched,
        "by_pain_point_id": by_id,
    }
    out = run_dir / "_raw" / "external_signals.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(
        f"✓ wrote {out.relative_to(ROOT)} "
        f"(mode={mode}, switch={switch_hits}, github={gh_enriched})"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--no-throttle", action="store_true")
    args = parser.parse_args()
    run(args.pipeline_id, throttle=not args.no_throttle)


if __name__ == "__main__":
    main()
