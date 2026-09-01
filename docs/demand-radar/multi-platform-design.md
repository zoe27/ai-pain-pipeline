# Multi-Platform Design (通用性设计)

## 1. 设计原则

DemandRadar 从 MVP（知乎单渠道）开始，但架构设计考虑未来扩展到多平台（Reddit、HN、Quora、Twitter 等）。

### 核心原则

1. **数据结构平台无关** — Schemas 支持多平台，用 `platform` 字段区分
2. **逻辑分层解耦** — Fetcher（平台特定）、Analyzer（通用）、Assembler（通用）分离
3. **渐进式扩展** — MVP 先做知乎，后续按需增加平台
4. **统一信号格式** — 不同平台的数据归一化为统一的 `demand_signal`

---

## 2. Growth ID 命名规范

```
growth_{platform}_{date}_{seq}
```

### 平台标识

| Platform | Prefix | 示例 |
|----------|--------|------|
| 知乎单渠道 | `zhihu` | `growth_zhihu_2026-09-01_001` |
| Reddit 单渠道 | `reddit` | `growth_reddit_2026-09-01_001` |
| HN 单渠道 | `hn` | `growth_hn_2026-09-01_001` |
| 多渠道混合 | `multi` | `growth_multi_2026-09-01_001` |

### 规则

- MVP 阶段使用 `growth_zhihu_*`
- Phase 2 支持多平台后，可选择：
  - 单独运行每个平台（独立 run）
  - 或使用 `growth_multi_*` 合并多平台数据

---

## 3. Schema 通用性设计

### 3.1 `product_context.schema.json`

**支持多平台扫描源：**

```json
{
  "scan_config": {
    "sources": ["zhihu", "reddit", "hackernews"],  // 可多选
    "date_range": "90_days"
  }
}
```

**支持多平台账号：**

```json
{
  "connected_accounts": {
    "zhihu": {...},
    "reddit": {...},
    "hackernews": {...},
    "twitter": {...}
  }
}
```

### 3.2 `demand_signal.schema.json` (新)

**统一的信号格式，支持所有平台：**

```json
{
  "signal_id": "zhihu_q_123456789",  // 平台前缀
  "platform": "zhihu",               // 平台标识
  "content_type": "question",        // 内容类型
  "platform_id": "123456789",        // 原生 ID
  "url": "https://www.zhihu.com/question/123456789",
  "title": "...",
  "engagement": {
    "follower_count": 847,   // Zhihu followers / Reddit subscribers
    "answer_count": 23,      // Zhihu answers / Reddit comments
    "view_count": 12400,
    "upvote_count": 0,       // Reddit/HN specific
    "comment_count": 23      // Generic
  },
  "intent_detected": true,
  "intent_type": "tool_recommendation",
  "language": "zh"           // 语言标识
}
```

### 3.3 平台映射

| Field | Zhihu | Reddit | HN |
|-------|-------|--------|-----|
| `signal_id` | `zhihu_q_{id}` | `reddit_post_{id}` | `hn_post_{id}` |
| `content_type` | `question` | `post` | `thread` |
| `engagement.follower_count` | 问题关注数 | Subreddit 订阅数 | — |
| `engagement.answer_count` | 回答数 | — | — |
| `engagement.comment_count` | — | 评论数 | 评论数 |
| `engagement.upvote_count` | — | Upvotes | Points |

---

## 4. 代码分层架构

### 4.1 Fetcher Layer（平台特定）

每个平台一个独立的 Fetcher：

```
helpers/
├── fetch_zhihu.py        # 知乎爬虫
├── fetch_reddit.py       # Reddit API (Phase 2)
├── fetch_hn.py           # HN API (Phase 2)
└── fetch_orchestrator.py # 多平台编排器 (Phase 2)
```

**职责：**
- 处理平台特定的 API/爬虫逻辑
- 反爬策略
- 输出原始数据到 `_raw/raw_{platform}_*.json`

### 4.2 Analyzer Layer（通用）

