# DemandRadar 架构设计（知乎 MVP）

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Growth Pipeline (G0-G4)                   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
         ┌─────────┐    ┌──────────┐    ┌─────────┐
         │ Helpers │    │  Skills  │    │ Configs │
         │  (拼装)  │    │ (判断)   │    │ (配置)  │
         └─────────┘    └──────────┘    └─────────┘
              ↓               ↓               ↓
         确定性逻辑       AI 判断        YAML 配置
              │               │               │
              └───────────────┼───────────────┘
                              ↓
                    ┌──────────────────┐
                    │  JSON Contracts  │
                    │  (Schema 校验)   │
                    └──────────────────┘
                              ↓
                    ┌──────────────────┐
                    │   runs/growth_*  │
                    │  (结构化输出)    │
                    └──────────────────┘
```

**设计原则（继承自 Pain Pipeline）：**
1. **判断与拼装分离**：AI 做判断 → 写 `_judgments/` → Helper 做确定性拼装
2. **结构化优先于智能**：每个阶段都有 JSON Schema 约束
3. **每片可独立运行**：G0-G4 可单独执行和调试
4. **从轻到重**：MVP 是 JSON + Markdown，不做自动发布

---

## 2. Growth Stage 流水线

### 阶段概览

```
G0: 产品锚定         → product_context.json
    ↓
G1: 知乎信号发现     → g1_zhihu_signals.json
    ↓
G2: 需求聚类         → g2_demand_clusters.json
    ↓
G3: 增长机会         → g3_growth_opportunities.json
    ↓
G4: 回答草稿生成     → g4_zhihu_answers.json
    ↓
Digest: 可读总结     → *.digest.md
```

### 详细流程

```
┌─────────────────────────────────────────────────────────────┐
│ G0 — 产品锚定                                               │
├─────────────────────────────────────────────────────────────┤
│ Input:  用户输入（URL/GitHub/描述）                         │
│ Skill:  product-focus                                       │
│ Helper: build_product_context.py                            │
│ Output: product_context.json                                │
│         - product_info (名称、描述、核心功能)               │
│         - scan_config (渠道、关键词)                        │
│         - connected_accounts (可选)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ G1 — 知乎信号发现                                           │
├─────────────────────────────────────────────────────────────┤
│ Step 1: 爬取                                                │
│   fetch_zhihu.py                                            │
│   → runs/growth_*/raw_zhihu_questions.json (原始数据)      │
│                                                             │
│ Step 2: AI 判断 Intent                                      │
│   Skill: zhihu-demand-radar                                 │
│   → _judgments/g1.json (哪些是真实 intent)                 │
│                                                             │
│ Step 3: 拼装                                                │
│   Helper: build_zhihu_signals.py                            │
│   → g1_zhihu_signals.json (结构化信号列表)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ G2 — 需求聚类 + Demand Score                                │
├─────────────────────────────────────────────────────────────┤
│ Skill:  demand-cluster (AI 聚类 + 评分)                    │
│ Helper: build_demand_clusters.py                            │
│ Input:  g1_zhihu_signals.json                               │
│ Output: g2_demand_clusters.json                             │
│         - clusters[] (PDF→Excel, OCR, API...)               │
│         - demand_score (基于频次、view、intent)             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ G3 — 增长机会总结                                           │
├─────────────────────────────────────────────────────────────┤
│ Skill:  growth-opportunity                                  │
│ Helper: build_growth_opportunities.py                       │
│ Input:  g2_demand_clusters.json                             │
│ Output: g3_growth_opportunities.json                        │
│         - zhihu_opportunities[] (回答机会)                  │
│         - seo_opportunities[] (页面建议，Phase 2)           │
│         - priority_ranking                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ G4 — 知乎回答草稿生成                                       │
├─────────────────────────────────────────────────────────────┤
│ Skill:  zhihu-answer-writer                                 │
│ Helper: build_zhihu_answers.py                              │
│ Input:  g3_growth_opportunities.json                        │
│         product_context.json                                │
│ Output: g4_zhihu_answers.json                               │
│         - zhihu_answers[] (完整回答草稿)                    │
│         - 每条包含：原问题、生成回答、metadata              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 目录结构

