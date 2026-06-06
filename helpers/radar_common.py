"""Shared helpers for pain-radar fetch scripts."""
from __future__ import annotations

import json
import os
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOP_PER_SOURCE = 10
DATE_RANGE_SECONDS = {
    "last_24_hours": 86400,
    "last_7_days": 7 * 86400,
    "last_month": 30 * 86400,
}

# Default noise for internet/SaaS focus (overridable via config filters.exclude_keywords)
DEFAULT_EXCLUDE_KEYWORDS = [
    "lego",
    "parenting",
    "renewable",
    "solar power",
    "wind power",
    "energy transition",
    "geopolitics",
    "nytimes",
    "journalism",
    "climate",
]

# GitHub issue titles that are usually framework bugs, not product pains
TECH_ISSUE_TITLE_RE = re.compile(
    r"(^fix[\(:]|^bug[\(:]|regression|typo|valueerror|typeerror|"
    r"doesn'?t work|fails when|broken test|ci fail|enum|"
    r"structured.?output|checkpoint|text-splitter|lint rule)",
    re.I,
)

BUG_REPORT_BODY_MARKERS = (
    "bug report",
    "### checked other resources",
    "### submission checklist",
    "### verify canary release",
    "### link to the code that reproduces",
)

# Heuristic post kinds for quality filter + eval benchmark
KIND_PAIN = "pain_candidate"
KIND_LAUNCH = "product_launch"
KIND_JOB = "job_seeking"
KIND_CELEBRATION = "celebration"
KIND_OTHER = "other"

DEFAULT_PAIN_PHRASES = [
    "i've tried",
    "i've done nearly everything",
    "nothing's working",
    "no customers",
    "no customer",
    "zero users",
    "zero traction",
    "what's wrong",
    "idk how",
    "don't know what else",
    "frustrated",
    "why is it so hard",
    "am i the only one",
    "killed my",
    "locked out",
    "my business bleeds",
    "doesn't land in the inbox",
    "don't land in the inbox",
    "0 response",
    "zero response",
    "losing hope",
    "still hasn't attracted",
    "not sure what i did wrong",
    "no real answer",
    "no timeline",
]

# Internet/SaaS business pain topics (not meta-web / pure DX)
BUSINESS_PAIN_KEYWORDS = (
    "saas",
    "startup",
    "customers",
    "customer",
    "mrr",
    "arr",
    "revenue",
    "churn",
    "billing",
    "pricing",
    "marketing",
    "acquisition",
    "onboarding",
    "subscription",
    "b2b",
    "outreach",
    "inbox",
    "founder",
    "users",
    "locked out",
    "suspended",
    "google cloud",
    "vendor",
)

OFF_TOPIC_META_WEB_RE = re.compile(
    r"(llm\.txt|/llm\.txt|gopher web|gemini web|markdown render|"
    r"web browsers like chrome|parsing the standard marketing)",
    re.I,
)

COMMENT_RESONANCE_PHRASES = (
    "+1",
    "same issue",
    "same problem",
    "me too",
    "we had this",
    "we've had this",
    "happened to me",
    "happened to us",
    "this happened",
    "exact same",
)

PAIN_THEME_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("vendor_lockin", ("locked out", "suspended", "google cloud", "vendor", "aws", "account")),
    ("gtm_distribution", ("no customers", "market my saas", "marketing", "0 response", "zero traction", "cold outreach")),
    ("email_deliverability", ("inbox", "deliverability", "warmup", "don't land")),
]

PRODUCT_LAUNCH_TITLE_RE = re.compile(r"^show\s+hn\s*:", re.I)
PRODUCT_LAUNCH_BODY_MARKERS = (
    "hi hn",
    "we're building",
    "we are building",
    "we’re building",
    "i'm excited to show",
    "i am excited to show",
    "excited to show off",
    "would appreciate any feedback",
    "feedback welcome",
    "feedbacks and questions are welcome",
    "let me know what you think",
    "try it and let me know",
    "we'd love for you",
    "we’d love for you",
    "built by founders who",
    "is the ai operator",
    "is the premium",
    "ultimate ai agent",
    "github:",
    "for anyone interested in trying",
)

JOB_SEEKING_RE = re.compile(
    r"(^ask hn:\s*who is hiring|who is hiring\??\s*$|"
    r"resume review|freelancer\?|looking for (a )?job\b|"
    r"job search thread|interview prep\b)",
    re.I,
)

CELEBRATION_RE = re.compile(
    r"(first (paying )?customer|hit \$\d|reached \$\d|"
    r"sold my (startup|company)|mrr milestone|"
    r"we hit \d+k users|just launched and got \d+ signups)",
    re.I,
)


def domain_context(config: dict) -> dict:
    ctx = config.get("domain_context") or {}
    return {
        "domain": (ctx.get("domain") or "").strip(),
        "target_user": (ctx.get("target_user") or "").strip(),
        "hypothesis": (ctx.get("hypothesis") or "").strip(),
        "known_competitors": list(ctx.get("known_competitors") or []),
        "search_keywords": [
            k.strip().lower() for k in (ctx.get("search_keywords") or []) if k.strip()
        ],
    }


