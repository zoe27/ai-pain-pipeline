# 知乎 MVP 策略

## 为什么选择知乎作为最小切入点？

### 1. 市场契合度

| 维度 | 知乎优势 |
|------|---------|
| **中文市场** | 国内最大的高质量问答社区，目标用户集中 |
| **Intent 信号明确** | 大量「求推荐」「有什么好用的」类问题 |
| **商业转化路径清晰** | 用户主动寻找工具，购买意愿强 |
| **内容长尾价值** | 知乎内容 SEO 友好，Google/百度收录好 |
| **技术可行性** | 有公开搜索接口，爬取相对容易 |

### 2. 与 Reddit/HN 对比

| | 知乎 | Reddit | HN |
|---|------|--------|-----|
| **语言** | 中文 | 英文 | 英文 |
| **目标市场** | 国内 SaaS | 海外 SaaS | 技术产品 |
| **Intent 信号** | 非常明确（求推荐帖） | 明确 | 中等 |
| **爬取难度** | 中等（需处理反爬） | 容易（有 API） | 容易 |
| **发布门槛** | 需账号权重 | 低 | 低 |
| **MVP 优先级** | **✅ Phase 1** | Phase 2 | Phase 2 |

---

## 知乎 MVP 工作流

### 输入

```yaml
产品: AI PDF 处理 SaaS
URL: https://yourproduct.com
关键词: [PDF 转换, PDF 转 Excel, OCR, PDF 工具]
```

### G1 — 知乎问题发现

**典型 Intent 句式（知乎版）：**

```
✅ 有哪些好用的 [产品类型] 工具？
✅ [需求场景]，求推荐工具
✅ [产品A] 和 [产品B] 哪个好？
✅ [需求] 有什么解决方案？
✅ 如何选择 [产品类型]？
❌ [产品] 为什么这么烂？（pain 模式，跳过）
❌ [产品] 的原理是什么？（技术讨论，跳过）
```

**爬取策略：**

```python
# 1. 关键词搜索
keywords = ["PDF 转 Excel", "PDF 转换工具", "PDF OCR"]
for kw in keywords:
    questions = zhihu_search(kw, type="question", sort="hot")
    
# 2. 话题关注
topics = ["PDF", "办公软件", "效率工具"]
for topic in topics:
    questions = zhihu_topic_questions(topic, sort="hot")

# 3. 竞品相关
competitors = ["Adobe Acrobat", "Smallpdf"]
for comp in competitors:
    questions = zhihu_search(f"{comp} 替代", type="question")
```

**输出示例：**

```json
{
  "zhihu_signals": [
    {
      "signal_id": "zhihu_q_123456789",
      "platform": "zhihu",
      "question_id": "123456789",
      "url": "https://www.zhihu.com/question/123456789",
      "title": "有哪些好用的 PDF 转 Excel 工具？",
      "detail": "工作中经常需要把 PDF 表格转成 Excel，手动复制太麻烦...",
      "created_at": "2026-08-25T10:00:00Z",
      "author": "知乎用户",
      "follower_count": 847,
      "answer_count": 23,
      "view_count": 12400,
      "latest_activity": "2026-08-30T15:30:00Z",
      "topics": ["PDF", "办公软件", "Excel"],
      "intent_detected": true,
      "intent_type": "tool_recommendation",
      "relevance_score": 95,
      "commercial_intent": "high",
      "keywords_matched": ["PDF", "Excel", "工具"]
    }
  ]
}
```

### G2 — 聚类

从 100+ 个问题中聚类出核心需求：

```
1. PDF → Excel 转换      (47 个问题)
2. PDF OCR 识别          (32 个问题)
3. PDF 批量处理          (18 个问题)
4. Invoice 提取          (15 个问题)
5. PDF API 集成          (12 个问题)
```

### G3 — 增长机会