```
ai-pain-pipeline/
│
├── docs/
│   └── demand-radar/
│       ├── README.md
│       ├── architecture.md                    ← 当前文档
│       ├── product-definition.md
│       ├── pain-pipeline-relationship.md
│       ├── mvp-roadmap.md
│       ├── ui-and-workflow-details.md
│       └── zhihu-mvp-strategy.md
│
├── contracts/
│   ├── product_context.schema.json            ← G0
│   ├── zhihu_signal.schema.json               ← G1
│   ├── demand_cluster.schema.json             ← G2
│   ├── growth_opportunity.schema.json         ← G3
│   └── zhihu_answer_draft.schema.json         ← G4
│
├── .claude/skills/
│   ├── product-focus/
│   │   └── SKILL.md                           ← G0 skill
│   ├── zhihu-demand-radar/
│   │   └── SKILL.md                           ← G1 skill
│   ├── demand-cluster/
│   │   └── SKILL.md                           ← G2 skill
│   ├── growth-opportunity/
│   │   └── SKILL.md                           ← G3 skill
│   └── zhihu-answer-writer/
│       └── SKILL.md                           ← G4 skill
│
├── helpers/
│   ├── fetch_zhihu.py                         ← G1 爬虫
│   ├── build_product_context.py               ← G0 拼装
│   ├── build_zhihu_signals.py                 ← G1 拼装
│   ├── build_demand_clusters.py               ← G2 拼装
│   ├── build_growth_opportunities.py          ← G3 拼装
│   ├── build_zhihu_answers.py                 ← G4 拼装
│   └── digest.py (扩展)                       ← Markdown 生成
│
├── configs/
│   └── radar.zhihu.example.yaml               ← 知乎爬取配置
│
├── runs/
│   └── growth_zhihu_YYYY-MM-DD_NNN/
│       ├── product_context.json               ← G0 输出
│       ├── g1_zhihu_signals.json              ← G1 输出
│       ├── g2_demand_clusters.json            ← G2 输出
│       ├── g3_growth_opportunities.json       ← G3 输出
│       ├── g4_zhihu_answers.json              ← G4 输出
│       ├── g4_zhihu_answers.digest.md         ← 可读总结
│       ├── _raw/
│       │   └── raw_zhihu_questions.json       ← 爬虫原始数据
│       └── _judgments/
│           ├── g0.json                        ← product-focus 判断
│           ├── g1.json                        ← intent 判断
│           ├── g2.json                        ← 聚类判断
│           ├── g3.json                        ← 机会判断
│           └── g4.json                        ← 回答判断
│
└── growth_orchestrator.py                     ← Growth Mode 编排器（新增）
```

---

## 4. 关键组件设计

### 4.1 `fetch_zhihu.py` — 知乎爬虫

**职责：**
- 读取 `product_context.json` 获取关键词
- 爬取知乎相关问题（搜索 + 话题 + 竞品）
- 处理反爬（频率控制、User-Agent 轮换）
- 输出原始 JSON 到 `_raw/`

**关键功能：**

```python
def search_zhihu_questions(keywords: List[str], max_per_keyword: int = 20):
    """通过关键词搜索知乎问题"""
    
def get_topic_questions(topic_id: str, max_count: int = 30):
    """获取话题下的热门问题"""
    
def get_competitor_related(competitor_name: str, max_count: int = 15):
    """获取竞品相关问题"""
    
def parse_question_detail(question_url: str) -> dict:
    """解析单个问题的详细信息"""
```

**反爬策略：**
```python
import time
import random
from fake_useragent import UserAgent

ua = UserAgent()
headers = {'User-Agent': ua.random}
time.sleep(random.uniform(2, 5))  # 随机延迟
```

### 4.2 Skills 设计

#### G0 — `product-focus` Skill

```markdown
# product-focus Skill

你是产品分析专家，负责从产品输入中提取增长锚点。

## 输入
- 产品 URL / GitHub / 描述

## 任务
1. 提取产品核心信息（名称、描述、功能）
2. 识别目标关键词（用于知乎搜索）
3. 识别竞品（用于竞品相关搜索）
4. 给出扫描配置建议

## 输出格式（写到 _judgments/g0.json）
{
  "product_info": {...},
  "target_keywords": [...],
  "competitors": [...],
  "scan_config": {...}
}
```

