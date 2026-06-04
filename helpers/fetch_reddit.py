"""Fetch Reddit top posts via OAuth and build runs/{pipeline_id}/_raw/top50.json.

Requires env (or project-root .env):
    REDDIT_CLIENT_ID
    REDDIT_CLIENT_SECRET
    REDDIT_USER_AGENT   e.g. pain-radar/0.1 by /u/yourname

Usage:
    python3 helpers/fetch_reddit.py <pipeline_id> [--config configs/radar.example.yaml]
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "radar.example.yaml"
TOP_PER_SOURCE = 10
DATE_RANGE_TO_T = {
    "last_24_hours": "day",
    "last_7_days": "week",
    "last_month": "month",
}


def load_dotenv(path: pathlib.Path) -> None:
    import os

    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def load_yaml(path: pathlib.Path) -> dict:
    try:
        import yaml
    except ImportError as e:
        raise SystemExit(
            "PyYAML required: pip install -r requirements.txt (in .venv)"
        ) from e
    return yaml.safe_load(path.read_text()) or {}


def reddit_credentials() -> tuple[str, str, str]:
    import os

    load_dotenv(ROOT / ".env")
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    user_agent = os.environ.get(
        "REDDIT_USER_AGENT", "pain-radar/0.1 by /u/unknown"
    ).strip()
    if not client_id or not client_secret:
        raise SystemExit(
            "Missing Reddit OAuth credentials.\n"
            "1. Create a 'script' app: https://www.reddit.com/prefs/apps\n"
            "2. Copy .env.example → .env and set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET\n"
            "3. Set REDDIT_USER_AGENT to e.g. pain-radar/0.1 by /u/YOUR_USERNAME"
        )
    if "unknown" in user_agent and "/u/" in user_agent:
        print(
            "warning: set REDDIT_USER_AGENT with your Reddit username",
            file=sys.stderr,
        )
    return client_id, client_secret, user_agent


def http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict | None = None,
    data: bytes | None = None,
    timeout: int = 30,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, body


def fetch_access_token(client_id: str, client_secret: str, user_agent: str) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    status, raw = http_request(
        "https://www.reddit.com/api/v1/access_token",
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=body,
    )
    if status != 200:
        text = raw.decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"OAuth token failed HTTP {status}: {text}")
    payload = json.loads(raw)
    token = payload.get("access_token")
    if not token:
        raise SystemExit(f"OAuth response missing access_token: {payload}")
    return token


def extract_posts(payload: dict) -> list[dict]:
    if payload.get("kind") == "Listing":
        children = payload.get("data", {}).get("children", [])
        return [c["data"] for c in children if c.get("kind") == "t3" and "data" in c]
    data = payload.get("data")
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]
    raise ValueError(f"unexpected Reddit JSON shape: keys={list(payload.keys())}")


def fetch_subreddit(
    token: str,
    user_agent: str,
    subreddit: str,
    *,
    t: str,
    limit: int,
) -> dict:
    qs = urllib.parse.urlencode({"t": t, "limit": limit, "raw_json": "1"})
    url = f"https://oauth.reddit.com/r/{subreddit}/top?{qs}"
    status, raw = http_request(
        url,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": user_agent,
        },
    )
    if status == 429:
        time.sleep(5)
        status, raw = http_request(
            url,
            headers={
                "Authorization": f"bearer {token}",
                "User-Agent": user_agent,
            },
        )
    if status != 200:
        text = raw.decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {status}: {text}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"non-JSON response: {raw[:200]!r}") from e
    return payload


def filter_posts(posts: list[dict], min_upvotes: int) -> list[dict]:
    out = []
    for d in posts:
        if d.get("ups", 0) < min_upvotes:
            continue
        if d.get("stickied"):
            continue
        if d.get("over_18"):
            continue
        text = d.get("selftext") or ""
        if text in ("[deleted]", "[removed]"):
            continue
        out.append(
            {
                "subreddit": d.get("subreddit", ""),
                "title": d.get("title", ""),
                "selftext": text,
                "ups": int(d.get("ups", 0)),
                "num_comments": int(d.get("num_comments", 0)),
                "permalink": d.get("permalink", ""),
            }
        )
    out.sort(key=lambda p: p["ups"], reverse=True)
    return out


def parse_reddit_source(config: dict) -> tuple[list[str], int, str, int, int]:
    sources = config.get("sources") or []
    reddit = next((s for s in sources if s.get("type") == "reddit"), None)
    if not reddit:
        raise SystemExit("config has no sources[].type: reddit")
    subreddits = reddit.get("subreddits") or []
    if not subreddits:
        raise SystemExit("reddit subreddits list is empty")
    min_upvotes = int(reddit.get("min_upvotes", 10))
    date_range = (config.get("filters") or {}).get("date_range", "last_7_days")
    t = DATE_RANGE_TO_T.get(date_range, "week")
    fetch_limit = int(config.get("limit_per_source", 50))
    top_n = int(config.get("top_per_source", TOP_PER_SOURCE))
    return subreddits, min_upvotes, t, fetch_limit, top_n


def run(pipeline_id: str, config_path: pathlib.Path) -> None:
    client_id, client_secret, user_agent = reddit_credentials()
    config = load_yaml(config_path)
    subreddits, min_upvotes, t, fetch_limit, top_n = parse_reddit_source(config)

    run_dir = ROOT / "runs" / pipeline_id
    raw_dir = run_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    token = fetch_access_token(client_id, client_secret, user_agent)
    print(f"✓ OAuth token obtained (user-agent: {user_agent[:60]}...)")

    ok, failed = 0, []
    merged: list[dict] = []

    for sr in subreddits:
        out_path = raw_dir / f"{sr}.json"
        try:
            listing = fetch_subreddit(
                token, user_agent, sr, t=t, limit=fetch_limit
            )
            posts = extract_posts(listing)
            out_path.write_text(json.dumps(listing, ensure_ascii=False) + "\n")
            filtered = filter_posts(posts, min_upvotes)[:top_n]
            top_path = raw_dir / f"{sr}_top.json"
            top_path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False) + "\n")
            merged.extend(filtered)
            print(f"✓ r/{sr}: fetched {len(posts)}, kept top {len(filtered)} → {top_path.name}")
            ok += 1
        except Exception as e:
            failed.append((sr, str(e)))
            print(f"WARN r/{sr}: {e}", file=sys.stderr)
        time.sleep(2)

    if ok == 0:
        raise SystemExit(
            "All subreddits failed. Check credentials, User-Agent, and network.\n"
            + "\n".join(f"  - r/{sr}: {err}" for sr, err in failed)
        )

    top50_path = raw_dir / "top50.json"
    top50_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {top50_path.relative_to(ROOT)} ({len(merged)} posts from {ok} subreddits)")
    if failed:
        print(f"warning: {len(failed)} subreddit(s) skipped", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_id", help="e.g. pipe_2026-05-29_003")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=DEFAULT_CONFIG,
        help="RadarConfig YAML path",
    )
    args = parser.parse_args()
    if not re.match(r"^pipe_\d{4}-\d{2}-\d{2}_\d{3}$", args.pipeline_id):
        print(f"warning: pipeline_id {args.pipeline_id!r} does not match pipe_YYYY-MM-DD_NNN")
    run(args.pipeline_id, args.config)


if __name__ == "__main__":
    main()
