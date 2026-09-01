# DemandRadar 产品定义

## 1. 定位

### 核心价值主张

> **告诉你用户正在寻找什么，并帮你把这些需求变成流量和客户。**

中文：**AI 用户需求捕获与增长引擎**

### 解决的割裂问题

当前增长工作分散在多条线，但本质都在做同一件事——**寻找用户有什么问题，然后满足它**：

```
SEO 团队     → 找关键词 → 写文章 → 做页面
社区运营     → 找帖子   → 发帖   → 跟帖
产品团队     → 看反馈   → 猜需求 → 排优先级
```

DemandRadar 把这些统一为一条流水线：

```
                    用户需求（Intent）
                           ↓
                  ┌────────────────┐
                  │  Demand Engine │
                  └───────┬────────┘
                          ↓
                 AI 识别 / 聚类 / 评分
                          ↓
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
         SEO 页面      社区回复       产品机会
            ↓             ↓             ↓
         Google        Reddit        Product
            └─────────────┼─────────────┘
                          ↓
                        流量
                          ↓
                        转化
                          ↓
                   Outcome Feedback
                          ↓
                   （回到 Demand Engine）
```

---

## 2. 命名

工作名：**DemandRadar**

备选：DemandOS · IntentOS · GrowthRadar · DemandMiner · IntentMiner

偏好 **DemandRadar** 的原因：强调 **持续扫描、发现需求**，而非「帮你写文章」。

---

## 3. 四模块架构

### Module 1 — Demand Discovery

自动发现互联网里的 **需求表达**（不是抱怨）。

**数据源（目标，MVP 子集见 roadmap）：**

| 来源 | 信号类型 |
|------|----------|
| Google 搜索 / Search Console | 搜索 query、长尾词 |
| Reddit | 「Anyone know a good X?」「Best tool for Y?」 |
| Quora / 论坛 | 求推荐、对比帖 |
| Hacker News | Ask HN、工具求推荐 |
| 产品评论（G2/App Store） | 「I wish it could…」「Looking for alternative that…」 |
| YouTube / 社交媒体评论 | 公开需求表达 |

**提取示例：**

输入帖子：「Is there a tool that converts PDF tables to Excel?」

```
Problem:     PDF → Excel
Intent:      寻找工具
Commercial:  High
Frequency:   High
Related:     PDF converter, OCR, table extraction, Excel
```

### Module 2 — Demand Intelligence

不是简单抓帖，而是 **理解帖子代表什么需求**。

1,000 条相关讨论 → AI 聚类：

```
PDF → Excel
├── 普通 PDF
├── 扫描 PDF
├── Invoice → Excel
├── 批量转换
├── 免费工具
└── API
```

**Demand Score**（与 Pain Pipeline 的 ICE / opportunity_score 不同）：

```
Demand Score ≈ Search Volume
             + Community Frequency
             + Commercial Intent
             + Growth Trend
             − Competition
```

输出：**「这是一个正在增长、商业意图高、竞争中等的需求。」**

### Module 3 — Content Generator

发现 demand 后，给出 **可执行建议**（不是自动发布）。

**SEO 机会：**

```
/create/pdf-to-excel          →  Converter 落地页
/create/pdf-to-excel-guide    →  How-to 教程
/create/pdf-to-excel-api      →  API 文档页（若 API 需求明显）
```

**Community 机会：**

```
Reddit 帖: "Anyone know a good PDF to Excel converter?"
→ 生成 Suggested Reply 草稿
→ 用户 Approve → 发布（可选 product mention / link）
```

### Module 4 — Programmatic SEO

Demand Intelligence 与 Programmatic SEO 的连接点：

```
Demand 发现: PDF→Excel, PDF→Word, PDF→CSV, PDF→JSON
维度组合:    免费 / 在线 / API / 批量 / OCR

潜在页面矩阵:
  /pdf-to-excel
  /free/pdf-to-excel
  /api/pdf-to-excel
  /bulk/pdf-to-excel
  /ocr/pdf-to-excel
```

**关键约束：** 不是所有组合都生成——只有 Demand Score 证明 **该组合真有需求** 才进入生成队列。

---

## 4. 用户工作流

### Step 1 — 输入产品

```
We are an AI PDF processing SaaS.
Website: https://example.com
```

### Step 2 — 扫描

```
12,431 search queries
 8,321 Reddit discussions
 2,312 forum threads
```

### Step 3 — 聚类 → Demand Map

```
1. PDF → Excel       Demand: 94
2. PDF OCR           Demand: 89
3. PDF API           Demand: 87
4. Invoice extraction Demand: 83
5. PDF → JSON        Demand: 78
```

### Step 4 — 增长建议

```
SEO Opportunities:      137
Community Opportunities: 82
Product Opportunities:   21
```

### Step 5 — Execute（人审核）

生成 SEO 页面草稿、文章、Reddit 回复、FAQ、内链建议。  
**人只负责审核，不手写内容骨架。**

---

## 5. 产品界面（MVP 设想）

### 首页

```
┌─────────────────────────────────────────┐
│             DemandRadar                 │
│     Discover what your customers want   │
│  [ Enter your website / product URL ]   │
│               [ Analyze ]               │
└─────────────────────────────────────────┘
```

### 分析结果 — Demand Map

```
Your Demand Map

🔥 High Opportunity

1. PDF → Excel          Demand Score: 94
   Search: High | Community: High | Competition: Medium
   [ Create SEO Page ]  [ Find Discussions ]

2. Invoice OCR          Demand Score: 89
   [ Explore ]

3. PDF API              Demand Score: 87
   [ Explore ]
```

设计原则：**Opportunity → Action**，不停留在数据分析。

---

## 6. 护城河

| 层 | 内容 | 壁垒 |
|----|------|------|
| **Demand Dataset** | query → discussion → intent → content → traffic → conversion | 数据飞轮 |
| **Intent Graph** | 需求树状/图状关系（PDF → convert → Excel） | 比关键词库更有结构 |
| **Outcome Feedback** | 哪些 demand 真能赚钱（page → visits → signups → customers） | 闭环机器学习 |

AI 本身易复制；**数据集 + 反馈闭环** 才是长期壁垒。

---

## 7. 商业模式（SaaS）

| 套餐 | 定价 | 能力 |
|------|------|------|
| **Free** | $0 | 1 project · 100 opportunities/月 |
| **Pro** | $49–99/月 | 多项目 · 大量 discovery · SEO/社区机会 · AI drafts |
| **Growth** | $199–499/月 | 大规模监控 · Programmatic SEO · 团队 · API · 自动化 workflow |
| **Enterprise** | 定制 | 大客户 |

---

## 8. 目标用户

| 用户 | 场景 |
|------|------|
| SaaS 创始人 / 独立开发者 | 已有产品，缺增长方向 |
| 增长 / SEO 负责人 | 程序化 SEO + 社区引流统一规划 |
| 内容运营 | 知道「写什么」比「怎么写」更缺 |

**不是** Pain Pipeline 的目标用户（还没确定做什么产品的人）。
