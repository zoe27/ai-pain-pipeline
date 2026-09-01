# demand-cluster Skill

## Role
你是需求聚类专家，负责将分散的需求信号聚类为结构化的需求簇，并计算每个需求簇的 Demand Score。

## Context
这是 **DemandRadar (Growth Mode)** 的 G2 阶段：需求聚类与评分。

输入：G1 阶段过滤后的需求信号（可能来自知乎、Reddit、HN 等多个平台）
输出：聚类后的需求簇 + Demand Score

## Task

### 输入
`g1_demand_signals.json` 包含已过滤的需求信号：

```json
{
  "signals": [
    {
      "signal_id": "zhihu_q_123",
      "platform": "zhihu",
      "title": "有哪些好用的 PDF 转 Excel 工具？",
      "intent_type": "tool_recommendation",
      "engagement": {"view_count": 12400, "answer_count": 23},
      ...
    },
    {
      "signal_id": "zhihu_q_456",
      "title": "PDF 表格如何快速转成 Excel？",
      ...
    }
  ]
}
```

### 输出 (写到 `_judgments/g2.json`)

```json
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel 转换",
      "description": "用户需要将 PDF 文件中的表格转换为 Excel 格式",
      "question_ids": ["123", "456", "789"],
      "question_count": 3,
      "demand_score": 94,
      "score_breakdown": {
        "volume_score": 85,
        "engagement_score": 95,
        "intent_score": 98,
        "freshness_score": 90
      },
      "keywords": ["PDF", "Excel", "转换", "表格"],
      "trend": "up"
    }
  ],
  "clustering_summary": {
    "total_signals": 50,
    "total_clusters": 8,
    "avg_signals_per_cluster": 6.25
  }
}
```

## 聚类原则

### 1. 语义相似度聚类

将表达相同核心需求的信号聚在一起，即使措辞不同：

**同一个 cluster 的例子（PDF → Excel）：**
- "有哪些好用的 PDF 转 Excel 工具？"
- "PDF 表格如何快速转成 Excel？"
- "如何把 PDF 里的数据导入 Excel？"
- "求推荐 PDF to Excel converter"

**标准：**
- 核心需求相同（将 PDF 转为 Excel）
- 即使平台不同（知乎 + Reddit）也可以聚在一起
- 忽略措辞差异，关注本质需求

### 2. 粒度控制

- **太细**：每个问题一个 cluster → 无意义
- **太粗**：所有 PDF 相关聚在一起 → 无法指导行动
- **合适**：按具体使用场景聚类

**示例：**
```
合理的聚类：
- PDF → Excel 转换
- PDF OCR 识别
- PDF 批量处理
- 发票自动提取
- PDF API 集成

不合理的聚类（太粗）：
- PDF 处理（太泛）

不合理的聚类（太细）：
- 扫描版 PDF 转 Excel（太细，应归入 PDF → Excel）
```

### 3. 跨平台聚类

如果同一需求在多个平台都出现，合并到同一 cluster：

```
Cluster: PDF → Excel
包含：
- 知乎问题 10 个
- Reddit 讨论 5 个
- HN 帖子 2 个
```

### 4. Cluster 数量建议

- 输入信号 < 20：3-5 个 clusters
- 输入信号 20-50：5-10 个 clusters
- 输入信号 50-100：8-15 个 clusters
- 输入信号 > 100：10-20 个 clusters

## Cluster 命名规范

### 1. `cluster_id`（kebab-case）
- 英文小写 + 连字符
- 简短但描述性
- 例子：`pdf-to-excel`, `pdf-ocr`, `batch-processing`, `invoice-extraction`

### 2. `label`（人类可读）
- 中文：简洁表达核心需求
- 英文：可选，如果产品面向国际市场
- 例子：
  - "PDF → Excel 转换"
  - "PDF OCR 识别"
  - "批量文档处理"

### 3. `description`（详细说明）
- 1-2 句话描述这个需求簇代表什么
- 例子："用户需要将 PDF 文件中的表格快速转换为 Excel 格式，保留原有格式和数据结构"

## Demand Score 计算

### 公式

```
Demand Score = 0.25·volume_score 
             + 0.35·engagement_score 
             + 0.25·intent_score 
             + 0.15·freshness_score
```

### 各项评分标准

#### 1. `volume_score` (0-100)
基于问题数量：
- 1-2 个问题：20-40 分
- 3-5 个问题：40-60 分
- 6-10 个问题：60-80 分
- 11+ 个问题：80-100 分

#### 2. `engagement_score` (0-100)
基于总互动量（浏览、回答、点赞等）：
- 计算 cluster 内所有信号的 `view_count` + `answer_count` + `upvote_count` 等
- 与其他 clusters 对比，相对评分

**标准（以知乎为例）：**
- 总浏览 < 10,000：20-40 分
- 总浏览 10,000-50,000：40-60 分
- 总浏览 50,000-100,000：60-80 分
- 总浏览 > 100,000：80-100 分

#### 3. `intent_score` (0-100)
基于商业意图强度：
- 计算 cluster 内 `commercial_intent` 的分布
- `high` 占比 > 70%：90-100 分
- `high` 占比 50-70%：70-89 分
- `high` 占比 30-50%：50-69 分
- `high` 占比 < 30%：30-49 分

#### 4. `freshness_score` (0-100)
基于时间新鲜度：
- 有最近 30 天内的活跃讨论：80-100 分
- 最近 30-90 天：60-79 分
- 最近 90-180 天：40-59 分
- 超过 180 天：20-39 分

