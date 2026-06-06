"""Fetch HN story comments via Algolia items API and count resonance phrases."""
from __future__ import annotations

import html
import re
import time

from radar_common import count_comment_resonance_in_texts, http_get_json, quality_settings

ALGOLIA_ITEMS = "https://hn.algolia.com/api/v1/items"


def clean_comment(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_item_comments(object_id: str, *, max_comments: int = 40) -> list[str]:
    payload = http_get_json(
        f"{ALGOLIA_ITEMS}/{object_id}",
        headers={"User-Agent": "pain-radar/0.6 (hn algolia items)"},
    )
    children = payload.get("children") or []
    texts: list[str] = []
    for child in children[:max_comments]:
        if not isinstance(child, dict):
            continue
        comment = child.get("comment") or child
        texts.append(clean_comment(comment.get("text") or comment.get("comment_text")))
    return [t for t in texts if t]


def enrich_comment_resonance(post: dict, config: dict) -> None:
    q = quality_settings(config)
    if not q["fetch_comment_resonance"]:
        post["comment_resonance"] = 0
        return
    if post.get("source") != "hackernews":
        post["comment_resonance"] = 0
        return
    oid = str(post.get("object_id", ""))
    if not oid:
        post["comment_resonance"] = 0
        return
    try:
        texts = fetch_item_comments(oid)
        post["comment_resonance"] = count_comment_resonance_in_texts(texts)
    except Exception:
        post["comment_resonance"] = 0
    time.sleep(0.3)
