# AI Pain Pipeline

> v0.3 · 2026-06 · 从市场痛点到产品机会的 AI 驱动流水线

一条由 **AI Agent 执行 + 人类在关键节点拍板** 的流水线，把公开社区里的用户抱怨，结构化为可评估、可研究、可进入 PRD 的产品机会。

**当前已实现**：Stage 1–3（痛点雷达 → ICE 评分 → 用户研究）  
**默认数据源**：Hacker News + Product Hunt + Reddit（`fetch_radar.py`；GitHub 默认关；PH/Reddit 需 `.env` token）

---

## 快速开始

```bash
# 1. 环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 生成 pipeline_id（格式 pipe_YYYY-MM-DD_NNN）
PIPE=pipe_$(date +%Y-%m-%d)_001
mkdir -p runs/$PIPE/_raw runs/$PIPE/_judgments

# 3. Stage 1 — 抓取互联网/SaaS 痛点（默认仅 HN ask_hn + show_hn）
python3 helpers/fetch_radar.py $PIPE --config configs/radar.example.yaml
# → Agent 写 runs/$PIPE/_judgments/stage1.json（sentiment + keywords）
python3 helpers/build_pain_batch.py $PIPE
python3 helpers/build_i18n.py $PIPE --stage 1   # Agent 先写 _judgments/stage1_i18n.json
python3 helpers/digest.py runs/$PIPE/1_pain_points.json

# 4. Stage 2 — ICE 评分
# → Agent 写 runs/$PIPE/_judgments/stage2.json
python3 helpers/build_scored_batch.py $PIPE
python3 helpers/build_i18n.py $PIPE --stage 2
python3 helpers/digest.py runs/$PIPE/2_scored_pain_points.json

# 5. Stage 3 — 用户研究
# → Agent 写 runs/$PIPE/_judgments/stage3.json
python3 helpers/build_opportunity.py $PIPE
python3 helpers/build_i18n.py $PIPE --stage 3
python3 helpers/digest.py runs/$PIPE/3_opportunity.json

# 6. 🚦 决策点 ① — 人读 digest，决定 GO / NO-GO
```

Agent 步骤（写 `_judgments/stageN.json`）在 Cursor / Claude Code 中触发对应 skill 即可，详见 [.claude/skills/](./.claude/skills/)。

---

## 流水线概览

```
[1 痛点雷达] ✅ → [2 ICE 评分] ✅ → [3 用户研究] ✅
                                        ↓
                                  🚦 决策点 ①  ← 当前停在这里
                                        ↓
[4 PRD] → [5 架构] → [6 编码] → [7 测试] → [8 部署] → [9 运营]  （未实现）
```

### 四个决策点（人必须介入）

| 决策点 | 阶段后 | 决定什么 |
|--------|--------|----------|
| ① GO/NO-GO | Stage 3 | 这个痛点值不值得做 |
| ② 方案审批 | Stage 5 | PRD 和技术方案对不对 |
| ③ 上线放行 | Stage 7 | 代码能不能上生产 |
| ④ 商业策略 | Stage 9 | 定价 / 营销 / 增长策略 |

### 数据流

```
PainPoint[]          Stage 1  output → 1_pain_points.json
    ↓ ICE 评分
ScoredPainPoint[]    Stage 2  output → 2_scored_pain_points.json
    ↓ 用户研究
Opportunity          Stage 3  output → 3_opportunity.json
    ↓ 🚦①
SelectedOpportunity  （待实现）
    ↓
PRD → TechSpec → …   （Stage 4–9 待实现）
```

---

## 已实现能力

### Stage 1 — 痛点雷达 [`pain-radar`](./.claude/skills/pain-radar/SKILL.md)

| 能力 | 说明 |
|------|------|
| 多源抓取 | `fetch_radar.py` — HN + GitHub + PH + Reddit（`enabled` 开关） |
| 单源调试 | `fetch_hn.py` / `fetch_github_issues.py` / `fetch_producthunt.py` / `fetch_reddit.py` |
| 过滤合并 | 每源 top N，跨源按 `source:object_id` 去重 → `_raw/top50.json` |
| Agent 判断 | sentiment（4 类）+ keywords（3–7 个） |
| 输出 | `1_pain_points.json`，严格校验 [`pain_point.schema.json`](./contracts/pain_point.schema.json) |

### Stage 2 — ICE 评分 [`score-pain`](./.claude/skills/score-pain/SKILL.md)

| 能力 | 说明 |
|------|------|
| ICE 框架 | Impact × Confidence × Ease，total 自动计算 |
| 假痛点过滤 | Show HN、新闻、社区帖、成功庆祝等降分规则 |
| 分档 digest | 🟢 total≥200 · 🟡 100–199 · ⚪ <100 |
| 输出 | `2_scored_pain_points.json` |

### Stage 3 — 用户研究 [`user-research`](./.claude/skills/user-research/SKILL.md)

