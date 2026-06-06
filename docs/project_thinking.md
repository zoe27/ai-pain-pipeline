# 项目思考：爬取质量与领域定向

## 一、如何提升爬取质量

现在的问题根源是**用平台热度代替痛点强度**，upvotes 高不等于痛点真实。

### 过滤层加强

现有过滤太浅（min_points + 情感标签），可以加：

- **语言模式过滤**：真正的痛点帖通常有特征句式，如「I've tried X, Y, Z but...」「why is it so hard to...」「am I the only one who...」，可以在 prompt 里专门识别
- **排除噪音类型**：Show HN 成功案例、Ask HN 求职帖、产品发布公告，这些虽然有降分规则，但目前是 prompt 级别的，不够稳定，应该做成硬过滤
- **评论质量信号**：一个帖子评论里有多少人说「+1」「same issue」「we had this problem too」，比 upvotes 更能说明痛点的普遍性

### 换更精准的数据源

HN/Reddit 是泛社区，信噪比先天不足。更高质量的来源：

| 来源 | 优势 |
|------|------|
| G2 / Capterra 差评 | 用户写的是真实使用痛点，结构化，可爬 |
| Twitter/X 抱怨帖 | 搜索「[产品名] + sucks/broken/frustrated」，实时且直接 |
| 竞品 GitHub Issues | `label:bug` + `label:enhancement`，用户真实需求 |
| App Store / Play Store 1-2 星评论 | 痛点密度极高，且用户已付钱，需求真实存在 |
| Changelog 评论区 | 用户对新功能的反应里藏着「但我更想要...」 |

### 评分模型引入外部信号

ICE 是 AI 自己估的，没有外部信号校准。可以引入：

- 同一痛点在多个平台同时出现 → 加权
- 帖子发布后 48 小时内评论增速（早期热度比总 upvotes 更真实）
- 该痛点相关关键词的 Google Trends 斜率（上升趋势比绝对值更有价值）

---

## 二、领域定向：通过交互输入锁定目标

### 核心思路

把 pipeline 从「泛用批处理」变成「对话式窄播」，每一轮对话都在缩小范围、提高精度。

### 交互输入的形式

在跑 pipeline 之前，通过对话明确领域锚点：

```
你关注的领域是什么？（如：B2B SaaS、开发者工具、HR Tech）
目标用户是谁？（如：10人以下 startup 的 CTO、独立开发者）
你想验证的假设是什么？（如：小团队部署监控太复杂）
你已经知道的竞品有哪些？（如：Datadog、New Relic）
```

这些输入影响两件事：

1. **爬取关键词**：根据领域自动生成精准搜索词，替换通用的 `saas, startup, frustrated`
2. **ICE 评分权重**：如果用户说「我只关注付费意愿强的」，Impact 的权重就应该高于 Ease

### 对话驱动的探索示例

```
用户：我想做开发者工具，CI/CD 方向

AI：好，我看到这些高频痛点聚类：
    - 构建缓存失效（32 条帖子提到）
    - 多云环境配置漂移（18 条）
    - PR 等待 CI 时间太长（45 条）
    你最感兴趣哪个方向？或者你自己有过这个痛点吗？

用户：第三个我深有感触，但不确定有没有人愿意付钱

AI：我去找付费意愿信号...（查 G2 评论 + 竞品定价）
```

### 实现方案

最小改动是在 `configs/radar.example.yaml` 里加 `domain_context` 字段：

```yaml
domain_context:
  domain: "developer tools / CI-CD"
  target_user: "indie dev, small startup engineering team"
  hypothesis: "CI wait time is a paid problem"
  known_competitors: ["CircleCI", "GitHub Actions"]
```

Stage 1 的 prompt 读这个上下文，Stage 2 的 ICE 评分也用它调整权重，不需要改架构。

更进一步，可以在 Stage 1 之前加一个 **Stage 0：领域对话**，输出就是 `domain_context`，由人和 AI 通过几轮对话共同生成，作为整条 pipeline 的「定向锚」。

```
[0 领域对话] → domain_context.json
    ↓
[1 痛点雷达]（带领域锚点的定向爬取）
    ↓
[2 ICE 评分]（权重由领域上下文调整）
    ↓
...
```

---

## 三、已落地路线图

### v0.5 — 可衡量基线

| 项 | 实现 |
|----|------|
| 硬过滤 Show HN / PH 产品发布 | `filters.quality` |
| 痛点句式（show_hn） | `DEFAULT_PAIN_PHRASES` |
| benchmark + eval | `benchmarks/`, `eval_radar_quality.py` |

### v0.6 — 本轮完成

| 项 | 实现 |
|----|------|
| ask_hn 业务痛点 / 排除元 Web 讨论 | `require_business_pain_for_ask_hn`, `drop_off_topic_meta_web` |
| HN 评论共鸣信号 | `hn_comments.py` → `comment_resonance` |
| 跨帖主题聚类 | `compute_radar_signals.py` → `radar_signals.json` |
| Stage 0 领域对话 | `domain-focus` skill + `build_domain_context.py` |
| Stage 2 外部信号 | `market_signals.comment_resonance` / `theme_mentions` |
| CI 门禁 | `.github/workflows/radar-quality.yml` |
| **成功标准** | pain_precision **100%**, pain_recall 100%, launch_leak 0% |

```bash
python3 helpers/eval_radar_quality.py --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json
```

详见 [`docs/radar_quality.md`](radar_quality.md)。

### 待扩展（非阻塞）

| 项 | 说明 |
|----|------|
| G2 / App Store / Twitter | 高信噪比源，需独立 fetcher |
| Google Trends | Stage 2 enrich |
| HN 定向关键词搜索 | project #4，独立 CLI |
