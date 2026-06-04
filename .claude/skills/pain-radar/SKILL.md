---
name: pain-radar
description: 抓取 Hacker News / Reddit 上 SaaS / 开发者工具相关痛点候选，输出符合 contracts/pain_point.schema.json 的 PainPointBatch JSON 到 runs/{pipeline_id}/1_pain_points.json。当用户要跑 pipeline 阶段 1、做痛点雷达扫描、或者运行 /pain-radar 时使用。
---

# Pain Radar — 阶段 1 痛点雷达

## 用途

扫描配置里指定的数据源（默认 **Hacker News**，可选 Reddit），抽取符合条件的痛点候选，落地为结构化 JSON。

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

根据 config 里 `sources[].type` 选择 helper：

#### Hacker News（默认，推荐）

**无需 API key**，使用 [HN Algolia API](https://hn.algolia.com/api)：

```bash
python3 helpers/fetch_hn.py {pipeline_id} --config {config_path}
```

Helper 会：
- 对每个 `tags`（如 `ask_hn`, `story`, `show_hn`）调用 Algolia `search_by_date`（按时间排序，适合抓近期内容）
- 有 `keywords` 时先服务端 query；若 0 条则拉近期帖子再本地关键词过滤；仍 0 则 WARN 并保留近期 top 帖（避免空跑）
- `date_range` 映射为 `created_at_i` 下限
- 每 tag 抓 `limit_per_source` 条，过滤后保留 `top_per_source`（默认 10）→ `runs/{pid}/_raw/{tag}_top.json`
- 按 config 里 tag **顺序** 去重合并 → `runs/{pid}/_raw/top50.json`
- 单 tag 失败 → 警告 + 继续；**全部失败 → 退出非零**
- **禁止**在抓取失败时复制其他 pipeline 的旧 `_raw` 冒充新数据

**过滤标准**（helper 内建）：
- `points < min_points` 跳过
- 无 title 跳过
- 跨 tag 按 `object_id` 去重

#### Reddit（可选，需 OAuth）

公开 `www.reddit.com/...json` 在云环境/Cursor 会 **403**。必须用 OAuth helper：

**一次性配置**（用户本机）：
1. [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) 创建 **script** 应用（需 Reddit 批准 Data API 访问）
2. 复制 `.env.example` → `.env`，填写 `REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`、`REDDIT_USER_AGENT`
3. `pip install -r requirements.txt`

```bash
python3 helpers/fetch_reddit.py {pipeline_id} --config configs/radar.reddit.example.yaml
```

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
| Reddit 未配置 `.env` / OAuth 失败 | 退出非零，提示创建 script app |
| 所有 tag/subreddit 都失败 | 退出非零，报告原因 |
| 抓取失败 | **禁止**复用其他日期的 `_raw` 数据 |
| `_judgments/stage1.json` 数量与 `top50.json` 不符 | helper 报错 → 检查判断有没有漏 |
| schema 校验失败 | helper 报错指出字段 → 修 stage1.json |

## 当前限制

- 已实现：**Hacker News**、Reddit
- 待实现：GitHub Issues、Product Hunt
- 默认每 tag 取 top 10（3 tags ≈ 30 条）
- 不并发抓取
- 跨 tag 去重（按 object_id）
