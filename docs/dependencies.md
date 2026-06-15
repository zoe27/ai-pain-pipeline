# 依赖清单：每阶段用什么 Skill / 工具 / API

> **当前实现（v0.4）** 见下表「已实现」；本文后半部分的 Postgres / agency-agents / Dashboard 等为**目标架构**，尚未落地。

## 已实现：本仓库 Skill + Helper（v0.4）

| 阶段 | Skill | 关键 Helper | 产出 |
|------|-------|-------------|------|
| 0 领域定向（可选） | [`domain-focus`](../.claude/skills/domain-focus/SKILL.md) | `build_domain_context.py`, `merge_radar_config.py` | `domain_context.json` |
| 1 痛点雷达 | [`pain-radar`](../.claude/skills/pain-radar/SKILL.md) | `fetch_radar.py`, `build_pain_batch.py`, `compute_pain_clusters.py`, `enrich_external_signals.py` | `1_pain_points.json` |
| 2 ICE 评分 | [`score-pain`](../.claude/skills/score-pain/SKILL.md) | `build_scored_batch.py`, `market_signals_enrich.py`, `build_commercial_prefill.py` | `2_scored_pain_points.json` |
| 3 用户研究 + 商业判断 | [`user-research`](../.claude/skills/user-research/SKILL.md) | `build_opportunity.py`, `digest.py`, `build_i18n.py` | `3_opportunity.json` |

**数据源（已实现 fetcher）**：HN · Product Hunt · Reddit · GitHub Issues · App Store 1–2★ RSS。G2/Capterra 暂缓（#6）。

**契约**：[`docs/contracts.md`](contracts.md) · JSON Schema 在 [`contracts/`](../contracts/)。

---

## 全局基础设施（目标架构，贯穿所有阶段）

| 类别 | 工具 | 用途 |
|------|------|------|
| **行为护栏** | `andrej-karpathy-skills` | 4 条原则全局启用 |
| **流程框架** | `obra/superpowers` | brainstorming / TDD / 子 Agent 派发 |
| **跨会话记忆** | `rohitg00/agentmemory` | Pipeline 状态 + 上下文持久化 |
| **上下文优化** | `colbymchenry/codegraph` + `rtk-ai/rtk` | 降低 token 消耗 60-90% |
| **生产级原则** | `humanlayer/12-factor-agents` | 配置外部化、可观测性、错误处理 |
| **Agent 平台** | Claude Code（Opus 4.7） | 主开发环境 |
| **可选辅助** | `tinyhumansai/openhuman` | 桌面级私人助理（接 Slack/Email） |

---

## 阶段 1：痛点雷达

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **本仓库 Skill** | `pain-radar` | Agent 写 `stage1.json` |
| **抓取脚本** | `fetch_radar.py` + `fetch_*.py` | 多源合并 → `_raw/top50.json` |
| **数据源 API** | HN Algolia、Product Hunt GraphQL、Reddit OAuth、GitHub REST、App Store RSS | PH/Reddit 需 `.env` |
| **后处理** | `compute_pain_clusters.py`, `enrich_external_signals.py` | `build_pain_batch.py` 自动调用 |
| **存储（当前）** | `runs/{pid}/1_pain_points.json` | 目标：PostgreSQL |
| **调度（目标）** | GitHub Actions cron | #15 待实现 |

---

## 阶段 2：机会评估

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **本仓库 Skill** | `score-pain` | ICE 评分 + 假痛点过滤 |
| **辅助数据** | Google Trends（`market_signals_enrich.py`）、HN 48h 评论增速、`pain_clusters` | confidence 自动加成 |
| **商业预填** | `build_commercial_prefill.py` | Stage 3 Agent 锚点 |
| **存储（当前）** | `runs/{pid}/2_scored_pain_points.json` | |

---

## 阶段 3：用户研究 + 商业判断

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **本仓库 Skill** | `user-research` | 含 V2 `commercial_assessment` |
| **数据源** | Stage 1 原文 + `commercial_prefill` + `external_signals` | quotes / 切换意愿 / 持续性 |
| **自动评分** | `build_opportunity.py` | `opportunity_score` + tier WARN |
| **输出** | `3_opportunity.json` + digest EN/ZH | 决策点 ① 输入 |

---

## 🚦 决策点 ①：人工 UI

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **当前实现** | 人读 `3_opportunity.digest.md` / `.zh.md` | 结合 `opportunity_score` + `recommendation` 拍板 |
| **通知（目标）** | Slack Bot + Email | 等你审 |
| **Web Dashboard（目标）** | Next.js + shadcn/ui | 简单的 GO/NO-GO 按钮 |
| **审批存储（目标）** | PostgreSQL `decisions` 表 | 审计 trail |

---

## 阶段 4：PRD 撰写（目标占位 · #16）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/product/product-manager` | PRD 模板 |
| **方法论** | `github/spec-kit` | 规格驱动 |
| **流程 Skill** | `superpowers/brainstorming` + `superpowers/writing-plans` | |
| **LLM 模型** | claude-opus-4-7（最复杂、最重要的产出） | |
| **存储** | Notion / Confluence / 本地 Markdown | 可读性优先 |

---

## 阶段 5：架构设计（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/engineering/software-architect` + `engineering/backend-architect` + `engineering/frontend-developer` | 多角色并行 |
| **流程 Skill** | `superpowers/dispatching-parallel-agents` | 并行评估方案 |
| **可视化** | Mermaid（架构图）+ Excalidraw | |
| **LLM 模型** | claude-opus-4-7 | |

