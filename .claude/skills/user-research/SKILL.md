---
name: user-research
description: 对 stage 2 高分痛点做用户研究，输出 Opportunity 到 runs/{pipeline_id}/3_opportunity.json。当用户要跑 pipeline 阶段 3、做用户研究、或者运行 /user-research 时使用。
---

# User Research — 阶段 3 用户研究

## 用途

读 stage 2 的 🟢 档 ScoredPainPoint，合并同主题条目，产出可进入 PRD 的 Opportunity 包。

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| `pipeline_id` | 是 | stage 1+2 已完成的 pipeline |
| `focus` | 否 | 指定 pain_point_id 或主题；默认取 ICE total ≥ 200 的最高分组 |

读 `runs/{pipeline_id}/2_scored_pain_points.json` + `1_pain_points.json`（取用户原话）。

## 输出

`runs/{pipeline_id}/3_opportunity.json` —— 符合 [`contracts/opportunity.schema.json`](../../../contracts/opportunity.schema.json)。

## 步骤

### 1. 选研究对象

- 从 stage 2 digest 取 🟢 档（total ≥ 200）
- **合并同主题**（如 job-search 的 spam + cold-apply 合成一条）
- 读 stage 1 原文提取 **真实 quotes**

### 2. 研究内容（Agent）

写到 `runs/{pipeline_id}/_judgments/stage3.json`：

| 字段 | 要求 |
|------|------|
| `pain_point_id` | 主锚点 UUID（ICE 最高那条） |
| `related_pain_point_ids` | 合并的其他 UUID（可空数组） |
| `title` | 机会主题名 |
| `one_liner` | 10-200 字符，一句话价值主张 |
| `target_personas` | 1-5 个，含 pain/WTP/规模/quotes |
| `existing_solutions` | 竞品 + 定价 + weaknesses |
| `market_size` | TAM / SAM / SOM（USD 整数，合理估算） |
| `product_hypothesis` | 50-1000 字符，具体 MVP 方向 |
| `recommendation` | `build` / `skip` / `partner` |
| `confidence` | `high` / `medium` / `low` |
| `research_notes` | 50-2000 字符，风险与下一步建议 |

### 3. 调 helper

```bash
python3 helpers/build_opportunity.py {pipeline_id}
```

### 4. 中文翻译 → `_judgments/stage3_i18n.json`（Agent）

与 `stage3.json` 同一机会，翻译所有面向读者的文本字段：

```json
{
  "title_zh": "科技求职信噪比污染",
  "one_liner_zh": "帮认真求职的人过滤 LLM 招聘垃圾和假职位，让每封邮件不再是空欢喜。",
  "target_personas": [
    {
      "name_zh": "被裁的软件工程师（3-10 年经验）",
      "quotes_zh": ["冷投已经没用了，每个职位帖都会被 bot 刷爆", "收件箱里每封邮件都是一丝希望，然后又被碾碎"]
    }
  ],
  "existing_solutions": [
    {
      "name_zh": "LinkedIn Premium",
      "weaknesses_zh": ["收件箱仍被 AI 招聘 spam 淹没", "幽灵职位常见"]
    }
  ],
  "product_hypothesis_zh": "MVP：Gmail 插件识别 LLM 模板推销 + 假职位 URL 检测 + 每周高信号 digest……",
  "research_notes_zh": "合并 ICE #1 与 #2……护城河弱，但 LLM outreach 检测可作为 1 周 MVP 切入点。"
}
```

```bash
python3 helpers/build_i18n.py {pipeline_id} --stage 3
python3 helpers/digest.py runs/{pipeline_id}/3_opportunity.json
```

生成 `3_opportunity.i18n.json` + **`3_opportunity.digest.zh.md`**。

## 失败处理

| 情况 | 处理 |
|------|------|
| stage 2 不存在 | 先跑 score-pain |
| pain_point_id 不在 stage 2 | 修正 stage3.json |
| schema 校验失败 | 按 helper 报错修字段长度/枚举 |

## v0.1 限制

- 不调用外部 API（Google Trends / web search）
- 市场规模为 LLM 估算，stage 3 后人应验证
- 一次只产出一个 Opportunity（多主题需多次跑或人工拆分）

## 下一步

🚦 **决策点 ①**：人读 digest，决定 GO / NO-GO → 进入 stage 4 PRD。
