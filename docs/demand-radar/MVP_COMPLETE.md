# DemandRadar MVP 完成 🎉

## 状态

**✅ 代码层面 ~90% 完成**
**⚠️ 产品级可用：还需 E2E 验证**

### 已实现

✅ **生成草稿**：产品输入 → 20+ 知乎回答草稿（需半手动操作）
✅ **人工 Review**：JSON 输出 → 可查看、修改
❌ **一键发布**：未实现（无 UI、无 OAuth、无发布 API）

### 当前工作流

```
半自动：
1. 运行 helpers（G0-G4）
2. 每步需手动运行 Claude Skills 生成 _judgments/*.json
3. 得到 g4_zhihu_answers.json
4. 人工 Review
5. 手动复制粘贴到知乎发布 ← 手动操作
```

### 距离「review 后一键发布」的差距

- ❌ 无 UI（纯命令行）
- ❌ 无知乎账号 OAuth 集成
- ❌ 无知乎发布 API 调用
- ❌ 无发布状态管理（published_at, published_url）
- ⚠️ 未真实跑通完整流程（缺 E2E 测试）

---

## 可以完成

✅ **给某个产品在知乎上生成可人工review的回答草稿**（目标达成）

---

## 不能完成

❌ **Review 后一键发布**（需 Phase 2 功能）

---

## 已实现功能

### G0-G4 完整流水线

```
产品输入
  ↓ G0: 产品锚定
关键词、竞品
  ↓ G1: 知乎信号发现（爬虫 + AI 过滤）
需求信号
  ↓ G2: 需求聚类 + Demand Score
需求簇
  ↓ G3: 增长机会分析
知乎回答机会列表
  ↓ G4: 回答草稿生成
20+ 条可发布的知乎回答
  ↓ 
人工 Review → 复制粘贴到知乎
```

### 核心组件

#### 1. **6 个 JSON Schemas**
- 支持多平台（知乎、Reddit、HN）
- 严格的数据校验
- 清晰的字段定义

#### 2. **5 个 AI Skills**
- `product-focus` — 产品分析与关键词提取
- `demand-radar` — Intent 信号识别
- `demand-cluster` — 需求聚类与评分
- `growth-opportunity` — 增长机会分析
- `zhihu-answer-writer` — 知乎回答撰写

#### 3. **6 个 Helpers**
- `build_product_context.py` — G0 拼装
- `fetch_zhihu.py` — 知乎爬虫
- `build_demand_signals.py` — G1 拼装
- `build_demand_clusters.py` — G2 拼装
- `build_growth_opportunities.py` — G3 拼装
- `build_zhihu_answers.py` — G4 拼装

#### 4. **完整文档**
- 11 份文档（架构、策略、Walkthrough）
- 清晰的使用指南
- 故障排除

---

## 如何使用

### 快速开始

```bash
# 1. 创建 run
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001
mkdir -p runs/$GROWTH/_judgments runs/$GROWTH/_raw

# 2. G0: 产品锚定（需要用 Claude + product-focus skill）
# → 生成 _judgments/g0.json
python3 helpers/build_product_context.py $GROWTH --product-url "YOUR_URL"

# 3. G1: 爬取知乎（自动）+ AI 过滤（需要 Claude）
python3 helpers/fetch_zhihu.py $GROWTH
# → 用 Claude + demand-radar skill 生成 _judgments/g1.json
python3 helpers/build_demand_signals.py $GROWTH

# 4. G2: AI 聚类（需要 Claude）
# → 用 Claude + demand-cluster skill 生成 _judgments/g2.json
python3 helpers/build_demand_clusters.py $GROWTH

# 5. G3: AI 分析机会（需要 Claude）
# → 用 Claude + growth-opportunity skill 生成 _judgments/g3.json
python3 helpers/build_growth_opportunities.py $GROWTH

# 6. G4: AI 生成回答（需要 Claude）
# → 用 Claude + zhihu-answer-writer skill 生成 _judgments/g4.json
python3 helpers/build_zhihu_answers.py $GROWTH

# 7. 查看结果
cat runs/$GROWTH/g4_zhihu_answers.json | jq -r '.zhihu_answers[0].generated_answer.text'
```

### 详细流程

参见：[END_TO_END_WALKTHROUGH.md](./END_TO_END_WALKTHROUGH.md)

---

## 输出示例

### G4 输出：知乎回答草稿

```json
{
  "growth_id": "growth_zhihu_2026-09-01_001",
  "product_title": "AI PDF 处理工具",
  "zhihu_answers": [
    {
      "answer_id": "ans_001",
      "question_title": "有哪些好用的 PDF 转 Excel 工具？",
      "question_url": "https://www.zhihu.com/question/123456789",
      "generated_answer": {
        "text": "推荐几个我用过的工具：\n\n## 1. [产品名]\n\n**优点：**\n- AI 识别准确率高...\n\n**缺点：**\n- 免费版有水印\n\n**适合场景：** 需要高准确率\n\n---\n\n## 2. Adobe Acrobat\n...",
        "word_count": 520
      },
      "opportunity_score": 92,
      "publish_status": "pending"
    }
  ],
  "metadata": {
    "total_answers": 20,
    "by_priority": {
      "urgent": 3,
      "high": 8,
      "medium": 7,
      "low": 2
    },
    "estimated_total_reach": 185000
  }
}
```

