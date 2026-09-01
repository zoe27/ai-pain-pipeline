# AI Pain Pipeline

> v0.4 · 2026-06 · 从市场痛点到产品机会的 AI 驱动流水线

一条由 **AI Agent 执行 + 人类在关键节点拍板** 的流水线，把公开社区里的用户抱怨，结构化为可评估、可研究、可进入 PRD 的产品机会。

> **Growth Mode（规划中）**：同一 Radar 引擎的延伸 **[DemandRadar](./docs/demand-radar/README.md)** — 面向已有产品，捕获 search/community intent → SEO 与社区增长机会。见 `feat/demand-radar` 分支。

**当前已实现**：Stage 0（可选领域定向）+ Stage 1–3（痛点雷达 → ICE 评分 → 用户研究 + **V2 商业判断**）  
**默认数据源**：Hacker News + Product Hunt + Reddit（`fetch_radar.py`）；可选 GitHub Issues、App Store 差评；PH/Reddit 需 `.env` token

> **版本号**：`v0.4` = 整条 pipeline（Stage 0–3 + 商业判断）。`v0.6` 等出现在 config/skill 里时指 **radar 过滤质量**版本，见 [`configs/README.md`](./configs/README.md)。

---

## 快速开始

```bash
# 1. 环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. （可选）API token — 仅本地 .env，切勿提交仓库
cp .env.example .env   # 填 PRODUCTHUNT_TOKEN / Reddit OAuth 等；HN 无需 key

# 3. 生成 pipeline_id（格式 pipe_YYYY-MM-DD_NNN）
PIPE=pipe_$(date +%Y-%m-%d)_001
mkdir -p runs/$PIPE/_raw runs/$PIPE/_judgments

# === 发现阶段：痛点 → 机会 ===

# 4. （可选）Stage 0 — 领域定向，收窄扫描范围
# → Agent 写 runs/$PIPE/_judgments/stage0.json
python3 helpers/build_domain_context.py $PIPE
python3 helpers/merge_radar_config.py $PIPE --base configs/radar.example.yaml

# 5. Stage 1 — 抓取互联网/SaaS 痛点
python3 helpers/fetch_radar.py $PIPE --config configs/radar.example.yaml
# → Agent 写 runs/$PIPE/_judgments/stage1.json（sentiment + keywords）
python3 helpers/build_pain_batch.py $PIPE   # 自动：聚类 + 外部信号 enrich
python3 helpers/build_i18n.py $PIPE --stage 1
python3 helpers/digest.py runs/$PIPE/1_pain_points.json

# 6. Stage 2 — ICE 评分
# → Agent 写 runs/$PIPE/_judgments/stage2.json
python3 helpers/build_scored_batch.py $PIPE   # 自动：Trends/HN 增速 + commercial_prefill
python3 helpers/build_i18n.py $PIPE --stage 2
python3 helpers/digest.py runs/$PIPE/2_scored_pain_points.json

# 7. Stage 3 — 用户研究 + 商业判断
# → Agent 写 runs/$PIPE/_judgments/stage3.json（含 commercial_assessment）
python3 helpers/build_opportunity.py $PIPE   # 自动：opportunity_score + tier WARN
python3 helpers/build_i18n.py $PIPE --stage 3
python3 helpers/digest.py runs/$PIPE/3_opportunity.json

# 8. 🚦 决策点 ① — 人读 digest，决定 GO / WAIT / NO-GO
#    ↓ GO

# === 设计阶段：需求 → 架构 ===

# 9. Stage 4 — PRD 撰写
# → Agent 写 runs/$PIPE/_judgments/stage4.json
python3 helpers/build_prd.py $PIPE
python3 helpers/build_i18n.py $PIPE --stage 4
python3 helpers/digest.py runs/$PIPE/4_prd.json

# 10. Stage 5 — 技术架构设计
# → Agent 写 runs/$PIPE/_judgments/stage5.json
python3 helpers/build_tech_spec.py $PIPE
python3 helpers/build_i18n.py $PIPE --stage 5
python3 helpers/init_codebase.py $PIPE
python3 helpers/digest.py runs/$PIPE/5_tech_spec.json

# 11. 🚦 决策点 ② — 人审 PRD + 架构，决定 PROCEED / REVISE / CANCEL

# === 实现阶段：代码 ===

# 12. Stage 6 — 编码 + TDD
# → 开发者在 Git repo 写代码
# → 持续运行 pytest / npm test
# → 提交 PR，CI/CD 触发

# 13. Stage 7 — 测试 + 自审
# → 自动化：lint, type check, security scan
# → 生成报告 runs/$PIPE/_judgments/stage7.json

# 14. 🚦 决策点 ③ — 人审代码/测试/安全，决定 MERGE / REQUEST_CHANGES

# === 运营阶段：上线 + 增长 ===

# 15. Stage 8 — 部署
# → 自动部署到 staging / production
# → 写部署报告 runs/$PIPE/_judgments/stage8.json
# → 启动监控告警

# 16. Stage 9 — 运营 + 商业化
# → 收集 DAU/MAU/ARR 指标
# → 追踪获客渠道效果
# → 生成增长报告 runs/$PIPE/_judgments/stage9.json

# 17. 🚦 决策点 ④ — 人复盘商业策略，决定 SCALE / OPTIMIZE / SUNSET
```

