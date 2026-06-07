"""Enrich Stage 2 market_signals with external data (Google Trends, HN 48h comment velocity).

Used by build_scored_batch.py. Network failures return partial/null signals — never abort scoring.

Usage (debug):
    python3 helpers/market_signals_enrich.py --keyword saas --hn-id 48396596
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOURS_48 = 48 * 3600
ALGOLIA_ITEMS = "https://hn.algolia.com/api/v1/items"
TRENDS_TIMEOUT = 15
_trends_cache: dict[str, int | None] = {}


def _http_get(url: str, *, headers: dict | None = None, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "pain-radar/0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def pick_trends_keyword(keywords: list[str], title: str) -> str | None:
    """Choose one keyword phrase for Trends lookup."""
    if keywords:
        # Prefer multi-word phrases; skip very short tokens
        for kw in sorted(keywords, key=len, reverse=True):
            low = kw.lower().strip()
            if len(low) >= 4 and low not in ("saas", "startup", "indie"):
                return low
        return keywords[0].lower().strip()
    # Fallback: first significant word from title
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{3,}", title.lower())
    skip = {"what", "when", "where", "how", "show", "with", "from", "that", "this", "your"}
    for w in words:
        if w not in skip:
            return w
    return None


def google_trends_score(keyword: str) -> int | None:
    """Return 0–100 score from recent Google Trends interest slope, or None on failure."""
    if not keyword:
        return None
    key = keyword.lower().strip()
    if key in _trends_cache:
        return _trends_cache[key]
    try:
        from pytrends.request import TrendReq
    except ImportError:
        _trends_cache[key] = None
        return None

    try:
        pt = TrendReq(hl="en-US", tz=360, timeout=(TRENDS_TIMEOUT, TRENDS_TIMEOUT))
        pt.build_payload([keyword], timeframe="today 3-m", geo="US")
        df = pt.interest_over_time()
        if df is None or df.empty or keyword not in df.columns:
            _trends_cache[key] = None
            return None
        series = df[keyword].tolist()
        if len(series) < 4:
            _trends_cache[key] = None
            return None
        mid = len(series) // 2
        recent = sum(series[mid:]) / max(len(series) - mid, 1)
        earlier = sum(series[:mid]) / max(mid, 1)
        if earlier <= 0:
            slope_pct = 100.0 if recent > 0 else 0.0
        else:
            slope_pct = ((recent - earlier) / earlier) * 100.0
        # Map slope -50%..+50% → 0..100 (flat ≈ 50)
        score = int(max(0, min(100, 50 + slope_pct)))
        _trends_cache[key] = score
        return score
    except Exception:
        _trends_cache[key] = None
        return None


def _walk_comment_timestamps(node: dict, out: list[int]) -> None:
    if not isinstance(node, dict):
        return
    comment = node.get("comment") if "comment" in node else node
    if isinstance(comment, dict):
        ts = comment.get("created_at_i")
        if ts is not None:
            try:
                out.append(int(ts))
            except (TypeError, ValueError):
                pass
        for child in comment.get("children") or []:
            _walk_comment_timestamps(child, out)
    for child in node.get("children") or []:
        _walk_comment_timestamps(child, out)


def hn_comments_48h(object_id: str) -> int | None:
    """Count HN comments posted within 48h of story creation. None if fetch fails."""
    if not object_id:
        return None
    try:
        raw = _http_get(
            f"{ALGOLIA_ITEMS}/{object_id}",
            headers={"User-Agent": "pain-radar/0.8 (hn algolia items)"},
        )
        payload = json.loads(raw)
    except Exception:
        return None

    story_ts = payload.get("created_at_i")
    if story_ts is None:
        return None
    try:
        story_ts = int(story_ts)
    except (TypeError, ValueError):
        return None

    cutoff = story_ts + HOURS_48
    timestamps: list[int] = []
    _walk_comment_timestamps(payload, timestamps)
    return sum(1 for ts in timestamps if story_ts <= ts <= cutoff)


def enrich_for_pain_point(
    *,
    source: str,
    object_id: str | None,
    title: str,
    keywords: list[str],
    throttle: bool = True,
) -> dict:
    """Build optional market_signals fields for one pain point."""
    signals: dict = {}

    if source == "hackernews" and object_id:
        c48 = hn_comments_48h(str(object_id))
        if c48 is not None:
            signals["comments_48h"] = c48
        if throttle:
            time.sleep(0.25)

    trend_kw = pick_trends_keyword(keywords, title)
    if trend_kw:
        score = google_trends_score(trend_kw)
        if score is not None:
            signals["google_trends_score"] = score
        if throttle:
            time.sleep(0.5)

    return signals


def load_top50_object_ids(run_dir: pathlib.Path) -> dict[str, str]:
    """Map pain-point title → HN object_id from _raw/top50.json."""
    top50 = run_dir / "_raw" / "top50.json"
    if not top50.is_file():
        return {}
    posts = json.loads(top50.read_text())
    return {
        p.get("title", ""): str(p.get("object_id", ""))
        for p in posts
        if p.get("source") == "hackernews" and p.get("object_id")
    }


def apply_confidence_boosts(
    confidence: int,
    market_signals: dict | None,
) -> int:
    """Adjust confidence from enriched signals (caps at 10)."""
    if not market_signals:
        return confidence
    c = confidence
    trends = market_signals.get("google_trends_score")
    if trends is not None and trends >= 60:
        c += 1
    c48 = market_signals.get("comments_48h")
    if c48 is not None and c48 >= 10:
        c += 1
    elif c48 is not None and c48 >= 5:
        c += 1
    resonance = market_signals.get("comment_resonance") or 0
    if resonance >= 3:
        c += 1
    themes = market_signals.get("theme_mentions") or 0
    if themes >= 2:
        c += 1
    return min(10, c)


def apply_ice_priority(
    impact: int,
    confidence: int,
    ease: int,
    ice_priority: dict | None,
) -> tuple[int, int, int]:
    """Scale ICE by domain_context ice_priority multipliers (clamp 1–10)."""
    if not ice_priority:
        return impact, confidence, ease

    def scale(val: int, key: str) -> int:
        mult = float(ice_priority.get(key, 1.0))
        return max(1, min(10, round(val * mult)))

    return (
        scale(impact, "impact"),
        scale(confidence, "confidence"),
        scale(ease, "ease"),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", help="Google Trends keyword")
    parser.add_argument("--hn-id", help="HN story object_id for 48h comment count")
    args = parser.parse_args()
    if args.keyword:
        print("google_trends_score:", google_trends_score(args.keyword))
    if args.hn_id:
        print("comments_48h:", hn_comments_48h(args.hn_id))
    if not args.keyword and not args.hn_id:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
