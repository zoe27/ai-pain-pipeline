---
name: pain-radar
description: 抓取 HN / GitHub Issues / Product Hunt / Reddit 上 SaaS / 开发者工具相关痛点候选，输出符合 contracts/pain_point.schema.json 的 PainPointBatch JSON 到 runs/{pipeline_id}/1_pain_points.json。当用户要跑 pipeline 阶段 1、做痛点雷达扫描、或者运行 /pain-radar 时使用。
---

# Pain Radar — 阶段 1 痛点雷达

## 用途

扫描配置里启用的数据源（默认 **HN + GitHub Issues**；可选 Product Hunt、Reddit），抽取符合条件的痛点候选，落地为结构化 JSON。

## 输入

| 参数 | 必需 | 默认 | 说明 |
|------|------|------|------|
| `pipeline_id` | 否 | 自动生成 `pipe_YYYY-MM-DD_NNN` | 现有 pipeline 续跑时传入 |
| `config_path` | 否 | `configs/radar.example.yaml` | RadarConfig YAML 路径 |

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

合并顺序：hackernews → github_issues → producthunt → reddit。单源失败 WARN 并继续；**全部源无数据 → 退出非零**。**禁止**复用其他 pipeline 的旧 `_raw`。

| 源 | `enabled` 默认 | 凭证 | 单源调试 |
|----|----------------|------|----------|
| `hackernews` | true | 无 | `fetch_hn.py` |
| `github_issues` | true | `GITHUB_TOKEN` 可选 | `fetch_github_issues.py` |
| `producthunt` | false | `PRODUCTHUNT_TOKEN` 必填 | `fetch_producthunt.py` |
| `reddit` | false | OAuth + Data API 批准 | `fetch_reddit.py` |

**HN**（[Algolia API](https://hn.algolia.com/api)）：每 `tags` 抓 `limit_per_source`，过滤后 `top_per_source` → `{tag}_top.json`；关键词 0 命中时 WARN 并保留近期 top 帖。

**GitHub Issues**：按 `repos` 拉 open issues（跳过 PR）；可选 `labels`；`min_comments` 过滤。

**Product Hunt**：GraphQL 热门帖；可选 `topics` 过滤。

**Reddit**：公开 JSON 会 403，必须 OAuth。配置见 `configs/radar.reddit.example.yaml` 与 `.env.example`。

**暂缓（#4）**：HN 按用户自定义 idea/关键词定向搜索（独立 CLI），不在本 skill 默认流程。

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

### 6. 生成可读 digest

```bash
python3 helpers/digest.py runs/{pipeline_id}/1_pain_points.json
```

会同目录生成 `1_pain_points.digest.md`，人类可读。**JSON 是给下一阶段用的，人不要直接读。**

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

- 已实现：**HN、GitHub Issues、Product Hunt、Reddit**（后两者默认 `enabled: false`）
- 暂缓：**HN 定向关键词/idea 搜索**（#4）
- 默认每源 `top_per_source: 10`；多源合并后条数 = 各源之和（跨源按 `source:object_id` 去重）
- 不并发抓取
