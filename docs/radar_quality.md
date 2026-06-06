# Radar 质量衡量

优化爬取质量需要可复现的指标，否则无法判断改动是否有效。

## 核心指标

在固定 **benchmark**（带人工标签的帖子快照）上对比过滤前后：

| 指标 | 公式 | 含义 |
|------|------|------|
| **pain_recall** | 保留的痛点帖 / 全部标注痛点帖 | 不能把真痛点滤掉 |
| **pain_precision** | 保留的痛点帖 / 全部保留帖 | 留下来的应 mostly 是痛点 |
| **product_launch_leak_rate** | 保留的产品发布帖 / 全部保留帖 | Show HN / PH 宣传泄漏率，越低越好 |
| **kept_count** | 过滤后条数 | 太少说明过滤过猛 |

## 成功标准（默认）

见 `benchmarks/*.json` 的 `success_criteria`：

```json
{
  "pain_recall_min": 1.0,
  "pain_precision_min": 0.75,
  "product_launch_leak_max": 0.0,
  "min_kept": 3
}
```

即：**3 条真痛点全部保留，精度 ≥75%，零产品发布泄漏，至少保留 3 条。**

## 如何跑评估

```bash
# 对比 v0.4（无质量层）vs v0.5（质量过滤）
python3 helpers/eval_radar_quality.py \
  --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json

# 对真实 pipeline 产出评估（需有对应 benchmark 标签）
python3 helpers/eval_radar_quality.py \
  --pipeline pipe_2026-06-06_002 \
  --config configs/radar.example.yaml \
  --output runs/pipe_2026-06-06_002/_eval/radar_quality.json
```

退出码 `0` = v0.5 达标；`1` = 未达标。

## v0.5 实现了什么

`configs/radar.example.yaml` → `filters.quality`：

- **硬过滤**：Show HN 产品发布、Product Hunt 发布、求职帖、庆祝帖
- **痛点句式**：`require_pain_signal_for_show_hn`（show_hn 须含抱怨句式）
- **domain_context**：`search_keywords` 追加到各源关键词（领域定向）

实现位于 `helpers/radar_common.py`（`should_drop_quality`, `classify_post`）。

## 如何扩充 benchmark

1. 跑一轮 pipeline，从 `_raw/top50.json` 复制帖子
2. 人工标注每条 `object_id` → `pain_candidate` | `product_launch` | `job_seeking` | `other`
3. 写入 `benchmarks/radar_quality_{pipeline_id}.json`
4. 重跑 `eval_radar_quality.py`，确认 legacy 不达标、quality 达标

## 与 Stage 2 的关系

| 阶段 | 衡量什么 |
|------|----------|
| **eval_radar_quality**（本工具） | 爬取/过滤层：进 pipeline 的帖子是否 mostly 真痛点 |
| **Stage 2 ICE** | 评分层：痛点是否值得做产品 |

优化目标：让 Stage 1 的 `kept_count` 下降、`pain_precision` 上升，从而减少 Stage 2 给 Show HN 产品帖打低分的浪费。

## 参考基线（pipe_2026-06-06_002）

| 版本 | kept | pain_precision | launch_leak | pain_recall |
|------|-----:|---------------:|------------:|------------:|
| v0.4 legacy | 7* | 43% | 43% | 100% |
| v0.5 quality | 4 | 75% | 0% | 100% |

\* benchmark 在相同 keyword/exclude 规则下重放；真实 `pipe_2026-06-06_002` 因 HN/PH fallback 保留了 16 条。

（以 `eval_radar_quality.py` 实际输出为准。）
