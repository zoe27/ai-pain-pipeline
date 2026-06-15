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

### 1. 选研究对象 + 读商业预填

- 从 stage 2 digest 取 🟢 档（total ≥ 200），或用 `focus` 指定 `pain_point_id`
- **合并同主题**（如 job-search 的 spam + cold-apply 合成一条）
- 读 stage 1 原文提取 **真实 quotes**
- 读 `runs/{pipeline_id}/_raw/commercial_prefill.json`（`build_scored_batch.py` 自动生成）
- 读 `_raw/external_signals.json` + `_raw/pain_clusters.json` 作为 `commercial_assessment` 数据锚点

**Focus 模式**（Stage 0 `domain_context`）：`commercial_prefill.mode=focus`，`known_competitors` 驱动竞品提及；无 Stage 0 时为 `broad` 全市场模式。

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
| `recommendation` | `build` / `validate` / `skip` / `partner`；证据不足但值得继续验证时用 `validate` |
| `confidence` | `high` / `medium` / `low` |
| `research_notes` | 50-2000 字符，风险与下一步建议 |
| `confidence_basis` | 置信度依据：source_count / product_count / cross_run / rationale 等 |
| `evidence_ledger` | 证据账本：每个关键 claim 必须引用真实 pain_point_id 和原话 |
| `unsupported_assumptions` | 尚未被本轮数据证明的假设 |
| `validation_required` | 下一步验证实验和成功标准 |
| `commercial_assessment` | V2 商业判断：迁移成本、替代方案、付费主体、持续性、ROI（见下方） |

### 商业判断（V2 commercial_assessment）

Stage 3 必须填写 `commercial_assessment`，回答「值得做吗？」而不只是「用户在抱怨什么？」。可先读 `_raw/pain_clusters.json` 的 `commercial_hints` 作为初筛参考。

| 维度 | 字段 | 评分指引 |
|------|------|----------|
| 痛点强度 | `pain_score` | 来自 persona pain_intensity 和证据强度 |
| 频率 | `frequency_score` | 每天/每周/每月触发 |
| 迁移意愿 | `switching_willingness` | 10=主动找替代，1=被锁死 |
| 迁移成本 | `switching_cost.score` + 子维度 | 10=极难迁移（记账、邮件） |
| 替代方案 | `workaround_analysis.quality_score` | 10=现有方案已够用（对新产品是坏事） |
| 付费主体 | `buyer_mapping.buyer_exists_score` | 10=明确独立预算，1=用户≠付款人 |
| 持续性 | `persistence.score` | 10=结构性永久，4=平台 bug 可能被修复 |
| 经济影响 | `economic_impact.roi_score` | 量化时间/收入/现金流损失 |
| 竞争 | `competition_score` | 10=红海+强 incumbent |

**Opportunity Score** 由 `build_opportunity.py` 自动计算：

```
Pain × Frequency × ROI × SwitchingWill × Buyer × Persistence ÷ Competition ÷ WorkaroundQuality
```

分级：high ≥ 2000 · medium ≥ 500 · low ≥ 100 · watch < 100。

`recommendation` 应与 tier 对齐：`high→build`，`medium→build|validate`，`low→validate|partner`，`watch→validate|skip|partner`。

### 置信度规则

- `low`：单一来源、少于 3 条证据、无明确切换意愿。
- `medium`：同一来源但多条独立证据，或跨两个产品/社区出现。
- `high`：至少两个来源 + 两个产品/社区 + 明确 WTP、金额损失或切换意愿。
- `validate`：痛点强但证据结构不足以直接 `build` 时使用。单源/单产品主导的机会默认不应给 `build + high`。

### 证据账本格式

`evidence_ledger` 中每条 evidence 的 `pain_point_id` 必须存在于 `2_scored_pain_points.json`，`quote` 必须来自 `1_pain_points.json` 原文或 Stage 2 引用，不能编造。

```json
{
  "confidence_basis": {
    "source_count": 1,
    "product_count": 1,
    "cross_run": true,
    "switch_intent_present": true,
    "wtp_signal_present": true,
    "rationale": "Payment hold appeared across two runs, but evidence is still mostly QuickBooks App Store."
  },
  "evidence_ledger": [
    {
      "claim": "QuickBooks users suffer from update-driven UX churn.",
      "strength": "medium",
      "evidence": [
        {
          "source": "app_store",
          "product": "QuickBooks",
          "pain_point_id": "00000000-0000-0000-0000-000000000000",
          "quote": "This app changes its format nearly every week for no reason."
        }
      ],
      "assumptions": ["Users will switch if migration is easy enough."]
    }
  ],
  "unsupported_assumptions": [
    "Stable UI alone is strong enough to drive paid switching."
  ],
  "validation_required": [
    {
      "experiment": "Interview 20 QuickBooks reviewers who explicitly mention switching.",
      "success_criterion": "At least 5 accept a migration concierge call or paid waitlist.",
      "priority": "high"
    }
  ]
}
```

### 3. 调 helper

```bash
# 若 stage 2 后尚无 commercial_prefill.json：
python3 helpers/build_commercial_prefill.py {pipeline_id}
# focus 指定锚点：
python3 helpers/build_commercial_prefill.py {pipeline_id} --pain-point-id {uuid}

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
  "confidence_basis_rationale_zh": "资金冻结跨两次 run 出现，但证据仍主要来自 QuickBooks App Store。",
  "unsupported_assumptions_zh": ["稳定界面本身足以驱动用户付费迁移。"],
  "validation_required": [
    {
      "experiment_zh": "访谈 20 位明确表示想换工具的 QuickBooks 评论用户",
      "success_criterion_zh": "至少 5 人愿意接受迁移服务访谈或加入付费 waitlist",
      "priority": "high"
    }
  ],
  "evidence_ledger": [
    {
      "claim_zh": "QuickBooks 用户受到更新驱动的界面频改困扰",
      "assumptions_zh": ["如果迁移足够简单，用户会愿意切换。"]
    }
  ],
  "product_hypothesis_zh": "MVP：Gmail 插件识别 LLM 模板推销 + 假职位 URL 检测 + 每周高信号 digest……",
  "research_notes_zh": "合并 ICE #1 与 #2……护城河弱，但 LLM outreach 检测可作为 1 周 MVP 切入点。",
  "commercial_assessment": {
    "switching_cost": { "rationale_zh": "迁移成本中文说明" },
    "workaround_analysis": {
      "current_workarounds_zh": ["用户现有替代方案"],
      "rationale_zh": "替代方案分析"
    },
    "buyer_mapping": {
      "user_zh": "使用者", "beneficiary_zh": "受益者",
      "buyer_zh": "付款人", "champion_zh": "推动者"
    },
    "persistence": { "rationale_zh": "持续性分析" },
    "economic_impact": { "quantification_notes_zh": "经济影响量化" }
  }
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
- `confidence_basis` 和 `evidence_ledger` 是审计字段：能提升可信度，但不能替代真实用户访谈

## 下一步

🚦 **决策点 ①**：人读 digest，决定 GO / NO-GO → 进入 stage 4 PRD。
