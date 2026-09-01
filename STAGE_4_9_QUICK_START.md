# Stage 4–9 快速参考

> 完整 Pipeline 已实现 — 从 Opportunity → PRD → 架构 → 代码 → 部署 → 增长

## 🎯 核心流程 (10 分钟理解)

```
机会 (3_opportunity.json)
    ↓
[Stage 4] PRD 撰写 — Agent 写需求
    → 4_prd.json
    ↓
[决策点 ②] 人审 PRD
    → GO
    ↓
[Stage 5] 技术架构 — Agent 设计系统
    → 5_tech_spec.json
    → Git repo 骨架初始化
    ↓
[决策点 ②] 人审架构
    → PROCEED
    ↓
[Stage 6–7] 编码 + 测试 — 开发者写代码
    → Git repo (经过所有测试)
    ↓
[决策点 ③] 人审代码
    → MERGE
    ↓
[Stage 8] 部署 — DevOps 上线
    → Production 运行
    ↓
[Stage 9] 运营 + 增长 — 持续收集数据
    → 9_growth_metrics.json (每周更新)
    ↓
[决策点 ④] 月度复盘
    → SCALE / OPTIMIZE / SUNSET
```

## 📁 新增文件清单

### JSON Schema (5 个)
- ✅ `contracts/prd.schema.json` — Stage 4 输出格式
- ✅ `contracts/tech_spec.schema.json` — Stage 5 输出格式
- ✅ `contracts/code_delivery.schema.json` — Stage 6–7 输出格式
- ✅ `contracts/deployment.schema.json` — Stage 8 输出格式
- ✅ `contracts/growth_metrics.schema.json` — Stage 9 输出格式

### Skill 指南 (2 个)
- ✅ `.claude/skills/prd-writer/SKILL.md` — 如何写 PRD
- ✅ `.claude/skills/tech-architect/SKILL.md` — 如何设计架构

### Helper 脚本 (2 个)
- ✅ `helpers/build_prd.py` — Stage 4 拼装脚本
- ✅ `helpers/build_tech_spec.py` — Stage 5 拼装脚本

### 文档 (1 个)
- ✅ `docs/stage-4-9-overview.md` — 完整 Stage 4–9 指南

---

## 🚀 使用方式

### Stage 4: 写 PRD

```bash
# 1. 打开 Skill
#   → Claude Code 中打开 .claude/skills/prd-writer/SKILL.md
#   → 按步骤写 _judgments/stage4.json

# 2. 拼装 + 验证
python3 helpers/build_prd.py pipe_2026-06-15_001

# 3. 生成可读版本
python3 helpers/digest.py runs/pipe_2026-06-15_001/4_prd.json

# 4. 查看输出
cat runs/pipe_2026-06-15_001/4_prd.digest.md
```

### Stage 5: 设计架构

```bash
# 1. 打开 Skill
#   → Claude Code 中打开 .claude/skills/tech-architect/SKILL.md
#   → 按步骤写 _judgments/stage5.json

# 2. 拼装 + 初始化代码库
python3 helpers/build_tech_spec.py pipe_2026-06-15_001
python3 helpers/init_codebase.py pipe_2026-06-15_001 --tech-stack nodejs-react-postgres

# 3. 生成可读版本
python3 helpers/digest.py runs/pipe_2026-06-15_001/5_tech_spec.json

# 4. 查看输出
cat runs/pipe_2026-06-15_001/5_tech_spec.digest.md
ls -la runs/pipe_2026-06-15_001/6_codebase/
```

### Stage 6–7: 开发 + 测试

```bash
# 1. 进入代码库
cd runs/pipe_2026-06-15_001/6_codebase

# 2. 安装 + 开发
npm install  # 或 pip install -r requirements.txt
npm run dev

# 3. 持续测试
npm test

# 4. 提交 PR
git add .
git commit -m "feat: implement core features"
git push origin feature/core

# 5. CI/CD 自动运行
#   → Lint / Type check / Security scan / Tests

# 6. 代码审查 + 合并
gh pr create --title "Stage 6–7: MVP Implementation"
gh pr merge
```

