"""Fetch GitHub Issues and return normalized posts for pain-radar.

Optional: GITHUB_TOKEN in .env (higher rate limits).

Usage:
    python3 helpers/fetch_github_issues.py <pipeline_id> [--config configs/radar.example.yaml]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

from radar_common import (
    ROOT,
    created_after_iso,
    filter_posts,
    global_filters,
    http_get_json,
    limits,
    load_dotenv,
    load_yaml,
    merge_posts,
    source_enabled,
)

DEFAULT_CONFIG = ROOT / "configs" / "radar.example.yaml"


def parse_github_source(config: dict) -> dict | None:
    sources = config.get("sources") or []
    gh = next((s for s in sources if s.get("type") == "github_issues"), None)
    if not gh or not source_enabled(gh):
        return None
    repos = gh.get("repos") or []
    if not repos:
        raise ValueError("github_issues repos list is empty")
    mode = gh.get("mode", "product_pain")
    pain_keywords = gh.get("pain_keywords") or gh.get("keywords") or []
    if mode == "product_pain" and not pain_keywords:
        raise ValueError(
            "github_issues mode=product_pain requires pain_keywords "
            "(business/UX pains, not framework bugs)"
        )
    return {
        "repos": repos,
        "labels": {lb.lower() for lb in (gh.get("labels") or [])},
        "min_comments": int(gh.get("min_comments", gh.get("min_upvotes", 5))),
        "keywords": gh.get("keywords") or [],
        "mode": mode,
        "pain_keywords": pain_keywords,
        "date_range": (config.get("filters") or {}).get("date_range", "last_7_days"),
    }


def github_headers() -> dict:
    import os

    load_dotenv(ROOT / ".env")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    hdrs = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pain-radar/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    return hdrs


def extract_issue(issue: dict, repo: str) -> dict | None:
    if issue.get("pull_request"):
        return None
    number = issue.get("number")
    if not number:
        return None
    comments = int(issue.get("comments") or 0)
    reactions = issue.get("reactions") or {}
    ups = int(reactions.get("+1") or 0) + int(reactions.get("heart") or 0)
    if ups < comments:
        ups = comments
    return {
        "source": "github_issues",
        "source_label": repo,
        "repo": repo,
        "object_id": str(number),
        "title": issue.get("title") or "",
        "selftext": issue.get("body") or "",
        "ups": ups,
        "num_comments": comments,
        "permalink": f"/{repo}/issues/{number}",
        "source_url": issue.get("html_url") or f"https://github.com/{repo}/issues/{number}",
        "author": (issue.get("user") or {}).get("login") or "",
        "url": issue.get("html_url"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
    }


def fetch_repo_issues(
    repo: str,
    *,
    fetch_limit: int,
    created_after: str | None,
    label_filter: set[str],
) -> list[dict]:
    qs = f"state=open&sort=comments&direction=desc&per_page={min(fetch_limit, 100)}"
    url = f"https://api.github.com/repos/{repo}/issues?{qs}"
    raw_issues = http_get_json(url, headers=github_headers())
    if not isinstance(raw_issues, list):
        raise RuntimeError(f"unexpected GitHub response for {repo}")

    posts = []
    for issue in raw_issues:
        if label_filter:
            issue_labels = {lb["name"].lower() for lb in issue.get("labels", [])}
            if not label_filter.intersection(issue_labels):
                continue
        post = extract_issue(issue, repo)
        if not post:
            continue
        # Use updated_at so high-comment threads recently active still count.
        ts = post.get("updated_at") or post.get("created_at") or ""
        if created_after and ts < created_after:
            continue
        posts.append(post)
    return posts, raw_issues


def collect(config: dict, raw_dir: pathlib.Path) -> list[dict]:
    gh = parse_github_source(config)
    if not gh:
        return []

    fetch_limit, top_n = limits(config)
    created_after = created_after_iso(gh["date_range"])
    exclude = global_filters(config)["exclude_keywords"]
    product_pain = gh["mode"] == "product_pain"
    raw_dir.mkdir(parents=True, exist_ok=True)

    mode_label = "product_pain" if product_pain else "all_issues"
    print(
        f"✓ GitHub Issues [{mode_label}] (repos={len(gh['repos'])}, "
        f"min_comments={gh['min_comments']}, date_range={gh['date_range']})"
    )

    merged: list[dict] = []
    ok, failed = 0, []

    for repo in gh["repos"]:
        safe = repo.replace("/", "_")
        try:
            posts, raw_issues = fetch_repo_issues(
                repo,
                fetch_limit=fetch_limit,
                created_after=created_after,
                label_filter=gh["labels"],
            )
            (raw_dir / f"github_{safe}.json").write_text(
                json.dumps(raw_issues, ensure_ascii=False) + "\n"
            )
            filtered = filter_posts(
                posts,
                min_score=gh["min_comments"],
                keywords=gh["keywords"] if not product_pain else [],
                exclude_keywords=exclude,
                github_product_pain=product_pain,
                pain_keywords=gh["pain_keywords"],
            )[:top_n]
            if product_pain and not filtered:
                print(
                    f"WARN github/{repo}: no product-pain issues matched "
                    f"(framework bugs filtered out)",
                    file=sys.stderr,
                )
            elif gh["keywords"] and not filtered and posts and not product_pain:
                print(
                    f"WARN github/{repo}: no keyword matches; keeping top {top_n} by engagement",
                    file=sys.stderr,
                )
                filtered = filter_posts(
                    posts,
                    min_score=gh["min_comments"],
                    exclude_keywords=exclude,
                )[:top_n]
            top_path = raw_dir / f"github_{safe}_top.json"
            top_path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False) + "\n")
            merge_posts(merged, filtered)
            print(f"✓ {repo}: fetched {len(posts)}, kept top {len(filtered)} → {top_path.name}")
            ok += 1
        except Exception as e:
            failed.append((repo, str(e)))
            print(f"WARN github/{repo}: {e}", file=sys.stderr)
        time.sleep(1)

    if ok == 0 and gh["repos"]:
        print("warning: all GitHub repos failed", file=sys.stderr)
    elif failed:
        print(f"warning: {len(failed)} repo(s) skipped", file=sys.stderr)
    return merged


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    config = load_yaml(config_path)
    raw_dir = ROOT / "runs" / pipeline_id / "_raw"
    merged = collect(config, raw_dir)
    if not merged and parse_github_source(config):
        raise SystemExit("GitHub Issues fetch produced no posts")
    top50_path = raw_dir / "top50.json"
    top50_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {top50_path.relative_to(ROOT)} ({len(merged)} posts)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id")
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    run(args.pipeline_id, args.config)


if __name__ == "__main__":
    main()
