# Helpers

通用脚本，被 skill 调用。原则：能用 skill 做的就别写代码，这里只放 skill 真的搞不定的事。

Agent 免审批运行这些脚本：见 [`.cursor/permissions.json`](../.cursor/permissions.json) 与 [`docs/cursor_agent_permissions.md`](../docs/cursor_agent_permissions.md)。

## 当前内容

| 脚本 | 用途 | 被谁调 |
|------|------|--------|
| `digest.py` | stage 输出 → `.digest.md` + `.digest.zh.md`（有 i18n 时） | 各 stage 末步 |
| `build_i18n.py <pid> --stage N` | `_judgments/stageN_i18n.json` → `N_*.i18n.json` | 各 stage 翻译步骤 |
| `fetch_radar.py <pid>` | **多源合并**：HN + GitHub + PH + App Store + Reddit（按 config `enabled`） | `pain-radar` skill 步骤 2–3（推荐） |
| `fetch_hn.py <pid>` | Algolia 抓取 HN（无需 API key） | 单源调试 |
| `fetch_github_issues.py <pid>` | GitHub REST Issues（`GITHUB_TOKEN` 可选） | 单源调试 |
| `fetch_producthunt.py <pid>` | Product Hunt GraphQL（需 `PRODUCTHUNT_TOKEN`） | 单源调试 |
| `fetch_reddit.py <pid>` | OAuth 抓取 Reddit | 单源调试（需 API 批准） |
| `fetch_app_store.py <pid>` | App Store 1–2★ 评论 RSS（无 API key） | 单源调试 / issue #7 |
| `radar_common.py` | 多源 fetch 共享：YAML、HTTP、过滤、质量硬规则、合并 | 被上述 fetch 脚本 import |
| `eval_radar_quality.py` | benchmark 对比 v0.4/v0.6 过滤指标（precision/recall/leak） | 优化验证 / CI |
| `hn_comments.py` | HN Algolia items API → `comment_resonance` | `fetch_hn.py` |
| `compute_radar_signals.py <pid>` | `top50.json` → `radar_signals.json` 主题聚类 | `fetch_radar.py` |
| `merge_radar_config.py <pid>` | Stage 0 `domain_context.json` → `runs/{pid}/radar.config.yaml` | `domain-focus` skill |
| `build_domain_context.py <pid>` | Stage 0 judgments → `domain_context.json` | `domain-focus` skill |
| `market_signals_enrich.py` | Google Trends 斜率 + HN 48h 评论增速 | `build_scored_batch.py` |
| `smoke_github_issues.py` | GitHub product_pain 过滤 smoke + JSON 报告 | CI / #10 验证 |
| `build_pain_batch.py <pid>` | 拼装 stage 1 输出（top50 + judgments → 1_pain_points.json）+ 严格校验 | `pain-radar` skill 步骤 5 |
| `build_scored_batch.py <pid>` | 拼装 stage 2 输出（pain_points + judgments → 2_scored_pain_points.json）+ 严格校验 | `score-pain` skill 步骤 3 |
| `build_opportunity.py <pid>` | 拼装 stage 3 输出（judgments → 3_opportunity.json）+ 自动算 `opportunity_score` | `user-research` skill 步骤 3 |

## 设计约定

- **判断（Claude 的 LLM 产出）和拼装（确定性代码）分开**
  - 判断 → `runs/{pid}/_judgments/stageN.json`（纯数据）
  - 中文 → `runs/{pid}/_judgments/stageN_i18n.json` → `N_*.i18n.json`
  - 拼装 → `helpers/build_*.py`（无 hardcode 数据）
- **每个 helper 单参数 `pipeline_id`**，路径都从 pid 推导
- **严格校验**：每个 helper 跑完都用对应的 jsonschema 验一遍，挂了立刻报错
- **证据可审计**：Stage 3 支持 `evidence_ledger` 和 `confidence_basis`，digest 会展示证据边界与待验证假设
- **商业判断 V2**：Stage 3 可选 `commercial_assessment`（迁移成本、替代方案、付费主体、持续性、ROI）；`build_opportunity.py` 自动计算 `opportunity_score` 并 WARN recommendation 与 tier 不一致
- **幂等**：可以重复跑，不会损坏前一阶段输出（但当前会覆盖自己的输出）

## 预期未来加的

| 文件 | 用途 | 何时加 |
|------|------|--------|
| `headless.sh` | cron / GitHub Actions 触发 `claude -p` | 需要定时跑时 |
| `build_*_batch.py`（更多 stage） | stage 3+ 落地工具 | 写 stage 3 skill 时 |
