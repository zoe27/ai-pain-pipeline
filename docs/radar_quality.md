# Radar 质量衡量

优化爬取质量需要可复现的指标，否则无法判断改动是否有效。

## 核心指标

在固定 **benchmark**（带人工标签的帖子快照）上对比过滤前后：

| 指标 | 公式 | 含义 |
|------|------|------|
| **pain_recall** | 保留的痛点帖 / 全部标注痛点帖 | 不能把真痛点滤掉 |
| **pain_precision** | 保留的痛点帖 / 全部保留帖 | 留下来的应全部是痛点 |
| **product_launch_leak_rate** | 保留的产品发布帖 / 全部保留帖 | Show HN / PH 宣传泄漏率，须为 0 |
| **kept_count** | 过滤后条数 | 太少说明过滤过猛 |

## 成功标准（v0.6）

```json
{
  "pain_recall_min": 1.0,
  "pain_precision_min": 1.0,
  "product_launch_leak_max": 0.0,
  "min_kept": 3
}
```

即：**3 条真痛点全部保留，精度 100%，零产品发布泄漏。**

CI：`.github/workflows/radar-quality.yml` 在相关 PR 上自动跑 benchmark。

## 如何跑评估

```bash
python3 helpers/eval_radar_quality.py \
  --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json
```

退出码 `0` = 达标；`1` = 未达标。

## v0.6 过滤层

| 能力 | 配置 / 代码 |
|------|------------|
| Show HN / PH / 求职 / 庆祝硬过滤 | `filters.quality` |
| ask_hn 业务痛点主题 | `require_business_pain_for_ask_hn` |
| 排除 llm.txt / gopher 等元 Web 讨论 | `drop_off_topic_meta_web` |
| HN 评论共鸣计数 | `fetch_comment_resonance` → `comment_resonance` 字段 |
| 跨帖主题聚类 | `_raw/radar_signals.json` → Stage 2 `market_signals` |
| 领域定向锚点 | `domain_context` + Stage 0 `domain-focus` skill |

## 参考基线（pipe_2026-06-06_002 benchmark）

| 版本 | kept | pain_precision | launch_leak | pain_recall |
|------|-----:|---------------:|------------:|------------:|
| v0.4 legacy | 7* | 43% | 43% | 100% |
| v0.5 quality | 4 | 75% | 0% | 100% |
| **v0.6 quality** | **3** | **100%** | **0%** | **100%** |

\* benchmark 在相同 keyword/exclude 下重放；真实 `_002` 因 fallback 保留了 16 条。

## 如何扩充 benchmark

1. 从 `_raw/top50.json` 复制帖子
2. 标注 `object_id` → `pain_candidate` | `product_launch` | `other`
3. 写入 `benchmarks/radar_quality_{pipeline_id}.json`
4. 重跑 eval，确认 PASS

## 与 Stage 2 的关系

| 工具 / 阶段 | 衡量什么 |
|-------------|----------|
| **eval_radar_quality** | 爬取层精度（进 pipeline 的帖子） |
| **radar_signals.json** | 跨帖主题重复、`comment_resonance` |
| **Stage 2 ICE** | 机会是否值得做（`build_scored_batch` 自动填 `market_signals`） |

## 尚未实现（见 project_thinking.md）

- G2 / Google Play / Twitter 等高信噪比源（**App Store RSS 已接**，见 `fetch_app_store.py`）
- Google Trends 实时 API（**Stage 2 enrich 已接** `market_signals_enrich.py`，非 radar 层）
- HN 评论全文 NLP（当前为短语计数）