**Agent 步骤说明**：写 `_judgments/stageN.json` 可在 Cursor / Claude Code 中触发对应 skill（见 [.claude/skills/](./.claude/skills/)）。**Helper 步骤**（自动运行）：Python 脚本拼装、校验、生成最终 JSON + digest。

**推荐配置：**

| 配置 | 用途 |
|------|------|
| [`configs/radar.example.yaml`](./configs/radar.example.yaml) | 默认轻量扫描（HN + PH；Reddit / GitHub / App Store 默认关闭） |
| [`configs/radar.market_balanced.yaml`](./configs/radar.market_balanced.yaml) | 推荐全局扫描（HN + GitHub + PH + Reddit + App Store；缺凭证的源会 WARN 后跳过） |
| [`configs/radar.full_run.yaml`](./configs/radar.full_run.yaml) | 单产品深潜（如 QuickBooks App Store） |

---

## 流水线概览

```
[0 领域定向] 可选 ✅ → [1 痛点雷达] ✅ → [2 ICE 评分] ✅ → [3 用户研究 + 商业判断] ✅
                                                              ↓
                                                        🚦 决策点 ①
                                                         GO ↓
[4 PRD] ✅ → [5 架构] ✅ → 🚦 决策点 ② → [6 编码] ✅ → [7 测试] ✅
                             ↓ PROCEED       ↓
                                        🚦 决策点 ③
                                         MERGE ↓
                                    [8 部署] ✅ → [9 运营] ✅
                                         ↓
                                    🚦 决策点 ④
```

**v0.4+** — 完整流水线已落地（Stage 0–9）

### 四个决策点（人必须介入）

| 决策点 | 阶段后 | 决定什么 |
|--------|--------|----------|
| ① GO/NO-GO | Stage 3 | 这个痛点值不值得做（结合 `opportunity_score` + `recommendation`） |
| ② 方案审批 | Stage 5 | PRD 和技术方案对不对 |
| ③ 上线放行 | Stage 7 | 代码能不能上生产 |
| ④ 商业策略 | Stage 9 | 定价 / 营销 / 增长策略 |

### 数据流

```
domain_context.json     Stage 0（可选）→ merge_radar_config → radar.config.yaml
    ↓
top50.json              fetch_radar
    ↓ judgments
PainPoint[]             build_pain_batch → pain_clusters + external_signals
    ↓ ICE 评分 + judgments
ScoredPainPoint[]       build_scored_batch → market_signals + commercial_prefill
    ↓ 用户研究 + commercial_assessment
Opportunity             build_opportunity → opportunity_score + external_signals_summary
    ↓ 🚦①
SelectedOpportunity     （待实现）
    ↓
PRD → TechSpec → …      （Stage 4–9 待实现）
```