def effective_keywords(base: list[str], config: dict) -> list[str]:
    """Merge per-source keywords with domain_context.search_keywords (deduped)."""
    extra = domain_context(config)["search_keywords"]
    seen: set[str] = set()
    out: list[str] = []
    for kw in list(base or []) + extra:
        low = kw.lower().strip()
        if low and low not in seen:
            seen.add(low)
            out.append(kw)
    return out


def quality_settings(config: dict) -> dict:
    flt = config.get("filters") or {}
    q = flt.get("quality") or {}
    return {
        "enabled": q.get("enabled", True) is not False,
        "drop_product_launches": q.get("drop_product_launches", True) is not False,
        "drop_job_seeking": q.get("drop_job_seeking", True) is not False,
        "drop_celebrations": q.get("drop_celebrations", True) is not False,
        "require_pain_signal_for_show_hn": q.get(
            "require_pain_signal_for_show_hn", True
        )
        is not False,
        "drop_producthunt_launches": q.get("drop_producthunt_launches", True)
        is not False,
        "pain_phrases": [
            p.lower() for p in (q.get("pain_phrases") or DEFAULT_PAIN_PHRASES)
        ],
        "require_business_pain_for_ask_hn": q.get(
            "require_business_pain_for_ask_hn", True
        )
        is not False,
        "drop_off_topic_meta_web": q.get("drop_off_topic_meta_web", True) is not False,
        "fetch_comment_resonance": q.get("fetch_comment_resonance", True) is not False,
        "min_comment_resonance": int(q.get("min_comment_resonance", 0)),
    }


def has_pain_signal(post: dict, pain_phrases: list[str] | None = None) -> bool:
    text = haystack(post)
    phrases = pain_phrases or DEFAULT_PAIN_PHRASES
    return any(p in text for p in phrases)


def has_business_pain_topic(post: dict) -> bool:
    text = haystack(post)
    return any(k in text for k in BUSINESS_PAIN_KEYWORDS)


def is_off_topic_meta_web(post: dict) -> bool:
    """Meta-web / llm.txt threads — 'marketing' in prose must not count as SaaS GTM pain."""
    text = haystack(post)
    if not OFF_TOPIC_META_WEB_RE.search(text):
        return False
    strong = (
        "saas",
        "customers",
        "customer",
        "mrr",
        "arr",
        "churn",
        "billing",
        "subscription",
        "startup killed",
        "locked out",
        "no customers",
        "market my saas",
        "cold outreach",
        "0 response",
    )
    return not any(k in text for k in strong)


def detect_pain_themes(post: dict) -> list[str]:
    text = haystack(post)
    return [name for name, keys in PAIN_THEME_RULES if any(k in text for k in keys)]


def count_comment_resonance_in_texts(texts: list[str]) -> int:
    count = 0
    for raw in texts:
        low = raw.lower()
        for phrase in COMMENT_RESONANCE_PHRASES:
            if phrase in low:
                count += 1
                break
    return count


def is_product_launch(post: dict) -> bool:
    title = (post.get("title") or "").strip()
    body = haystack(post)
    label = (post.get("source_label") or "").lower()
    if post.get("source") == "producthunt":
        return True
    if label == "show_hn" or PRODUCT_LAUNCH_TITLE_RE.match(title):
        if any(m in body for m in PRODUCT_LAUNCH_BODY_MARKERS):
            return True
        if post.get("url") and len((post.get("selftext") or "")) > 200:
            return True
    return False


def is_job_seeking(post: dict) -> bool:
    title = post.get("title") or ""
    if JOB_SEEKING_RE.search(title):
        return True
    # "laid off" + SaaS marketing is pain, not job thread
    text = haystack(post)
    if "laid off" in text and any(
        k in text for k in ("market my saas", "marketing my saas", "my saas")
    ):
        return False
    if "laid off" in text and "who is hiring" not in text:
        return False
    return JOB_SEEKING_RE.search(text) is not None


def is_celebration(post: dict) -> bool:
    return CELEBRATION_RE.search(haystack(post)) is not None


def classify_post(post: dict) -> str:
    """Heuristic label for eval benchmark (not LLM)."""
    if is_job_seeking(post):
        return KIND_JOB
    if is_celebration(post):
        return KIND_CELEBRATION
    if is_product_launch(post):
        return KIND_LAUNCH
    if has_pain_signal(post) and has_business_pain_topic(post):
        return KIND_PAIN
    if has_pain_signal(post) and not is_off_topic_meta_web(post):
        return KIND_PAIN
    return KIND_OTHER


