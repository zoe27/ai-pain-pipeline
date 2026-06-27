---
name: xiaohongshu
description: 为本项目（AI Pain Pipeline）撰写小红书笔记。先加载 xiaohongshu-specialist 专家能力，再把 pipeline 洞察、产品机会或 builder 故事写成可发帖子。不参与 Stage 0–3。用户要发小红书、写笔记或运行 /xiaohongshu 时使用。
---

# Xiaohongshu — 本项目小红书发帖

## 用途

为 **AI Pain Pipeline** 写小红书笔记：独立开发者 / AI 工具 / SaaS 痛点洞察 / 机会验证故事。  
**不参与**痛点发现 pipeline（不跑 `fetch_radar`、`build_*` 等）。

## 专家技能（必须先读）

执行本 skill 前，读取并遵循：

[`../xiaohongshu-specialist/SKILL.md`](../xiaohongshu-specialist/SKILL.md)

内容标准、平台习惯、KPI、工作流以专家 skill 为准；本文件只补充**本项目语境与素材来源**。

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| `topic` | 是* | 本轮写什么；*若给了 `pipeline_id` 可从 digest 推导 |
| `pipeline_id` | 否 | 只读 `runs/{id}/3_opportunity.digest.zh.md`（或 `.digest.md`）作素材 |
| `angle` | 否 | `builder`（做 pipeline 的人）/ `insight`（某次机会洞察）/ `tutorial`（怎么用 pipeline） |
| `cta` | 否 | 关注 / 收藏 / 私信关键词 / 外链（仓库、waitlist 等） |

## 本项目常见选题

| 角度 | 素材 | 小红书化方向 |
|------|------|----------------|
| **Builder** | 本仓库 README、跑 pipeline 经历 | 「我用 AI 从 HN/差评里挖痛点」「一周跑 3 次 radar 的收获」 |
| **Insight** | `3_opportunity.digest.zh.md` | 把 ClearWave / DevPulse 等写成 SMB 或开发者**避坑帖**（不堆 TAM 数字） |
| **Method** | Stage 0–3 流程 | 「决策点① 之前别写 PRD」「ICE 高≠值得做」干货清单 |
| **Tool** | `pain-radar` / `user-research` skill | 轻教程：怎么用 Cursor skill 跑一轮发现 |

**禁止直接搬运**：`opportunity_score` 公式、英文 schema 字段名、`validate` 术语——改成读者能懂的人话。

## 输出

写入 `content/xiaohongshu/{YYYY-MM-DD}_{slug}/post.md`：

```markdown
# 标题（3 个候选）

## 正文

## 标签

## 封面字（≤20 字）

## 配图建议（1 句话/张）

## 发布备忘（时段 + 首评）
```

可选同目录 `thread.md`：同一机会拆成 2–3 篇连载提纲。

## 步骤

1. **读专家 skill**（见上）
2. **收素材**：用户描述；或 `pipeline_id` → 读 digest 摘 quotes、痛点场景、**一个**核心结论（不写完整商业报告）
3. **定角度**：默认 `insight`；讲仓库本身用 `builder`；教用法用 `tutorial`
4. **按专家规则写帖**：70/20/10 配比、生活方式叙事、2h 内互动等
5. **自检**：无未验证数据当事实、无拉踩具体竞品人身攻击、无「已帮你发布」

## 示例

```
/xiaohongshu pipeline_id=pipe_2026-06-15_003 angle=insight
/xiaohongshu topic=独立开发者用 AI 扫描 SaaS 差评找产品机会 angle=builder
/xiaohongshu topic=ICE 分数高为什么还不值得做 angle=method
```