AI Skills 平台无关，只关注 Intent 识别：

```
.claude/skills/
├── product-focus/          # G0 (通用)
├── demand-radar/           # G1 (通用，读取 platform 字段)
├── demand-cluster/         # G2 (通用)
├── growth-opportunity/     # G3 (通用)
└── answer-writer/          # G4 (平台特定提示词)
    ├── zhihu/              # 知乎风格
    ├── reddit/             # Reddit 风格
    └── hn/                 # HN 风格
```

**职责：**
- 判断 Intent（tool_recommendation / comparison / how_to / pain_expression）
- 聚类需求
- 生成回答草稿（根据平台风格调整）

### 4.3 Assembler Layer（通用）

Helpers 拼装逻辑平台无关：

```
helpers/
├── build_product_context.py  # G0 (通用)
├── build_demand_signals.py   # G1 (通用，替代 build_zhihu_signals.py)
├── build_demand_clusters.py  # G2 (通用)
├── build_growth_opportunities.py  # G3 (通用)
└── build_content_drafts.py   # G4 (通用)
```

**职责：**
- 读取 AI 判断
- 确定性拼装
- Schema 校验
- 输出结构化 JSON

---

## 5. Intent 类型通用化

### 5.1 Growth Mode Intent Types

```python
INTENT_TYPES = [
    "tool_recommendation",   # "有哪些好用的 X?" / "What's the best X?"
    "comparison",            # "A vs B" / "A 和 B 哪个好？"
    "how_to",               # "How to..." / "如何..."
    "alternative_seeking",   # "除了 X 还有什么？" / "Alternative to X"
]
```

### 5.2 Pain Pipeline Compatibility

为了与 Pain Pipeline 兼容，`demand_signal.schema.json` 也支持：

```python
INTENT_TYPES += [
    "pain_expression",       # "X sucks" / "X 太烂了"（Pain Pipeline 模式）
]
```

这样同一套基础设施可以：
- **Growth Mode**: 过滤 `intent_type in ["tool_recommendation", "comparison", ...]`
- **Pain Mode**: 过滤 `intent_type == "pain_expression"`

---

## 6. 多平台扩展示例

### Phase 1 (MVP) — 知乎单渠道

```bash
# G0: 产品锚定
scan_config.sources = ["zhihu"]

# G1: 知乎爬取
fetch_zhihu.py → raw_zhihu_questions.json

# G1: Intent 判断（通用 skill）
demand-radar skill → _judgments/g1.json

# G1: 拼装
build_demand_signals.py → g1_demand_signals.json  # 通用格式

# G2-G4: 通用流程
```

### Phase 2 — Reddit 扩展

```bash
# G0: 产品锚定
scan_config.sources = ["zhihu", "reddit"]

# G1: 多平台爬取
fetch_orchestrator.py
  ├── fetch_zhihu.py → raw_zhihu_questions.json
  └── fetch_reddit.py → raw_reddit_posts.json

# G1: Intent 判断（同一个 skill）
demand-radar skill → _judgments/g1.json
  # Skill 读取 platform 字段，自动适配

# G1: 拼装（同一个 helper）
build_demand_signals.py
  # 合并 zhihu + reddit signals
  → g1_demand_signals.json

# G2: 聚类（平台无关）
demand-cluster skill
  # 自动跨平台聚类（如 "PDF to Excel" 同时出现在知乎和 Reddit）
  → g2_demand_clusters.json

# G4: 回答生成（根据平台调整风格）
answer-writer/zhihu skill → 知乎风格回答
answer-writer/reddit skill → Reddit 风格回复
```

### Phase 3 — 完全多渠道

```bash
scan_config.sources = ["zhihu", "reddit", "hackernews", "quora"]
growth_id = "growth_multi_2026-09-01_001"

# 单次 run 获取所有渠道数据
# AI 自动跨平台发现需求
# 根据各平台特点生成内容
```

---

## 7. 实现优先级

