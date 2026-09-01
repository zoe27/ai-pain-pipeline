# 🎯 快速参考卡

## ⚡ 一行命令

```bash
./run_demo.sh          # 交互式启动
./setup_and_run.sh     # 一键安装+启动
python test_setup.py   # 测试环境
```

---

## 🚀 标准启动（2 个终端）

### 终端 1: Dashboard
```bash
source .venv/bin/activate
python decision_dashboard.py --port 8080
```

### 终端 2: Orchestrator
```bash
source .venv/bin/activate
python pipeline_orchestrator.py run
```

---

## 📋 常用命令

### Pipeline 管理
```bash
# 查看状态
python pipeline_orchestrator.py status --pipeline-id <pid>

# 审批决策点 ①
python pipeline_orchestrator.py approve \
  --pipeline-id <pid> \
  --decision-point 1 \
  --decision GO

# 指定 Pipeline ID 运行
python pipeline_orchestrator.py run --pipeline-id pipe_demo_001
```

### Helper 脚本
```bash
# Stage 4: 生成 PRD
python helpers/build_prd.py <pid>

# Stage 5: 生成技术规范
python helpers/build_tech_spec.py <pid>

# 生成 Digest
python helpers/digest.py runs/<pid>/N_*.json

# 查看 Pipeline 列表
ls -la runs/
```

### 查看输出
```bash
# 美化 JSON
cat runs/<pid>/4_prd.json | python -m json.tool

# 查看 Digest
cat runs/<pid>/4_prd.digest.md

# 查看状态文件
cat runs/<pid>/_state.json | python -m json.tool
```

---

## 🎯 决策点速查

| # | 名称 | 时机 | 选项 |
|---|------|------|------|
| ① | GO/NO-GO | Stage 3 后 | GO / WAIT / NO-GO |
| ② | 方案审批 | Stage 5 后 | PROCEED / REVISE / CANCEL |
| ③ | 上线放行 | Stage 7 后 | MERGE / REQUEST_CHANGES / BLOCK |
| ④ | 商业策略 | Stage 9 后 | SCALE / OPTIMIZE / SUNSET / PIVOT |

---

## 🔧 故障排查

```bash
# 检查虚拟环境
ls -la .venv/

# 重装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 端口被占用
lsof -i :8080
python decision_dashboard.py --port 8090

# 清理重启
rm runs/<pid>/_state.json
python pipeline_orchestrator.py run --pipeline-id <pid>
```

---

## 📁 文件位置

```
runs/<pid>/
├── _state.json              # Pipeline 状态
├── _judgments/              # Agent 判断
│   ├── stage1.json
│   ├── stage2.json
│   └── stage3.json
├── 1_pain_points.json       # Stage 1 输出
├── 2_scored_pain_points.json # Stage 2 输出
├── 3_opportunity.json       # Stage 3 输出
├── 4_prd.json              # Stage 4 输出
└── 5_tech_spec.json        # Stage 5 输出
```

---

## 🔗 URL

- Dashboard: http://localhost:8080
- GitHub Actions: `.github/workflows/daily-pain-radar.yml`
- Slack Webhook: 配置在 GitHub Secrets

---

## 📚 文档快速导航

| 时间 | 文档 |
|------|------|
| 1 分钟 | 本文件 |
| 5 分钟 | `START_HERE.md` |
| 10 分钟 | `HOW_TO_RUN.md` |
| 30 分钟 | `AUTOMATION_SUMMARY.md` |
| 1 小时 | `docs/automation.md` |

---

## 💡 Pro Tips

1. **先测试再运行**: `python test_setup.py`
2. **使用演示模式**: `./run_demo.sh` 选 4
3. **Dashboard 自动刷新**: 30 秒
4. **状态持久化**: Ctrl+C 后可恢复
5. **多 Pipeline**: 每个 pipeline_id 独立

---

**打印这张卡片，放在手边！** 📌
