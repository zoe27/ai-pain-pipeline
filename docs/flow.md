# 完整流程图

## 端到端流程（含决策点）

```mermaid
flowchart TD
    subgraph Discovery [发现阶段：AI 全自动]
        S1[1 痛点雷达<br/>Reddit/HN/PH/GitHub Issues]
        S2[2 机会评估<br/>ICE/RICE 评分]
        S3[3 用户研究<br/>画像 + 市场容量]
    end

    D1{🚦 决策点 ①<br/>GO/NO-GO}

    subgraph Design [设计阶段：AI 全自动]
        S4[4 PRD<br/>spec-kit + 验收标准]
        S5[5 架构设计<br/>backend-architect 等]
    end

    D2{🚦 决策点 ②<br/>方案审批}

    subgraph Build [实现阶段：AI 全自动]
        S6[6 编码 + TDD<br/>karpathy + superpowers]
        S7[7 测试 + 自审<br/>code-reviewer]
    end

    D3{🚦 决策点 ③<br/>上线放行}

    subgraph Operate [运营阶段：AI 半自动]
        S8[8 部署 + 监控<br/>devops-automator + sre]
        S9[9 运营 + 商业化<br/>marketing/cro/paid-media]
    end

    D4{🚦 决策点 ④<br/>商业策略}

    S1 --> S2 --> S3 --> D1
    D1 -- GO --> S4 --> S5 --> D2
    D1 -- NO-GO --> Reject[弃置 + 反馈池]
    D2 -- 通过 --> S6 --> S7 --> D3
    D2 -- 修改 --> S4
    D3 -- 通过 --> S8 --> S9 --> D4
    D3 -- 退回 --> S6
    D4 -- 调整 --> S9
    D4 -- 沉淀 --> Loop[反馈数据 → S1]
    Loop -.-> S1
```

## 数据流转视角

```mermaid
flowchart LR
    PP[PainPoint] -->|评分| SPP[ScoredPainPoint]
    SPP -->|研究| OPP[Opportunity]
    OPP -->|🚦①| SO[SelectedOpportunity]
    SO -->|PRD| PRD[PRD]
    PRD -->|设计| TS[TechSpec]
    TS -->|🚦②| AS[ApprovedSpec]
    AS -->|实现| PR[PullRequest]
    PR -->|🚦③| DEP[Deployment]
    DEP -->|运营| LP[LiveProduct]
    LP -->|🚦④| GM[GrowthMetrics]
    GM -.->|回流| PP
```

## 失败/退回路径（重要）

```mermaid
flowchart TD
    Stage[任意 AI 阶段] --> OK{成功?}
    OK -- 是 --> Next[下一阶段]
    OK -- 否 --> Retry{已重试 3 次?}
    Retry -- 否 --> Stage
    Retry -- 是 --> HumanAlert[告警 + 人工介入]
    HumanAlert --> Decide{人决定}
    Decide -- 修复重试 --> Stage
    Decide -- 跳过 --> Skip[标记 skip]
    Decide -- 终止 --> Abort[终止 pipeline]
```

## 并行 vs 串行

| 阶段 | 串/并 | 说明 |
|------|------|------|
| 1 痛点雷达 | 并行 | 多数据源同时抓取 |
| 2 机会评估 | 并行 | 每个痛点独立评分 |
| 3 用户研究 | 串行 | 在选中痛点后顺序进行 |
| 4 PRD | 串行 | 一次一个 |
| 5 架构设计 | 串行 | 依赖 PRD |
| 6 编码 | 并行 | 子任务可派多个 subagent（superpowers/dispatching-parallel-agents） |
| 7 测试 | 并行 | 单元/集成/E2E 可并发 |
| 8 部署 | 串行 | 必须有序 |
| 9 运营 | 并行 | 多渠道同时跑 |

## 时间维度

```
单条 Pipeline 从痛点到上线，目标周期：
   - 简单工具类：2-4 周
   - 中型 SaaS：6-12 周
   - 复杂产品：> 12 周（建议拆分多个 MVP）

每天/每周节奏：
   - 阶段 1（痛点雷达）：每天定时跑，沉淀候选池
   - 阶段 2-3：每周批量处理新候选
   - 决策点 ①：每周一次（你的 review 时间）
   - 阶段 4-7：项目化，按 sprint 跑
   - 决策点 ②③：按需触发
   - 阶段 8-9：持续运行
   - 决策点 ④：每月一次复盘
```
