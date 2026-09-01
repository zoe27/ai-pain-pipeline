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
- G1 Demand 发现（**知乎单一渠道**，**intent 模式**）
- G2 聚类 + Demand Score
- G3 增长机会列表（知乎回答机会 + SEO 页面建议）
- G4 知乎回答草稿生成（包含原问题链接、问题内容、生成的回答）
- Demand Map digest（`.digest.md`）

**不做：**

- Reddit/HN 等海外渠道（Phase 2）
- Google Search 全量接入（Phase 2）
- 知乎自动发布（Phase 2，MVP 只生成草稿）
- 页面自动发布 / Programmatic SEO（Phase 3）
- Outcome Feedback 闭环（Phase 3+，需 traffic 数据）

### 2.2 MVP 用户故事

```
作为已有 PDF SaaS 的创始人，
我输入产品 URL 或描述，
系统扫描知乎相关问题（如「有哪些好用的 PDF 转换工具？」），
告诉我 top 20 个最值得回答的问题，
每个问题给出：
  - 问题热度和商业价值评分
  - AI 生成的回答草稿
  - 原问题链接
以便我快速复制粘贴到知乎获取流量。
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

`g4_content_drafts.json` 中的知乎回答示例：

```json
{
  "zhihu_answers": [
    {
      "answer_id": "ans_001",
      "cluster_id": "pdf-to-excel",
      "platform": "zhihu",
      "source": {
        "url": "https://www.zhihu.com/question/123456789",
        "question_id": "123456789",
        "title": "有哪些好用的 PDF 转 Excel 工具？",
        "author": "知乎用户",
        "created_at": "2026-08-25T10:00:00Z",
        "follower_count": 847,
        "answer_count": 23,
        "view_count": 12400,
        "question_detail": "工作中经常需要把 PDF 表格转成 Excel，手动复制太麻烦，有什么好工具推荐吗？最好能保留格式..."
      },
      "generated_answer": {
        "text": "推荐几个我用过的工具：\n\n1. **[你的产品]**\n优点：AI 识别准确率高，特别是复杂表格...\n\n2. Adobe Acrobat（付费）\n3. Smallpdf（免费额度有限）\n\n如果是批量处理，建议用...",
        "tone": "professional",
        "mentions_product": true,
        "product_position": "first",
        "word_count": 420
      },
      "opportunity_score": 87,
      "signals": {
        "relevance": 95,
        "commercial_intent": "high",
        "competition_level": "medium",
        "freshness": "recent",
        "engagement": "high"
      },
      "publish_status": "pending",
      "published_at": null,
      "published_url": null
    }
  ]
}
```

### 2.4 MVP 技术任务清单

| # | 任务 | 依赖 | 状态 |
|---|------|------|------|
| D1 | 需求文档（知乎版） | — | ✅ |
| D2 | `contracts/product_context.schema.json` | D1 | ⬜ |
| D3 | `contracts/zhihu_signal.schema.json` | D1 | ⬜ |
| D4 | `contracts/zhihu_answer_draft.schema.json` | D1 | ⬜ |
| D5 | `contracts/growth_opportunities.schema.json` | D1 | ⬜ |
| D6 | `.claude/skills/product-focus/SKILL.md` (G0) | D2 | ⬜ |
| D7 | `.claude/skills/zhihu-demand-radar/SKILL.md` (G1) | D2 | ⬜ |
| D8 | `configs/radar.zhihu.example.yaml` | D7 | ⬜ |
| D9 | 知乎 Intent 过滤 prompt / 句式库 | D7 | ⬜ |
| D10 | `helpers/fetch_zhihu.py` (爬取知乎问题) | D3 | ⬜ |
| D11 | `helpers/build_product_context.py` | D2, D6 | ⬜ |
| D12 | `helpers/build_zhihu_signals.py` (G1 拼装) | D3, D7 | ⬜ |
| D13 | `helpers/build_demand_clusters.py` (G2 聚类) | D3 | ⬜ |
| D14 | `helpers/build_zhihu_answers.py` (G4 生成回答) | D4 | ⬜ |
| D15 | `helpers/build_growth_opportunities.py` (G3) | D5 | ⬜ |
| D16 | `helpers/digest.py` 扩展 Growth 阶段 | D15 | ⬜ |
| D17 | `docs/contracts.md` 补充 Growth Stage | D2–D5 | ⬜ |
| D18 | 示例 run `runs/growth_zhihu_*` + walkthrough | D16 | ⬜ |

### 2.5 MVP 运行命令（目标态）

```bash
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001
mkdir -p runs/$GROWTH/_raw runs/$GROWTH/_judgments

# G0 — 产品锚定（Agent: product-focus skill）
# 输入：产品 URL 或描述
# → 写 runs/$GROWTH/_judgments/g0.json
python3 helpers/build_product_context.py $GROWTH

# G1 — 知乎 Demand 发现（Agent: zhihu-demand-radar skill）
# 爬取知乎相关问题
python3 helpers/fetch_zhihu.py $GROWTH --config configs/radar.zhihu.example.yaml
# Agent 判断哪些是真实 intent
# → 写 runs/$GROWTH/_judgments/g1.json
python3 helpers/build_zhihu_signals.py $GROWTH

# G2 — 聚类 + Demand Score
# → 写 runs/$GROWTH/_judgments/g2.json
python3 helpers/build_demand_clusters.py $GROWTH

# G3 — 增长机会总结
# → 写 runs/$GROWTH/g3_growth_opportunities.json
python3 helpers/build_growth_opportunities.py $GROWTH

# G4 — 知乎回答草稿生成
# → 写 runs/$GROWTH/g4_zhihu_answers.json
python3 helpers/build_zhihu_answers.py $GROWTH

# Digest
python3 helpers/digest.py runs/$GROWTH/g4_zhihu_answers.json
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