#### G1 — `zhihu-demand-radar` Skill

```markdown
# zhihu-demand-radar Skill

你是需求信号识别专家，判断知乎问题是否包含真实 Intent。

## Intent 定义
✅ 求推荐：「有哪些好用的...」
✅ 对比选择：「A 和 B 哪个好？」
✅ 替代品：「除了 X 还有什么？」
❌ 抱怨：「X 太烂了」（Pain 模式，跳过）
❌ 技术讨论：「X 的原理是什么？」

## 输入
- 原始知乎问题列表

## 任务
对每个问题判断：
1. 是否包含 Intent？
2. Intent 类型（tool_recommendation / comparison / alternative_seeking）
3. 相关度评分（0-100）
4. 商业意图（low / medium / high）

## 输出格式（写到 _judgments/g1.json）
{
  "filtered_signals": [
    {
      "question_id": "123456789",
      "intent_detected": true,
      "intent_type": "tool_recommendation",
      "relevance_score": 95,
      "commercial_intent": "high",
      "reasoning": "..."
    }
  ]
}
```

#### G2 — `demand-cluster` Skill

```markdown
# demand-cluster Skill

你是需求聚类专家，将分散的知乎问题聚类为核心需求。

## 输入
- g1_zhihu_signals.json（已过滤的信号）

## 任务
1. 聚类相似需求（如「PDF 转 Excel」相关的 N 个问题）
2. 为每个 cluster 计算 Demand Score
3. 识别每个 cluster 的关键词

## Demand Score 计算
Score = w1·问题数量 + w2·总浏览量 + w3·平均商业意图 + w4·时间新鲜度

## 输出格式（写到 _judgments/g2.json）
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel 转换",
      "question_ids": ["123", "456", ...],
      "demand_score": 94,
      "keywords": ["PDF", "Excel", "转换"]
    }
  ]
}
```

#### G4 — `zhihu-answer-writer` Skill

```markdown
# zhihu-answer-writer Skill

你是知乎回答撰写专家，为知乎问题生成高质量回答草稿。

## 知乎内容规范
- 字数：300-800 字
- 结构：清晰小标题 + 对比多个产品
- 风格：专业但不硬广
- 排版：Markdown 格式

## 输入
- 知乎问题详情
- 产品信息（product_context.json）
- 竞品列表

## 任务
生成回答草稿，包括：
1. 推荐 3-5 个工具（自己的产品排第一，但不唯一）
2. 每个工具的优缺点
3. 适用场景建议
4. 避免过度推销

## 输出格式（写到 _judgments/g4.json）
{
  "answers": [
    {
      "question_id": "123456789",
      "generated_answer": {
        "text": "推荐几个我用过的工具：\n\n## 1. [产品名]...",
        "word_count": 520,
        "tone": "professional_helpful"
      }
    }
  ]
}
```

### 4.3 Helper 拼装逻辑

所有 helper 都遵循相同模式：

```python
def main(growth_id: str):
    # 1. 读取上游输出
    input_data = load_json(f"runs/{growth_id}/input.json")
    
    # 2. 调用 Claude Skill（或确定性逻辑）
    judgment = call_skill("skill-name", input_data)
    
    # 3. 校验判断结果
    validate_judgment(judgment)
    
    # 4. 确定性拼装
    output = assemble_output(judgment, input_data)
    
    # 5. Schema 校验
    validate_schema(output, "output.schema.json")
    
    # 6. 写入文件
    save_json(output, f"runs/{growth_id}/output.json")
```

---

## 5. 数据流示例

### G0 → G1 → G2 → G3 → G4

**G0 输出：**
```json
{
  "growth_id": "growth_zhihu_2026-09-01_001",
  "product_info": {
    "name": "AI PDF Processor",
    "description": "AI-powered PDF processing SaaS"
  },
  "target_keywords": ["PDF 转 Excel", "PDF OCR", "PDF 工具"],
  "competitors": ["Adobe Acrobat", "Smallpdf"]
}
```

