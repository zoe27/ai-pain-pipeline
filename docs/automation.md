# Pipeline 自动化指南

> 让 AI 自动运行整个流水线，人只在 4 个决策点 review + 审批

## 🎯 自动化架构

```
┌─────────────────────────────────────────────────────────┐
│                GitHub Actions (定时)                     │
│  每天 10:00 自动抓取痛点 → Slack 通知                    │
└─────────────┬───────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────┐
│           Pipeline Orchestrator (主控)                   │
│  自动运行 Stage 0-9，在决策点停止等待人工审批           │
└─────────────┬───────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────┐
│              Decision Dashboard (Web)                   │
│  http://localhost:8080 — 可视化审批界面                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始（5 分钟）

### 1. 安装依赖

```bash
pip install flask markdown
```

### 2. 启动 Decision Dashboard

```bash
python3 decision_dashboard.py --port 8080
```

访问：http://localhost:8080

### 3. 启动 Pipeline

#### 方式 A: 手动启动（推荐第一次使用）

```bash
# 启动新 pipeline
python3 pipeline_orchestrator.py run

# 或指定 pipeline ID
python3 pipeline_orchestrator.py run --pipeline-id pipe_2026-06-15_001
```

#### 方式 B: 定时自动启动（GitHub Actions）

配置 `.github/workflows/daily-pain-radar.yml`，每天自动运行。

需要在 GitHub Secrets 中配置：
- `PRODUCTHUNT_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `SLACK_WEBHOOK_URL`

---

## 📋 完整工作流

### 阶段 1: 发现 (自动 + 1 次决策)

```
[自动] Stage 1: 抓取痛点
  → GitHub Actions 每天 10:00 运行
  → 或手动运行: python3 helpers/fetch_radar.py <pid>
  
[人工] Agent 写 stage1.json
  → 在 Claude Code 中运行 'pain-radar' skill
  → 写 runs/<pid>/_judgments/stage1.json
  
[自动] 拼装 + Digest
  → python3 helpers/build_pain_batch.py <pid>
  → python3 helpers/digest.py runs/<pid>/1_pain_points.json
  
[自动] Stage 2: ICE 评分
  → 同 Stage 1 流程
  
[自动] Stage 3: 用户研究
  → 同 Stage 1 流程
  
🚦 决策点 ①: GO / WAIT / NO-GO
  → Dashboard 显示通知
  → 人审查 3_opportunity.digest.md
  → 点击按钮批准
```

### 阶段 2: 设计 (自动 + 1 次决策)

```
[自动] Stage 4: PRD 撰写
  → Agent 写 stage4.json
  → Helper 拼装 4_prd.json
  
[自动] Stage 5: 技术架构
  → Agent 写 stage5.json
  → Helper 拼装 5_tech_spec.json
  → 初始化 Git repo 骨架
  
🚦 决策点 ②: PROCEED / REVISE / CANCEL
  → Dashboard 显示通知
  → 人审查 PRD + Tech Spec
  → 点击按钮批准
```

### 阶段 3: 实现 (手动 + 1 次决策)

```
[手动] Stage 6-7: 编码 + 测试
  → 开发者在 Git repo 写代码
  → CI/CD 自动运行测试
  → 提交 PR
  
🚦 决策点 ③: MERGE / REQUEST_CHANGES / BLOCK
  → Dashboard 显示通知
  → 人审查 PR + 测试结果
  → 点击按钮批准
```

### 阶段 4: 运营 (半自动 + 1 次决策)

```
[手动] Stage 8: 部署
  → DevOps 部署到 staging
  → 验证健康检查
  → 部署到 production
  
[自动] Stage 9: 运营 + 数据收集
  → 每周自动生成增长报告
  → python3 helpers/build_growth_metrics.py <pid> --period weekly
  
🚦 决策点 ④: SCALE / OPTIMIZE / SUNSET / PIVOT
  → Dashboard 显示通知 (每月)
  → 人审查增长指标
  → 点击按钮批准
```