**Opportunity Score 公式：**

```
Pain × Frequency × ROI × SwitchingWill × Buyer × Persistence ÷ Competition ÷ WorkaroundQuality
```

分级：high ≥ 2000 · medium ≥ 500 · low ≥ 100 · watch < 100。`recommendation` 与 tier 不一致时 helper 会 WARN。

---

## 已实现能力

### Stage 0 — 领域定向 [`domain-focus`](./.claude/skills/domain-focus/SKILL.md)（可选）

| 能力 | 说明 |
|------|------|
| 对话锚定 | 锁定 `domain`、`target_user`、`known_competitors`、`search_keywords` |
| ICE 权重 | `ice_priority` 调整 Stage 2 评分侧重 |
| 配置合并 | `merge_radar_config.py` 将 `domain_context.json` 注入 radar YAML |
| 输出 | `domain_context.json` + `runs/{pid}/radar.config.yaml` |

无 Stage 0 时 pipeline 以 **broad scan** 模式运行。

### Stage 1 — 痛点雷达 [`pain-radar`](./.claude/skills/pain-radar/SKILL.md)

| 能力 | 说明 |
|------|------|
| 多源抓取 | `fetch_radar.py` — HN + GitHub + PH + App Store + Reddit（`enabled` 开关） |
| 单源调试 | `fetch_hn.py` / `fetch_github_issues.py` / `fetch_producthunt.py` / `fetch_reddit.py` / `fetch_app_store.py` |
| 过滤合并 | 每源 top N，跨源按 `source:object_id` 去重 → `_raw/top50.json` |
| 痛点聚类 | `compute_pain_clusters.py` — 主题@产品聚类 + 商业预筛 hints |
| 外部信号 | `enrich_external_signals.py` — 切换意愿短语、GitHub issue 持续性、竞品定价片段 |
| Agent 判断 | sentiment（4 类）+ keywords（3–7 个） |
| 输出 | `1_pain_points.json`，严格校验 [`pain_point.schema.json`](./contracts/pain_point.schema.json) |

### Stage 2 — ICE 评分 [`score-pain`](./.claude/skills/score-pain/SKILL.md)

| 能力 | 说明 |
|------|------|
| ICE 框架 | Impact × Confidence × Ease，total 自动计算 |
| 假痛点过滤 | Show HN、新闻、社区帖、成功庆祝等降分规则 |
| 聚类 dampening | 单源 echo 重复时 confidence -1~-2 |
| 市场信号 | Google Trends 斜率 + HN 48h 评论增速 |
| 商业预填 | `commercial_prefill.json` — Stage 3 Agent 的启发式锚点 |
| 分档 digest | 🟢 total≥200 · 🟡 100–199 · ⚪ <100 |
| 输出 | `2_scored_pain_points.json` |

### Stage 3 — 用户研究 + 商业判断 [`user-research`](./.claude/skills/user-research/SKILL.md)

| 能力 | 说明 |
|------|------|
| 机会包 | 用户画像、竞品、TAM/SAM/SOM、产品假设 |
| 多痛点合并 | 同主题多条 ICE 高分项合成一个 Opportunity |
| 建议 | `build` / `validate` / `skip` / `partner` + confidence 等级 |
| 证据审计 | `confidence_basis`、`evidence_ledger`、`unsupported_assumptions`、`validation_required` |
| **V2 商业判断** | `commercial_assessment`：迁移成本、替代方案、付费主体、持续性、ROI |
| **机会评分** | `opportunity_score` 自动计算 + tier；digest 展示商业判断与外部信号摘要 |
| Focus 模式 | `--pain-point-id` 或 Stage 0 `known_competitors` 驱动竞品检测 |
| 输出 | `3_opportunity.json` |

