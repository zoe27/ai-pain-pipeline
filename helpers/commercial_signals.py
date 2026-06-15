"""Text heuristics for V2 commercial pre-screening (Phase 2b).

Scans pain-point text for switch intent, platform-bug signals, and workaround mentions.
Used by compute_pain_clusters.py and build_scored_batch.py.
"""
from __future__ import annotations

import re

SWITCH_PHRASES = (
    "looking for alternative",
    "looking for another",
    "looking at other",
    "looking at other options",
    "switching to",
    "switched to",
    "moved to",
    "moving to",
    "replace quickbooks",
    "cancel my subscription",
    "uninstall",
    "competitor",
    "any alternatives",
    "better alternative",
)

SWITCH_PATTERNS = (
    re.compile(r"switch(?:ing|ed)?\s+to\s+\w+", re.I),
    re.compile(r"look(?:ing)?\s+for\s+(?:a\s+)?alternative", re.I),
    re.compile(r"migrat(?:e|ing|ed)\s+(?:to|from|away)", re.I),
)

PLATFORM_BUG_PHRASES = (
    "turbopack",
    "vercel",
    "known issue",
    "will be fixed",
    "fixed in next",
    "regression",
    "heap out of memory",
    "out of memory",
    "platform bug",
)

WORKAROUND_PHRASES = (
    "workaround",
    "node_options",
    "--max-old-space-size",
    "fallback to webpack",
    "fall back to webpack",
    "pin version",
    "pinned version",
    "manual export",
    "spreadsheet",
    "google sheets",
)

PAIN_THEME_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("ux_churn", ("update broke", "new update", "every week", "ui change", "hard to use")),
    ("payment_hold", ("hold", "frozen", "5 to 7 days", "5-7 days", "ach fee", "payment")),
    ("dev_oom", ("out of memory", "heap limit", "oom", "memory usage", "8000 mb", "8gb")),
    ("build_regression", ("production build", "build broken", "broken when", "regression")),
    ("billing_pricing", ("billing", "pricing", "too expensive", "subscription", "invoice")),
    ("migration", ("migration", "migrate", "import data", "switching")),
]


def haystack(title: str, body: str) -> str:
    return f"{title}\n{body}".lower()


def detect_themes(title: str, body: str) -> list[str]:
    text = haystack(title, body)
    themes = [name for name, keys in PAIN_THEME_KEYWORDS if any(k in text for k in keys)]
    return themes or ["misc"]


def scan_commercial_hints(title: str, body: str) -> dict:
    text = haystack(title, body)
    return {
        "switch_intent": any(p in text for p in SWITCH_PHRASES),
        "platform_bug_signal": any(p in text for p in PLATFORM_BUG_PHRASES),
        "workaround_signal": any(p in text for p in WORKAROUND_PHRASES),
    }


def extract_switch_intent(title: str, body: str) -> dict:
    text = haystack(title, body)
    phrases = [p for p in SWITCH_PHRASES if p in text]
    for pat in SWITCH_PATTERNS:
        for match in pat.findall(f"{title} {body}"):
            token = match.strip().lower()
            if token and token not in phrases:
                phrases.append(token[:80])
    score = 1
    if phrases:
        score = min(10, 3 + len(phrases) * 2)
    return {"detected": bool(phrases), "phrases": phrases[:8], "score": score}


def extract_workarounds(title: str, body: str) -> dict:
    text = haystack(title, body)
    found = [p for p in WORKAROUND_PHRASES if p in text]
    score = min(10, 2 + len(found) * 2) if found else 1
    return {"detected": bool(found), "phrases": found[:8], "score": score}


def persistence_score_from_github(
    *,
    state: str,
    closed_at: str | None,
    created_at: str | None,
    labels: list[str],
    platform_bug_signal: bool,
) -> dict:
    """Map GitHub issue lifecycle to persistence hint (1-10) for commercial prefill."""
    label_set = {lb.lower() for lb in labels}
    if "wontfix" in label_set or "won't fix" in label_set:
        return {
            "root_cause_type": "structural_permanent",
            "owner": "platform",
            "score": 8,
            "rationale": "Issue closed as wontfix — pain likely persists for users.",
        }
    if state == "closed" and closed_at:
        return {
            "root_cause_type": "platform_bug",
            "owner": "platform",
            "score": 3,
            "rationale": "GitHub issue already closed — platform may have shipped a fix.",
        }
    if platform_bug_signal:
        return {
            "root_cause_type": "platform_bug",
            "owner": "platform",
            "score": 4,
            "rationale": "Open platform/engineering issue with bug/regression signals.",
        }
    return {
        "root_cause_type": "unknown",
        "owner": "platform",
        "score": 6,
        "rationale": "Open issue without clear fix trajectory.",
    }


PRICING_RE = re.compile(
    r"\$\s*(\d+(?:\.\d+)?)\s*(?:/mo|/month|per month|monthly|/yr|/year)",
    re.I,
)


def extract_pricing_mentions(text: str) -> list[str]:
    return [m.group(0).strip() for m in PRICING_RE.finditer(text)][:5]


def match_competitors_in_text(text: str, competitors: list[str]) -> list[str]:
    low = text.lower()
    hits = []
    for name in competitors:
        if name.lower() in low:
            hits.append(name)
    return hits


def product_slug(source: str, source_label: str | None) -> str:
    label = (source_label or source or "unknown").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", label).strip("_")
    return slug[:48] or "unknown"


def cluster_key(title: str, body: str, source: str, source_label: str | None) -> str:
    themes = detect_themes(title, body)
    theme = themes[0]
    return f"{theme}@{product_slug(source, source_label)}"
