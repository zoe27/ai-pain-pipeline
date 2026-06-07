---
name: pain-radar
description: 抓取 HN / GitHub Issues / Product Hunt / App Store / Reddit 上 SaaS / 开发者工具相关痛点候选，输出符合 contracts/pain_point.schema.json 的 PainPointBatch JSON 到 runs/{pipeline_id}/1_pain_points.json。当用户要跑 pipeline 阶段 1、做痛点雷达扫描、或者运行 /pain-radar 时使用。
---

# Pain Radar — 阶段 1 痛点雷达

## 用途

扫描配置里启用的数据源，聚焦 **互联网 / SaaS / 线上业务痛点**（获客、留存、定价、变现等），排除时政新闻、生活杂谈和纯框架 bug。

## 输入

| 参数 | 必需 | 默认 | 说明 |
|------|------|------|------|
| `pipeline_id` | 否 | 自动生成 `pipe_YYYY-MM-DD_NNN` | 现有 pipeline 续跑时传入 |
| `config_path` | 否 | `configs/radar.example.yaml` | RadarConfig YAML 路径（v0.6 含 `filters.quality`） |

**可选 Stage 0**：先跑 `domain-focus` skill 产出 `runs/{pid}/domain_context.json`，再把 `search_keywords` 写入 config 的 `domain_context`。

## 输出

`runs/{pipeline_id}/1_pain_points.json` —— 由 helper 严格校验 schema，符合 [`contracts/pain_point.schema.json`](../../../contracts/pain_point.schema.json)。

## 步骤

### 1. 准备

- **生成 pipeline_id**（如未提供）：
  - 格式：`pipe_$(date +%Y-%m-%d)_NNN`，NNN 是当天序号（已有数 + 1，三位补零）
- **创建目录**：`mkdir -p runs/{pipeline_id}/_raw runs/{pipeline_id}/_judgments`
- **冲突检查**：如果 `runs/{pipeline_id}/1_pain_points.json` 已存在，问用户：覆盖 / 跳过 / 改 pipeline_id
- **读 config**：解析 YAML，提取 `sources`、`filters`、`limit_per_source`

### 2–3. 抓取 + 过滤 + 合并

**推荐**：一次跑齐所有 `enabled: true` 的源：

```bash
python3 helpers/fetch_radar.py {pipeline_id} --config {config_path}
```

合并顺序：hackernews → github_issues → producthunt → app_store → reddit。单源失败 WARN 并继续；**全部源无数据 → 退出非零**。**禁止**复用其他 pipeline 的旧 `_raw`。

抓取完成后 helper 自动写 `runs/{pid}/_raw/radar_signals.json`（跨帖主题 + `comment_resonance`），供 Stage 2 使用。

**质量回归**（改过滤规则后必跑）：

```bash
python3 helpers/eval_radar_quality.py --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json
```

| 源 | `enabled` 默认 | 凭证 | 单源调试 |
|----|----------------|------|----------|
| `hackernews` | true | 无 | `fetch_hn.py` |
| `github_issues` | **false** | `GITHUB_TOKEN` 可选 | `fetch_github_issues.py` |
| `producthunt` | true | `PRODUCTHUNT_TOKEN` 必填 | `fetch_producthunt.py` |
| `app_store` | **false** | 无（公开 RSS） | `fetch_app_store.py` |
| `reddit` | true | OAuth + Data API 批准 | `fetch_reddit.py` |