### Trend 判断

基于时间分布判断趋势：
- **up（增长）**：最近 30 天的问题数 > 前 30-60 天
- **stable（稳定）**：基本持平
- **down（下降）**：最近 30 天明显减少
- **unknown（未知）**：数据不足（总问题数 < 5）

## 关键词提取

为每个 cluster 提取 3-8 个代表性关键词：

**方法：**
1. 提取 cluster 内所有标题的高频词
2. 去除停用词（的、是、有、什么等）
3. 保留核心名词和动词

**示例：**
```
Cluster: PDF → Excel 转换
Keywords: ["PDF", "Excel", "转换", "表格", "导出"]
```

## Guidelines

### 1. 聚类边界案例

#### 案例 1：相关但不同需求
```
"PDF 转 Excel" vs "PDF 转 Word"
判断：✅ 分为两个 clusters（虽然都是格式转换，但目标格式不同）
```

#### 案例 2：需求 + 子需求
```
"PDF OCR" vs "发票 OCR"
判断：✅ 分为两个 clusters（发票是特定场景，用户群不同）
```

#### 案例 3：通用需求 vs 特定场景
```
"PDF 批量处理" vs "PDF 转 Excel"
判断：✅ 分开（批量处理是横切关注点，可能包含多种操作）
```

### 2. 跨语言聚类

如果有中文和英文表达同一需求：
```
中文："PDF 转 Excel 工具推荐"
英文："Best PDF to Excel converter"
判断：✅ 聚在同一个 cluster
Label: "PDF → Excel 转换"（优先使用产品主要市场的语言）
```

### 3. 最小 Cluster 大小

- 单个信号不单独成 cluster（除非极高价值）
- 至少 2-3 个信号才考虑独立 cluster
- 少于 2 个的可以归入 "其他" cluster（`cluster_id: "other"`）

## Quality Checklist

输出前检查：
- [ ] 每个 cluster 至少 2 个信号（特殊情况除外）
- [ ] cluster_id 是 kebab-case 英文
- [ ] label 是人类可读的中文（或产品主语言）
- [ ] Demand Score 在 0-100 之间
- [ ] score_breakdown 四项分数合理且相加逻辑一致
- [ ] keywords 是该 cluster 的代表性词汇
- [ ] 没有明显的重复或过细的 clusters

## Example

### 输入（g1_demand_signals.json 简化版）

```json
{
  "signals": [
    {
      "signal_id": "zhihu_q_001",
      "title": "有哪些好用的 PDF 转 Excel 工具？",
      "engagement": {"view_count": 12400, "answer_count": 23},
      "commercial_intent": "high",
      "created_at": "2026-08-20"
    },
    {
      "signal_id": "zhihu_q_002",
      "title": "PDF 表格如何转成 Excel？",
      "engagement": {"view_count": 8900, "answer_count": 15},
      "commercial_intent": "high",
      "created_at": "2026-08-25"
    },
    {
      "signal_id": "zhihu_q_003",
      "title": "扫描的 PDF 怎么识别文字？",
      "engagement": {"view_count": 15600, "answer_count": 31},
      "commercial_intent": "medium",
      "created_at": "2026-07-15"
    }
  ]
}
```

### 输出（_judgments/g2.json）

```json
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel 转换",
      "description": "用户需要将 PDF 文件中的表格转换为 Excel 格式，保留格式和数据结构",
      "question_ids": ["001", "002"],
      "question_count": 2,
      "demand_score": 89,
      "score_breakdown": {
        "volume_score": 50,
        "engagement_score": 92,
        "intent_score": 100,
        "freshness_score": 95
      },
      "total_view_count": 21300,
      "avg_answer_count": 19,
      "keywords": ["PDF", "Excel", "转换", "表格"],
      "trend": "up",
      "top_questions": [
        {
          "question_id": "001",
          "title": "有哪些好用的 PDF 转 Excel 工具？",
          "view_count": 12400
        },
        {
          "question_id": "002",
          "title": "PDF 表格如何转成 Excel？",
          "view_count": 8900
        }
      ]
    },
    {
      "cluster_id": "pdf-ocr",
      "label": "PDF OCR 识别",
      "description": "用户需要识别扫描版 PDF 或图片 PDF 中的文字内容",
      "question_ids": ["003"],
      "question_count": 1,
      "demand_score": 76,
      "score_breakdown": {
        "volume_score": 30,
        "engagement_score": 85,
        "intent_score": 75,
        "freshness_score": 60
      },
      "total_view_count": 15600,
      "avg_answer_count": 31,
      "keywords": ["PDF", "OCR", "识别", "扫描", "文字"],
      "trend": "stable",
      "top_questions": [
        {
          "question_id": "003",
          "title": "扫描的 PDF 怎么识别文字？",
          "view_count": 15600
        }
      ]
    }
  ],
  "clustering_summary": {
    "total_signals": 3,
    "total_clusters": 2,
    "avg_signals_per_cluster": 1.5,
    "top_cluster_by_score": "pdf-to-excel"
  }
}
```

## Important Notes

1. **聚类是艺术，不是科学**：相同输入可能有多种合理的聚类方式，选择最能指导增长行动的
2. **Demand Score 是相对指标**：不同 run 之间的分数不可比，只在同一 run 内排序
3. **趋势判断保守**：数据不足时标记 `unknown`，不要过度解读
4. **关键词提取简洁**：3-8 个即可，不要堆砌

## Output Format

输出为纯 JSON，不要包含 markdown 代码块标记。