### Stage 4 — PRD 撰写 [`prd-writer`](./.claude/skills/prd-writer/SKILL.md)

| 能力 | 说明 |
|------|------|
| 产品愿景 | 连接痛点→解决方案的北极星 |
| 用户故事 | 基于 Stage 3 personas，写出 3-5 个故事，每个 3-5 个验收标准 |
| 功能分解 | 5-15 个核心功能，按优先级 (P0/P1/P2/P3) 分档，评估工作量 |
| 验收标准 | 产品级验收标准 (5-20 条)，可自动化验证 |
| 成功指标 | 北极星 + 关键指标 (3-10 个)，带基线 / 目标 / 测量周期 |
| 约束与假设 | 技术、业务、法律约束；产品假设 |
| 风险与应对 | 列举 2-5 个主要风险，每个都有缓解方案 |
| 竞争定位 | 独特价值主张 + vs 竞品的 3-5 个优势 + 市场窗口 |
| 商业模式 | 订阅 / 按用量 / 一次性 / 混合，定价策略，目标 ARR |
| 时间估算 | MVP 实现周数 (4-16 周) |
| 输出 | `4_prd.json` |

### Stage 5 — 技术架构 [`tech-architect`](./.claude/skills/tech-architect/SKILL.md)

| 能力 | 说明 |
|------|------|
| 架构模式 | 选择：单体 / 微服务 / Serverless / WebSocket，附带理由 |
| 技术栈选择 | 前端 / 后端 / 数据库 / 基础设施，每层都有决策理由 |
| 系统设计 | 文字 + ASCII/Mermaid 图，显示数据流 |
| 数据库模式 | 表定义、列类型、主键、外键、索引 |
| API 契约 | 5-10 个 REST 端点，含请求/响应 schema、速率限制 |
| 部署架构 | 环境描述、容器编排、监控告警、备份策略 |
| 安全考虑 | 认证、授权、数据加密、速率限制、合规性 |
| 可扩展性计划 | 预期负载 (100 → 10k DAU)，纵向/横向扩展，性能目标 |
| 开发阶段 | 3-5 个交付阶段，每个 1-3 周，清晰的依赖关系 |
| 工作量估算 | 总小时数 (用于 Stage 6 规划) |
| 输出 | `5_tech_spec.json` |

### Stage 6–7 — 编码与测试 (开发者) 

| 能力 | 说明 |
|------|------|
| TDD 开发 | 按 Stage 5 阶段交付，每个 PR 都要测试覆盖 |
| 自动化检查 | Lint, type check, security scan 在 CI/CD |
| 代码审查 | 自审 + 对等审查 |
| 测试报告 | 单元 / 集成 / E2E 覆盖率 |
| 输出 | Git repo + PR + `7_code_delivery.json` |

### Stage 8 — 部署 (DevOps / SRE)

| 能力 | 说明 |
|------|------|
| 环境配置 | Vercel / Railway / Neon / 等云服务配置 |
| 监控告警 | Sentry / PostHog / Better Uptime 启用 |
| 故障应对 | On-call 日程、升级流程、运行手册 |
| 性能基线 | 部署后的延迟 / 错误率 / 资源使用 |
| 零停机部署 | 蓝绿部署 / 金丝雀 / 回滚策略 |
| 输出 | `8_deployment.json` |

### Stage 9 — 运营 (增长 / 营销 / 数据)

| 能力 | 说明 |
|------|------|
| 产品指标 | DAU / MAU / 留存率 (D1/D7/D30) / 平均会话长度 |
| 商业指标 | 注册用户 / 转化率 / ARR / MRR / CAC / CLV |
| 获客渠道 | 有机 / 付费搜索 / 付费社交 / 推荐 / 合作，各渠道的 ROAS |
| 流失分析 | 月度流失率，流失原因 + 留存改进计划 |
| 功能采纳 | 各功能的采用率 + 趋势 + 用户反馈 |
| 收入汇总 | 总收入 / 按套餐分解 / 退款率 / 支付成功率 |
| 增长建议 | 列举 2-5 个高杠杆机会，评估影响 / 工作量 / 优先级 |
| 对标目标 | 与计划比较 (MAU / ARR 是否达成)，差异说明 |
| 下季度计划 | 重点方向 / 功能路线图 / 增长实验 / 扩展机会 |
| 输出 | `9_growth_metrics.json` |

