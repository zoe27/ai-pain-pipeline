# 🎯 如何让整个系统跑起来

## 问题：只有 Dashboard，如何运行完整流程？

Dashboard 只是**查看界面**，要让流程真正运行，需要启动 **Pipeline Orchestrator**。

---

## 🚀 快速方案：两个终端

### 终端 1: 启动 Dashboard (Web UI)

```bash
source .venv/bin/activate
python decision_dashboard.py --port 8080
```

保持运行，访问 http://localhost:8080

### 终端 2: 启动 Orchestrator (执行引擎)

```bash
# 新终端
source .venv/bin/activate
python pipeline_orchestrator.py run
```

这会自动运行 Stage 1-3，然后在决策点 ① 停下等你审批。

---

## 📋 更简单：使用演示脚本

```bash
./run_demo.sh
```

选择 `1` (完整模式)，脚本会指导你如何同时运行两者。

---

## 🎬 三种运行场景

### 场景 A: 体验完整自动化（从零开始）

```bash
# 终端 1
python decision_dashboard.py --port 8080

# 终端 2
python pipeline_orchestrator.py run --pipeline-id pipe_demo_001
```

Orchestrator 会：
1. 运行 Stage 1 (抓取痛点)
2. 提示你在 Claude Code 中运行 `pain-radar` skill
3. 你完成后按 Enter
4. 自动继续 Stage 2, 3
5. 到决策点 ① 时，Dashboard 会显示通知

### 场景 B: 使用已有数据（快速演示）

你已经有 `pipe_2026-06-07_001` 的 Stage 3 数据，可以直接演示 Stage 4：

```bash
# 方式 1: 使用演示脚本
./run_demo.sh
# 选择 4 (演示模式)

# 方式 2: 手动运行
python helpers/build_prd.py pipe_2026-06-07_001
```

### 场景 C: 仅查看状态（不运行新流程）

```bash
# 只启动 Dashboard
python decision_dashboard.py --port 8080

# 查看已有 Pipeline
python pipeline_orchestrator.py status --pipeline-id pipe_2026-06-07_001
```

---

## 🔄 完整流程示意图

```
你的操作                         系统响应
───────────────────────────────────────────────────

1️⃣ 启动 Dashboard
   python decision_dashboard.py
                            ────→  ✅ Web 界面运行
                                   http://localhost:8080
                                   (但没有新 Pipeline)

2️⃣ 新终端启动 Orchestrator
   python pipeline_orchestrator.py run
                            ────→  🤖 开始运行 Stage 1
                                   📡 抓取痛点...
                                   ⏳ 等待 Agent 写 stage1.json

3️⃣ 在 Claude Code 运行 skill
   打开 pain-radar skill
                            ────→  ✍️  Agent 生成 stage1.json
                                   
4️⃣ 回到 Orchestrator 按 Enter
                            ────→  ✅ Stage 1 完成
                                   🤖 自动运行 Stage 2
                                   ⏳ 等待 Agent 写 stage2.json

5️⃣ 重复 Agent 工作
                            ────→  ✅ Stage 2 完成
                                   🤖 自动运行 Stage 3
                                   ⏳ 等待 Agent 写 stage3.json

6️⃣ Stage 3 完成
                            ────→  🚦 到达决策点 ①
                                   📊 Dashboard 显示通知
                                   
7️⃣ 在 Dashboard 点击审批
   [GO] / [WAIT] / [NO-GO]
                            ────→  ✅ 决策已记录
                                   🤖 继续 Stage 4 (如果 GO)
```

---

## 🎯 关键理解

### Dashboard 的作用

- ✅ **查看** Pipeline 进度
- ✅ **审批** 决策点
- ✅ **预览** Digest 文件
- ❌ **不会执行** Pipeline (只是 UI)

### Orchestrator 的作用

- ✅ **执行** 所有 Stage
- ✅ **调用** Helper 脚本
- ✅ **等待** Agent 完成判断
- ✅ **暂停** 在决策点
- ✅ **记录** 状态到 `_state.json`

---

## 💡 为什么需要两个进程？

这是标准的 **前后端分离** 架构：

```
Dashboard (前端)          Orchestrator (后端)
     │                          │
     │◄────────读取状态─────────│
     │                          │
     │─────────审批决策────────►│
     │                          │
     │◄────────更新进度─────────│
```

好处：
- Dashboard 可以关闭，不影响 Pipeline 运行
- 可以同时管理多个 Pipeline
- 多人可以访问同一个 Dashboard

---

## 🔧 故障排查

### Q: Orchestrator 运行但 Dashboard 看不到？

**原因**: Dashboard 需要刷新才能看到新 Pipeline

**解决**:
1. 在 Dashboard 页面刷新 (F5)
2. 或等待 30 秒自动刷新

### Q: Orchestrator 卡住不动？

**原因**: 正在等待 Agent 写 `stageN.json`

**解决**:
1. 检查提示信息
2. 在 Claude Code 中运行对应的 skill
3. 完成后回到 Orchestrator 按 Enter

### Q: 如何停止 Orchestrator？

```bash
Ctrl + C
```

状态会保存到 `_state.json`，下次运行会从断点继续。

---

## 📝 实战示例

### 最小化演示（5 分钟）

```bash
# 1. 终端 1
source .venv/bin/activate
python decision_dashboard.py --port 8080

# 2. 终端 2
source .venv/bin/activate

# 使用已有数据快速演示 Stage 4
python helpers/build_prd.py pipe_2026-06-07_001

# 3. 浏览器
# 访问 http://localhost:8080
# 查看 Dashboard (虽然这个操作不会在 Dashboard 显示，因为我们直接运行了 Helper)

# 4. 查看生成的 PRD
cat runs/pipe_2026-06-07_001/4_prd.json | python -m json.tool
```

### 完整演示（30 分钟）

```bash
# 使用演示脚本
./run_demo.sh

# 选择 1 (完整模式)
# 按照指示操作
```

---

## 🎓 下一步

1. ✅ 理解两个进程的作用
2. ✅ 启动 Dashboard + Orchestrator
3. ✅ 体验完整流程
4. 📖 阅读 `docs/automation.md` 了解更多
5. 🚀 实际使用：定时抓取痛点，自动化分析

---

**记住**: Dashboard 是查看器，Orchestrator 是执行器，两者配合才能完整运行！🚀