| 能力 | 说明 |
|------|------|
| 机会包 | 用户画像、竞品、TAM/SAM/SOM、产品假设 |
| 多痛点合并 | 同主题多条 ICE 高分项合成一个 Opportunity |
| 建议 | `build` / `validate` / `skip` / `partner` + confidence 等级 |
| 证据审计 | `confidence_basis`、`evidence_ledger`、`unsupported_assumptions`、`validation_required` 区分事实与假设 |
| 输出 | `3_opportunity.json` |

---

## 数据源

| 来源 | 抓取 | 配置 | 状态 |
|------|------|------|------|
| **Hacker News** | `fetch_hn.py` / `fetch_radar.py` | [`configs/radar.example.yaml`](./configs/radar.example.yaml) | ✅ 默认开启（internet_saas 聚焦） |
| GitHub Issues | `fetch_github_issues.py` | 同上（`mode: product_pain`） | 默认关闭；仅产品/业务向 issue |
| Product Hunt | `fetch_producthunt.py` | 同上 + `PRODUCTHUNT_TOKEN` | ✅ 默认开启 |
| Reddit | `fetch_reddit.py` | 同上 + OAuth（见 `.env.example`） | ✅ 默认开启（需 API 审批） |
| HN 定向 idea 搜索 | — | — | 暂缓（#4） |

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
│   ├── pain-radar/                 Stage 1
│   ├── score-pain/                 Stage 2
│   └── user-research/              Stage 3
│
├── contracts/                      JSON Schema（跨阶段契约）
│   ├── pain_point.schema.json      Stage 1 ✅
│   ├── scored_pain_point.schema.json  Stage 2 ✅
│   └── opportunity.schema.json     Stage 3 ✅
│
├── configs/
│   ├── radar.example.yaml          多源配置（HN + GitHub 默认）
│   └── radar.reddit.example.yaml Reddit 配置（可选）
│
├── helpers/                        确定性脚本（skill 调用）
│   ├── fetch_radar.py              多源合并抓取
│   ├── fetch_hn.py / fetch_github_issues.py / fetch_producthunt.py / fetch_reddit.py
│   ├── radar_common.py             多源共享工具
│   ├── build_pain_batch.py         拼装 Stage 1
│   ├── build_scored_batch.py       拼装 Stage 2
│   ├── build_opportunity.py        拼装 Stage 3
│   └── digest.py                   输出 → 人类可读 .digest.md
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
        ├── _judgments/               Agent 判断（stage1/2/3.json）
        ├── 1_pain_points.json
        ├── 2_scored_pain_points.json
        └── 3_opportunity.json
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
| `python3 helpers/fetch_radar.py <pid> [--config configs/radar.example.yaml]` | 多源 → `_raw/top50.json`（推荐） |
| `python3 helpers/fetch_hn.py` / `fetch_github_issues.py` / … | 单源调试 |
| `python3 helpers/build_pain_batch.py <pid>` | Stage 1 拼装 + 校验 |
| `python3 helpers/build_scored_batch.py <pid>` | Stage 2 拼装 + 校验 |
| `python3 helpers/build_opportunity.py <pid>` | Stage 3 拼装 + 校验 |
| `python3 helpers/digest.py runs/<pid>/N_*.json` | 生成 `.digest.md` + `.digest.zh.md` |
| `python3 helpers/build_i18n.py <pid> --stage 1\|2\|3` | 生成 `N_*.i18n.json` 中文版 sidecar |

`pipeline_id` 格式：`pipe_YYYY-MM-DD_NNN`（如 `pipe_2026-05-31_001`）。

---

## 架构文档

| 文件 | 内容 |
|------|------|
| [docs/flow.md](./docs/flow.md) | Mermaid 完整流程图 |
| [docs/contracts.md](./docs/contracts.md) | 每阶段输入/输出（人类描述） |
| [docs/state-machine.md](./docs/state-machine.md) | Pipeline 状态机 |
| [docs/dependencies.md](./docs/dependencies.md) | 每阶段 Skill / 工具 / API |
| [docs/execution-modes.md](./docs/execution-modes.md) | 5 种执行模式 |

---

## 实现进度

| 模块 | 状态 |
|------|------|
| Stage 1 痛点雷达（HN + GitHub + PH + Reddit） | ✅ |
| Stage 2 ICE 评分 | ✅ |
| Stage 3 用户研究 | ✅ |
| Stage 4 PRD | ❌ |
| Stage 5–9 | ❌ |
| 决策点 UX（Slack / Email / Dashboard） | ❌ |
| 定时调度（cron / GitHub Actions） | ❌ |
| HN 定向 idea/关键词搜索（#4） | ❌ 暂缓 |

---

## 示例运行

仓库内已有完整跑通示例：`runs/pipe_2026-05-31_001/`（本地生成，默认 gitignore）。

| Stage | 结果摘要 |
|-------|---------|
| 1 | 24 条 HN 帖子 → 4 negative / 7 positive |
| 2 | 4 条 🟢（ICE≥200），16 条 ⚪ 丢弃 |
| 3 | 合并求职主题 → **Tech job search signal pollution**，建议 **BUILD** |

读摘要：`runs/pipe_2026-05-31_001/3_opportunity.digest.md`

---

## 许可证

待定。