def should_drop_quality(post: dict, config: dict) -> str | None:
    """Return drop reason string, or None if post should be kept."""
    q = quality_settings(config)
    if not q["enabled"]:
        return None
    if q["drop_job_seeking"] and is_job_seeking(post):
        return "job_seeking"
    if q["drop_celebrations"] and is_celebration(post):
        return "celebration"
    if post.get("source") == "producthunt" and q["drop_producthunt_launches"]:
        return "producthunt_launch"
    if q["drop_product_launches"] and is_product_launch(post):
        return "product_launch"
    label = (post.get("source_label") or "").lower()
    title = (post.get("title") or "").lower()
    is_show = label == "show_hn" or title.startswith("show hn:")
    if is_show and q["require_pain_signal_for_show_hn"]:
        if not has_pain_signal(post, q["pain_phrases"]):
            return "show_hn_no_pain_signal"
    is_ask = label == "ask_hn" or title.startswith("ask hn:")
    if is_ask and q["drop_off_topic_meta_web"] and is_off_topic_meta_web(post):
        return "off_topic_meta_web"
    if is_ask and q["require_business_pain_for_ask_hn"]:
        if not has_business_pain_topic(post) and not has_pain_signal(
            post, q["pain_phrases"]
        ):
            return "ask_hn_no_business_pain"
    min_res = q["min_comment_resonance"]
    if min_res > 0 and is_ask:
        resonance = int(post.get("comment_resonance") or 0)
        if resonance < min_res and not has_pain_signal(post, q["pain_phrases"]):
            return "low_comment_resonance"
    return None


def global_filters(config: dict) -> dict:
    """Shared filter knobs from config.filters."""
    flt = config.get("filters") or {}
    exclude = list(flt.get("exclude_keywords") or DEFAULT_EXCLUDE_KEYWORDS)
    return {
        "focus": flt.get("focus", "internet_saas"),
        "exclude_keywords": [k.lower() for k in exclude],
    }


def haystack(post: dict) -> str:
    return f"{post.get('title', '')} {post.get('selftext', '')}".lower()


def matches_keywords(post: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = haystack(post)
    return any(kw.lower() in text for kw in keywords)


def matches_exclude(post: dict, exclude_keywords: list[str]) -> bool:
    if not exclude_keywords:
        return False
    text = haystack(post)
    return any(kw in text for kw in exclude_keywords)


def looks_like_framework_bug_issue(post: dict) -> bool:
    """GitHub issues that read as bug reports / DX fixes, not user/business pains."""
    if post.get("source") != "github_issues":
        return False
    title = post.get("title", "")
    body = (post.get("selftext") or "")[:800].lower()
    if TECH_ISSUE_TITLE_RE.search(title):
        return True
    if any(m in body for m in BUG_REPORT_BODY_MARKERS):
        return True
    return False


def filter_posts(
    posts: list[dict],
    *,
    min_score: int,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    source: str | None = None,
    github_product_pain: bool = False,
    pain_keywords: list[str] | None = None,
    config: dict | None = None,
    quality_filter: bool = True,
) -> list[dict]:
    keywords = keywords or []
    exclude_keywords = exclude_keywords or []
    pain_keywords = pain_keywords or []

    out = []
    seen: set[str] = set()
    for post in posts:
        key = f"{post['source']}:{post.get('object_id', post.get('permalink', ''))}"
        if key in seen:
            continue
        seen.add(key)
        if post["ups"] < min_score:
            continue
        if not post["title"].strip():
            continue
        if matches_exclude(post, exclude_keywords):
            continue
        if source and post.get("source") != source:
            continue
        if config and quality_filter and should_drop_quality(post, config):
            continue
        if github_product_pain and looks_like_framework_bug_issue(post):
            if not matches_keywords(post, pain_keywords):
                continue
        elif github_product_pain and pain_keywords:
            if not matches_keywords(post, pain_keywords):
                continue
        elif keywords and not matches_keywords(post, keywords):
            continue
        out.append(post)
    out.sort(key=lambda p: p["ups"], reverse=True)
    return out


def filter_posts_legacy(
    posts: list[dict],
    *,
    min_score: int,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict]:
    """v0.4 behavior without quality layer — for before/after eval."""
    return filter_posts(
        posts,
        min_score=min_score,
        keywords=keywords,
        exclude_keywords=exclude_keywords,
        config=None,
        quality_filter=False,
    )


def load_dotenv(path: pathlib.Path) -> None:
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


def source_enabled(entry: dict) -> bool:
    return entry.get("enabled", True) is not False


def limits(config: dict) -> tuple[int, int]:
    fetch_limit = int(config.get("limit_per_source", 50))
    top_n = int(config.get("top_per_source", TOP_PER_SOURCE))
    return fetch_limit, top_n


def created_after_iso(date_range: str) -> str | None:
    import datetime

    seconds = DATE_RANGE_SECONDS.get(date_range)
    if seconds is None:
        return None
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get_json(
    url: str,
    *,
    headers: dict | None = None,
    timeout: int = 30,
) -> dict | list:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


def http_post_json(
    url: str,
    payload: dict,
    *,
    headers: dict | None = None,
    timeout: int = 30,
) -> dict:
    data = json.dumps(payload).encode()
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


def merge_posts(merged: list[dict], new_posts: list[dict]) -> None:
    seen = {f"{p['source']}:{p.get('object_id', p.get('permalink', ''))}" for p in merged}
    for post in new_posts:
        key = f"{post['source']}:{post.get('object_id', post.get('permalink', ''))}"
        if key not in seen:
            seen.add(key)
            merged.append(post)
