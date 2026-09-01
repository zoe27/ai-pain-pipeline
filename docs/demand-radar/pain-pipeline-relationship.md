# DemandRadar 与 Pain Pipeline 的关系

## 1. 两条流水线，一个引擎

```
┌─────────────────────────────────────────────────────────────────┐
│                     共享 Radar 引擎层                              │
│  多源抓取 · 聚类 · 外部信号 enrich · Agent judgment + Helper 拼装  │
└────────────────────────────┬────────────────────────────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           ↓                                   ↓
   Discovery Mode                        Growth Mode
   (Pain Pipeline)                       (DemandRadar)
           │                                   │
   Stage 0–9                             Growth Stage G0–G4
   痛点 → 机会 → PRD → 产品               产品 → demand → 内容 → 流量
```

**Pain Pipeline**：发现机会 → 做产品（Stage 0–9）  
**DemandRadar**：已有产品 → 捕获 demand → 生成内容 → 获流量 → 反馈闭环

---

## 2. 信号类型差异（最关键）

同一条 Reddit 帖子，两种模式读出不同含义：

| 帖子 | Pain Pipeline 读法 | DemandRadar 读法 |
|------|-------------------|------------------|
| "QuickBooks pricing is insane" | 定价痛点 → 做替代品 | （通常跳过，非 intent） |
| "Anyone know a good PDF to Excel tool?" | 可能标为 generic ask | **高 intent** → SEO 页 + 社区回复 |
| "Best free OCR for invoices?" | 商业痛点候选 | **Invoice OCR cluster** → `/invoice-ocr` 页面 |

| 维度 | Pain | Intent |
|------|------|--------|
| 典型句式 | "X sucks" · "frustrated with" · "why is it so hard" | "best tool for" · "anyone know" · "how to" · "alternative to" |
| 商业价值 | 发现市场空白、新产品 | 捕获已有产品的获客机会 |
| 评分框架 | ICE · opportunity_score | Demand Score |

---

## 3. Stage 映射

### Pain Pipeline（已实现 / 规划中）

| Stage | 名称 | 产出 |
|-------|------|------|
| 0 | 领域定向 | `domain_context.json` |
| 1 | 痛点雷达 | `1_pain_points.json` |
| 2 | ICE 评分 | `2_scored_pain_points.json` |
| 3 | 用户研究 | `3_opportunity.json` |
| 4–9 | PRD → 运营 | `4_prd.json` … `9_growth_metrics.json` |

### DemandRadar（Growth Stage，待实现）

| Growth Stage | 名称 | 类比 Pain Stage | 产出（规划） |
|--------------|------|-------------------|--------------|
| **G0** | 产品锚定 | Stage 0 | `product_context.json` |
| **G1** | Demand 发现 | Stage 1（intent 模式） | `g1_demand_signals.json` |
| **G2** | Demand 聚类 + 评分 | Stage 1 聚类 + Stage 2 | `g2_demand_clusters.json` |
| **G3** | 增长机会包 | Stage 3 | `g3_growth_opportunities.json` |
| **G4** | 内容草稿 | （新） | `g4_content_drafts.json` |

Growth Stage 使用独立 `growth_id`（格式待定，如 `growth_YYYY-MM-DD_NNN`），与 `pipe_*` 并行，可关联同一产品的 pipeline run。

---

## 4. 组件复用矩阵

| 组件 | Pain | Demand | 复用方式 |
|------|------|--------|----------|
| `fetch_radar.py` / `fetch_reddit.py` 等 | ✅ | ✅ | 改 keywords + intent 过滤 prompt |
| `compute_pain_clusters.py` | ✅ | 🔄 | 改为 intent cluster；schema 不同 |
| `market_signals_enrich.py` (Trends) | ✅ | ✅ | Search volume 权重加大 |
| Stage 0 `domain-focus` | ✅ | 🔄 | 改为 G0 `product-focus`（URL 输入） |
| ICE / opportunity_score | ✅ | ❌ | 改用 Demand Score |
| `build_prd.py` 等 Stage 4–9 | ✅ | ❌ | Growth 走 G4 内容草稿 |
| orchestrator + dashboard | ✅ | 🔄 | 新增 Growth Mode 分支 |
| JSON Schema + helper 拼装模式 | ✅ | ✅ | 新 contracts + helpers |

图例：✅ 直接复用 · 🔄 改 prompt/schema · ❌ 新建

---

## 5. 输入锚点差异

### Pain Pipeline — Stage 0

```yaml
domain: "developer tools / CI-CD"
target_user: "indie dev, small startup"
hypothesis: "CI wait time is a paid problem"
known_competitors: ["CircleCI", "GitHub Actions"]
search_keywords: [ci, pipeline, slow build]
```

模式：**broad scan** 或 **领域窄播**，找「还没做的产品」。

### DemandRadar — G0 产品锚定

```yaml
product_url: "https://example.com"
product_description: "AI PDF processing SaaS"
core_capabilities: [pdf-to-excel, ocr, batch-processing]
target_keywords: [pdf converter, pdf ocr, pdf api]
competitors: [Adobe Acrobat, Smallpdf, ILovePDF]
scan_sources: [reddit, hackernews, google_autocomplete]  # MVP 子集
```

模式：**产品锚定扫描**，只找「与已有产品相关的 demand」。

---

## 6. 生命周期衔接

```
Pain Pipeline                          DemandRadar
─────────────                          ───────────
Stage 0–3  发现机会
     ↓ GO
Stage 4–8  做产品 → 上线
     ↓
Stage 9    运营复盘（DAU/ARR/渠道 ROAS）  ← 事后、周期性
     │
     └──────────────────────────────────→  G0 启动持续 demand 扫描
                                          ↓
                                    G1–G4 执行增长
                                          ↓
                                    Outcome Feedback
                                          ↓
                                    反哺 G2 Demand Score
```

Stage 9 的 `growth_recommendations` 是 **复盘**；DemandRadar 是 **持续扫描 + 可执行**。两者互补，不是替代。

---

## 7. 运行目录结构（规划）

```
runs/
├── pipe_YYYY-MM-DD_NNN/          # Pain Pipeline（已有）
│   ├── domain_context.json
│   ├── 1_pain_points.json
│   └── ...
│
└── growth_YYYY-MM-DD_NNN/        # DemandRadar（新增）
    ├── product_context.json      # G0
    ├── g1_demand_signals.json    # G1
    ├── g2_demand_clusters.json   # G2
    ├── g3_growth_opportunities.json  # G3
    ├── g4_content_drafts.json    # G4
    ├── _raw/                     # 原始抓取
    └── _judgments/               # Agent 判断
```

可选：`product_context.json` 中 `linked_pipeline_id` 字段关联 Pain Pipeline 的 `pipe_*` run。

---

## 8. 设计原则（继承自 Pain Pipeline）

1. **结构化优先于智能** — 每阶段 JSON Schema + helper 校验
2. **判断与拼装分离** — Agent 写 `_judgments/`，helper 做确定性拼装
3. **每片可独立运行** — G0–G4 可单独跑
4. **从轻到重** — MVP 是 Markdown + JSON，不是全自动发布
5. **人审核关键动作** — 社区回复、页面发布必须 Approve
