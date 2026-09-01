# DemandRadar MVP 路线图

## 1. 分阶段策略

ChatGPT 原始建议：**第一版不要做大**。本路线图遵循同一原则。

```
Phase 1 (MVP)     Reddit/论坛 demand 发现 + AI 分析 + SEO Opportunity
Phase 2           Community Reply Copilot（审核后发布）
Phase 3           Programmatic SEO Engine（模板 → 生成 → 监控）
```

---

## 2. Phase 1 — MVP（本分支目标）

### 2.1 范围

**做：**

- G0 产品锚定（输入产品 URL / 描述 → `product_context.json`）
- G1 Demand 发现（Reddit + HN，**intent 模式**）
- G2 聚类 + Demand Score
- G3 SEO Opportunity 列表（「你应该做这 N 个页面，以及为什么」）
- Demand Map digest（`.digest.md`）

**不做：**

- Google Search 全量接入（Phase 1 可用 Trends / autocomplete 轻量替代）
- 社区回复自动生成（Phase 2）
- 页面自动发布 / Programmatic SEO（Phase 3）
- Outcome Feedback 闭环（Phase 3+，需 traffic 数据）

### 2.2 MVP 用户故事

```
作为已有 PDF SaaS 的创始人，
我输入产品 URL，
系统告诉我与产品相关的 top 50 demand clusters，
每个 cluster 给出 SEO 页面建议和 Demand Score，
以便我决定优先做哪些落地页。
```

### 2.3 MVP 输出示例

`g3_growth_opportunities.json` 片段：

```json
{
  "growth_id": "growth_2026-09-01_001",
  "product_title": "AI PDF SaaS",
  "demand_map": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel",
      "demand_score": 94,
      "signals": {
        "community_frequency": "high",
        "commercial_intent": "high",
        "competition": "medium",
        "trend": "up"
      },
      "seo_opportunities": [
        {
          "slug": "/pdf-to-excel",
          "type": "converter_landing",
          "title_suggestion": "PDF to Excel Converter — Free Online",
          "rationale": "47 Reddit threads in 90 days asking for PDF to Excel tools"
        },
        {
          "slug": "/guides/how-to-convert-pdf-to-excel",
          "type": "how_to",
          "title_suggestion": "How to Convert PDF to Excel (2026 Guide)",
          "rationale": "Long-tail search intent + tutorial gap vs competitors"
        }
      ]
    }
  ],
  "summary": {
    "total_clusters": 12,
    "seo_opportunities": 37,
    "community_opportunities": 0,
    "top_priority": ["pdf-to-excel", "invoice-ocr", "pdf-api"]
  }
}
```

### 2.4 MVP 技术任务清单

| # | 任务 | 依赖 | 状态 |
|---|------|------|------|
| D1 | 需求文档 | — | ✅ |
| D2 | `contracts/product_context.schema.json` | D1 | ⬜ |
| D3 | `contracts/demand_cluster.schema.json` | D1 | ⬜ |
| D4 | `contracts/growth_opportunities.schema.json` | D1 | ⬜ |
| D5 | `.claude/skills/product-focus/SKILL.md` (G0) | D2 | ⬜ |
| D6 | `.claude/skills/demand-radar/SKILL.md` (G1) | D2 | ⬜ |
| D7 | `configs/radar.intent.example.yaml` | D6 | ⬜ |
| D8 | Intent 过滤 prompt / 句式库 | D6 | ⬜ |
| D9 | `helpers/build_product_context.py` | D2, D5 | ⬜ |
| D10 | `helpers/build_demand_batch.py` (G1 拼装) | D3, D6 | ⬜ |
| D11 | `helpers/build_demand_clusters.py` (G2) | D3 | ⬜ |
| D12 | `helpers/build_growth_opportunities.py` (G3) | D4 | ⬜ |
| D13 | `helpers/digest.py` 扩展 Growth 阶段 | D12 | ⬜ |
| D14 | `docs/contracts.md` 补充 Growth Stage | D2–D4 | ⬜ |
| D15 | 示例 run `runs/growth_*` + walkthrough | D12 | ⬜ |

