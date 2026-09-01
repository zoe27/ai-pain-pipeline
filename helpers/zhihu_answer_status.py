#!/usr/bin/env python3
"""
Check whether the logged-in Zhihu account already answered a question.

Parses js-initialData from the question page (same data the web UI uses).

Usage:
    python3 helpers/zhihu_answer_status.py 2068302620620542437 --cookies configs/zhihu.cookies.json
"""

from __future__ import annotations

import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

try:
    from helpers.fetch_zhihu import load_cookies_into_session
except ImportError:
    from fetch_zhihu import load_cookies_into_session

PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def make_session(cookies_path: Optional[str] = None, session: Optional[requests.Session] = None) -> requests.Session:
    """Return a requests session, optionally bootstrapped with Zhihu cookies."""
    s = session or requests.Session()
    if cookies_path:
        load_cookies_into_session(s, cookies_path)
    try:
        s.get("https://www.zhihu.com/", headers=PAGE_HEADERS, timeout=20)
    except Exception:
        pass
    return s


def check_question_answered(session: requests.Session, question_id: str) -> Dict:
    """Return whether the session's logged-in user already answered this question."""
    checked_at = datetime.now().isoformat()
    url = f"https://www.zhihu.com/question/{question_id}"
    try:
        resp = session.get(url, headers=PAGE_HEADERS, timeout=25)
        if resp.status_code != 200:
            return {
                "answered": False,
                "answer_id": None,
                "url": None,
                "checked_at": checked_at,
                "error": f"HTTP {resp.status_code}",
            }

        match = re.search(
            r'id="js-initialData" type="text/json">(.*?)</script>',
            resp.text,
            re.S,
        )
        if not match:
            return {
                "answered": False,
                "answer_id": None,
                "url": None,
                "checked_at": checked_at,
                "error": "无法解析页面数据",
            }

        payload = json.loads(match.group(1))
        question = (
            payload.get("initialState", {})
            .get("entities", {})
            .get("questions", {})
            .get(str(question_id), {})
        )
        my_answer = (question.get("relationship") or {}).get("myAnswer") or {}
        answer_id = my_answer.get("answerId")
        if answer_id and not my_answer.get("isDeleted"):
            answer_id = str(answer_id)
            return {
                "answered": True,
                "answer_id": answer_id,
                "url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
                "checked_at": checked_at,
                "error": None,
            }

        return {
            "answered": False,
            "answer_id": None,
            "url": None,
            "checked_at": checked_at,
            "error": None,
        }
    except Exception as e:
        return {
            "answered": False,
            "answer_id": None,
            "url": None,
            "checked_at": checked_at,
            "error": str(e),
        }


def check_questions_answered(
    question_ids: List[str],
    cookies_path: Optional[str] = None,
    session: Optional[requests.Session] = None,
    delay_range: tuple[float, float] = (1.0, 2.0),
) -> Dict[str, Dict]:
    """Batch-check answer status for multiple question IDs."""
    s = make_session(cookies_path, session)
    results: Dict[str, Dict] = {}
    for i, question_id in enumerate(question_ids):
        results[question_id] = check_question_answered(s, question_id)
        if i + 1 < len(question_ids):
            time.sleep(random.uniform(*delay_range))
    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check if logged-in user answered Zhihu questions")
    parser.add_argument("question_ids", nargs="+", help="Zhihu question ID(s)")
    parser.add_argument("--cookies", default="configs/zhihu.cookies.json")
    args = parser.parse_args()

    results = check_questions_answered(args.question_ids, cookies_path=args.cookies)
    for qid, status in results.items():
        label = "已回答" if status.get("answered") else "未回答"
        print(f"{qid}: {label}", status.get("url") or status.get("error") or "")


if __name__ == "__main__":
    main()