```json
{
  "zhihu_opportunities": [
    {
      "cluster_id": "pdf-to-excel",
      "cluster_label": "PDF → Excel 转换",
      "demand_score": 94,
      "question_count": 47,
      "total_view_count": 580000,
      "avg_answer_count": 18,
      "top_questions": [
        {
          "question_id": "123456789",
          "title": "有哪些好用的 PDF 转 Excel 工具？",
          "opportunity_score": 92,
          "signals": {
            "view_count": 12400,
            "follower_count": 847,
            "freshness": "active",
            "competition_level": "medium"
          }
        }
      ],
      "seo_opportunities": [
        {
          "slug": "/pdf-to-excel",
          "rationale": "知乎高频问题，可引流到产品页"
        }
      ]
    }
  ]
}
```

### G4 — 知乎回答草稿

```json
{
  "answer_id": "ans_001",
  "question_id": "123456789",
  "question_title": "有哪些好用的 PDF 转 Excel 工具？",
  "question_url": "https://www.zhihu.com/question/123456789",
  "generated_answer": {
    "text": "推荐几个我用过的工具：\n\n## 1. [你的产品名称]\n\n**优点：**\n- AI 识别准确率高，特别是复杂表格和合并单元格\n- 支持批量处理，可以一次转换多个文件\n- 免费版额度足够个人使用\n\n**适合场景：** 需要高准确率，或者有批量处理需求\n\n[产品链接]\n\n---\n\n## 2. Adobe Acrobat（付费）\n\n老牌工具，识别率不错，但价格较贵...\n\n## 3. Smallpdf（免费受限）\n\n在线工具，方便快捷，但免费版每小时只能转 2 个文件...\n\n---\n\n**选择建议：**\n\n如果预算有限 → 试试 [你的产品] 或 Smallpdf\n如果要批量处理 → [你的产品] 或 Adobe\n如果只是偶尔用 → Smallpdf 够用\n\n希望有帮助！",
    "word_count": 380,
    "structure": {
      "intro": true,
      "product_comparison": true,
      "recommendation_logic": true,
      "call_to_action": false
    },
    "tone": "professional_helpful",
    "product_mention": {
      "position": "first",
      "style": "comparative",
      "prominence": "balanced"
    }
  },
  "metadata": {
    "opportunity_score": 87,
    "estimated_impact": "medium-high",
    "competition_analysis": {
      "existing_answers": 23,
      "top_answer_upvotes": 340,
      "avg_answer_length": 520,
      "product_mentions": ["Adobe", "WPS", "Smallpdf"]
    },
    "publish_recommendation": {
      "should_publish": true,
      "priority": "high",
      "timing": "ASAP",
      "notes": "热门问题，competition 中等，建议尽快发布"
    }
  }
}
```

---

## 知乎特有考虑

### 1. 反爬策略

```python
# 需要处理的知乎反爬机制
- User-Agent 轮换
- Cookie 管理
- 请求频率控制（建议 2-5 秒/次）
- 可选：使用已登录账号的 Cookie（提高成功率）
```

### 2. 内容质量要求

知乎算法偏好：

| 维度 | 要求 |
|------|------|
| **字数** | 建议 300-800 字（太短会被折叠） |
| **结构** | 清晰的段落 + 小标题 |
| **客观性** | 对比多个产品，不能只推自己 |
| **专业度** | 有理有据，避免硬广 |
| **排版** | Markdown 格式，图文并茂更佳 |

### 3. 账号权重

| 账号等级 | 限制 | 建议 |
|---------|------|------|
| **新账号** | 回答可能被折叠 | Phase 1 用已有账号测试 |
| **低权重** | 链接被限制 | 少放外链，用品牌词引导搜索 |
| **中高权重** | 正常 | 可适当放产品链接 |

---

## MVP 成功标准（知乎版）