### 2.5 MVP 运行命令（目标态）

```bash
GROWTH=growth_$(date +%Y-%m-%d)_001
mkdir -p runs/$GROWTH/_raw runs/$GROWTH/_judgments

# G0 — 产品锚定（Agent: product-focus skill）
# → 写 runs/$GROWTH/_judgments/g0.json
python3 helpers/build_product_context.py $GROWTH

# G1 — Demand 发现（Agent: demand-radar skill）
python3 helpers/fetch_radar.py $GROWTH --config configs/radar.intent.example.yaml
# → 写 runs/$GROWTH/_judgments/g1.json
python3 helpers/build_demand_batch.py $GROWTH

# G2 — 聚类 + Demand Score
# → 写 runs/$GROWTH/_judgments/g2.json
python3 helpers/build_demand_clusters.py $GROWTH

# G3 — SEO Opportunity
# → 写 runs/$GROWTH/_judgments/g3.json
python3 helpers/build_growth_opportunities.py $GROWTH
python3 helpers/digest.py runs/$GROWTH/g3_growth_opportunities.json
```

---

## 3. Phase 2 — Community Reply Copilot

```
发现帖子 → 判断相关度 → 判断商业意图 → 生成回复草稿 → 人工 Approve → 发布
```

新增：

- `g4_content_drafts.json` 中 `community_replies[]`
- 相关度 + 商业意图评分
- 审核 UI（可扩展 `decision_dashboard.py`）

**仍不做** 自动发布。

---

## 4. Phase 3 — Programmatic SEO

```
Demand → Keyword Cluster → Page Template → Generate → Internal Linking → Publish → Monitor
```

新增：

- 页面模板引擎
- 内链图（Intent Graph 可视化）
- Outcome Feedback：page → visits → signups → 反哺 Demand Score

产品从 **「发现机会」** 升级为 **「执行增长」**。

---

## 5. Demand Score vs ICE / opportunity_score

| 维度 | ICE (Pain) | opportunity_score (Pain) | Demand Score (Growth) |
|------|------------|--------------------------|------------------------|
| 目的 | 值不值得做产品 | 商业机会综合分 | 值不值得做 SEO/内容 |
| Impact 类比 | 痛点强度 | pain_score | search + community volume |
| Ease 类比 | 实现难度 | — | content effort / competition |
| 关键差异 | 面向 0→1 | 付费意愿、竞争 | 搜索意图、排名机会、转化路径 |

Demand Score 公式（初版，待 benchmark 校准）：

```
Demand Score = w1·normalized_search_interest
             + w2·community_frequency
             + w3·commercial_intent
             + w4·trend_slope
             − w5·competition_index
```

权重可通过 G0 `product_context.json` 中的 `score_weights` 调整（类比 Stage 0 的 `ice_priority`）。

---

## 6. 成功标准（Phase 1）

| 指标 | 目标 |
|------|------|
| 输入 | 1 个真实 SaaS 产品 URL |
| 输出 | ≥10 个 demand clusters，≥30 条 SEO opportunities |
| 质量 | 人工抽检 top 10：≥7 条「确实值得做页面」 |
| 工程 | G0–G3 可独立跑通；schema 校验通过 |
| 文档 | walkthrough + 示例 run |

---

## 7. 开放问题

| # | 问题 | 倾向 |
|---|------|------|
| 1 | `growth_id` vs 复用 `pipe_id`？ | 独立 `growth_*`，可选 `linked_pipeline_id` |
| 2 | G1 是否复用 `pain_point.schema.json`？ | 新建 `demand_signal.schema.json`，避免 pain/intent 混淆 |
| 3 | Google Search 数据从哪来？ | MVP: Trends + autocomplete；后期: Search Console API |
| 4 | 与 Stage 9 合并还是独立？ | 独立 Growth Mode；Stage 9 可消费 Outcome Feedback |
| 5 | 独立产品 vs repo 内模式？ | 先在 repo 内 Growth Mode 验证，再考虑 fork |