### 人工 Review 流程

1. 打开 `runs/$GROWTH/g4_zhihu_answers.json`
2. 逐条查看：
   - `question_title` — 问题标题
   - `question_url` — 知乎问题链接
   - `generated_answer.text` — 生成的回答
   - `opportunity_score` — 机会评分
3. Review 并修改回答（如有需要）
4. 复制粘贴到知乎发布

---

## 限制与后续计划

### MVP 当前限制

**代码层面**：
- ⚠️ 需要每步手动运行 Claude Skills（_judgments/*.json 需人工生成）
- ⚠️ 未做真实 E2E 测试（理论可行，但需验证）
- ⚠️ 爬虫可能遇到知乎反爬限制

**产品层面**：
- ❌ **无一键发布**（手动复制粘贴到知乎）
- ❌ 无 UI（纯命令行 + JSON）
- ❌ 无知乎账号集成
- ❌ 无发布后 metrics 跟踪
- ❌ 无 orchestrator（自动化 AI 调用）

### 达到产品级可用还需

**最小可用（1-2 天）**：
1. 真实数据 E2E 测试一次
2. 创建示例 run（mock 数据）
3. 简化 AI 调用流程（prompt 模板或简单 UI）

**完整可用（Phase 2，1-2 周）**：
1. 知乎账号 OAuth 集成
2. 知乎发布 API 封装
3. Review + 一键发布 UI
4. 发布后 metrics 跟踪
5. Orchestrator 自动化

---

## 技术亮点

### 1. **通用性设计**

从 Day 1 就考虑多平台扩展：
- 统一的 `demand_signal` 格式
- 平台无关的 Skills
- 灵活的 `growth_id` 命名

### 2. **判断与拼装分离**

继承 Pain Pipeline 的核心模式：
```
AI 判断 (_judgments/*.json)
  ↓
Helper 确定性拼装
  ↓
Schema 严格校验
  ↓
结构化输出 (g*.json)
```

### 3. **每片可独立运行**

G0-G4 完全解耦，可以：
- 单独调试某个阶段
- 重新运行某个阶段
- 跳过某些阶段测试

### 4. **高质量 AI Prompts**

5 个 Skills 包含：
- 详细的任务定义
- 丰富的示例
- 边界案例处理
- Quality Checklist

---

## 文件清单

### 总计

- **Contracts**: 6 个
- **Skills**: 5 个
- **Helpers**: 6 个
- **Configs**: 1 个
- **Docs**: 11 个

### 完整列表

```
contracts/
├── product_context.schema.json
├── demand_signal.schema.json
├── zhihu_signal.schema.json
├── demand_cluster.schema.json
├── growth_opportunity.schema.json
└── zhihu_answer_draft.schema.json

.claude/skills/
├── product-focus/SKILL.md
├── demand-radar/SKILL.md
├── demand-cluster/SKILL.md
├── growth-opportunity/SKILL.md
└── zhihu-answer-writer/SKILL.md

helpers/
├── build_product_context.py
├── fetch_zhihu.py
├── build_demand_signals.py
├── build_demand_clusters.py
├── build_growth_opportunities.py
└── build_zhihu_answers.py

configs/
└── radar.zhihu.example.yaml

docs/demand-radar/
├── README.md
├── architecture.md
├── product-definition.md
├── pain-pipeline-relationship.md
├── mvp-roadmap.md
├── ui-and-workflow-details.md
├── zhihu-mvp-strategy.md
├── multi-platform-design.md
├── WALKTHROUGH_G0.md
├── END_TO_END_WALKTHROUGH.md
└── IMPLEMENTATION_STATUS.md
```

---

## 性能预期

### 时间成本

- **首次 run**：50-80 分钟
  - G0: 5 分钟
  - G1: 10-30 分钟（爬虫）
  - G2: 10 分钟
  - G3: 10 分钟
  - G4: 15 分钟

- **后续 runs**：30-40 分钟（熟悉流程）

### 输出规模

- **输入**：1 个产品 + 3-20 个关键词
- **G1 爬取**：30-100 个知乎问题
- **G1 过滤**：15-50 个 Intent 信号
- **G2 聚类**：5-15 个 Demand Clusters
- **G4 输出**：15-30 条知乎回答草稿

---

## 下一步

### 达到 MVP 完全可用（立即）

1. **E2E 真实测试**
   - 用真实产品跑一遍
   - 验证爬虫、AI Skills、输出质量
   - 修复发现的问题

2. **示例 run**
   - 创建 mock 数据
   - 提供完整的参考输出

3. **简化操作**
   - Prompt 模板（方便调用 Skills）
   - 或简单的 CLI 交互界面

### Phase 2 功能（1-2 周）

**核心**：Review 后一键发布
- 知乎账号集成（OAuth）
- 发布 API 封装
- 简单 Web UI
- 发布状态管理

**增强**：
- 自动化 orchestrator
- Reddit、HN 支持
- SEO 页面生成
- Metrics 跟踪

---

## 贡献者

- 架构设计：基于 Pain Pipeline 模式
- 实现：AI-assisted development
- 测试：待补充

---

## License

与主项目保持一致。