**HN**（[Algolia API](https://hn.algolia.com/api)）：每 `tags` 抓 `limit_per_source`，过滤后 `top_per_source` → `{tag}_top.json`；关键词 0 命中时 WARN 并保留近期 top 帖。

**GitHub Issues**：按 `repos` 拉 open issues（跳过 PR）；可选 `labels`；`min_comments` 过滤。

**Product Hunt**：GraphQL 热门帖；可选 `topics` 过滤。

**Reddit**：公开 JSON 会 403，必须 OAuth。配置见 `configs/radar.reddit.example.yaml` 与 `.env.example`。

**App Store**（issue #7）：抓取 1–2★ 用户评论；`app_ids` 或 `search_terms` 指定目标 App。RSS 对许多 App 返回空 feed，先用 `fetch_app_store.py` 单源验证。示例：`configs/radar.app_store.example.yaml`。

**暂缓（#4）**：HN 按用户自定义 idea/关键词定向搜索（独立 CLI），不在本 skill 默认流程。

### 聚焦范围（v0.4 默认 config）

| 要 | 不要 |
|----|------|
| SaaS / 独立开发 / 线上获客·留存·定价·支持 | 能源、时政、育儿、乐高等非互联网话题 |
| 「用户/客户/创始人」抱怨的业务流程痛点 | GitHub 框架 bug、lint 规则、enum 报错 |
| Ask HN 里「怎么做增长/怎么找客户」 | 纯 infra 论文/内核/量化优化帖 |

- **HN**：默认仅 `ask_hn` + `show_hn`（去掉 `story` 新闻流）；`filters.exclude_keywords` 过滤噪音
- **GitHub Issues**：**默认 `enabled: false`**。若开启须 `mode: product_pain` + `pain_keywords`（onboarding/billing/customer…），helper 自动剔除 bug report 模板帖
- **Reddit**（可选）：sub 选 SaaS/startups/Entrepreneur，不用 devtools

### 4. 抽取判断 → 写 `_judgments/stage1.json`（Agent）

对每条保留下来的 post，你只做两个判断：

- **`sentiment`**：4 选 1
  - `negative` —— 抱怨、痛点、bug、frustration（**这是你最想要的**）
  - `positive` —— 赞美、推荐、成就分享
  - `neutral` —— 信息分享、问问题
  - `mixed` —— 一段抱怨 + 一段乐观 / 多个混合主题

- **`keywords`**：3-7 个
  - **全小写**，正则 `^[a-z0-9][a-z0-9 +#.-]*$`
  - 优先名词（`onboarding`, `auth`, `billing`），少用形容词
  - 不带空格的优先（`oauth`, `b2b-saas`）
  - 去掉太泛的词（`software`, `app`, `thing`）

按顺序（与 `_raw/top50.json` 一致）写到 `runs/{pipeline_id}/_judgments/stage1.json`：

```json
[
  {"sentiment": "negative", "keywords": ["onboarding", "saas", "auth"]},
  {"sentiment": "positive", "keywords": ["revenue", "milestone"]}
]
```

### 5. 调 helper 拼装 + 校验 + 落地

```bash
python3 helpers/build_pain_batch.py {pipeline_id}
```

Helper 自动做：
- 读 `_raw/top50.json` + `_judgments/stage1.json`
- 按每条 `source` 构造 `source_url`（HN / Reddit 等）、生成 UUID、加 `extracted_at`
- 用 `contracts/pain_point.schema.json` **严格 jsonschema 校验**
- 写 `runs/{pid}/1_pain_points.json`

校验失败 → helper 报错指出哪个字段不符合 schema → 你修 `_judgments/stage1.json` 后重跑。

### 6. 中文翻译 → `_judgments/stage1_i18n.json`（Agent）

与 `stage1.json` **同序、同条数**，为每条 post 写中文阅读版（翻译 title + 摘要，关键词可中文化）：

```json
[
  {
    "title_zh": "请不要向求职者群发推销，这很残忍",
    "summary_zh": "失业六个月的开发者在 HN 求职帖下收到 LLM 群发的推销邮件，引发大量共鸣。",
    "keywords_zh": ["求职", "招聘", "ai", "spam"]
  }
]
```

- `title_zh`：1–200 字，准确翻译标题
- `summary_zh`：10–500 字，概括 `title` + `selftext` 核心痛点（不必全文翻译）
- `keywords_zh`：3–7 个中文关键词

```bash
python3 helpers/build_i18n.py {pipeline_id} --stage 1
```

产出 `runs/{pid}/1_pain_points.i18n.json`（不影响英文 schema 输出）。

### 7. 生成可读 digest

```bash
python3 helpers/digest.py runs/{pipeline_id}/1_pain_points.json
```

会生成：
- `1_pain_points.digest.md` — 统计 + 英文标题摘要
- `1_pain_points.digest.zh.md` — **中文版**（需先完成 step 6）

**JSON 是给下一阶段用的；人读 digest，优先读 `.digest.zh.md`。**

## 失败处理

| 情况 | 处理 |
|------|------|
| 单 tag/subreddit HTTP 错 / 解析失败 / 超时 | 警告 + 继续 |
| 收到 429 | helper 等 5s 重试一次，再失败则跳过 |
| Reddit/PH 已启用但缺 token | WARN，跳过该源 |
| 所有启用源都无数据 | `fetch_radar` 退出非零 |
| 抓取失败 | **禁止**复用其他日期的 `_raw` 数据 |
| `_judgments/stage1.json` 数量与 `top50.json` 不符 | helper 报错 → 检查判断有没有漏 |
| schema 校验失败 | helper 报错指出字段 → 修 stage1.json |

## 当前限制

- 已实现：**HN、GitHub Issues、Product Hunt、App Store、Reddit**（HN + PH 默认开；App Store / GitHub / Reddit 默认关）
- 默认聚焦：**internet_saas**（见 `configs/radar.example.yaml` 的 `filters.focus`）
- 暂缓：**HN 定向关键词/idea 搜索**（#4）
- 默认每源 `top_per_source: 10`；多源合并后条数 = 各源之和（跨源按 `source:object_id` 去重）
- 不并发抓取
