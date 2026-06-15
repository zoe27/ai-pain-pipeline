"""Generate human-readable digest of any pipeline stage output.

Usage:
    python3 helpers/digest.py runs/pipe_xxx/2_scored_pain_points.json
    python3 helpers/digest.py runs/pipe_xxx/1_pain_points.json

Outputs:
    - Prints digest to stdout
    - Writes <input>.digest.md alongside the input file
    - If matching *.i18n.json exists, also writes <input>.digest.zh.md
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

SENTIMENT_ZH = {
    "negative": "负面/抱怨",
    "positive": "正面",
    "neutral": "中性",
    "mixed": "混合",
}

RECOMMENDATION_ZH = {
    "build": "建议做",
    "skip": "建议跳过",
    "partner": "建议合作",
    "validate": "建议验证",
}

CONFIDENCE_ZH = {"high": "高", "medium": "中", "low": "低"}

TIER_ZH = {"high": "高机会", "medium": "中等机会", "low": "低机会", "watch": "观察名单"}

ROOT_CAUSE_ZH = {
    "structural_permanent": "结构性永久问题",
    "platform_bug": "平台/版本问题",
    "regulatory": "监管/合规问题",
    "unknown": "未知",
}


def _i18n_path(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.stem + ".i18n.json")


def _load_i18n(path: pathlib.Path) -> dict | None:
    i18n = _i18n_path(path)
    if not i18n.is_file():
        return None
    return json.loads(i18n.read_text())


def digest_stage1(data: dict) -> str:
    out = []
    out.append("# Stage 1 — Pain Radar 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Generated**: {data['generated_at']}  ")
    out.append(f"**Count**: {data['count']} 条 PainPoint\n")

    sent = Counter(p["signals"]["sentiment"] for p in data["pain_points"])
    out.append("## Sentiment 分布\n")
    for s in ["negative", "positive", "neutral", "mixed"]:
        out.append(f"- **{s}**: {sent.get(s, 0)} 条")
    out.append("")

    src = Counter(p.get("source", "unknown") for p in data["pain_points"])
    out.append("## 数据源分布\n")
    for s, c in src.most_common():
        out.append(f"- **{s}**: {c}")
    out.append("")

    out.append("## Top 10 by upvotes\n")
    out.append("| ups | comments | sentiment | title |")
    out.append("|----:|---------:|:---------:|-------|")
    for p in sorted(data["pain_points"], key=lambda x: -x["signals"]["upvotes"])[:10]:
        title = p["title"][:70].replace("|", "\\|")
        out.append(
            f"| {p['signals']['upvotes']} | {p['signals']['comments_count']} "
            f"| {p['signals']['sentiment']} | {title} |"
        )
    out.append("")

    kws = Counter(k for p in data["pain_points"] for k in p["extracted_keywords"])
    out.append("## 关键词频次 (>= 2)\n")
    for k, c in kws.most_common():
        if c < 2:
            break
        out.append(f"- `{k}`: {c}")
    return "\n".join(out)


def digest_stage1_zh(data: dict, i18n: dict) -> str:
    by_id = {item["id"]: item for item in i18n["items"]}
    out = []
    out.append("# Stage 1 — 痛点雷达（中文版）\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**生成时间**: {data['generated_at']}  ")
    out.append(f"**条数**: {data['count']}\n")

    sent = Counter(p["signals"]["sentiment"] for p in data["pain_points"])
    out.append("## 情感分布\n")
    for s in ["negative", "positive", "neutral", "mixed"]:
        label = SENTIMENT_ZH.get(s, s)
        out.append(f"- **{label}**: {sent.get(s, 0)} 条")
    out.append("")

    src = Counter(p.get("source", "unknown") for p in data["pain_points"])
    out.append("## 数据源\n")
    for s, c in src.most_common():
        out.append(f"- **{s}**: {c} 条")
    out.append("")

    out.append("## 高互动 Top 10\n")
    out.append("| 赞 | 评论 | 情感 | 标题（中文） | 摘要 |")
    out.append("|---:|-----:|:----:|-------------|------|")
    for p in sorted(data["pain_points"], key=lambda x: -x["signals"]["upvotes"])[:10]:
        zh = by_id.get(p["id"], {})
        title = (zh.get("title_zh") or p["title"])[:40].replace("|", "\\|")
        summary = (zh.get("summary_zh") or "")[:60].replace("|", "\\|")
        sent = SENTIMENT_ZH.get(p["signals"]["sentiment"], p["signals"]["sentiment"])
        out.append(
            f"| {p['signals']['upvotes']} | {p['signals']['comments_count']} "
            f"| {sent} | {title} | {summary} |"
        )
    out.append("")

    out.append("## 全部条目（中文）\n")
    for i, p in enumerate(
        sorted(data["pain_points"], key=lambda x: -x["signals"]["upvotes"]), 1
    ):
        zh = by_id.get(p["id"], {})
        title = zh.get("title_zh") or p["title"]
        summary = zh.get("summary_zh") or ""
        kws = zh.get("keywords_zh") or p["extracted_keywords"]
        sent = SENTIMENT_ZH.get(p["signals"]["sentiment"], p["signals"]["sentiment"])
        out.append(f"### {i}. {title}\n")
        out.append(
            f"**情感**: {sent} · **赞/评**: {p['signals']['upvotes']}/"
            f"{p['signals']['comments_count']} · **来源**: {p.get('source', '?')}\n"
        )
        if summary:
            out.append(f"{summary}\n")
        out.append("**关键词**: " + " · ".join(f"`{k}`" for k in kws) + "\n")
    return "\n".join(out)


def digest_stage2(data: dict) -> str:
    out = []
    out.append("# Stage 2 — Score Pain 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Scored at**: {data['scored_at']}  ")
    out.append(f"**Input**: `{data['input_file']}`  ")
    out.append(f"**Count**: {data['count']} 条\n")

    scored = sorted(data["scored"], key=lambda s: -s["ice_score"]["total"])
    high = [s for s in scored if s["ice_score"]["total"] >= 200]
    mid = [s for s in scored if 100 <= s["ice_score"]["total"] < 200]
    low = [s for s in scored if s["ice_score"]["total"] < 100]
    out.append("## 评分分布\n")
    out.append(f"- 🟢 **值得认真考虑** (total ≥ 200): **{len(high)} 条**")
    out.append(f"- 🟡 **观察名单** (100 ≤ total < 200): {len(mid)} 条")
    out.append(f"- ⚪ **基本可丢弃** (total < 100): {len(low)} 条\n")

    echo = []
    seen_clusters: set[str] = set()
    for s in scored:
        ms = s.get("market_signals") or {}
        cid = ms.get("cluster_id")
        if not cid or cid in seen_clusters:
            continue
        size = ms.get("cluster_size") or 1
        if size >= 2:
            seen_clusters.add(cid)
            hints = ms.get("commercial_hints") or {}
            echo.append((cid, size, hints.get("persistence_hint", "?"), hints.get("single_source_echo", False)))
    if echo:
        out.append("## Pain clusters (V2 pre-screen)\n")
        out.append("| cluster | size | persistence hint | single-source echo |")
        out.append("|---------|-----:|------------------|--------------------|")
        for cid, size, ph, sse in sorted(echo, key=lambda x: -x[1]):
            out.append(f"| `{cid}` | {size} | {ph} | {sse} |")
        out.append("")

    out.append(f"## 🟢 值得认真考虑 ({len(high)} 条)\n")
    for i, s in enumerate(high, 1):
        ice = s["ice_score"]
        out.append(f"### {i}. {s['title']}\n")
        out.append(
            f"**ICE**: I={ice['impact']} × C={ice['confidence']} × E={ice['ease']} "
            f"= **{ice['total']}**\n"
        )
        out.append(f"**理由**: {s['ai_reasoning']}\n")
        if s["red_flags"]:
            out.append("**Red flags**: " + " · ".join(f"`{r}`" for r in s["red_flags"]))
        out.append("")

    out.append(f"## 🟡 观察名单 ({len(mid)} 条)\n")
    out.append("| total | I·C·E | title | red flags |")
    out.append("|------:|:------|-------|-----------|")
    for s in mid:
        ice = s["ice_score"]
        title = s["title"][:55].replace("|", "\\|")
        rf = ", ".join(s["red_flags"][:2]).replace("|", "\\|")
        out.append(
            f"| {ice['total']} | {ice['impact']}·{ice['confidence']}·{ice['ease']} "
            f"| {title} | {rf} |"
        )
    out.append("")

    out.append(f"## ⚪ 基本可丢弃 ({len(low)} 条)\n")
    rf_counts = Counter(r for s in low for r in s["red_flags"])
    out.append("被压低的主要原因(top red flags):\n")
    for r, c in rf_counts.most_common(10):
        out.append(f"- `{r}`: {c}")
    out.append("")

    out.append("## 全部 Red flags 频次 (>= 2)\n")
    all_rf = Counter(r for s in scored for r in s["red_flags"])
    for r, c in all_rf.most_common():
        if c < 2:
            break
        out.append(f"- `{r}`: {c}")
    return "\n".join(out)


def digest_stage2_zh(data: dict, i18n: dict) -> str:
    by_id = {item["pain_point_id"]: item for item in i18n["items"]}
    scored = sorted(data["scored"], key=lambda s: -s["ice_score"]["total"])
    high = [s for s in scored if s["ice_score"]["total"] >= 200]
    mid = [s for s in scored if 100 <= s["ice_score"]["total"] < 200]
    low = [s for s in scored if s["ice_score"]["total"] < 100]

    out = []
    out.append("# Stage 2 — ICE 评分（中文版）\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**评分时间**: {data['scored_at']}  ")
    out.append(f"**条数**: {data['count']}\n")

    out.append("## 分档\n")
    out.append(f"- 🟢 **值得认真考虑** (≥200): **{len(high)} 条**")
    out.append(f"- 🟡 **观察名单** (100–199): {len(mid)} 条")
    out.append(f"- ⚪ **基本可丢弃** (<100): {len(low)} 条\n")

    out.append(f"## 🟢 值得认真考虑 ({len(high)} 条)\n")
    for i, s in enumerate(high, 1):
        zh = by_id.get(s["pain_point_id"], {})
        title = zh.get("title_zh") or s["title"]
        ice = s["ice_score"]
        out.append(f"### {i}. {title}\n")
        out.append(
            f"**ICE**: 影响={ice['impact']} × 把握={ice['confidence']} × "
            f"易做={ice['ease']} = **{ice['total']}**\n"
        )
        reasoning = zh.get("ai_reasoning_zh") or s["ai_reasoning"]
        out.append(f"**评分理由**: {reasoning}\n")
        flags = zh.get("red_flags_zh") or s["red_flags"]
        if flags:
            out.append("**风险点**: " + " · ".join(f"`{r}`" for r in flags))
        out.append("")

    if mid:
        out.append(f"## 🟡 观察名单 ({len(mid)} 条)\n")
        out.append("| 总分 | 影响·把握·易做 | 标题（中文） | 风险 |")
        out.append("|-----:|:--------------|-------------|------|")
        for s in mid:
            zh = by_id.get(s["pain_point_id"], {})
            ice = s["ice_score"]
            title = (zh.get("title_zh") or s["title"])[:40].replace("|", "\\|")
            flags = zh.get("red_flags_zh") or s["red_flags"]
            rf = ", ".join(flags[:2]).replace("|", "\\|")
            out.append(
                f"| {ice['total']} | {ice['impact']}·{ice['confidence']}·{ice['ease']} "
                f"| {title} | {rf} |"
            )
        out.append("")

    if low:
        out.append(f"## ⚪ 基本可丢弃 ({len(low)} 条)\n")
        out.append("仅列标题，详情见英文版 digest。\n")
        for s in low[:15]:
            zh = by_id.get(s["pain_point_id"], {})
            title = (zh.get("title_zh") or s["title"])[:60]
            out.append(f"- [{s['ice_score']['total']}] {title}")
        if len(low) > 15:
            out.append(f"- … 另有 {len(low) - 15} 条")
    return "\n".join(out)


def _append_commercial_sections(out: list[str], data: dict) -> None:
    commercial = data.get("commercial_assessment")
    score = data.get("opportunity_score")
    if not commercial:
        return

    out.append("## Commercial Assessment (V2)\n")
    if score:
        out.append(
            f"**Opportunity Score**: **{score['total']}** ({score['tier']})  "
            f"· formula: {score.get('formula', '')}\n"
        )

    sc = commercial["switching_cost"]
    wa = commercial["workaround_analysis"]
    bm = commercial["buyer_mapping"]
    pe = commercial["persistence"]
    ec = commercial["economic_impact"]

    out.append("| Dimension | Score | Notes |")
    out.append("|-----------|------:|-------|")
    out.append(f"| Pain | {commercial['pain_score']}/10 | |")
    out.append(f"| Frequency | {commercial['frequency_score']}/10 | |")
    note = ec["quantification_notes"][:80].replace("|", "\\|")
    out.append(f"| ROI / Economic Impact | {ec['roi_score']}/10 | {note} |")
    out.append(
        f"| Switching willingness | {commercial['switching_willingness']}/10 | "
        f"cost={sc['score']}/10 |"
    )
    out.append(f"| Buyer exists | {bm['buyer_exists_score']}/10 | buyer: {bm['buyer']} |")
    out.append(
        f"| Persistence | {pe['score']}/10 | {pe['root_cause_type']} / {pe['owner']} |"
    )
    out.append(f"| Competition (÷) | {commercial['competition_score']}/10 | |")
    out.append(
        f"| Workaround quality (÷) | {wa['quality_score']}/10 | "
        f"satisfaction={wa['satisfaction']}/10 |"
    )
    out.append("")

    out.append("### Switching Cost Breakdown\n")
    out.append(
        f"Data migration {sc.get('data_migration', '?')} · "
        f"Learning {sc.get('learning_curve', '?')} · "
        f"Team {sc.get('team_collaboration', '?')} · "
        f"Ecosystem {sc.get('ecosystem_lock_in', '?')} · "
        f"Sunk cost {sc.get('sunk_cost', '?')}\n"
    )
    out.append(f"{sc['rationale']}\n")

    out.append("### Workarounds Users Already Use\n")
    for w in wa["current_workarounds"]:
        out.append(f"- {w}")
    out.append(f"\n{wa['rationale']}\n")

    out.append("### Buyer Mapping\n")
    out.append(f"- **User**: {bm['user']}")
    out.append(f"- **Beneficiary**: {bm['beneficiary']}")
    out.append(f"- **Buyer**: {bm['buyer']}")
    out.append(f"- **Champion**: {bm['champion']}\n")


def _append_commercial_sections_zh(out: list[str], data: dict, i18n: dict) -> None:
    commercial = data.get("commercial_assessment")
    score = data.get("opportunity_score")
    if not commercial:
        return

    ca_zh = i18n.get("commercial_assessment") or {}
    out.append("## 商业判断（V2）\n")
    if score:
        tier = TIER_ZH.get(score["tier"], score["tier"])
        out.append(f"**机会分数**: **{score['total']}**（{tier}）\n")

    sc = commercial["switching_cost"]
    wa = commercial["workaround_analysis"]
    bm = commercial["buyer_mapping"]
    pe = commercial["persistence"]
    ec = commercial["economic_impact"]
    sc_zh = ca_zh.get("switching_cost") or {}
    wa_zh = ca_zh.get("workaround_analysis") or {}
    bm_zh = ca_zh.get("buyer_mapping") or {}
    pe_zh = ca_zh.get("persistence") or {}
    ec_zh = ca_zh.get("economic_impact") or {}

    out.append("| 维度 | 分数 | 说明 |")
    out.append("|------|-----:|------|")
    out.append(f"| 痛点强度 | {commercial['pain_score']}/10 | |")
    out.append(f"| 频率 | {commercial['frequency_score']}/10 | |")
    roi_note = (ec_zh.get("quantification_notes_zh") or ec["quantification_notes"])[:60]
    out.append(f"| ROI / 经济影响 | {ec['roi_score']}/10 | {roi_note} |")
    out.append(
        f"| 迁移意愿 | {commercial['switching_willingness']}/10 | "
        f"迁移成本={sc['score']}/10 |"
    )
    buyer_label = bm_zh.get("buyer_zh") or bm["buyer"]
    out.append(f"| 付费主体存在 | {bm['buyer_exists_score']}/10 | 付款人：{buyer_label} |")
    rc = ROOT_CAUSE_ZH.get(pe["root_cause_type"], pe["root_cause_type"])
    out.append(f"| 持续性 | {pe['score']}/10 | {rc} |")
    out.append(f"| 竞争（除） | {commercial['competition_score']}/10 | |")
    out.append(f"| 替代方案质量（除） | {wa['quality_score']}/10 | |")
    out.append("")

    out.append("### 迁移成本\n")
    out.append(f"{sc_zh.get('rationale_zh') or sc['rationale']}\n")

    out.append("### 用户现有替代方案\n")
    workarounds = wa_zh.get("current_workarounds_zh") or wa["current_workarounds"]
    for w in workarounds:
        out.append(f"- {w}")
    out.append(f"\n{wa_zh.get('rationale_zh') or wa['rationale']}\n")

    out.append("### 付费主体映射\n")
    out.append(f"- **使用者**：{bm_zh.get('user_zh') or bm['user']}")
    out.append(f"- **受益者**：{bm_zh.get('beneficiary_zh') or bm['beneficiary']}")
    out.append(f"- **付款人**：{bm_zh.get('buyer_zh') or bm['buyer']}")
    out.append(f"- **推动者**：{bm_zh.get('champion_zh') or bm['champion']}\n")


def _append_stage3_audit_sections(out: list[str], data: dict) -> None:
    basis = data.get("confidence_basis")
    if basis:
        out.append("## Confidence Basis\n")
        out.append(
            f"- Sources: {basis['source_count']} · Products: {basis['product_count']} · "
            f"Cross-run: {basis['cross_run']}"
        )
        if "switch_intent_present" in basis:
            out.append(f"- Switch intent present: {basis['switch_intent_present']}")
        if "wtp_signal_present" in basis:
            out.append(f"- WTP signal present: {basis['wtp_signal_present']}")
        out.append(f"- Rationale: {basis['rationale']}\n")

    ledger = data.get("evidence_ledger") or []
    if ledger:
        out.append("## Evidence Ledger\n")
        for entry in ledger:
            out.append(f"### [{entry['strength']}] {entry['claim']}\n")
            for item in entry["evidence"]:
                product = f" · {item['product']}" if item.get("product") else ""
                out.append(f"- `{item['source']}`{product}: \"{item['quote']}\"")
            assumptions = entry.get("assumptions") or []
            if assumptions:
                out.append("")
                out.append("Assumptions:")
                for assumption in assumptions:
                    out.append(f"- {assumption}")
            out.append("")

    assumptions = data.get("unsupported_assumptions") or []
    if assumptions:
        out.append("## Unsupported Assumptions\n")
        for assumption in assumptions:
            out.append(f"- {assumption}")
        out.append("")

    validations = data.get("validation_required") or []
    if validations:
        out.append("## Validation Required\n")
        for i, item in enumerate(validations, 1):
            out.append(
                f"{i}. **[{item['priority']}] {item['experiment']}** — "
                f"{item['success_criterion']}"
            )
        out.append("")


def _append_stage3_audit_sections_zh(out: list[str], data: dict, i18n: dict) -> None:
    basis = data.get("confidence_basis")
    if basis:
        rationale = i18n.get("confidence_basis_rationale_zh") or basis["rationale"]
        out.append("## 置信度依据\n")
        out.append(
            f"- 来源数：{basis['source_count']} · 产品数：{basis['product_count']} · "
            f"跨 run：{basis['cross_run']}"
        )
        if "switch_intent_present" in basis:
            out.append(f"- 有明确切换意愿：{basis['switch_intent_present']}")
        if "wtp_signal_present" in basis:
            out.append(f"- 有付费/损失信号：{basis['wtp_signal_present']}")
        out.append(f"- 依据：{rationale}\n")

    ledger = data.get("evidence_ledger") or []
    ledger_zh = i18n.get("evidence_ledger") or []
    if ledger:
        out.append("## 证据账本\n")
        strength_zh = {"high": "强", "medium": "中", "low": "弱"}
        for idx, entry in enumerate(ledger):
            zh = ledger_zh[idx] if idx < len(ledger_zh) else {}
            claim = zh.get("claim_zh") or entry["claim"]
            out.append(f"### [{strength_zh.get(entry['strength'], entry['strength'])}] {claim}\n")
            for item in entry["evidence"]:
                product = f" · {item['product']}" if item.get("product") else ""
                out.append(f"- `{item['source']}`{product}: 「{item['quote']}」")
            assumptions = zh.get("assumptions_zh") or entry.get("assumptions") or []
            if assumptions:
                out.append("")
                out.append("仍需假设：")
                for assumption in assumptions:
                    out.append(f"- {assumption}")
            out.append("")

    assumptions = i18n.get("unsupported_assumptions_zh") or data.get("unsupported_assumptions") or []
    if assumptions:
        out.append("## 尚未验证的假设\n")
        for assumption in assumptions:
            out.append(f"- {assumption}")
        out.append("")

    validations = data.get("validation_required") or []
    validations_zh = i18n.get("validation_required") or []
    if validations:
        out.append("## 下一步验证\n")
        priority_zh = {"high": "高", "medium": "中", "low": "低"}
        for idx, item in enumerate(validations, 1):
            zh = validations_zh[idx - 1] if idx - 1 < len(validations_zh) else {}
            experiment = zh.get("experiment_zh") or item["experiment"]
            criterion = zh.get("success_criterion_zh") or item["success_criterion"]
            priority = priority_zh.get(item["priority"], item["priority"])
            out.append(f"{idx}. **[{priority}] {experiment}** — {criterion}")
        out.append("")


def digest_stage3(data: dict) -> str:
    out = []
    out.append("# Stage 3 — User Research 摘要\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**Researched**: {data['researched_at']}  ")
    out.append(
        f"**Recommendation**: **{data['recommendation'].upper()}** "
        f"(confidence: {data['confidence']})\n"
    )
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
        out.append(
            f"Pain {p['pain_intensity']}/10 · WTP {p['willingness_to_pay']}/10 · "
            f"~{p['persona_size_estimate']:,} people\n"
        )
        for q in p["quotes"]:
            out.append(f'- "{q}"')
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

    _append_commercial_sections(out, data)
    _append_stage3_audit_sections(out, data)

    out.append("## 研究结论\n")
    out.append(data["research_notes"])
    return "\n".join(out)


def digest_stage3_zh(data: dict, i18n: dict) -> str:
    out = []
    rec = RECOMMENDATION_ZH.get(data["recommendation"], data["recommendation"])
    conf = CONFIDENCE_ZH.get(data["confidence"], data["confidence"])
    out.append("# Stage 3 — 用户研究（中文版）\n")
    out.append(f"**Pipeline**: `{data['pipeline_id']}`  ")
    out.append(f"**研究时间**: {data['researched_at']}  ")
    out.append(f"**建议**: **{i18n.get('recommendation_zh', rec)}**（置信度：{i18n.get('confidence_zh', conf)}）\n")
    out.append(f"## {i18n['title_zh']}\n")
    out.append(f"> {i18n['one_liner_zh']}\n")

    ms = data["market_size"]
    out.append("## 市场规模（美元）\n")
    out.append(f"- **TAM（总市场）**: ${ms['tam_usd']:,}")
    out.append(f"- **SAM（可服务市场）**: ${ms['sam_usd']:,}")
    out.append(f"- **SOM（首年现实目标）**: ${ms['som_usd']:,}\n")

    out.append("## 目标用户\n")
    for p, p_zh in zip(data["target_personas"], i18n["target_personas"]):
        out.append(f"### {p_zh['name_zh']}\n")
        out.append(
            f"痛点强度 {p['pain_intensity']}/10 · 付费意愿 {p['willingness_to_pay']}/10 · "
            f"约 {p['persona_size_estimate']:,} 人\n"
        )
        for q in p_zh.get("quotes_zh") or p["quotes"]:
            out.append(f"- 「{q}」")
        out.append("")

    out.append("## 现有方案与弱点\n")
    out.append("| 方案 | 定价 | 主要弱点 |")
    out.append("|------|------|----------|")
    for s, s_zh in zip(data["existing_solutions"], i18n["existing_solutions"]):
        weak = " · ".join(s_zh.get("weaknesses_zh") or s["weaknesses"][:2]).replace("|", "\\|")
        out.append(f"| {s_zh['name_zh']} | {s['pricing']} | {weak} |")
    out.append("")

    out.append("## 产品假设\n")
    out.append(i18n["product_hypothesis_zh"] + "\n")

    _append_commercial_sections_zh(out, data, i18n)
    _append_stage3_audit_sections_zh(out, data, i18n)

    out.append("## 研究结论\n")
    out.append(i18n["research_notes_zh"])
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 helpers/digest.py <stage_output.json>", file=sys.stderr)
        sys.exit(2)
    path = pathlib.Path(sys.argv[1]).resolve()
    data = json.loads(path.read_text())
    i18n = _load_i18n(path)

    name = path.name
    if "1_pain_points" in name:
        md = digest_stage1(data)
        md_zh = digest_stage1_zh(data, i18n) if i18n else None
    elif "2_scored_pain_points" in name:
        md = digest_stage2(data)
        md_zh = digest_stage2_zh(data, i18n) if i18n else None
    elif "3_opportunity" in name:
        md = digest_stage3(data)
        md_zh = digest_stage3_zh(data, i18n) if i18n else None
    else:
        print(f"unknown stage file: {name}", file=sys.stderr)
        sys.exit(2)

    out = path.with_suffix(".digest.md")
    out.write_text(md + "\n")
    print(md)

    written = [out]
    if md_zh:
        out_zh = path.with_name(path.stem + ".digest.zh.md")
        out_zh.write_text(md_zh + "\n")
        written.append(out_zh)

    print("\n→ wrote " + ", ".join(str(p) for p in written), file=sys.stderr)
    if not md_zh:
        print(
            "→ 无中文版：先写 _judgments/stageN_i18n.json 并运行 build_i18n.py",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
