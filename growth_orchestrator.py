#!/usr/bin/env python3
"""
DemandRadar Growth Orchestrator — 一条命令跑到人工 Review 前

无需 Cursor Agent：用 Claude API 生成 G0–G4 judgment，再调用 helpers 拼装。

用法:
  export ANTHROPIC_API_KEY=your-key
  pip install anthropic

  python3 growth_orchestrator.py run --product-url https://www.yibelin.com/
  python3 growth_orchestrator.py run --product-url https://example.com \\
      --cookies configs/zhihu.cookies.json --max-answers 6 --open-review

完成后:
  - runs/<growth_id>/g4_zhihu_answers.json
  - runs/<growth_id>/answers_for_review.md
  - 人工: python3 review_dashboard.py --growth-id <growth_id>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / ".claude/skills"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def _require_anthropic():
    if not ANTHROPIC_API_KEY:
        print("❌ 请设置 ANTHROPIC_API_KEY")
        print("   export ANTHROPIC_API_KEY=your-key")
        print("   pip install anthropic")
        sys.exit(1)
    try:
        import anthropic  # noqa: F401
    except ImportError:
        print("❌ 请安装: pip install anthropic")
        sys.exit(1)


def load_skill(skill_dir: str) -> str:
    path = SKILLS / skill_dir / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text(encoding="utf-8")


def extract_json(text: str) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError("无法从模型响应中解析 JSON")


class GrowthOrchestrator:
    def __init__(
        self,
        growth_id: str,
        cookies_path: str = "configs/zhihu.cookies.json",
        max_answers: int = 6,
        model: str = ANTHROPIC_MODEL,
    ):
        self.growth_id = growth_id
        self.run_dir = ROOT / "runs" / growth_id
        self.judgments_dir = self.run_dir / "_judgments"
        self.cookies_path = cookies_path
        self.max_answers = max_answers
        self.model = model
        _require_anthropic()
        import anthropic

        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def _call_claude(self, system: str, user: str, max_tokens: int = 8192) -> str:
        print("  🤖 调用 Claude API...")
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    def _call_claude_json(self, system: str, user: str, max_tokens: int = 8192) -> Any:
        text = self._call_claude(system, user, max_tokens)
        try:
            return extract_json(text)
        except ValueError as e:
            print("  ⚠️ JSON 解析失败，重试一次...")
            text = self._call_claude(
                system + "\n\n你必须只输出合法 JSON，不要 markdown 代码块。",
                user + "\n\n请只输出 JSON。",
                max_tokens,
            )
            return extract_json(text)

    def _run(self, cmd: List[str], label: str) -> None:
        print(f"  → {label}")
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.rstrip())
        if result.returncode != 0:
            if result.stderr:
                print(result.stderr.rstrip())
            raise RuntimeError(f"{label} 失败 (exit {result.returncode})")

    def _write_judgment(self, stage: str, data: Any) -> Path:
        self.judgments_dir.mkdir(parents=True, exist_ok=True)
        path = self.judgments_dir / f"{stage}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ 已写入 {path.relative_to(ROOT)}")
        return path

    def _read_json(self, rel: str) -> Any:
        path = self.run_dir / rel
        return json.loads(path.read_text(encoding="utf-8"))

    def setup_dirs(self):
        (self.run_dir / "_raw").mkdir(parents=True, exist_ok=True)
        self.judgments_dir.mkdir(parents=True, exist_ok=True)

    def fetch_product_page(self, url: str) -> str:
        print(f"  抓取产品页: {url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        body = soup.get_text("\n", strip=True)
        return f"URL: {url}\nTitle: {title}\n\n{body[:12000]}"

    def run_g0(self, product_url: Optional[str], description: Optional[str]) -> None:
        print("\n📌 G0 — 产品锚定")
        skill = load_skill("product-focus")
        if product_url:
            page_text = self.fetch_product_page(product_url)
            user = f"产品官网:\n{product_url}\n\n页面内容摘要:\n{page_text}\n\n请输出 g0.json 完整 JSON。"
            product_input_flag = ["--product-url", product_url]
        elif description:
            user = f"产品描述:\n{description}\n\n请输出 g0.json 完整 JSON。"
            product_input_flag = ["--description", description]
        else:
            raise ValueError("需要 --product-url 或 --description")

        system = (
            f"{skill}\n\n"
            "你是自动化流水线的一部分。严格按 skill 输出 JSON 对象，"
            "包含 product_info 与 scan_config。target_keywords 至少 10 个中文词。"
            "只输出 JSON，不要 markdown。"
        )
        g0 = self._call_claude_json(system, user)
        self._write_judgment("g0", g0)
        self._run(
            [sys.executable, "helpers/build_product_context.py", self.growth_id] + product_input_flag,
            "build_product_context.py",
        )

    def run_fetch(self, skip_fetch: bool) -> None:
        raw_path = self.run_dir / "_raw" / "raw_zhihu_questions.json"
        if skip_fetch and raw_path.exists():
            print("\n🔍 G1 抓取 — 跳过（已有 raw 数据）")
            return
        print("\n🔍 G1 — 知乎抓取")
        cmd = [
            sys.executable,
            "helpers/fetch_zhihu.py",
            self.growth_id,
            "--cookies",
            str(ROOT / self.cookies_path),
        ]
        self._run(cmd, "fetch_zhihu.py")

    def run_g1(self) -> None:
        print("\n📡 G1 — 需求信号过滤")
        raw = self._read_json("_raw/raw_zhihu_questions.json")
        product = self._read_json("product_context.json")
        questions = raw.get("questions", [])
        compact = [
            {
                "question_id": q["question_id"],
                "title": q.get("title", ""),
                "detail": (q.get("detail") or "")[:300],
                "url": q.get("url", ""),
            }
            for q in questions
        ]
        skill = load_skill("demand-radar")
        system = (
            f"{skill}\n\n"
            "输出 _judgments/g1.json 格式：filtered_signals 数组（仅 intent_detected=true 的条目），"
            "以及 filtering_summary。每条含 question_id, platform, intent_type, relevance_score, "
            "commercial_intent, keywords_matched, reasoning。只输出 JSON。"
        )
        user = (
            f"产品信息:\n{json.dumps(product['product_info'], ensure_ascii=False, indent=2)}\n\n"
            f"共 {len(compact)} 条知乎问题，请过滤出与产品相关的需求信号:\n"
            f"{json.dumps(compact, ensure_ascii=False)}"
        )
        g1 = self._call_claude_json(system, user, max_tokens=16384)
        self._write_judgment("g1", g1)
        self._run(
            [sys.executable, "helpers/build_demand_signals.py", self.growth_id],
            "build_demand_signals.py",
        )

    def run_g2(self) -> None:
        print("\n📊 G2 — 需求聚类")
        signals = self._read_json("g1_demand_signals.json")
        skill = load_skill("demand-cluster")
        compact_signals = [
            {
                "question_id": s.get("platform_id") or s["signal_id"].replace("zhihu_q_", ""),
                "title": s.get("title", ""),
                "intent_type": s.get("intent_type"),
                "relevance_score": s.get("relevance_score"),
                "commercial_intent": s.get("commercial_intent"),
            }
            for s in signals.get("signals", [])
        ]
        system = (
            f"{skill}\n\n"
            "输出 g2.json：clusters 数组 + clustering_summary。"
            "每个 cluster 含 cluster_id, label, description, question_ids, demand_score, "
            "score_breakdown, keywords, trend。3–8 个 cluster。只输出 JSON。"
        )
        user = f"需求信号 ({len(compact_signals)} 条):\n{json.dumps(compact_signals, ensure_ascii=False)}"
        g2 = self._call_claude_json(system, user, max_tokens=16384)
        self._write_judgment("g2", g2)
        self._run(
            [sys.executable, "helpers/build_demand_clusters.py", self.growth_id],
            "build_demand_clusters.py",
        )

    def run_g3(self) -> None:
        print("\n🎯 G3 — 增长机会")
        clusters = self._read_json("g2_demand_clusters.json")
        product = self._read_json("product_context.json")
        skill = load_skill("growth-opportunity")
        system = (
            f"{skill}\n\n"
            "输出 g3.json：zhihu_opportunities 数组 + summary（含 top_priority）。"
            "每个 cluster 选 top 1–3 个问题，含 opportunity_score, signals, why_answer。"
            "可含 seo_opportunities。只输出 JSON。"
        )
        user = (
            f"产品:\n{json.dumps(product['product_info'], ensure_ascii=False, indent=2)}\n\n"
            f"需求簇:\n{json.dumps(clusters['clusters'], ensure_ascii=False)}"
        )
        g3 = self._call_claude_json(system, user, max_tokens=16384)
        self._write_judgment("g3", g3)
        self._run(
            [sys.executable, "helpers/build_growth_opportunities.py", self.growth_id],
            "build_growth_opportunities.py",
        )

    def run_g4(self) -> None:
        print("\n✍️ G4 — 知乎回答草稿")
        opps = self._read_json("g3_growth_opportunities.json")
        product = self._read_json("product_context.json")
        skill = load_skill("zhihu-answer-writer")

        targets: List[Dict] = []
        for opp in opps.get("zhihu_opportunities", []):
            for q in opp.get("top_questions", []):
                targets.append(
                    {
                        "question_id": q["question_id"],
                        "title": q.get("title", ""),
                        "url": q.get("url", ""),
                        "cluster_id": opp.get("cluster_id"),
                        "opportunity_score": q.get("opportunity_score", 0),
                        "why_answer": q.get("why_answer", ""),
                    }
                )
        targets.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        targets = targets[:self.max_answers]

        system = (
            f"{skill}\n\n"
            f"为下列 {len(targets)} 个知乎问题各写一篇回答草稿。"
            "输出 g4.json：{{ \"answers\": [...], \"notes\": \"...\" }}。"
            "每条含 question_id, cluster_id, opportunity_score, generated_answer "
            "(text 300–800字, word_count, tone, product_mention, products_mentioned), "
            "metadata.publish_recommendation。客观对比多款工具，译比邻可突出版式保留。"
            "只输出 JSON。"
        )
        user = (
            f"产品:\n{json.dumps(product['product_info'], ensure_ascii=False, indent=2)}\n\n"
            f"待回答问题:\n{json.dumps(targets, ensure_ascii=False, indent=2)}"
        )
        g4 = self._call_claude_json(system, user, max_tokens=16384)
        self._write_judgment("g4", g4)
        self._run(
            [sys.executable, "helpers/build_zhihu_answers.py", self.growth_id],
            "build_zhihu_answers.py",
        )

    def write_review_md(self) -> Path:
        data = self._read_json("g4_zhihu_answers.json")
        lines = [
            f"# {data.get('product_title', '产品')} · 知乎回答草稿 Review\n",
            f"**Run**: `{data['growth_id']}`  \n",
            f"**共 {data['metadata']['total_answers']} 篇草稿**\n\n---\n",
        ]
        for i, a in enumerate(data.get("zhihu_answers", []), 1):
            pr = a.get("metadata", {}).get("publish_recommendation", {})
            lines.append(f"## {i}. {a['question_title']}\n")
            lines.append(f"- **链接**: {a['question_url']}\n")
            lines.append(f"- **Cluster**: {a['cluster_id']}\n")
            lines.append(
                f"- **优先级**: {pr.get('priority', 'medium')} | "
                f"**建议发布**: {pr.get('should_publish', True)}\n\n"
            )
            lines.append(a["generated_answer"]["text"] + "\n\n---\n")
        out = self.run_dir / "answers_for_review.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n📄 Review 文档: {out.relative_to(ROOT)}")
        return out

    def run_full(
        self,
        product_url: Optional[str],
        description: Optional[str],
        skip_fetch: bool,
        open_review: bool,
        review_port: int,
    ) -> None:
        print(f"\n{'=' * 60}")
        print(f"🚀 DemandRadar 全自动: {self.growth_id}")
        print(f"{'=' * 60}")

        cookie_file = ROOT / self.cookies_path
        if not cookie_file.exists():
            print(f"❌ Cookie 文件不存在: {cookie_file}")
            print("   请先导出 configs/zhihu.cookies.json（见 zhihu-cookie-export skill）")
            sys.exit(1)

        self.setup_dirs()
        self.run_g0(product_url, description)
        self.run_fetch(skip_fetch)
        self.run_g1()
        self.run_g2()
        self.run_g3()
        self.run_g4()
        self.write_review_md()

        print(f"\n{'=' * 60}")
        print("✅ 全自动流水线完成 — 请人工 Review 后发布")
        print(f"   JSON: runs/{self.growth_id}/g4_zhihu_answers.json")
        print(f"   Markdown: runs/{self.growth_id}/answers_for_review.md")
        cmd = f"python3 review_dashboard.py --growth-id {self.growth_id} --port {review_port}"
        print(f"   Dashboard: {cmd}")
        print(f"{'=' * 60}\n")

        if open_review:
            webbrowser.open(f"http://127.0.0.1:{review_port}")
            subprocess.Popen(
                [sys.executable, "review_dashboard.py", "--growth-id", self.growth_id, "--port", str(review_port)],
                cwd=ROOT,
            )


def new_growth_id() -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    base = f"growth_zhihu_{date}"
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    n = 1
    while (runs / f"{base}_{n:03d}").exists():
        n += 1
    return f"{base}_{n:03d}"


def main():
    parser = argparse.ArgumentParser(description="DemandRadar 全自动编排（到人工 Review 前）")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="从产品 URL 跑到 G4 草稿")
    run_p.add_argument("--product-url", help="产品官网 URL")
    run_p.add_argument("--description", help="手动产品描述（无 URL 时）")
    run_p.add_argument("--growth-id", help="Growth run ID（默认自动生成）")
    run_p.add_argument(
        "--cookies",
        default="configs/zhihu.cookies.json",
        help="知乎 Cookie 文件路径",
    )
    run_p.add_argument("--max-answers", type=int, default=6, help="G4 最多生成几篇回答")
    run_p.add_argument("--skip-fetch", action="store_true", help="跳过知乎抓取（使用已有 raw）")
    run_p.add_argument("--open-review", action="store_true", help="完成后自动打开 Review Dashboard")
    run_p.add_argument("--review-port", type=int, default=8081)
    run_p.add_argument("--model", default=ANTHROPIC_MODEL, help="Claude 模型")

    args = parser.parse_args()
    if args.command != "run":
        parser.print_help()
        sys.exit(0)

    if not args.product_url and not args.description:
        print("❌ 需要 --product-url 或 --description")
        sys.exit(1)

    growth_id = args.growth_id or new_growth_id()
    orch = GrowthOrchestrator(
        growth_id=growth_id,
        cookies_path=args.cookies,
        max_answers=args.max_answers,
        model=args.model,
    )
    try:
        orch.run_full(
            product_url=args.product_url,
            description=args.description,
            skip_fetch=args.skip_fetch,
            open_review=args.open_review,
            review_port=args.review_port,
        )
    except Exception as e:
        print(f"\n❌ 流水线失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