| 指标 | 目标 |
|------|------|
| **输入** | 1 个真实 SaaS 产品 URL/描述 |
| **发现** | ≥30 个相关知乎问题 |
| **聚类** | ≥5 个 demand clusters |
| **回答草稿** | ≥20 条高质量回答草稿 |
| **质量** | 人工抽检 top 10 草稿：≥7 条「可直接复制粘贴到知乎」 |
| **工程** | G0–G4 可独立跑通；schema 校验通过 |
| **文档** | 知乎版 walkthrough + 示例 run |

---

## Phase 1 → Phase 2 演进路径

### Phase 1 (MVP)
- ✅ 知乎问题发现
- ✅ 回答草稿生成
- ✅ 手动复制粘贴到知乎

### Phase 2
- 知乎账号连接（Cookie/OAuth）
- 一键发布到知乎
- 回答发布后跟踪（浏览量、点赞、评论）
- 增加 Reddit/HN 渠道

### Phase 3
- 多账号管理（避免单账号被限流）
- 发布时间优化（根据问题活跃时间）
- 自动关注问题动态
- SEO 页面自动生成

---

## 技术栈建议

```python
# 知乎爬虫
import requests
from bs4 import BeautifulSoup

# 或使用现成库
# pip install zhihu-oauth  # 官方 OAuth，但可能受限
# pip install zhihu-api    # 非官方，更灵活

# MVP 推荐：requests + BeautifulSoup + 浏览器模拟
```

---

## 数据结构补充

### `zhihu_signal.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["signal_id", "platform", "question_id", "url", "title"],
  "properties": {
    "signal_id": { "type": "string" },
    "platform": { "const": "zhihu" },
    "question_id": { "type": "string" },
    "url": { "type": "string", "format": "uri" },
    "title": { "type": "string" },
    "detail": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "author": { "type": "string" },
    "follower_count": { "type": "integer" },
    "answer_count": { "type": "integer" },
    "view_count": { "type": "integer" },
    "latest_activity": { "type": "string", "format": "date-time" },
    "topics": { "type": "array", "items": { "type": "string" } },
    "intent_detected": { "type": "boolean" },
    "intent_type": { 
      "type": "string",
      "enum": ["tool_recommendation", "comparison", "how_to", "alternative_seeking"]
    },
    "relevance_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "commercial_intent": { "enum": ["low", "medium", "high"] }
  }
}
```

### `zhihu_answer_draft.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["answer_id", "question_id", "generated_answer"],
  "properties": {
    "answer_id": { "type": "string" },
    "question_id": { "type": "string" },
    "question_title": { "type": "string" },
    "question_url": { "type": "string", "format": "uri" },
    "generated_answer": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": { "type": "string", "minLength": 200 },
        "word_count": { "type": "integer" },
        "tone": { 
          "type": "string",
          "enum": ["professional_helpful", "casual_friendly", "expert_technical"]
        },
        "product_mention": {
          "type": "object",
          "properties": {
            "position": { "enum": ["first", "middle", "last"] },
            "style": { "enum": ["comparative", "standalone", "mention_only"] },
            "prominence": { "enum": ["subtle", "balanced", "prominent"] }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "opportunity_score": { "type": "integer", "minimum": 0, "maximum": 100 },
        "publish_recommendation": {
          "type": "object",
          "properties": {
            "should_publish": { "type": "boolean" },
            "priority": { "enum": ["low", "medium", "high", "urgent"] },
            "notes": { "type": "string" }
          }
        }
      }
    },
    "publish_status": { 
      "enum": ["pending", "published", "failed", "skipped"]
    }
  }
}
```

---

## 下一步

1. ✅ 知乎 MVP 策略文档（当前）
2. ⬜ 实现 `fetch_zhihu.py`（爬虫 + 反爬处理）
3. ⬜ 实现 `zhihu-demand-radar` skill（Intent 判断）
4. ⬜ 实现 G4 回答生成 skill
5. ⬜ 跑通第一个完整 run：`growth_zhihu_2026-09-01_001`