---

## 数据源

| 来源 | 抓取 | 配置 | 状态 |
|------|------|------|------|
| **Hacker News** | `fetch_hn.py` / `fetch_radar.py` | [`configs/radar.example.yaml`](./configs/radar.example.yaml) | ✅ 默认开启 |
| **App Store** | `fetch_app_store.py` | [`configs/radar.app_store.example.yaml`](./configs/radar.app_store.example.yaml) | ✅ 1–2★ 差评 RSS，无 API key |
| GitHub Issues | `fetch_github_issues.py` | 同上（`mode: product_pain`） | 可选；`GITHUB_TOKEN` 提升限额 |
| Product Hunt | `fetch_producthunt.py` | 同上 + `PRODUCTHUNT_TOKEN` | ✅ 默认开启 |
| Reddit | `fetch_reddit.py` | 同上 + OAuth（见 `.env.example`） | 需 API 审批（#12） |
| HN 定向 idea 搜索 | — | — | 暂缓（#14） |
| G2 / Capterra | — | — | 暂缓（#6 epic） |

HN 配置示例：

```yaml
sources:
  - type: hackernews
    tags: [ask_hn, story, show_hn]
    keywords: [saas, startup, frustrated, alternative, struggle]
    min_points: 10
filters:
  date_range: last_7_days   # last_24_hours | last_7_days | last_month
limit_per_source: 50
top_per_source: 10
```

---

## 项目结构

```
ai-pain-pipeline/
├── README.md                       本文档
├── requirements.txt                jsonschema, PyYAML
├── .env.example                    Reddit OAuth 模板（可选）
│
├── .claude/skills/                 Agent 执行指令
│   ├── domain-focus/               Stage 0（可选）
│   ├── pain-radar/                 Stage 1
│   ├── score-pain/                 Stage 2
│   ├── user-research/              Stage 3
│   ├── prd-writer/                 Stage 4 ✅
│   ├── tech-architect/             Stage 5 ✅
│   └── [coding/qa/devops]/         Stage 6–9 框架
│
├── contracts/                      JSON Schema（跨阶段契约）
│   ├── domain_context.schema.json  Stage 0
│   ├── pain_point.schema.json      Stage 1
│   ├── scored_pain_point.schema.json  Stage 2
│   ├── opportunity.schema.json     Stage 3
│   ├── prd.schema.json             Stage 4 ✅
│   ├── tech_spec.schema.json       Stage 5 ✅
│   ├── code_delivery.schema.json   Stage 6–7 ✅
│   ├── deployment.schema.json      Stage 8 ✅
│   └── growth_metrics.schema.json  Stage 9 ✅
│
├── configs/
│   ├── radar.example.yaml          多源默认配置
│   ├── radar.market_balanced.yaml  全市场 balanced 扫描
│   ├── radar.full_run.yaml         单产品深潜
│   └── radar.*.example.yaml        领域示例（PDF、indie GTM、CI/CD 等）
│
├── helpers/                        确定性脚本（skill 调用）
│   ├── fetch_radar.py              多源合并抓取
│   ├── fetch_*.py                  单源调试（HN / GitHub / PH / Reddit / App Store）
│   ├── compute_pain_clusters.py    Stage 1 聚类 + 商业 hints
│   ├── enrich_external_signals.py  Stage 1 外部信号 enrich
│   ├── market_signals_enrich.py    Stage 2 Trends + HN 增速
│   ├── build_commercial_prefill.py Stage 2 商业分数预填
│   ├── build_pain_batch.py         拼装 Stage 1
│   ├── build_scored_batch.py       拼装 Stage 2
│   ├── build_opportunity.py        拼装 Stage 3
│   ├── build_prd.py                拼装 Stage 4 ✅
│   ├── build_tech_spec.py          拼装 Stage 5 ✅
│   ├── init_codebase.py            Stage 5 后初始化 Git 骨架 ✅
│   ├── build_code_delivery.py      拼装 Stage 6–7 ✅
│   ├── build_deployment.py         拼装 Stage 8 ✅
│   ├── build_growth_metrics.py     拼装 Stage 9 ✅
│   ├── build_domain_context.py     Stage 0 拼装
│   ├── merge_radar_config.py       Stage 0 → radar YAML
│   ├── digest.py                   JSON → .digest.md / .digest.zh.md
│   └── build_i18n.py               生成中文版 .i18n.json
│
├── docs/                           架构设计文档
│   ├── flow.md                     完整流程图
│   ├── contracts.md                数据契约（人类可读）
│   ├── state-machine.md            状态机
│   ├── dependencies.md             依赖清单
│   └── execution-modes.md          执行模式
│
└── runs/                           运行产出（gitignore）
    └── pipe_YYYY-MM-DD_NNN/
        ├── _raw/                   原始抓取
        ├── _judgments/             Agent 判断 (stage0–9.json)
        ├── 1_pain_points.json
        ├── 2_scored_pain_points.json
        ├── 3_opportunity.json
        ├── 4_prd.json              Stage 4 ✅
        ├── 5_tech_spec.json        Stage 5 ✅
        ├── 6_codebase/             Git repo 骨架 ✅
        ├── 7_code_delivery.json    Stage 6–7 ✅
        ├── 8_deployment.json       Stage 8 ✅
        └── 9_growth_metrics.json   Stage 9 ✅
```

