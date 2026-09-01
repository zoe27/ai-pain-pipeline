# 🚀 从这里开始

## ⚡ 最快开始（1 条命令）

```bash
./run_demo.sh
```

选择 `1` (完整模式)，脚本会指导你完整运行。

---

## 📖 理解系统架构

整个系统由 **2 个进程** 组成：

```
Dashboard (Web UI)              Orchestrator (执行引擎)
     │                                │
     │  查看进度、审批决策              │  自动运行 Stage、调用脚本
     │                                │
     └────────────共享状态─────────────┘
                (_state.json)
```

**重要**: 只启动 Dashboard 不会运行流程，需要同时启动 Orchestrator！

---

## 🎯 完整启动步骤

### 第一步：激活环境并测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 测试环境（可选但推荐）
python test_setup.py
```

### 第二步：启动 Dashboard（终端 1）

```bash
python decision_dashboard.py --port 8080
```

保持运行，浏览器访问: http://localhost:8080

### 第三步：启动 Orchestrator（终端 2）

```bash
# 打开新终端
source .venv/bin/activate

# 运行 Pipeline
python pipeline_orchestrator.py run
```

现在 Dashboard 会显示 Pipeline 进度！

---

## 🎬 快速演示（使用已有数据）

如果不想等 Agent 生成判断，可以直接演示 Stage 4：

```bash
source .venv/bin/activate

# 生成 PRD（基于已有的 Stage 3 数据）
python helpers/build_prd.py pipe_2026-06-07_001

# 查看结果
cat runs/pipe_2026-06-07_001/4_prd.json | python -m json.tool
```

---

## 第三步：体验自动化

### 如果有示例数据

```bash
# 查看状态
python pipeline_orchestrator.py status --pipeline-id pipe_2026-06-07_001

# 审批决策点 ① (假设在等待)
python pipeline_orchestrator.py approve \
  --pipeline-id pipe_2026-06-07_001 \
  --decision-point 1 \
  --decision GO
```

### 如果没有数据，启动新 Pipeline

```bash
python pipeline_orchestrator.py run --pipeline-id pipe_demo_001
```

---

## 📚 文档导航

| 时间 | 读什么 | 学到什么 |
|------|--------|----------|
| **5 分钟** | [QUICK_START_CN.md](./QUICK_START_CN.md) | 快速启动 |
| **10 分钟** | [AUTOMATION_SUMMARY.md](./AUTOMATION_SUMMARY.md) | 自动化概览 |
| **30 分钟** | [docs/automation.md](./docs/automation.md) | 完整指南 |
| **1 小时** | [docs/stage-4-9-overview.md](./docs/stage-4-9-overview.md) | Stage 4-9 详解 |

---

## 🆘 遇到问题？

### 虚拟环境问题

```bash
# 检查虚拟环境
ls -la .venv/

# 重新创建 (如果损坏)
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 依赖安装问题

```bash
# 更新 pip
pip install --upgrade pip

# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt
```

### 端口被占用

```bash
# 使用其他端口
python decision_dashboard.py --port 8090
```

### Python 版本问题

```bash
# 检查版本 (需要 3.9+)
python --version

# 如果版本太低，使用 python3
python3 --version
```

---

## ✅ 验证清单

- [ ] Python 3.9+ 已安装
- [ ] 虚拟环境 `.venv` 已激活
- [ ] 依赖已安装 (`test_setup.py` 通过)
- [ ] Dashboard 可以访问 (http://localhost:8080)
- [ ] Orchestrator 可以运行

---

## 🎯 下一步

1. ✅ 环境测试通过
2. ✅ Dashboard 启动成功
3. ✅ 体验完整流程
4. 📖 阅读详细文档
5. 🚀 开始实际使用

---

**现在开始吧！** 运行 `./setup_and_run.sh` 🎉
