"""Generate human-readable digest of any pipeline stage output.

Usage:
    python3 helpers/digest.py runs/pipe_xxx/2_scored_pain_points.json
    python3 helpers/digest.py runs/pipe_xxx/1_pain_points.json

Outputs:
    - Prints digest to stdout
    - Writes <input>.digest.md alongside the input file
"""
import json, sys, pathlib
from collections import Counter

def digest_stage1(data: dict) -> str:
    out = []
    out.append(f"# Stage 1 — Pain Radar 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Generated**: {data['generated_at']}  ")
    out.append(f"**Count**: {data['count']} 条 PainPoint\n")

    # sentiment
    sent = Counter(p["signals"]["sentiment"] for p in data["pain_points"])
    out.append("## Sentiment 分布\n")
    for s in ["negative", "positive", "neutral", "mixed"]:
        out.append(f"- **{s}**: {sent.get(s, 0)} 条")
    out.append("")

    # source breakdown
    src = Counter(p.get("source", "unknown") for p in data["pain_points"])
    out.append("## 数据源分布\n")
    for s, c in src.most_common():
        out.append(f"- **{s}**: {c}")
    out.append("")

    # top by upvotes
    out.append("## Top 10 by upvotes\n")
    out.append("| ups | comments | sentiment | title |")
    out.append("|----:|---------:|:---------:|-------|")
    for p in sorted(data["pain_points"], key=lambda x: -x["signals"]["upvotes"])[:10]:
        title = p["title"][:70].replace("|", "\\|")
        out.append(f"| {p['signals']['upvotes']} | {p['signals']['comments_count']} | {p['signals']['sentiment']} | {title} |")
    out.append("")

    # all keywords
    kws = Counter(k for p in data["pain_points"] for k in p["extracted_keywords"])
    out.append("## 关键词频次 (>= 2)\n")
    for k, c in kws.most_common():
        if c < 2: break
        out.append(f"- `{k}`: {c}")
    return "\n".join(out)


def digest_stage2(data: dict) -> str:
    out = []
    out.append(f"# Stage 2 — Score Pain 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Scored at**: {data['scored_at']}  ")
    out.append(f"**Input**: `{data['input_file']}`  ")
    out.append(f"**Count**: {data['count']} 条\n")

    scored = sorted(data["scored"], key=lambda s: -s["ice_score"]["total"])

    # buckets
    high = [s for s in scored if s["ice_score"]["total"] >= 200]
    mid = [s for s in scored if 100 <= s["ice_score"]["total"] < 200]
    low = [s for s in scored if s["ice_score"]["total"] < 100]
    out.append("## 评分分布\n")
    out.append(f"- 🟢 **值得认真考虑** (total ≥ 200): **{len(high)} 条**")
    out.append(f"- 🟡 **观察名单** (100 ≤ total < 200): {len(mid)} 条")
    out.append(f"- ⚪ **基本可丢弃** (total < 100): {len(low)} 条\n")

    # top tier with full detail
    out.append(f"## 🟢 值得认真考虑 ({len(high)} 条)\n")
    for i, s in enumerate(high, 1):
        ice = s["ice_score"]
        out.append(f"### {i}. {s['title']}\n")
        out.append(f"**ICE**: I={ice['impact']} × C={ice['confidence']} × E={ice['ease']} = **{ice['total']}**\n")
        out.append(f"**理由**: {s['ai_reasoning']}\n")
        if s["red_flags"]:
            out.append("**Red flags**: " + " · ".join(f"`{r}`" for r in s["red_flags"]))
        out.append("")

    # mid tier with one-line
    out.append(f"## 🟡 观察名单 ({len(mid)} 条)\n")
    out.append("| total | I·C·E | title | red flags |")
    out.append("|------:|:------|-------|-----------|")
    for s in mid:
        ice = s["ice_score"]
        title = s["title"][:55].replace("|", "\\|")
        rf = ", ".join(s["red_flags"][:2]).replace("|", "\\|")
        out.append(f"| {ice['total']} | {ice['impact']}·{ice['confidence']}·{ice['ease']} | {title} | {rf} |")
    out.append("")

    # low tier — just count by red flag
    out.append(f"## ⚪ 基本可丢弃 ({len(low)} 条)\n")
    rf_counts = Counter(r for s in low for r in s["red_flags"])
    out.append("被压低的主要原因(top red flags):\n")
    for r, c in rf_counts.most_common(10):
        out.append(f"- `{r}`: {c}")
    out.append("")

    # red flag summary across all
    out.append("## 全部 Red flags 频次 (>= 2)\n")
    all_rf = Counter(r for s in scored for r in s["red_flags"])
    for r, c in all_rf.most_common():
        if c < 2: break
        out.append(f"- `{r}`: {c}")
    return "\n".join(out)


def digest_stage3(data: dict) -> str:
    out = []
    out.append(f"# Stage 3 — User Research 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Researched**: {data['researched_at']}  ")
    out.append(f"**Recommendation**: **{data['recommendation'].upper()}** (confidence: {data['confidence']})\n")
    out.append(f"## {data['title']}\n")
    out.append(f"> {data['one_liner']}\n")

    ms = data["market_size"]
    out.append("## 市场规模\n")
    out.append(f"- **TAM**: ${ms['tam_usd']:,}")
    out.append(f"- **SAM**: ${ms['sam_usd']:,}")
    out.append(f"- **SOM** (realistic Y1): ${ms['som_usd']:,}\n")

    out.append("## 目标用户\n")
    for p in data["target_personas"]:
        out.append(f"### {p['name']}\n")
        out.append(f"Pain {p['pain_intensity']}/10 · WTP {p['willingness_to_pay']}/10 · ~{p['persona_size_estimate']:,} people\n")
        for q in p["quotes"]:
            out.append(f"- \"{q}\"")
        out.append("")

    out.append("## 现有方案 & 弱点\n")
    out.append("| 方案 | 定价 | 主要弱点 |")
    out.append("|------|------|----------|")
    for s in data["existing_solutions"]:
        weak = " · ".join(s["weaknesses"][:2]).replace("|", "\\|")
        out.append(f"| {s['name']} | {s['pricing']} | {weak} |")
    out.append("")

    out.append("## 产品假设\n")
    out.append(data["product_hypothesis"] + "\n")

    out.append("## 研究结论\n")
    out.append(data["research_notes"])
    return "\n".join(out)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 helpers/digest.py <stage_output.json>", file=sys.stderr)
        sys.exit(2)
    path = pathlib.Path(sys.argv[1]).resolve()
    data = json.loads(path.read_text())

    name = path.name
    if "1_pain_points" in name:
        md = digest_stage1(data)
    elif "2_scored_pain_points" in name:
        md = digest_stage2(data)
    elif "3_opportunity" in name:
        md = digest_stage3(data)
    else:
        print(f"unknown stage file: {name}", file=sys.stderr)
        sys.exit(2)

    out = path.with_suffix(".digest.md")
    out.write_text(md + "\n")
    print(md)
    print(f"\n→ wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
