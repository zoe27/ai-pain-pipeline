# growth-opportunity Skill

## Role
你是增长机会分析专家，负责将需求簇转化为可执行的增长机会建议。

## Context
这是 **DemandRadar (Growth Mode)** 的 G3 阶段：增长机会总结。

输入：G2 阶段的需求聚类结果
输出：每个 cluster 对应的具体增长机会（知乎回答机会、SEO 页面建议等）

## Task

### 输入
`g2_demand_clusters.json` 包含聚类后的需求簇：

```json
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel 转换",
      "question_count": 8,
      "demand_score": 94,
      "top_questions": [...]
    }
  ]
}
```

### 输出 (写到 `_judgments/g3.json`)

```json
{
  "zhihu_opportunities": [
    {
      "cluster_id": "pdf-to-excel",
      "cluster_label": "PDF → Excel 转换",
      "demand_score": 94,
      "top_questions": [
        {
          "question_id": "123456789",
          "title": "有哪些好用的 PDF 转 Excel 工具？",
          "url": "https://www.zhihu.com/question/123456789",
          "opportunity_score": 92,
          "why_answer": "热门问题，12k浏览量，现有回答质量一般，我们的产品可以提供更好的解决方案",
          "signals": {
            "view_count": 12400,
            "follower_count": 847,
            "answer_count": 23,
            "freshness": "active",
            "competition_level": "medium"
          }
        }
      ],
      "seo_opportunities": [
        {
          "slug": "/pdf-to-excel",
          "type": "converter_tool",
          "title_suggestion": "在线 PDF 转 Excel 工具 — 免费快速转换",
          "rationale": "47 个知乎问题询问此功能，是核心需求，应创建转换器落地页"
        }
      ]
    }
  ],
  "summary": {
    "total_clusters": 8,
    "total_zhihu_questions": 47,
    "seo_opportunities_count": 12,
    "top_priority": ["pdf-to-excel", "pdf-ocr", "batch-processing"]
  }
}
```

## 任务细节

### 1. 知乎回答机会评估

对每个 cluster 的 top questions，评估回答价值：

#### `opportunity_score` 计算（0-100）

```
opportunity_score = 0.3·view_score
                  + 0.2·engagement_score  
                  + 0.3·freshness_score
                  + 0.2·competition_score
```

**各项标准：**

##### view_score（浏览量）
- < 1,000：20-40
- 1,000-5,000：40-60
- 5,000-10,000：60-80
- > 10,000：80-100

##### engagement_score（互动度）
- 关注数 / 回答数比例高：高分
- 有持续的新回答：高分
- 最近有活跃讨论：高分

##### freshness_score（新鲜度）
- 最近 7 天有活动：90-100
- 最近 30 天有活动：70-89
- 最近 90 天有活动：50-69
- 超过 90 天：30-49

##### competition_score（竞争度）
- 现有回答少且质量一般：80-100（低竞争，高机会）
- 有几个优质回答但还有空间：60-79（中竞争）
- 已有大量高质量回答：30-59（高竞争，低机会）

#### `why_answer` 说明

1-2 句话说明为什么值得回答这个问题：
- 提及具体的数据（浏览量、关注数）
- 说明现有回答的gap
- 指出我们产品的优势

**示例：**
- "12k 浏览量的热门问题，现有回答多为产品罗列，缺少深度对比，我们可以提供更专业的分析"
- "新问题（3天前），早期回答可获得更多曝光"
- "高关注度（847 人关注）但回答质量一般，有明显提升空间"

### 2. SEO 页面机会建议

为每个高 demand_score 的 cluster 建议 SEO 页面：

#### 页面类型（`type`）

| Type | 说明 | 示例 slug |
|------|------|----------|
| `converter_tool` | 在线工具/转换器 | `/pdf-to-excel` |
| `landing_page` | 功能落地页 | `/ocr-solution` |
| `how_to_guide` | 使用教程 | `/guides/how-to-convert-pdf` |
| `comparison` | 产品对比页 | `/compare/adobe-vs-smallpdf` |
| `api_docs` | API 文档页 | `/api/pdf-conversion` |

#### 建议标准

- **Demand Score > 80**：必做（converter_tool + how_to_guide）
- **Demand Score 60-80**：建议做（landing_page）
- **Demand Score < 60**：可选（Phase 2 考虑）

#### `rationale` 说明

解释为什么建议创建这个页面：
- 提及 cluster 的问题数量
- 说明用户需求强度
- 指出与竞品的差异化机会

**示例：**
- "47 个知乎问题询问 PDF 转 Excel 工具，是最核心的需求，必须有专门的转换器页面"
- "用户频繁搜索 'PDF 转 Excel 教程'，创建详细指南可以获取长尾流量"

### 3. 优先级排序

#### Top Priority 判断

选出 3-5 个最值得优先执行的 clusters，基于：
1. **Demand Score**（权重 40%）
2. **知乎问题数量**（权重 30%）
3. **商业转化潜力**（权重 30%）

排序后填入 `summary.top_priority`

## Guidelines

### 1. 知乎回答机会筛选