---

## 🎛️ Pipeline Orchestrator 命令

### 运行 Pipeline

```bash
# 启动新 pipeline (交互式)
python3 pipeline_orchestrator.py run

# 指定 pipeline ID
python3 pipeline_orchestrator.py run --pipeline-id pipe_2026-06-15_001

# 后台持续运行 (未来支持)
python3 pipeline_orchestrator.py run --mode continuous
```

### 审批决策

```bash
# 决策点 ① — GO/NO-GO
python3 pipeline_orchestrator.py approve \
  --pipeline-id pipe_2026-06-15_001 \
  --decision-point 1 \
  --decision GO

# 决策点 ② — 方案审批
python3 pipeline_orchestrator.py approve \
  --pipeline-id pipe_2026-06-15_001 \
  --decision-point 2 \
  --decision PROCEED

# 决策点 ③ — 上线放行
python3 pipeline_orchestrator.py approve \
  --pipeline-id pipe_2026-06-15_001 \
  --decision-point 3 \
  --decision MERGE

# 决策点 ④ — 商业策略
python3 pipeline_orchestrator.py approve \
  --pipeline-id pipe_2026-06-15_001 \
  --decision-point 4 \
  --decision SCALE
```

### 查看状态

```bash
python3 pipeline_orchestrator.py status --pipeline-id pipe_2026-06-15_001
```

---

## 🌐 Decision Dashboard 使用

### 启动 Dashboard

```bash
python3 decision_dashboard.py --port 8080
```

### 功能

1. **Pipeline 列表** — 显示所有活跃的 pipeline
2. **进度可视化** — Stage 0-9 进度条
3. **决策点提醒** — 高亮显示等待审批的 pipeline
4. **一键审批** — 点击按钮即可批准/拒绝
5. **Digest 预览** — 直接查看 Markdown 报告
6. **自动刷新** — 每 30 秒自动刷新

### 截图示例

```
┌────────────────────────────────────────────────────────┐
│  🚀 AI Pain Pipeline Dashboard                        │
├────────────────────────────────────────────────────────┤
│  pipe_2026-06-15_001          🚦 等待决策点 1         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  0  1  2  3  [4] 5  6  7  8  9                        │
│                                                        │
│  🚦 决策点 1: GO/NO-GO                                │
│  请查看: Opportunity Digest                            │
│  [ GO ]  [ WAIT ]  [ NO-GO ]                          │
└────────────────────────────────────────────────────────┘
```

---

## 📅 定时调度（GitHub Actions）

### 配置文件

`.github/workflows/daily-pain-radar.yml` 已配置好，会：

1. **每天 UTC 02:00** (北京时间 10:00) 自动运行
2. 生成新的 `pipeline_id`
3. 运行 `fetch_radar.py` 抓取痛点
4. 上传数据到 Artifact
5. 发送 Slack 通知

### 需要配置的 Secrets

在 GitHub Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 | 获取方式 |
|--------|------|----------|
| `PRODUCTHUNT_TOKEN` | Product Hunt API token | https://api.producthunt.com/v2/oauth/applications |
| `REDDIT_CLIENT_ID` | Reddit OAuth ID | https://www.reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit OAuth secret | 同上 |
| `SLACK_WEBHOOK_URL` | Slack 通知 webhook | https://api.slack.com/messaging/webhooks |

### 手动触发

也可以在 GitHub Actions 页面手动触发 workflow。

---

## 🔔 通知系统

### Slack 通知

当以下事件发生时发送通知：

- ✅ Stage 1 抓取完成
- 🚦 决策点到达（需要人工审批）
- ❌ Stage 失败
- 🎉 Pipeline 完成

### 通知示例

```
🎯 新 Pipeline 已启动
Pipeline ID: pipe_2026-06-15_001
Stage 1 抓取完成 ✅

下一步: 运行 pain-radar skill 生成 stage1.json

[ 查看数据 ]
```

