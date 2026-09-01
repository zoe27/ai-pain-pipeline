# DemandRadar — 需求捕获与增长引擎

> **状态**：文档阶段（`feat/demand-radar` 分支）  
> **定位**：Pain Pipeline 的 **Growth Mode** 延伸，面向已有产品的 demand → content → traffic → conversion 闭环

---

## 一句话

**DemandRadar** 是一个 AI 驱动的 **Demand Capture Engine**：自动从 Google、Reddit、论坛等渠道发现用户正在表达的需求，并把这些需求转化成 SEO 页面机会、社区回复和产品增长动作。

> 机器找需求，人做决策，AI 做内容，SEO 和社区负责获客。

---

## 与 Pain Pipeline 的关系

| | Pain Pipeline | DemandRadar |
|---|---------------|-------------|
| **阶段** | 0→1 产品发现 | 1→N 增长执行 |
| **问题** | 该做什么新产品？ | 已有产品该怎么获流量？ |
| **信号** | Pain（抱怨、不满） | Intent（搜索、求推荐） |
| **输入** | 领域定向 / broad scan | **产品 URL** 锚定 |
| **产出** | PRD → 代码 → 部署 | Demand Map → SEO/社区内容 → 流量 |

完整关系见 [pain-pipeline-relationship.md](./pain-pipeline-relationship.md)。

---

## 文档索引

| 文档 | 内容 |
|------|------|
| **[architecture.md](./architecture.md)** | **🏗️ 整体架构、G0-G4 流水线、组件设计、数据流、实现顺序** |
| [product-definition.md](./product-definition.md) | 产品定义、四模块、用户工作流、护城河、商业模式 |
| [pain-pipeline-relationship.md](./pain-pipeline-relationship.md) | 与 Stage 0–9 的映射、复用与增量、信号差异 |
| [mvp-roadmap.md](./mvp-roadmap.md) | 三阶段 MVP、Growth Stage 规划、实现清单 |
| [ui-and-workflow-details.md](./ui-and-workflow-details.md) | 输入方式、渠道配置、账号连接、UI 设计、一键发布、数据结构 |
| [zhihu-mvp-strategy.md](./zhihu-mvp-strategy.md) | 知乎最小切入点、爬取策略、回答生成、Phase 1 聚焦 |

---

## 产品边界（不是什么）

- ❌ 不是「AI SEO 写文章工具」（核心是 **发现 demand**，不是生成器）
- ❌ 不是「Reddit 自动发帖 bot」（社区动作需 **人工审核**）
- ✅ 是 **需求捕获 → 机会评分 → 可执行增长动作** 的统一引擎

---

## 一条命令（全自动到 Review）

无需 Cursor Agent，需 `ANTHROPIC_API_KEY` + 本地知乎 Cookie：

```bash
export ANTHROPIC_API_KEY=your-key
pip install -r requirements.txt

python3 growth_orchestrator.py run \
  --product-url https://www.yibelin.com/ \
  --cookies configs/zhihu.cookies.json \
  --open-review
```

产出 `g4_zhihu_answers.json` 与 `answers_for_review.md`，人工在 Dashboard 点发布。

---

## 下一步（本分支）

1. ✅ 需求与架构文档
2. ✅ 知乎 MVP 策略
3. ⬜ Growth Stage JSON Schema 契约（知乎版）
4. ⬜ `product-focus` skill（产品 URL → 扫描锚点）
5. ⬜ `zhihu-demand-radar` skill（知乎 intent 识别 + 聚类）
6. ⬜ `fetch_zhihu.py`（爬虫 + 反爬）
7. ⬜ G4 知乎回答生成 skill
8. ⬜ Demand Score + 知乎回答 Opportunity 输出
9. ⬜ Demand Map digest / 简单 UI
