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
| [product-definition.md](./product-definition.md) | 产品定义、四模块、用户工作流、护城河、商业模式 |
| [pain-pipeline-relationship.md](./pain-pipeline-relationship.md) | 与 Stage 0–9 的映射、复用与增量、信号差异 |
| [mvp-roadmap.md](./mvp-roadmap.md) | 三阶段 MVP、Growth Stage 规划、实现清单 |

---

## 产品边界（不是什么）

- ❌ 不是「AI SEO 写文章工具」（核心是 **发现 demand**，不是生成器）
- ❌ 不是「Reddit 自动发帖 bot」（社区动作需 **人工审核**）
- ✅ 是 **需求捕获 → 机会评分 → 可执行增长动作** 的统一引擎

---

## 下一步（本分支）

1. ✅ 需求与架构文档（当前）
2. ⬜ Growth Stage JSON Schema 契约
3. ⬜ `product-focus` skill（产品 URL → 扫描锚点）
4. ⬜ `demand-radar` skill（intent 模式抓取 + 聚类）
5. ⬜ Demand Score + SEO Opportunity 输出
6. ⬜ Demand Map digest / 简单 UI