| Phase | 平台 | 状态 |
|-------|------|------|
| **Phase 1 (MVP)** | 知乎 | ✅ In Progress |
| **Phase 2A** | Reddit | ⬜ Planned |
| **Phase 2B** | HN | ⬜ Planned |
| **Phase 3** | Quora, Twitter | ⬜ Future |

### MVP 聚焦点

1. ✅ Schemas 已支持多平台（`platform` 字段、统一 engagement）
2. ✅ `growth_id` 支持平台前缀（`zhihu` / `reddit` / `hn` / `multi`）
3. ✅ `demand_signal.schema.json` 通用格式
4. ⬜ 实现知乎全流程（G0-G4）
5. ⬜ 验证通用性（用 Reddit 测试数据模拟）

---

## 8. 代码示例：平台检测

### Helper 中的平台检测

```python
def get_primary_platform(growth_id: str) -> str:
    """从 growth_id 提取平台"""
    # growth_zhihu_2026-09-01_001 → "zhihu"
    # growth_multi_2026-09-01_001 → "multi"
    parts = growth_id.split('_')
    return parts[1] if len(parts) > 1 else "unknown"

def load_fetchers(platforms: List[str]) -> Dict[str, Fetcher]:
    """根据 scan_config.sources 加载对应的 fetcher"""
    fetchers = {}
    for platform in platforms:
        if platform == "zhihu":
            from helpers.fetch_zhihu import ZhihuFetcher
            fetchers['zhihu'] = ZhihuFetcher()
        elif platform == "reddit":
            from helpers.fetch_reddit import RedditFetcher
            fetchers['reddit'] = RedditFetcher()
        # ... 更多平台
    return fetchers
```

### Skill 中的平台适配

```python
# demand-radar skill 伪代码

for signal in raw_signals:
    platform = signal['platform']
    
    # 平台特定的 intent 句式
    if platform == "zhihu":
        intent_patterns = ["有哪些", "推荐", "对比", "替代"]
    elif platform == "reddit":
        intent_patterns = ["best", "recommend", "alternative", "vs"]
    
    # 判断 intent（逻辑通用，句式适配）
    intent_detected = check_intent(signal['title'], intent_patterns)
```

---

## 9. 文件命名规范

### 平台特定文件

```
_raw/
├── raw_zhihu_questions.json       # 知乎原始数据
├── raw_reddit_posts.json          # Reddit 原始数据
└── raw_hn_threads.json            # HN 原始数据
```

### 通用输出文件

```
runs/growth_zhihu_2026-09-01_001/
├── product_context.json              # G0 (通用)
├── g1_demand_signals.json            # G1 (通用，包含 platform 字段)
├── g2_demand_clusters.json           # G2 (通用)
├── g3_growth_opportunities.json      # G3 (通用)
└── g4_content_drafts.json            # G4 (包含多平台草稿)
```

---

## 10. 测试策略

### Phase 1 测试

```bash
# 1. 知乎单平台完整流程
GROWTH=growth_zhihu_2026-09-01_001
# ... 运行 G0-G4

# 2. Schema 通用性验证
# 手动创建 Reddit 格式的 mock 数据
# 验证 schema 可以校验通过
```

### Phase 2 测试

```bash
# 1. Reddit 单平台测试
GROWTH=growth_reddit_2026-09-01_001

# 2. 多平台混合测试
GROWTH=growth_multi_2026-09-01_001
scan_config.sources = ["zhihu", "reddit"]
```

---

## 11. 待办事项（通用性相关）

- [x] Schemas 支持多平台（`platform` 字段）
- [x] `growth_id` 支持平台前缀
- [x] 创建通用 `demand_signal.schema.json`
- [x] `product_context` 支持多 sources
- [ ] 实现 `fetch_orchestrator.py`（多平台调度）
- [ ] 实现 `build_demand_signals.py`（通用版，替代 `build_zhihu_signals.py`）
- [ ] 测试用 Reddit mock 数据验证通用性
- [ ] Phase 2: 实现 `fetch_reddit.py`
- [ ] Phase 2: answer-writer skill 支持多平台风格

