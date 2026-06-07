---
name: domain-focus
description: Stage 0 领域对话，产出 domain_context.json 作为 pipeline 定向锚。当用户要收窄扫描范围、设定 ICE 评分优先级、或运行 /domain-focus 时使用。
---

# Domain Focus — 阶段 0 领域定向

## 用途

在跑 pain-radar 之前，通过对话锁定本轮研究的领域锚点，避免泛扫 `saas, startup, frustrated`。

## 输出

`runs/{pipeline_id}/domain_context.json` —— 符合 [`contracts/domain_context.schema.json`](../../../contracts/domain_context.schema.json)。

## 对话收集（Agent）

向用户确认（可一轮或多轮）：

| 字段 | 示例 |
|------|------|
| `domain` | internet SaaS / indie GTM |
| `target_user` | solo founders, bootstrapped SaaS |
| `hypothesis` | 小团队冷启动 outreach 是付费问题（可空） |
| `known_competitors` | Mailwarm, Elentaria |
| `search_keywords` | gtm, cold email, zero customers |
| `ice_priority` | `impact: 1.2` 若用户更看重付费意愿 |
| `notes` | 本轮不关注纯开发者工具 |

写入 `runs/{pipeline_id}/_judgments/stage0.json`：

```json
{
  "domain": "internet SaaS / indie GTM",
  "target_user": "solo founders with live product, zero revenue",
  "hypothesis": "Distribution failure is the bottleneck, not product quality",
  "known_competitors": ["Mailwarm", "Hunter.io"],
  "search_keywords": ["gtm", "cold email", "zero customers"],
  "ice_priority": { "impact": 1.2, "confidence": 1.0, "ease": 1.0 },
  "notes": "Skip infra/devtools Show HN unless business pain explicit"
}
```

## 调 helper

```bash
mkdir -p runs/{pipeline_id}/_judgments
python3 helpers/build_domain_context.py {pipeline_id}
python3 helpers/merge_radar_config.py {pipeline_id} --base configs/radar.example.yaml
```

可选 `--base configs/radar.indie_gtm.example.yaml` 或 `configs/radar.cicd.example.yaml` 作为模板。

## 下游使用

1. **Stage 1**：用合并后的 config 抓取：
   ```bash
   python3 helpers/fetch_radar.py {pipeline_id} --config runs/{pipeline_id}/radar.config.yaml
   ```
2. **Stage 2**：`build_scored_batch.py` 自动读 `domain_context.json` 的 `ice_priority` 缩放 ICE；`market_signals_enrich.py` 填 Trends / 48h 评论
3. **Stage 1 后**：`_raw/radar_signals.json` 的 `multi_post_themes` 与上述信号一起提升 confidence

## 可选

若用户未指定领域，可跳过 Stage 0，使用 `configs/radar.example.yaml` 默认 `domain_context`。
