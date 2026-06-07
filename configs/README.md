# Configs

| 文件 | 用途 |
|------|------|
| `radar.example.yaml` | 阶段 1 默认 v0.6：**internet_saas** + 业务痛点/评论共鸣/主题聚类；HN + PH 开；App Store 默认关 |
| `radar.app_store.example.yaml` | App Store 1–2★ 差评单源（issue #7 MVP） |
| `radar.indie_gtm.example.yaml` | Stage 0 示例：indie GTM / 零客户（#8） |
| `radar.cicd.example.yaml` | Stage 0 示例：CI/CD + GitHub product_pain（#8） |
| `radar.pdf.example.yaml` | Stage 0 示例：PDF 解析/OCR/表单（PyMuPDF + pdf.js；验证 run `pipe_2026-06-07_003`） |
| `radar.github_smoke.yaml` | GitHub Issues product_pain smoke test（#10） |
| `radar.full_run.yaml` | HN + PH + App Store 多源验证 |
| `radar.reddit.example.yaml` | 仅 Reddit 单源调试（OAuth） |

## 质量衡量

```bash
python3 helpers/eval_radar_quality.py --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json
```

指标与成功标准见 [`docs/radar_quality.md`](../docs/radar_quality.md)。

## 默认开启的渠道（v0.5）

| 渠道 | 凭证 |
|------|------|
| Hacker News | 无 |
| Product Hunt | `.env` → `PRODUCTHUNT_TOKEN` |
| Reddit | `.env` → `REDDIT_CLIENT_ID/SECRET/USER_AGENT` + Data API 批准 |

缺 token 时 `fetch_radar.py` 会 **WARN 并跳过**该源，不会拖垮整次抓取。

GitHub Issues 仍默认 `enabled: false`（框架 bug 多）；要开见 `mode: product_pain` + `pain_keywords`。

新增渠道步骤：加 `fetch_*.py` → `contracts/pain_point.schema.json` 的 `source` enum → `radar.example.yaml` → `fetch_radar.py` 注册。

## 已实现：App Store（#7 MVP）

| 渠道 | 凭证 | 说明 |
|------|------|------|
| App Store 评论 | 无 | 公开 RSS；仅 1–2★；许多 App feed 为空，见 `radar.app_store.example.yaml` |

```bash
python3 helpers/fetch_app_store.py pipe_test --config configs/radar.app_store.example.yaml
python3 helpers/eval_radar_quality.py --benchmark benchmarks/radar_quality_app_store_v1.json
```

## Stage 0 → config 合并（#8）

```bash
# 1. 写 runs/{pid}/_judgments/stage0.json → build_domain_context.py
# 2. 合并到本轮专用 config
python3 helpers/merge_radar_config.py {pipeline_id} --base configs/radar.indie_gtm.example.yaml
python3 helpers/fetch_radar.py {pipeline_id} --config runs/{pipeline_id}/radar.config.yaml
```

## GitHub Issues smoke（#10）

默认仍 **关闭** `github_issues`；验证 product_pain 过滤：

```bash
python3 helpers/smoke_github_issues.py
# → docs/github_issues_smoke.json（kept/rejected 比例）
```

2026-06-07 实测：`supabase/supabase` + `vercel/next.js`，keep_rate ≈ 15–25%，框架 bug 被剔除。

## 尚未实现

| 来源 | 适合抓什么 | 实现难度 | 备注 |
|------|-----------|----------|------|
| **Indie Hackers** | indie 获客/收入讨论 | 中 | 无官方 API，需 RSS/Playwright |
| **Hacker News 评论** | 帖子下真实抱怨 | 低 | Algolia comment API，扩展现有 HN |
| **G2 / Capterra 差评** | B2B SaaS 产品痛点 | 高 | 反爬 + ToS |
| **Google Play 评论** | 消费级 app 痛点 | 中 | 待接 #7 |
| **Twitter/X** | 实时吐槽 | 中–高 | API 付费 tier |
| **Discord/Slack 社区** | 垂直社区 | 高 | 需 bot + 授权 |
| **Google Trends** | 趋势验证（Stage 2 enrich） | 低 | 更适合 score-pain 而非 radar |
| **LinkedIn 帖子** | B2B 痛点 | 高 | 严格反爬 |

新增渠道步骤：加 `fetch_*.py` → `contracts/pain_point.schema.json` 的 `source` enum → `radar.example.yaml` → `fetch_radar.py` 注册。