---

## 设计原则

1. **结构化优先于智能** — 每阶段输出符合 JSON Schema，helper 严格校验
2. **判断与拼装分离** — Agent 写 `_judgments/`，helper 做确定性拼装
3. **每片可独立运行** — 任意 stage 可单独跑，只依赖上一 stage 产出
4. **工具中立** — Cursor / Claude Code / Codex CLI / API 均可驱动 skill
5. **从轻到重** — v0.x 是 Markdown + JSON 文件，不是 K8s

详见 [docs/execution-modes.md](./docs/execution-modes.md)。

---

## Helper 命令参考

| 命令 | 作用 |
|------|------|
| `python3 helpers/build_domain_context.py <pid>` | Stage 0 拼装 `domain_context.json` |
| `python3 helpers/merge_radar_config.py <pid> --base <yaml>` | Stage 0 → `radar.config.yaml` |
| `python3 helpers/fetch_radar.py <pid> [--config <yaml>]` | 多源 → `_raw/top50.json` |
| `python3 helpers/fetch_*.py <pid>` | 单源调试 |
| `python3 helpers/build_pain_batch.py <pid>` | Stage 1 拼装 + 聚类 + 外部信号 |
| `python3 helpers/build_scored_batch.py <pid>` | Stage 2 拼装 + 市场信号 + commercial_prefill |
| `python3 helpers/build_opportunity.py <pid>` | Stage 3 拼装 + opportunity_score |
| `python3 helpers/enrich_external_signals.py <pid>` | 单独重跑外部信号 enrich |
| `python3 helpers/build_commercial_prefill.py <pid> [--pain-point-id <id>]` | 单独重跑商业预填 |
| `python3 helpers/digest.py runs/<pid>/N_*.json` | 生成 `.digest.md` + `.digest.zh.md` |
| `python3 helpers/build_i18n.py <pid> --stage 0\|1\|2\|3` | 生成 `N_*.i18n.json` 中文版 sidecar |

`pipeline_id` 格式：`pipe_YYYY-MM-DD_NNN`（如 `pipe_2026-06-15_001`）。