```
🚦 决策点到达
Pipeline ID: pipe_2026-06-15_001
决策点 ①: GO/NO-GO

请审查: runs/pipe_2026-06-15_001/3_opportunity.digest.md

[ 审批 ]  [ 查看详情 ]
```

### Email 通知（可选）

可以配置 Gmail SMTP 发送邮件通知（需要实现）。

---

## 🎯 使用场景

### 场景 A: 每天自动发现痛点

```bash
# 1. 配置 GitHub Actions
# 2. 每天自动运行，无需干预
# 3. Dashboard 中查看新 pipeline
# 4. 在决策点 ① 审批
```

### 场景 B: 专注模式（单个产品）

```bash
# 1. 手动启动特定 pipeline
python3 pipeline_orchestrator.py run --pipeline-id pipe_my_idea_001

# 2. 一次性跑完 Stage 1-3
# 3. 决策点 ① 审批 GO
# 4. 继续跑 Stage 4-9
```

### 场景 C: 批量模式（多个候选）

```bash
# 1. 每天定时抓取
# 2. 积累 10-20 个候选 pipeline
# 3. 每周五集中审批
# 4. 批量 GO 通过的进入 Stage 4
```

---

## 📊 State Machine (状态文件)

每个 pipeline 的状态存储在 `runs/<pid>/_state.json`：

```json
{
  "pipeline_id": "pipe_2026-06-15_001",
  "created_at": "2026-06-15T10:00:00Z",
  "updated_at": "2026-06-15T12:30:00Z",
  "current_stage": 3,
  "stage_status": {
    "1": {
      "status": "complete",
      "completed_at": "2026-06-15T10:30:00Z",
      "output_file": "1_pain_points.json"
    },
    "2": {
      "status": "complete",
      "completed_at": "2026-06-15T11:00:00Z",
      "output_file": "2_scored_pain_points.json"
    },
    "3": {
      "status": "complete",
      "completed_at": "2026-06-15T12:00:00Z",
      "output_file": "3_opportunity.json"
    }
  },
  "decisions": {
    "1": {
      "decision": "GO",
      "reviewer": "web_dashboard",
      "decided_at": "2026-06-15T12:30:00Z"
    }
  },
  "mode": "auto"
}
```

---

## 🔧 故障排查

### Pipeline 卡住了怎么办？

```bash
# 1. 查看状态
python3 pipeline_orchestrator.py status --pipeline-id <pid>

# 2. 检查是否在等待决策
#   → 去 Dashboard 审批

# 3. 检查是否 stage 失败
#   → 查看 _state.json 中的 error

# 4. 手动重跑某个 stage
python3 helpers/build_*.py <pid>
```

### Agent 没有生成 stageN.json？

```bash
# 手动在 Claude Code 中运行对应 skill
# 然后继续 pipeline
```

### Dashboard 无法访问？

```bash
# 检查端口是否被占用
lsof -i :8080

# 换个端口
python3 decision_dashboard.py --port 8090
```

---

## 🚀 高级功能（未来）

### 完全自动化模式

```bash
# Agent 自动写 stageN.json，无需人工触发
python3 pipeline_orchestrator.py run --mode full-auto
```

### 多 pipeline 并行

```bash
# 同时运行 10 个 pipeline
python3 pipeline_orchestrator.py run --mode batch --count 10
```

### Webhook 触发

```bash
# 监听 Slack / GitHub 事件，自动启动 pipeline
python3 webhook_listener.py --port 9000
```

---

## 📚 相关文档

- [README.md](../README.md) — 项目概览
- [STAGE_4_9_QUICK_START.md](../STAGE_4_9_QUICK_START.md) — Stage 4-9 快速上手
- [docs/stage-4-9-overview.md](./stage-4-9-overview.md) — 详细指南

---

**现在就开始自动化你的产品发现流程！** 🎉