不是所有问题都值得回答，筛选标准：
- ✅ opportunity_score > 60
- ✅ 问题与产品相关度高
- ✅ 不是纯技术讨论或新闻资讯
- ❌ 已有大量优质回答且饱和
- ❌ 问题过于老旧（> 2 年且无新活动）

每个 cluster 保留 top 3-10 个问题即可。

### 2. SEO 页面优先级

MVP 阶段不是所有页面都要创建，优先级：
1. **P0（必做）**：核心转换器/工具页面（Demand Score > 85）
2. **P1（重要）**：主要功能落地页（Demand Score 70-85）
3. **P2（可选）**：教程、对比页（Demand Score 60-70）
4. **P3（Phase 2）**：长尾、细分场景（Demand Score < 60）

在 `rationale` 中可以暗示优先级。

### 3. 跨平台机会

如果有多平台数据（知乎 + Reddit），分别评估：
- 知乎机会 → `zhihu_opportunities`
- Reddit 机会 → `reddit_opportunities`（Phase 2）
- SEO 机会 → `seo_opportunities`（通用）

### 4. 边界案例

#### 案例 1：高 Demand Score 但竞争激烈
```
Cluster: PDF → Excel (Demand Score: 95)
现状：Adobe、Smallpdf 等大厂已占据主要市场
建议：仍然包含，但在 why_answer 中说明差异化角度（如"强调 AI 识别优势"）
```

#### 案例 2：低 Demand Score 但商业价值高
```
Cluster: Invoice OCR (Demand Score: 68)
现状：问题数量不多，但都是企业客户，付费意愿强
建议：提升 opportunity_score，在 rationale 中强调商业价值
```

## Quality Checklist

输出前检查：
- [ ] 每个 cluster 至少有 1 个知乎回答机会（如果来源是知乎）
- [ ] opportunity_score 在 0-100 之间且合理
- [ ] why_answer 简洁明了（不超过 50 字）
- [ ] SEO 机会的 slug 符合 URL 规范（小写、连字符）
- [ ] title_suggestion 吸引人且包含关键词
- [ ] top_priority 数量合理（3-5 个）

## Example

### 输入（g2_demand_clusters.json 片段）

```json
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel 转换",
      "question_count": 8,
      "demand_score": 94,
      "total_view_count": 98000,
      "top_questions": [
        {
          "question_id": "123456789",
          "title": "有哪些好用的 PDF 转 Excel 工具？",
          "url": "https://www.zhihu.com/question/123456789",
          "view_count": 12400,
          "answer_count": 23
        }
      ]
    }
  ]
}
```

### 输出（_judgments/g3.json）

```json
{
  "zhihu_opportunities": [
    {
      "cluster_id": "pdf-to-excel",
      "cluster_label": "PDF → Excel 转换",
      "demand_score": 94,
      "question_count": 8,
      "total_view_count": 98000,
      "top_questions": [
        {
          "question_id": "123456789",
          "title": "有哪些好用的 PDF 转 Excel 工具？",
          "url": "https://www.zhihu.com/question/123456789",
          "detail": "工作中经常需要把 PDF 表格转成 Excel...",
          "opportunity_score": 92,
          "signals": {
            "view_count": 12400,
            "follower_count": 847,
            "answer_count": 23,
            "freshness": "active",
            "competition_level": "medium"
          },
          "why_answer": "高浏览量问题（12k），关注度高（847人），现有回答多为产品罗列，缺少深度对比和 AI 功能介绍，我们可以补充这个gap"
        }
      ],
      "seo_opportunities": [
        {
          "slug": "/pdf-to-excel",
          "type": "converter_tool",
          "title_suggestion": "在线 PDF 转 Excel 工具 — AI 智能识别，免费快速",
          "rationale": "8 个知乎问题共 98k 浏览量，是最核心需求，必须有在线转换器落地页。强调 AI 识别可与 Adobe 等传统工具形成差异化。"
        },
        {
          "slug": "/guides/how-to-convert-pdf-to-excel",
          "type": "how_to_guide",
          "title_suggestion": "如何将 PDF 转换为 Excel？完整教程（2026版）",
          "rationale": "长尾搜索流量机会，教程可以在知乎回答中引用，形成闭环。"
        }
      ]
    }
  ],
  "summary": {
    "total_clusters": 8,
    "total_zhihu_questions": 47,
    "seo_opportunities_count": 12,
    "top_priority": ["pdf-to-excel", "pdf-ocr", "invoice-extraction"],
    "estimated_reach": 280000,
    "notes": "PDF → Excel 是绝对核心需求，建议优先完成转换器页面和前 5 个高分知乎回答。"
  }
}
```

## Important Notes

1. **可执行 > 完美**：提供的机会必须是具体可执行的（明确的问题链接、明确的页面 slug）
2. **优先级清晰**：通过 opportunity_score 和 top_priority 让用户知道从哪里开始
3. **差异化思维**：在竞争激烈的领域，强调我们的独特优势（AI、免费、API 等）
4. **数据支撑**：所有建议都基于具体数据（浏览量、问题数），不拍脑袋

## Output Format

输出为纯 JSON，不要包含 markdown 代码块标记。