**G1 输出（30 个问题 → 过滤 → 18 个）：**
```json
{
  "signals": [
    {
      "signal_id": "zhihu_q_123456789",
      "question_id": "123456789",
      "title": "有哪些好用的 PDF 转 Excel 工具？",
      "url": "https://www.zhihu.com/question/123456789",
      "view_count": 12400,
      "answer_count": 23,
      "intent_type": "tool_recommendation",
      "relevance_score": 95,
      "commercial_intent": "high"
    }
  ]
}
```

**G2 输出（18 个问题 → 聚类 → 5 个 clusters）：**
```json
{
  "clusters": [
    {
      "cluster_id": "pdf-to-excel",
      "label": "PDF → Excel",
      "question_count": 8,
      "demand_score": 94,
      "total_views": 98000,
      "question_ids": ["123456789", "234567890", ...]
    }
  ]
}
```

**G4 输出（top 20 问题 → 生成 20 条回答）：**
```json
{
  "zhihu_answers": [
    {
      "answer_id": "ans_001",
      "question_id": "123456789",
      "question_url": "https://www.zhihu.com/question/123456789",
      "generated_answer": {
        "text": "推荐几个我用过的工具：\n\n## 1. [产品名]...",
        "word_count": 520
      },
      "opportunity_score": 87,
      "publish_status": "pending"
    }
  ]
}
```

---

## 6. 运行方式

### 方式 1：逐步运行（调试模式）

```bash
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001

# G0
python3 helpers/build_product_context.py $GROWTH

# G1
python3 helpers/fetch_zhihu.py $GROWTH
python3 helpers/build_zhihu_signals.py $GROWTH

# G2
python3 helpers/build_demand_clusters.py $GROWTH

# G3
python3 helpers/build_growth_opportunities.py $GROWTH

# G4
python3 helpers/build_zhihu_answers.py $GROWTH

# Digest
python3 helpers/digest.py runs/$GROWTH/g4_zhihu_answers.json
```

### 方式 2：一键运行（生产模式）

```bash
# 类似 pipeline_orchestrator.py
python3 growth_orchestrator.py --mode zhihu --product-url https://example.com
```

---

## 7. MVP 实现顺序

### Phase 1A — 基础设施（1-2 天）
1. ✅ 文档（已完成）
2. ⬜ JSON Schema（5 个）
3. ⬜ 目录结构创建
4. ⬜ `fetch_zhihu.py` 基础版（硬编码测试）

### Phase 1B — Skills（2-3 天）
5. ⬜ `product-focus` skill
6. ⬜ `zhihu-demand-radar` skill
7. ⬜ `demand-cluster` skill
8. ⬜ `zhihu-answer-writer` skill

### Phase 1C — Helpers（2-3 天）
9. ⬜ `build_product_context.py`
10. ⬜ `build_zhihu_signals.py`
11. ⬜ `build_demand_clusters.py`
12. ⬜ `build_zhihu_answers.py`
13. ⬜ `digest.py` 扩展

### Phase 1D — 集成测试（1-2 天）
14. ⬜ 端到端跑通第一个 growth run
15. ⬜ 调试 + 优化
16. ⬜ Walkthrough 文档

**总计：6-10 天可完成 MVP**

---

## 8. 与 Pain Pipeline 对比

| 维度 | Pain Pipeline | DemandRadar (Growth) |
|------|--------------|---------------------|
| **输入** | 领域 / 假设 | 产品 URL / 描述 |
| **信号** | Pain（抱怨） | Intent（需求） |
| **渠道** | Reddit/HN/论坛 | 知乎（MVP） |
| **输出** | PRD → 代码 → 部署 | 回答草稿 → 手动发布 |
| **阶段** | 0-9 | G0-G4 |
| **复用** | Radar 基础设施 | ✅ |
| **独立性** | 独立 repo 分支 | 同 repo，`runs/growth_*` |

---

## 9. 开放问题 / 待决定

| # | 问题 | 倾向方案 |
|---|------|---------|
| 1 | 知乎爬虫用什么库？ | requests + BeautifulSoup（轻量） |
| 2 | 是否需要登录知乎？ | MVP 可不登录（搜索接口公开） |
| 3 | `growth_orchestrator.py` 何时实现？ | Phase 1D 再做，先手动跑 |
| 4 | Digest 格式？ | 表格 + 完整回答文本，方便复制 |
| 5 | 是否支持 GitHub 输入？ | Phase 1 支持，读 README |

