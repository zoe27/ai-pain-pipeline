"""Tests for Phase 2c commercial signal extraction."""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "helpers"))

from commercial_signals import (  # noqa: E402
    extract_switch_intent,
    extract_workarounds,
    persistence_score_from_github,
)


def test_switch_intent_detects_phrases():
    r = extract_switch_intent(
        "Looking for alternative",
        "We are switching to FreshBooks next month.",
    )
    assert r["detected"]
    assert r["score"] >= 5


def test_workaround_heap_flag():
    r = extract_workarounds("OOM", "Set NODE_OPTIONS=--max-old-space-size=8192")
    assert r["detected"]
    assert r["score"] >= 3


def test_github_closed_low_persistence():
    r = persistence_score_from_github(
        state="closed",
        closed_at="2026-06-01T00:00:00Z",
        created_at="2026-05-01T00:00:00Z",
        labels=[],
        platform_bug_signal=True,
    )
    assert r["score"] <= 4
    assert r["root_cause_type"] == "platform_bug"
