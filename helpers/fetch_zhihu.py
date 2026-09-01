#!/usr/bin/env python3
"""
Zhihu Question Fetcher

Fetches Zhihu questions related to the product for demand discovery.
Handles anti-scraping measures (delays, UA rotation, etc.)

Usage:
    python3 helpers/fetch_zhihu.py growth_zhihu_2026-09-01_001
    python3 helpers/fetch_zhihu.py growth_zhihu_2026-09-01_001 --cookies configs/zhihu.cookies.json

Cookie file (JSON, from a logged-in browser after completing Zhihu verification):
    {
      "z_c0": "...",
      "_xsrf": "...",
      "d_c0": "..."
    }
"""

import argparse
import json
import os
import random
import re
import time
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
import yaml
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Constants
BASE_ZHIHU_SEARCH_URL = "https://www.zhihu.com/api/v4/search_v3"
BASE_ZHIHU_QUESTION_URL = "https://www.zhihu.com/question"


def load_cookies_into_session(session: requests.Session, cookies_path: str) -> None:
    """Load cookies from JSON dict or Netscape cookies.txt into session."""
    path = Path(cookies_path)
    if not path.exists():
        raise FileNotFoundError(f"Cookie file not found: {cookies_path}")

    if path.suffix.lower() in {'.txt', '.cookie'}:
        jar = MozillaCookieJar(str(path))
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies.update(jar)
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Support {"cookies": {...}} or flat {"z_c0": "..."}
    if isinstance(data, dict) and 'cookies' in data and isinstance(data['cookies'], dict):
        data = data['cookies']

    if isinstance(data, list):
        # Browser extension export: [{name, value, domain, ...}, ...]
        for item in data:
            name = item.get('name')
            value = item.get('value')
            if name and value is not None:
                session.cookies.set(name, value, domain=item.get('domain', '.zhihu.com'))
        return

    if not isinstance(data, dict):
        raise ValueError("Cookie file must be a JSON object or Netscape cookies.txt")

    for name, value in data.items():
        if value is not None:
            session.cookies.set(str(name), str(value), domain='.zhihu.com')


