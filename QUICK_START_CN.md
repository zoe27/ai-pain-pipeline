# ⚡ 5 分钟快速开始（中文）

## 方式 1: 一键启动（推荐）

```bash
./setup_and_run.sh
```

这会：
1. ✅ 自动激活虚拟环境 (`.venv`)
2. ✅ 安装所有依赖
3. ✅ 提供启动选项

---

## 方式 2: 手动启动

### 步骤 1: 激活虚拟环境

```bash
source .venv/bin/activate
```

激活后，终端提示符会变成：
```
(.venv) your-username@machine:~/ai-pain-pipeline$
```

### 步骤 2: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 3: 启动系统

#### 选项 A: 启动 Web Dashboard

```bash
python decision_dashboard.py --port 8080
```

然后在浏览器访问：http://localhost:8080

#### 选项 B: 启动 Pipeline Orchestrator

```bash
python pipeline_orchestrator.py run
```

#### 选项 C: 查看示例 Pipeline 状态

```bash
python pipeline_orchestrator.py status --pipeline-id pipe_2026-06-07_001
```

---

## 方式 3: 测试运行（不启动完整流程）

### 验证安装

```bash
# 激活虚拟环境
source .venv/bin/activate

# 验证 Python 版本
python --version  # 应该是 3.9+

# 验证依赖
pip list | grep -E "flask|markdown|jsonschema"

# 语法检查
python -m py_compile pipeline_orchestrator.py
python -m py_compile decision_dashboard.py

# 查看帮助
python pipeline_orchestrator.py --help
```

### 测试 Helper 脚本

```bash
# 查看已有的 Pipeline
ls -la runs/

# 查看某个 Pipeline 的文件
ls -la runs/pipe_2026-06-07_001/

# 如果已有 Stage 3 数据，可以测试 Stage 4
python helpers/build_prd.py pipe_2026-06-07_001
```

---

## 🎯 完整工作流示例

### 1. 启动 Dashboard (终端 1)

```bash
source .venv/bin/activate
python decision_dashboard.py --port 8080
```

保持这个终端运行。

### 2. 启动 Orchestrator (终端 2)

```bash
# 新终端
source .venv/bin/activate
python pipeline_orchestrator.py run --pipeline-id pipe_demo_001
```

### 3. 在浏览器中审批

访问 http://localhost:8080，你会看到：
- 📊 Pipeline 进度可视化
- 🚦 决策点提醒
- 📄 Digest 文件链接
- 🔘 一键审批按钮

---

## 🔧 常见问题

### Q: 虚拟环境在哪里？
**A**: `.venv` 文件夹在项目根目录，已存在。

### Q: 如何退出虚拟环境？
```bash
deactivate
```

### Q: 如何重新激活？
```bash
source .venv/bin/activate
```

### Q: 依赖安装失败？
```bash
# 更新 pip
pip install --upgrade pip

# 重新安装
pip install -r requirements.txt
```

### Q: 端口 8080 被占用？
```bash
# 使用其他端口
python decision_dashboard.py --port 8090
```

### Q: 找不到 Python 3？
```bash
# 检查 Python 版本
python3 --version

# 或使用 python3 命令
python3 decision_dashboard.py --port 8080
```

---

## 📁 项目结构速览

```
ai-pain-pipeline/
├── .venv/                      ← 虚拟环境 (已存在)
├── pipeline_orchestrator.py    ← 主控引擎
├── decision_dashboard.py       ← Web 审批界面
├── helpers/                    ← 自动化脚本
│   ├── build_prd.py
│   ├── build_tech_spec.py
│   └── ...
├── contracts/                  ← JSON Schema
├── runs/                       ← Pipeline 数据
│   └── pipe_YYYY-MM-DD_NNN/
│       ├── _state.json         ← 状态文件
│       ├── _judgments/         ← Agent 判断
│       └── *.json              ← 输出文件
└── docs/                       ← 文档
    ├── automation.md           ← 自动化详细指南
    └── ...
```

---

## 🎓 学习路径

| 时间 | 内容 | 文件 |
|------|------|------|
| 5 分钟 | 快速开始 | 本文件 |
| 10 分钟 | 自动化概览 | `AUTOMATION_SUMMARY.md` |
| 30 分钟 | 完整自动化指南 | `docs/automation.md` |
| 1 小时 | Stage 4-9 详解 | `docs/stage-4-9-overview.md` |
| 2 小时 | 完整项目理解 | `README.md` + 实际运行 |

---

## 🚀 现在开始

最简单的方式：

```bash
./setup_and_run.sh
```

选择 `1` 启动 Dashboard，或 `2` 启动 Orchestrator。

**开始探索自动化的痛点到产品流程吧！** 🎉

---

## 📚 相关文档

- [AUTOMATION_SUMMARY.md](./AUTOMATION_SUMMARY.md) — 自动化总结
- [docs/automation.md](./docs/automation.md) — 详细指南
- [README.md](./README.md) — 项目总览

---

**提示**: 首次运行建议先查看 Dashboard (选项 1)，熟悉界面后再运行完整 Pipeline (选项 2)。
