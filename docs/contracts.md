# 数据契约（每阶段输入/输出）

> 关键原则：所有阶段输入/输出都是 **结构化 JSON**。AI 可以读自由文本，但**必须输出符合 schema 的 JSON**，否则视为失败。

## 阶段 1：痛点雷达

**输入：** `RadarConfig`
```yaml
sources:                           # 数据源列表
  - type: reddit
    subreddits: [SaaS, Entrepreneur, Indiehackers]
    min_upvotes: 10
  - type: hackernews
    keywords: [pain, struggle, broken]
  - type: github_issues
    repos: ["popular/repo1"]
    labels: [bug, enhancement]
  - type: producthunt
    categories: [productivity, dev-tools]
filters:
  language: en
  date_range: last_7_days
limit_per_source: 100
```

**输出：** `PainPoint[]`
```yaml
- id: uuid
  source: reddit
  source_url: https://...
  title: "Why is X so hard to do?"
  raw_content: "..."
  signals:
    upvotes: 152
    comments_count: 47
    sentiment: negative
  extracted_keywords: ["onboarding", "saas", "auth"]
  extracted_at: 2026-05-20T10:00:00Z
```

---

## 阶段 2：机会评估

**输入：** `PainPoint[]`

**输出：** `ScoredPainPoint[]`
```yaml
- pain_point_id: uuid
  ice_score:
    impact: 8       # 1-10
    confidence: 7   # 1-10
    ease: 5         # 1-10
    total: 280      # I × C × E
  market_signals:
    google_trends_score: 75
    competitor_count: 3
    estimated_market_size_usd: 50000000
  ai_reasoning: "理由说明 200 字以内"
  red_flags: ["竞争激烈", "需要监管牌照"]
  green_flags: ["搜索趋势上升", "无强势开源方案"]
```

---

## 阶段 3：用户研究

**输入：** `ScoredPainPoint`（单个，已被排序选中候选）

**输出：** `Opportunity`
```yaml
pain_point_id: uuid
target_personas:
  - name: "独立开发者"
    pain_intensity: 9        # 1-10
    willingness_to_pay: 7    # 1-10
    persona_size_estimate: 100000
    quotes: ["真实用户原话1", "原话2"]
existing_solutions:
  - name: "竞品 A"
    pricing: "$29/mo"
    weaknesses: ["UX 差", "缺 X 功能"]
  - name: "竞品 B"
market_size:
  tam_usd: 50000000
  sam_usd: 5000000
  som_usd: 500000
recommendation: build | validate | skip | partner
confidence: high | medium | low
confidence_basis:
  source_count: 2
  product_count: 2
  cross_run: true
  switch_intent_present: true
  wtp_signal_present: true
  rationale: "为什么是这个置信度"
evidence_ledger:
  - claim: "核心结论"
    strength: high | medium | low
    evidence:
      - source: app_store
        product: "QuickBooks"
        pain_point_id: uuid
        quote: "真实用户原话"
    assumptions: ["仍需验证的假设"]
unsupported_assumptions:
  - "本轮数据没有直接证明的关键假设"
validation_required:
  - experiment: "下一步验证实验"
    success_criterion: "成功标准"
    priority: high | medium | low
commercial_assessment:          # V2 商业判断（可选，由 build_opportunity 自动算 opportunity_score）
  pain_score: 1-10
  frequency_score: 1-10
  switching_willingness: 1-10   # 10 = 主动找替代
  switching_cost:
    score: 1-10
    data_migration / learning_curve / team_collaboration / ecosystem_lock_in / sunk_cost: 1-10
    rationale: "迁移成本说明"
  workaround_analysis:
    current_workarounds: ["用户已在用的替代方案"]
    quality_score: 1-10         # 10 = 替代方案已足够好（对新产品是坏事）
    cost_to_user: low | medium | high
    satisfaction: 1-10
    rationale: "替代方案分析"
  buyer_mapping:
    user / beneficiary / buyer / champion: "角色描述"
    buyer_exists_score: 1-10
  persistence:
    root_cause_type: structural_permanent | platform_bug | regulatory | unknown
    owner: incumbent | platform | market | none
    score: 1-10
    rationale: "痛点是否持久"
  economic_impact:
    roi_score: 1-10
    time_loss / revenue_at_risk / cashflow_impact: none | low | medium | high
    quantification_notes: "量化说明"
  competition_score: 1-10       # 10 = 竞争极度激烈
opportunity_score:              # 由 build_opportunity.py 自动计算，勿手写
  total: 1440
  tier: high | medium | low | watch
  formula: "Pain × Frequency × ROI × SwitchingWill × Buyer × Persistence ÷ Competition ÷ WorkaroundQuality"
```

`validate` 用于“痛点强但证据结构还不足以直接 build”的机会。单一来源/单一产品主导的结论，应通过 `confidence_basis` 和 `evidence_ledger` 明确标注证据边界。