---

## 架构文档

| 文件 | 内容 | 范围 |
|------|------|------|
| [docs/contracts.md](./docs/contracts.md) | 每阶段输入/输出（含 V2 商业判断字段） | **已实现** Stage 0–3 |
| [helpers/README.md](./helpers/README.md) | Helper 脚本详细说明 | **已实现** |
| [configs/README.md](./configs/README.md) | Radar 配置与数据源 | **已实现** |
| [docs/flow.md](./docs/flow.md) | Mermaid 流程图 | Stage 0–3 已实现；4–9 **目标占位** |
| [docs/state-machine.md](./docs/state-machine.md) | Pipeline 状态机 | **目标占位**（当前为 `runs/` JSON + 人工 digest） |
| [docs/dependencies.md](./docs/dependencies.md) | 每阶段 Skill / 工具 / API | 文首表=已实现；后半=**目标占位** |
| [docs/execution-modes.md](./docs/execution-modes.md) | 5 种执行模式 | **目标占位**（无 `pipeline run` CLI） |
| [docs/project_thinking.md](./docs/project_thinking.md) | 爬取质量与领域定向思路 | 混合：§三 路线图跟踪实现进度 |
| [docs/radar_quality.md](./docs/radar_quality.md) | Radar 质量 benchmark | **已实现** 度量与门禁 |
| [docs/demand-radar/](./docs/demand-radar/README.md) | **DemandRadar** Growth Mode 产品定义与 MVP | **规划中** `feat/demand-radar` |

---

## 实现进度

| 模块 | 状态 |
|------|------|
| Stage 0 领域定向 | ✅ |
| Stage 1 痛点雷达（HN + GitHub + PH + App Store + Reddit） | ✅ |
| Stage 2 ICE 评分 + 聚类 dampening + 市场信号 | ✅ |
| Stage 3 用户研究 + 证据审计 | ✅ |
| **V2 商业判断层**（commercial_assessment + opportunity_score + 外部信号） | ✅ |
| **Stage 4 PRD 撰写** | ✅ |
| **Stage 5 技术架构** | ✅ |
| **Stage 6 编码 + TDD** | ✅ |
| **Stage 7 测试 + 自审** | ✅ |
| **Stage 8 部署** | ✅ |
| **Stage 9 运营 + 增长** | ✅ |
| 决策点 UX（Slack / Email / Dashboard） | ❌ |
| 定时调度（cron / GitHub Actions） | ❌ #15 |
| HN 定向 idea/关键词搜索 | ❌ #14 |
| Reddit OAuth smoke test | ❌ #12 |
| G2 / Capterra 适配器 | ❌ #6 |
| **DemandRadar Growth Mode**（G0–G4） | 🚧 [docs/demand-radar/](./docs/demand-radar/README.md) |

---

## 示例运行

仓库内已有完整跑通示例（本地生成，默认 gitignore）：

| Run | 配置 | 选中机会 | Score | Tier | 要点 |
|-----|------|----------|------:|------|------|
| `pipe_2026-06-15_001` | full_run | SteadyBooks（QuickBooks） | 1440 | medium | switching=2，结构性 persistence |
| `pipe_2026-06-15_002` | market_balanced | DevPulse（Next.js OOM） | 370 | low | ICE #1 但 buyer=3、platform_bug |
| `pipe_2026-06-15_003` | market_balanced | ClearWave（Wave 付款冻结） | 3024 | high | SMB 付款痛点集群，recommendation 仍为 validate |

读摘要：`runs/pipe_2026-06-15_003/3_opportunity.digest.zh.md`

早期示例：`runs/pipe_2026-05-31_001/`（纯 HN，无商业判断层）。

---

## 许可证

[MIT](./LICENSE) — 见仓库根目录 `LICENSE`。

安全与凭证说明见 [SECURITY.md](./SECURITY.md)。`.env` 与 `runs/` 已在 `.gitignore` 中，请勿强行加入版本库。
