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
    "switching to",
    "moved to",
    "moving to",
    "replace quickbooks",
    "replace ",
    "cancel my subscription",
    "uninstall",
    "competitor",
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


def product_slug(source: str, source_label: str | None) -> str:
    label = (source_label or source or "unknown").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", label).strip("_")
    return slug[:48] or "unknown"


def cluster_key(title: str, body: str, source: str, source_label: str | None) -> str:
    themes = detect_themes(title, body)
    theme = themes[0]
    return f"{theme}@{product_slug(source, source_label)}"