class ZhihuFetcher:
    """Fetches Zhihu questions with anti-scraping measures"""

    def __init__(
        self,
        config_path: str = "configs/radar.zhihu.example.yaml",
        cookies_path: Optional[str] = None,
    ):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ua = UserAgent()
        self.session = requests.Session()
        self.cookies_path = cookies_path or self.config.get('anti_scraping', {}).get('cookies_file')
        if self.cookies_path:
            load_cookies_into_session(self.session, self.cookies_path)
            print(f"  Loaded cookies from {self.cookies_path}")
            self._bootstrap_session()

    def _bootstrap_session(self) -> None:
        """Visit homepage to obtain _xsrf / d_c0 when only login cookies were exported."""
        try:
            self.session.get(
                'https://www.zhihu.com/',
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/128.0.0.0 Safari/537.36'
                    ),
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                },
                timeout=30,
            )
        except Exception as e:
            print(f"  Warning: session bootstrap failed: {e}")
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers (prefer stable Chrome UA when cookies are used)."""
        use_random = self.config['anti_scraping']['use_random_ua'] and not self.cookies_path
        ua = self.ua.random if use_random else (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/128.0.0.0 Safari/537.36'
        )
        headers = {
            'User-Agent': ua,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.zhihu.com/search?type=content',
            'Origin': 'https://www.zhihu.com',
            'x-requested-with': 'fetch',
        }
        xsrf = self.session.cookies.get('_xsrf')
        if xsrf:
            headers['x-xsrftoken'] = xsrf
        return headers

    def probe_access(self) -> bool:
        """Quick check whether Zhihu search API is reachable with current session."""
        try:
            response = self.session.get(
                BASE_ZHIHU_SEARCH_URL,
                params={'q': 'PDF', 'type': 'content', 'offset': 0, 'limit': 1},
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                return True
            print(f"  Zhihu probe failed: HTTP {response.status_code}")
            print(f"  Body: {response.text[:300]}")
            if response.status_code == 403 and '验证' in response.text:
                print(
                    "\n  知乎要求人机验证/登录。请用浏览器登录知乎并完成验证后，"
                    "导出 Cookie 到 configs/zhihu.cookies.json，再加 --cookies 重试。"
                )
            return False
        except Exception as e:
            print(f"  Zhihu probe error: {e}")
            return False
    
    def _delay(self):
        """Random delay to avoid rate limiting"""
        min_delay = self.config['anti_scraping']['min_delay']
        max_delay = self.config['anti_scraping']['max_delay']
        time.sleep(random.uniform(min_delay, max_delay))
    
    def search_questions(self, keyword: str, max_count: int = 20) -> List[Dict]:
        """
        Search Zhihu for questions related to keyword
        
        Args:
            keyword: Search keyword
            max_count: Maximum questions to fetch
            
        Returns:
            List of question data dicts
        """
        questions = []
        offset = 0
        limit = 10  # Zhihu API pagination size
        
        print(f"  Searching keyword: '{keyword}'...")
        
        for page in range((max_count // limit) + 1):
            if len(questions) >= max_count:
                break
                
            try:
                # Zhihu search API (simplified, may need auth for full access)
                params = {
                    'q': keyword,
                    'type': 'content',
                    'offset': offset,
                    'limit': limit,
                }
                
                response = self.session.get(
                    BASE_ZHIHU_SEARCH_URL,
                    params=params,
                    headers=self._get_headers(),
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"    Warning: Status {response.status_code}, skipping page")
                    break
                
                data = response.json()
                
                # Extract questions from search results (questions + answers linking to questions)
                if 'data' in data:
                    for item in data['data']:
                        if item.get('type') != 'search_result' or 'object' not in item:
                            continue
                        question = self._parse_question_from_search(item['object'])
                        if question:
                            questions.append(question)
                        if len(questions) >= max_count:
                            break
                
                # Check if there are more results
                if not data.get('paging', {}).get('is_end', True):
                    offset += limit
                    self._delay()
                else:
                    break
                    
            except Exception as e:
                print(f"    Error searching keyword '{keyword}': {e}")
                break
        
        print(f"    Found {len(questions)} questions")
        return questions[:max_count]
    
    def _strip_html(self, text: str) -> str:
        return re.sub(r'</?em>', '', text or '').strip()

    def _parse_question_from_search(self, obj: Dict) -> Optional[Dict]:
        """Parse question data from search result object (question or answer)."""
        try:
            obj_type = obj.get('type')
            if obj_type == 'question':
                question_id = str(obj.get('id', ''))
                title = self._strip_html(obj.get('title') or obj.get('name', ''))
                detail = self._strip_html(obj.get('excerpt', ''))
                author = obj.get('author', {}).get('name', 'Unknown')
                follower_count = obj.get('follower_count', 0)
                answer_count = obj.get('answer_count', 0)
                view_count = obj.get('visit_count', 0)
                topics = [t.get('name', '') for t in obj.get('topics', [])]
                created_at = self._parse_timestamp(obj.get('created'))
                latest_activity = self._parse_timestamp(obj.get('updated_time'))
            elif obj_type == 'answer':
                q = obj.get('question') or {}
                question_id = str(q.get('id', ''))
                title = self._strip_html(q.get('title') or q.get('name', ''))
                detail = self._strip_html(obj.get('excerpt') or obj.get('content', ''))
                author = obj.get('author', {}).get('name', 'Unknown')
                follower_count = q.get('follow_count', q.get('follower_count', 0))
                answer_count = q.get('answer_count', 0)
                view_count = 0
                topics = []
                created_at = self._parse_timestamp(obj.get('created_time'))
                latest_activity = self._parse_timestamp(obj.get('updated_time'))
            else:
                return None

            if not question_id or not title:
                return None

            return {
                'question_id': question_id,
                'url': f"{BASE_ZHIHU_QUESTION_URL}/{question_id}",
                'title': title,
                'detail': detail,
                'created_at': created_at,
                'author': author,
                'follower_count': follower_count or 0,
                'answer_count': answer_count or 0,
                'view_count': view_count or 0,
                'topics': topics,
                'latest_activity': latest_activity,
            }
        except Exception as e:
            print(f"    Warning: Failed to parse question: {e}")
            return None
    
    def _parse_timestamp(self, ts) -> Optional[str]:
        """Convert timestamp to ISO format"""
        if not ts:
            return None
        try:
            if isinstance(ts, int):
                return datetime.fromtimestamp(ts).isoformat()
            return str(ts)
        except:
            return None
    
    def get_topic_questions(self, topic_id: str, max_count: int = 30) -> List[Dict]:
        """Fetch questions from a specific Zhihu topic (placeholder)"""
        print(f"  Topic fetching not yet implemented (topic_id: {topic_id})")
        return []
    
    def get_competitor_related(self, competitor_name: str, max_count: int = 15) -> List[Dict]:
        """
        Fetch questions related to competitors
        
        Args:
            competitor_name: Competitor product name
            max_count: Maximum questions
            
        Returns:
            List of questions
        """
        # Search for "X 替代" or "除了 X 还有什么"
        keywords = [
            f"{competitor_name} 替代",
            f"除了 {competitor_name}",
            f"{competitor_name} 对比",
        ]
        
        all_questions = []
        for kw in keywords:
            questions = self.search_questions(kw, max_count=max_count // len(keywords))
            all_questions.extend(questions)
        
        # Deduplicate by question_id
        seen = set()
        unique_questions = []
        for q in all_questions:
            qid = q['question_id']
            if qid not in seen:
                seen.add(qid)
                unique_questions.append(q)
        
        return unique_questions[:max_count]


def load_product_context(growth_id: str) -> Dict:
    """Load product context from G0 output"""
    path = Path(f"runs/{growth_id}/product_context.json")
    if not path.exists():
        raise FileNotFoundError(
            f"Product context not found: {path}\n"
            f"Run 'python3 helpers/build_product_context.py {growth_id}' first"
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Fetch Zhihu questions for demand discovery')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    parser.add_argument('--config', default='configs/radar.zhihu.example.yaml', help='Config file path')
    parser.add_argument(
        '--cookies',
        default=None,
        help='Path to Zhihu cookies JSON / cookies.txt (required when IP is challenged)',
    )
    parser.add_argument(
        '--probe-only',
        action='store_true',
        help='Only test whether Zhihu API is accessible, then exit',
    )
    args = parser.parse_args()
    
    # Load product context
    print(f"Loading product context for {args.growth_id}...")
    product_ctx = load_product_context(args.growth_id)
    
    # Initialize fetcher
    fetcher = ZhihuFetcher(config_path=args.config, cookies_path=args.cookies)
    config = fetcher.config['fetch']

    print("\n0. Probing Zhihu access...")
    if not fetcher.probe_access():
        raise SystemExit(1)
    print("  ✓ Zhihu search API reachable")
    if args.probe_only:
        return
    
    all_questions = []
    
    # 1. Search by target keywords
    print("\n1. Searching by target keywords...")
    keywords = product_ctx['product_info']['target_keywords']
    for keyword in keywords:
        questions = fetcher.search_questions(
            keyword,
            max_count=config['max_questions_per_keyword']
        )
        all_questions.extend(questions)
    
    # 2. Search by competitor-related queries
    print("\n2. Searching competitor-related questions...")
    competitors = product_ctx['product_info'].get('competitors', [])
    for comp in competitors:
        questions = fetcher.get_competitor_related(
            comp,
            max_count=config['max_questions_per_competitor']
        )
        all_questions.extend(questions)
    
    # Deduplicate
    seen = set()
    unique_questions = []
    for q in all_questions:
        qid = q['question_id']
        if qid not in seen:
            seen.add(qid)
            unique_questions.append(q)
    
    # Save raw output
    output_dir = Path(f"runs/{args.growth_id}/_raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "raw_zhihu_questions.json"
    output_data = {
        'growth_id': args.growth_id,
        'fetched_at': datetime.now().isoformat(),
        'total_count': len(unique_questions),
        'keywords_searched': keywords,
        'competitors_searched': competitors,
        'questions': unique_questions,
        'source': 'zhihu_live',
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    if not unique_questions:
        print(f"\n❌ Fetched 0 questions (API reachable but empty / filtered)")
        print(f"  Saved empty result to: {output_path}")
        raise SystemExit(1)
    
    print(f"\n✓ Fetched {len(unique_questions)} unique questions")
    print(f"  Saved to: {output_path}")
    print(f"\nNext: create _judgments/g1.json then run:")
    print(f"  python3 helpers/build_demand_signals.py {args.growth_id}")


if __name__ == '__main__':
    main()