### Stage 8: 部署

```bash
# 1. 部署到 Staging
#   → GitHub Actions 自动触发
#   → 验证：curl https://staging.example.com/health

# 2. 部署到 Production
git tag v0.1.0
git push origin v0.1.0
#   → 自动部署到 Production

# 3. 生成部署报告
python3 helpers/build_deployment.py pipe_2026-06-15_001

# 4. 启动监控
#   → Sentry / PostHog / Better Uptime 告警已启用
```

### Stage 9: 运营

```bash
# 1. 每周更新指标
python3 helpers/build_growth_metrics.py pipe_2026-06-15_001 \
  --period weekly

# 2. 每月汇总
python3 helpers/build_growth_metrics.py pipe_2026-06-15_001 \
  --period monthly

# 3. 查看报告
cat runs/pipe_2026-06-15_001/9_growth_metrics.digest.md

# 4. 月度复盘
#   → 决策：SCALE / OPTIMIZE / SUNSET
```

---

## 📊 输出物汇总

| Stage | Agent 输出 | Helper 输出 | 格式 |
|-------|-----------|-----------|------|
| 4 | `_judgments/stage4.json` | `4_prd.json` | JSON Schema ✅ |
| 5 | `_judgments/stage5.json` | `5_tech_spec.json` | JSON Schema ✅ |
| 6–7 | Git repo + PR | `7_code_delivery.json` | JSON Schema ✅ |
| 8 | 部署日志 | `8_deployment.json` | JSON Schema ✅ |
| 9 | 指标数据 | `9_growth_metrics.json` | JSON Schema ✅ |

---

## 🎓 学习资源

### 快速了解
- 本文件 (5 分钟)
- [`docs/stage-4-9-overview.md`](./docs/stage-4-9-overview.md) (20 分钟)

### 详细指南
- [`prd-writer/SKILL.md`](./.claude/skills/prd-writer/SKILL.md) — Stage 4 完整流程 (30 分钟)
- [`tech-architect/SKILL.md`](./.claude/skills/tech-architect/SKILL.md) — Stage 5 完整流程 (40 分钟)

### Schema 参考
- [`contracts/prd.schema.json`](./contracts/prd.schema.json)
- [`contracts/tech_spec.schema.json`](./contracts/tech_spec.schema.json)
- [`contracts/code_delivery.schema.json`](./contracts/code_delivery.schema.json)
- [`contracts/deployment.schema.json`](./contracts/deployment.schema.json)
- [`contracts/growth_metrics.schema.json`](./contracts/growth_metrics.schema.json)

---

## ❓ FAQ

**Q: 能跳过某个 Stage 吗?**  
A: 不建议。每个 Stage 的输出是下一个 Stage 的输入。跳过会导致上游信息不足。

**Q: 多久能从 Opportunity 到上线?**  
A: 典型时间线：发现 (1w) + 设计 (1w) + 开发 (4-8w) + 部署 (1d) + 初期增长 (1-4w) = **7–17 周**

**Q: 第一次用，应该从哪里开始?**  
A: 
1. 读本文 (5 分钟)
2. 读 [`docs/stage-4-9-overview.md`](./docs/stage-4-9-overview.md) (20 分钟)
3. 选一个已完成的 Stage 3 机会 (例 `pipe_2026-06-07_001`)
4. 在 Claude Code 中打开 [`prd-writer/SKILL.md`](./.claude/skills/prd-writer/SKILL.md)
5. 按步骤写 PRD

**Q: 遇到问题怎么办?**  
A: 检查对应的 Schema 文件和 Skill 指南，看是否遗漏了必需字段。

---

**祝你们愉快地从痛点到产品！** 🎉