---

## 🚦 决策点 ②：人工 UI（目标占位）

同决策点 ①，外加：
- 显示 PRD diff（如果是修改后的版本）
- 显示成本估算（前一阶段消耗 + 后续预估）

---

## 阶段 6：编码 + TDD（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/engineering/senior-developer` + `engineering/code-reviewer`（自审） | |
| **流程 Skill** | `superpowers/test-driven-development` + `superpowers/subagent-driven-development` + `superpowers/using-git-worktrees` | |
| **行为护栏** | `karpathy-skills/karpathy-guidelines` | 必须启用 |
| **代码上下文** | `colbymchenry/codegraph` | 减少 token |
| **执行环境** | Claude Code（本地）或 GitHub Actions（云端） | |
| **版本控制** | Git + GitHub | |
| **LLM 模型** | claude-opus-4-7（关键代码） + claude-haiku-4-5（脚手架） | |

---

## 阶段 7：测试 + 自审（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/engineering/code-reviewer` + `engineering/security-engineer` + `testing/qa-engineer` | 多视角审查 |
| **流程 Skill** | `superpowers/requesting-code-review` + `superpowers/verification-before-completion` | |
| **测试工具** | pytest / vitest / playwright（按技术栈） | |
| **自动 lint** | ruff / eslint / prettier | |
| **安全扫描** | Bandit / Snyk / GitHub CodeQL | |
| **LLM 模型** | claude-sonnet-4-6（多次 review 用） | |

---

## 🚦 决策点 ③：人工 UI（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **PR 平台** | GitHub PR | 标准 review 流程 |
| **测试报告** | 自动 comment 到 PR | |
| **预览环境** | Vercel Preview / Railway Preview | 可视化验证 |

---

## 阶段 8：部署 + 监控（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/engineering/devops-automator` + `engineering/sre` | |
| **托管平台** | Vercel（前端）+ Railway / Fly.io（后端） | 简单优先 |
| **数据库** | Neon / Supabase / Railway Postgres | |
| **监控** | Sentry（错误）+ PostHog（产品）+ Better Uptime（可用性） | |
| **CI/CD** | GitHub Actions | |
| **域名 / DNS** | Cloudflare | |
| **LLM 模型** | claude-haiku-4-5（部署脚本，不用太聪明） | |

---

## 阶段 9：运营 + 商业化（目标占位）

| 资源类型 | 选择 | 备注 |
|---------|------|------|
| **AI 角色** | `agency-agents/marketing/copywriter` + `marketing/seo-specialist` + `paid-media/google-ads-specialist` + `sales/cro-optimizer` | |
| **支付** | Stripe / Lemon Squeezy | |
| **邮件营销** | Resend / Loops | |
| **分析** | PostHog + Plausible | |
| **客服** | Crisp / Intercom（可选） | |
| **社交媒体自动化** | Buffer API / Twitter API | |
| **LLM 模型** | claude-sonnet-4-6（文案）+ claude-haiku-4-5（自动化任务） | |

---

## 🚦 决策点 ④：人工 UI（目标占位）

显示：
- 月度营收 / 增长曲线
- 渠道效果对比
- AI 建议的 3 个候选策略

---

## 模型路由策略（成本 vs 质量）

```yaml
# 不要全用 Opus！按任务难度分配模型
model_routing:
  # 高质量必须（决策影响大）
  opus_4_7:
    - 阶段 4 PRD 撰写
    - 阶段 5 架构设计
    - 阶段 6 关键代码（核心业务逻辑）
  
  # 中等质量（推理 + 评估）
  sonnet_4_6:
    - 阶段 2 机会评估
    - 阶段 3 用户研究
    - 阶段 7 代码审查
    - 阶段 9 营销文案
  
  # 大批量任务（分类 + 提取）
  haiku_4_5:
    - 阶段 1 痛点抓取后初筛
    - 阶段 6 脚手架代码生成
    - 阶段 8 部署脚本
    - 阶段 9 自动化任务
```

## 第三方 API 总清单

```yaml
data_sources:
  implemented:
    - hackernews_algolia_api
    - producthunt_graphql_api
    - reddit_api
    - github_rest_api
    - app_store_rss
    - google_trends_api          # Stage 2 enrich
  deferred:
    - g2_capterra                # #6
    - similarweb_api
    - twitter_api

llm_providers:
  - anthropic_api  # Claude 模型
  - openai_api      # 备用 / 嵌入

infrastructure:
  - vercel_api
  - railway_api
  - cloudflare_api
  - github_api
  - stripe_api

monitoring:
  - sentry_api
  - posthog_api
  - better_uptime_api

communication:
  - slack_webhook
  - resend_api (邮件)
  - twitter_api (营销)
```

## 估算成本（Pipeline 跑一遍）

```yaml
# 假设第一个产品从痛点到上线
estimated_cost_per_product_usd:
  llm_tokens:
    阶段 1-3: $5    # 大量 Haiku
    阶段 4-5: $15   # Opus 高密度推理
    阶段 6-7: $50   # Opus 编码 + Sonnet review
    阶段 8-9: $5    # Haiku
    总计: $75
  
  infrastructure_monthly:
    hosting: $20
    db: $10
    monitoring: $0  # 免费额度
    总计: $30 / 月
  
  third_party_api_monthly:
    google_trends: $0
    similarweb: $0
    total: $0
  
  人工时间:
    决策点 ①: 30 分钟
    决策点 ②: 1 小时
    决策点 ③: 1 小时
    决策点 ④: 1 小时/月
```