**Opportunity Score 分级**：high ≥ 2000 · medium ≥ 500 · low ≥ 100 · watch < 100。`recommendation` 应与 tier 大致对齐（helper 会 WARN 不一致）。

---

## 🚦 决策点 ①：GO / NO-GO

**输入：** `Opportunity[]`（一批候选）
**人输出：** `SelectedOpportunity`
```yaml
chosen_pain_point_id: uuid
human_notes: "我决定做这个，原因..."
decided_at: 2026-05-20T15:00:00Z
decided_by: "user_id"
```

---

## 阶段 4：PRD

**输入：** `SelectedOpportunity`

**输出：** `PRD`
```yaml
opportunity_id: uuid
product_name: "..."
one_liner: "用一句话说清楚"
target_users: [...]
core_features:
  - id: f1
    name: "..."
    priority: must | should | could
    user_story: "As a... I want... so that..."
    acceptance_criteria:
      - "Given... When... Then..."
non_goals:
  - "明确不做的事"
mvp_scope:
  in: [f1, f2]
  out: [f3, f4]
success_metrics:
  - "30 天内 100 个付费用户"
  - "MRR 达到 $1000"
```

---

## 阶段 5：架构设计

**输入：** `PRD`

**输出：** `TechSpec`
```yaml
prd_id: uuid
tech_stack:
  frontend: "Next.js 15"
  backend: "Python FastAPI"
  database: "PostgreSQL + Redis"
  hosting: "Vercel + Railway"
  auth: "Clerk"
  payments: "Stripe"
data_model:
  entities:
    - name: User
      fields: [...]
    - name: Project
api_endpoints:
  - method: POST
    path: /api/projects
    request_schema: {...}
    response_schema: {...}
infrastructure:
  estimated_monthly_cost_usd: 50
  scaling_plan: "..."
risks:
  - risk: "..."
    mitigation: "..."
```

---

## 🚦 决策点 ②：方案审批

**输入：** `PRD + TechSpec`
**人输出：** `ApprovedSpec`
```yaml
prd_id: uuid
status: approved | revise
revision_notes: "如 status=revise，写改什么"
approved_at: 2026-05-21T10:00:00Z
```

---

## 阶段 6：编码 + TDD

**输入：** `ApprovedSpec`

**输出：** `BuildArtifact`
```yaml
spec_id: uuid
git_repo_url: "..."
branch: feature/mvp-v1
tasks_completed:
  - task_id: t1
    description: "..."
    pr_url: "..."
    tests_added: 12
test_summary:
  total: 87
  passed: 87
  coverage_percent: 78
```

---

## 阶段 7：测试 + 自审

**输入：** `BuildArtifact`

**输出：** `ReviewedPR`
```yaml
artifact_id: uuid
pr_url: "..."
reviews:
  - reviewer: "ai/code-reviewer"
    issues:
      - severity: critical | high | medium | low
        file: "src/auth.py:45"
        description: "..."
        suggested_fix: "..."
  - reviewer: "ai/security-engineer"
    issues: [...]
auto_fix_applied: true
ready_for_human: true
```

---

## 🚦 决策点 ③：上线放行

**输入：** `ReviewedPR`
**人输出：** `DeploymentApproval`
```yaml
pr_id: uuid
status: approved | reject | needs_changes
deployment_target: production | staging | canary
approved_at: 2026-05-22T10:00:00Z
```

---

## 阶段 8：部署 + 监控

**输入：** `DeploymentApproval`

**输出：** `Deployment`
```yaml
pr_id: uuid
deployed_url: "https://..."
deployed_at: 2026-05-22T11:00:00Z
monitoring_setup:
  sentry_dsn: "..."
  posthog_project_id: "..."
  uptime_monitor: "..."
health_check_passed: true
```

---

## 阶段 9：运营 + 商业化

**输入：** `Deployment`

**输出：** `GrowthMetrics`
```yaml
deployment_id: uuid
period: 2026-05-22 ~ 2026-05-29
metrics:
  signups: 145
  activations: 87
  paid_users: 12
  mrr_usd: 348
  churn_rate: 0.05
campaigns_running:
  - channel: producthunt
    status: live
    cost_usd: 0
    conversions: 23
  - channel: google_ads
    spend_usd: 200
    conversions: 8
```

---

## 🚦 决策点 ④：商业策略

**输入：** `GrowthMetrics`
**人输出：** `StrategyDecision`
```yaml
deployment_id: uuid
decisions:
  pricing_change: null | "..."
  feature_priority: [...]
  channel_focus: producthunt | seo | ads
next_review_at: 2026-06-22
```

---

## 通用字段（每个对象都有）

```yaml
_meta:
  pipeline_run_id: uuid     # 整条流水线的运行 ID
  stage_name: string        # 哪个阶段产出
  generated_at: datetime
  generated_by: string      # AI agent 名字
  cost_usd: float          # 这一步消耗的 token 成本
  model_used: string       # claude-opus-4-7 / claude-sonnet-4-6 / etc.
```
