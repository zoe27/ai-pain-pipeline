---
name: score-pain
description: 对 stage 1 (pain-radar) 产出的痛点用 ICE 框架评分，识别真正值得做产品的机会。读 runs/{pipeline_id}/1_pain_points.json，输出 runs/{pipeline_id}/2_scored_pain_points.json，符合 contracts/scored_pain_point.schema.json。当用户要跑 pipeline 阶段 2、做 ICE 评分、或者运行 /score-pain 时使用。
---

# Score Pain — 阶段 2 机会评估

## 用途

读 stage 1 产出的 PainPoint[]，为每条做 ICE 评分（Impact × Confidence × Ease）+ red flags，把"成功庆祝 / 社区分享 / 无产品空间的吐槽"这些假痛点筛掉。

## 输入

| 参数 | 必需 | 默认 | 说明 |
|------|------|------|------|
| `pipeline_id` | 是 | — | 必须指定 stage 1 已跑过的 pipeline |

读 `runs/{pipeline_id}/1_pain_points.json`。可选读 `domain_context.json`（ICE 侧重）与 `_raw/radar_signals.json`（`multi_post_themes` 可支撑 confidence）。

## 输出

`runs/{pipeline_id}/2_scored_pain_points.json` —— helper 严格校验，符合 [`contracts/scored_pain_point.schema.json`](../../../contracts/scored_pain_point.schema.json)。

## ICE 评分定义

| 维度 | 1-10 含义 | 怎么判断 |
|------|----------|---------|
| **Impact** | 解决这个痛苦能带来多大价值？ | 影响人数 × 痛苦严重程度。10 = 深度刚需，付费意愿高；1 = "nice to have" / 没人真的关心 |
| **Confidence** | 我们多确信这是真痛点而不是噪音？ | 多人重复抱怨 + 描述具体 + 没有现成解决方案 → 高；单一抱怨 / 只是吐槽 → 低 |
| **Ease** | 做产品来解决它有多容易？ | 10 = 一个人 1 个月做出 MVP；5 = 3-6 月 + 集成多 API；1 = 需要监管牌照 / 大数据 / 大团队 |
| **total** | I × C × E | 1-1000，**helper 自动计算，你不要手算** |

## ⚠️ 关键判断：不是所有 negative 都是真痛点

**这个 skill 最重要的事**：把假痛点筛掉。常见的假痛点形态（首跑数据归纳）：

| 形态 | 示例 | 怎么处理 |
|------|------|---------|
| 成功庆祝 | "我赚到第一笔 $100"、"卖掉项目 $42K" | Impact=1-2，total<10 |
| 社区分享/求曝光 | "Drop your projects"、"Friday share thread" | Impact=1，total<5 |
| 单纯抱怨/无产品空间 | "founder loneliness"、"burnout" | Impact 可能高，但 **Ease=1-2（产品做不了）**，total<50 |
| 已有强大竞品 | "Stripe 收费贵" → Stripe 已经无敌 | Confidence 高，但 Ease 低 |
| 新闻/段子/吐槽 | "Atlassian 挂了"、"Fraud-as-a-Service 段子" | Impact=2-3，total<30 |
| 纯产品宣传 | "I built X" 帖（描述自己的产品） | 看 X 解决的问题是不是真痛点；否则 Impact=1-2 |
| **纯技术 / 框架 bug** | GitHub issue：`fix enum`、`structured output fails`、lint 规则失效 | **Impact≤4, Ease≤4, total<80**；这是维护面不是产品机会 |
| **开源 DX / 开发者工具细节** | Turbopack 内存、text-splitter PERL enum | 除非能包装成 **面向业务用户的 SaaS**，否则降权 |
| **大科技/infra 新闻** | 能源转型、模型量化 backend | Impact=1-2，非互联网产品痛点 |

**真痛点的特征**：具体 **线上业务场景** + 反复出现 + **非技术人员也会付钱** + 单人/小团队 1-3 月可做出 **互联网产品**（不是给框架提 PR）。

**source 降权指引**（Stage 2 必用）：

