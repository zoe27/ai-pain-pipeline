"""Tests for App Store RSS feed normalization."""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "helpers"))

from fetch_app_store import _normalize_feed_entries, extract_review  # noqa: E402


def test_single_review_dict_not_iterated_as_keys():
    feed = {
        "entry": {
            "im:rating": {"label": "1"},
            "id": {"label": "123"},
            "title": {"label": "Bad"},
            "content": {"label": "App broke"},
            "updated": {"label": "2026-06-01T00:00:00-07:00"},
        }
    }
    entries = _normalize_feed_entries(feed)
    assert len(entries) == 1
    review = extract_review(entries[0], app_id="1", app_name="Test")
    assert review is not None
    assert review["star_rating"] == 1


def test_list_mixed_skips_non_dict():
    feed = {"entry": [{"im:rating": {"label": "2"}, "id": {"label": "1"}, "title": {"label": "x"}, "content": {"label": "y"}, "updated": {"label": "2026-06-01T00:00:00-07:00"}}, "stray"]}
    entries = _normalize_feed_entries(feed)
    assert len(entries) == 1