| source | 默认处理 |
|--------|----------|
| `hackernews` / `reddit` | 正常 ICE；`ask_hn` 商业问题可高分 |
| `github_issues` | 预设为 **技术维护**；仅当标题/正文明确 **customer/billing/onboarding/pricing/workflow** 且非 bug 模板时才给 Impact≥6 |
| `producthunt` | 区分「展示自家产品」vs「描述行业痛点」 |

## 步骤

### 1. 读输入

- 校验 `runs/{pipeline_id}/1_pain_points.json` 存在，否则报错并提示先跑 pain-radar
- 解析，确认 `count == pain_points.length`

### 2. 对每条 PainPoint 评分

读 `title` + `raw_content`，在心里答 3 个问题：

1. **谁会因为这个问题真的付钱？** → Impact
2. **这是噪音还是反复出现的真问题？** → Confidence
3. **做出 MVP 需要多少工程量？** → Ease

每条产出：
- `impact` (1-10)
- `confidence` (1-10)
- `ease` (1-10)
- `ai_reasoning` （20-500 字符，**解释三个分数怎么来的，引用 post 里的具体内容**）
- `red_flags`（0-10 条，每条 3-80 字符，简短，不想做的理由）

### 3. 写 `_judgments/stage2.json` → 调 helper

把所有判断写到 `runs/{pipeline_id}/_judgments/stage2.json`，**按 `pain_point_id` 关联**（不是按顺序）：

```json
[
  {
    "pain_point_id": "uuid-from-stage-1",
    "impact": 9,
    "confidence": 8,
    "ease": 5,
    "ai_reasoning": "10 年 SEO 业务过去 12 个月流量掉 20%，归因到 Google 把 AI 结果塞前面。是大量类似企业的共同问题，付费意愿高。",
    "red_flags": ["已有 Profound/Athena 等 GEO 工具", "AI 模型变化快需持续追赶"]
  }
]
```

跑 helper：

```bash
python3 helpers/build_scored_batch.py {pipeline_id}
```

Helper 自动做：
- 读 stage 1 输出，按 `id` 关联 judgments（缺判断 → 报错列出哪些 pain_point 没打分）
- 自动算 `total = impact × confidence × ease`
- 设 `market_signals: null`（v0.1 不评估，stage 3 填）
- 严格 jsonschema 校验
- 写 `runs/{pid}/2_scored_pain_points.json`

### 4. 中文翻译 → `_judgments/stage2_i18n.json`（Agent）

按 `pain_point_id` 关联，翻译标题、评分理由、风险点（若 `ai_reasoning` 已是中文，`ai_reasoning_zh` 可润色为更通顺的中文）：

```json
[
  {
    "pain_point_id": "uuid-from-stage-1",
    "title_zh": "请不要向求职者群发推销",
    "ai_reasoning_zh": "失业求职者在 HN 收到 LLM 群发推销，952 赞说明共鸣极强。可做 outreach 检测，但需邮箱集成。",
    "red_flags_zh": ["行为问题难产品化", "Gmail 上游可解决", "付费意愿未验证"]
  }
]
```

```bash
python3 helpers/build_i18n.py {pipeline_id} --stage 2
```

### 5. 生成可读 digest

```bash
python3 helpers/digest.py runs/{pipeline_id}/2_scored_pain_points.json
```

生成 `2_scored_pain_points.digest.md` + **`2_scored_pain_points.digest.zh.md`**。

## 失败处理

| 情况 | 处理 |
|------|------|
| `1_pain_points.json` 不存在 | helper 报错，提示先跑 pain-radar |
| `_judgments/stage2.json` 缺某个 pain_point_id 的判断 | helper 报错列出 missing IDs |
| `ai_reasoning` 长度不在 [20, 500] | helper 报错，扩写或精简后重跑 |
| `red_flags` 单条 > 80 字符或 > 10 条 | helper 报错 |
| 输出文件已存在 | 询问：覆盖 / 改 pipeline_id / 跳过 |

## v0.1 限制

- `market_signals` 不评估，固定 null。stage 3 (user research) 填真实数据
- 不调用外部数据（Google Trends / SimilarWeb / web search）
- 评分依赖 LLM 主观判断，无 ground truth
- 不做去重/聚类：同主题多条会各自打分，后果是 top 10 可能 4 条都是 burnout 类
