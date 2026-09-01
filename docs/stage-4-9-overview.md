# Stage 4–9 实现概览

> **完整 Pipeline 已落地** — 从痛点发现到产品上线再到增长运营的闭环。

## 📋 快速导航

| Stage | 名称 | Agent Skill | 输出 JSON | 状态 |
|-------|------|-----------|---------|------|
| **4** | PRD 撰写 | [`prd-writer`](../.claude/skills/prd-writer/SKILL.md) | `4_prd.json` | ✅ |
| **5** | 技术架构 | [`tech-architect`](../.claude/skills/tech-architect/SKILL.md) | `5_tech_spec.json` | ✅ |
| **6–7** | 编码 + 测试 | 开发者 | `7_code_delivery.json` | ✅ |
| **8** | 部署 | DevOps/SRE | `8_deployment.json` | ✅ |
| **9** | 运营 + 增长 | 数据/营销 | `9_growth_metrics.json` | ✅ |

---

## 🎯 Stage 4: PRD 撰写

**输入** → `3_opportunity.json` (opportunity_score + commercial_assessment)

**输出** → `4_prd.json` (符合 `contracts/prd.schema.json`)

### 关键产出

1. **产品愿景** — 北极星，连接痛点→解决方案
2. **用户故事** — 基于 Stage 3 personas，3–5 个故事，每个 3–5 个验收标准
3. **功能分解** — 5–15 个核心功能，优先级 P0/P1/P2/P3，工作量估算
4. **验收标准** — 产品级 5–20 条，可自动化验证
5. **成功指标** — 北极星 + 3–10 个关键指标 (DAU/MAU/ARR/NPS 等)
6. **风险与应对** — 2–5 个主要风险 + 缓解方案
7. **竞争定位** — 独特价值主张，vs 竞品的优势
8. **商业模式** — 定价策略、目标 ARR
9. **时间估算** — MVP 实现周数 (4–16 周)

### 使用流程

```bash
# 1. Agent 在 Claude Code 中打开 Skill
# → 写 runs/{pid}/_judgments/stage4.json

# 2. Helper 拼装
python3 helpers/build_prd.py pipe_2026-06-15_001
python3 helpers/build_i18n.py pipe_2026-06-15_001 --stage 4
python3 helpers/digest.py runs/pipe_2026-06-15_001/4_prd.json

# 3. 输出
# → 4_prd.json (schema validated)
# → 4_prd.digest.md (human readable)
# → 4_prd.digest.zh.md (Chinese)
```

---

## 🏗️ Stage 5: 技术架构

**输入** → `4_prd.json` (features, constraints, timeline)

**输出** → `5_tech_spec.json` (符合 `contracts/tech_spec.schema.json`)

### 关键产出

1. **架构模式** — 单体 / 微服务 / Serverless / WebSocket + 理由
2. **技术栈选择**
   - 前端：React/Vue/Svelte + 构建工具 + UI 库
   - 后端：Node/Python/Go + 框架 + ORM
   - 数据库：PostgreSQL / MongoDB + 缓存 / 搜索
   - 基础设施：Vercel / Railway / AWS 等
3. **系统设计** — ASCII/Mermaid 图表，数据流
4. **数据库模式** — 表、列、主键、外键、索引
5. **API 契约** — 5–10 个 REST 端点 (或 GraphQL types)
6. **部署架构** — 环境描述、容器编排、监控
7. **安全考虑** — 认证、授权、加密、合规性
8. **可扩展性** — 负载预测 (100 → 10k DAU)，纵横向扩展
9. **开发阶段** — 3–5 个交付阶段，清晰依赖

### 使用流程

```bash
# 1. Agent 在 Claude Code 中打开 Skill
# → 写 runs/{pid}/_judgments/stage5.json

# 2. Helper 拼装 + 初始化代码库
python3 helpers/build_tech_spec.py pipe_2026-06-15_001
python3 helpers/init_codebase.py pipe_2026-06-15_001 --tech-stack nodejs-react-postgres
python3 helpers/build_i18n.py pipe_2026-06-15_001 --stage 5
python3 helpers/digest.py runs/pipe_2026-06-15_001/5_tech_spec.json

# 3. 输出
# → 5_tech_spec.json (schema validated)
# → runs/pipe_2026-06-15_001/6_codebase/ (git repo scaffold)
# → 5_tech_spec.digest.md (diagrams + details)
```

### 🚦 决策点 ②

人工审查：
- PRD 和架构是否匹配？
- 技术栈适合时间线吗？
- 架构能否支持预期的规模增长？
- DevOps 能支持这个部署模型吗？

**决定** → PROCEED (Stage 6) / REVISE (回到步骤 2) / CANCEL

---

## 💻 Stage 6–7: 编码 + 测试

**输入** → `5_tech_spec.json` (architecture + tech choices)

**输出** → Git repo + PR + `7_code_delivery.json`

### 关键产出

1. **代码实现** — 按 Stage 5 定义的阶段交付
   - Phase 1: 基础设施 + 认证
   - Phase 2: 核心功能 (P0)
   - Phase 3: 集成 + 前端
   - Phase 4: 优化 + 清理
   - Phase 5: 上线准备

2. **测试覆盖** — 单元 / 集成 / E2E 测试
   - 目标覆盖率：关键路径 ≥ 80%
   - 脆弱路径 ≥ 60%

3. **代码质量**
   - Lint / Type checking (TS) 通过
   - 安全扫描 (Snyk / Bandit) 零 critical 漏洞
   - 性能基线达成 (API p95 < 200ms)

4. **文档** — README, API docs, deployment docs

### 工作流

```bash
# 1. 初始化本地开发环境
cd runs/pipe_2026-06-15_001/6_codebase
npm install  # or pip install -r requirements.txt
npm run dev

# 2. TDD: 写测试 → 实现 → 重构
npm test     # 持续跑测试

# 3. 提交 PR
git add .
git commit -m "feat: implement document upload + processing"
git push origin feature/document-processing
# → GitHub Actions 触发 CI/CD

# 4. CI/CD 自动运行
# - Lint (ESLint + Prettier)
# - Type check (TypeScript)
# - Security scan (Snyk)
# - Tests (Jest + Playwright)
# - Coverage report

# 5. 代码审查 (peer review + agent review)
gh pr create --title "Stage 6: Core Features MVP" \
  --body "完成 Phase 1-3，测试覆盖 82%，无 security 问题"

# 6. 合并
git merge
```

### 🚦 决策点 ③

人工审查：
- 所有测试通过了吗？
- 安全扫描结果？
- 代码质量达标？
- 能否合并到 main？

**决定** → MERGE / REQUEST_CHANGES / BLOCK

---

## 🚀 Stage 8: 部署

**输入** → Git repo (经过所有测试)

**输出** → Staged/Production 部署 + `8_deployment.json`

### 关键产出

1. **部署环境** — 现在 Vercel (前端) + Railway (后端) + Neon (DB)
2. **监控设置** — Sentry / PostHog / Better Uptime 启用
3. **故障应对** — On-call 日程、升级流程、运行手册
4. **性能基线** — API 延迟 / 错误率 / 资源使用
5. **回滚计划** — 蓝绿部署 / 金丝雀 / 回滚步骤

### 部署流程

```bash
# 1. 部署到 Staging
# → GitHub Actions 自动触发
# → Vercel: auto-deploy preview

# 2. 验证 Staging
curl https://app-staging.example.com/health
# → 所有服务 healthy

# 3. 部署到 Production
git tag v0.1.0
git push origin v0.1.0
# → GitHub Actions 检测 tag
# → Railway: auto-deploy
# → Vercel: auto-deploy

# 4. 生成部署报告
python3 helpers/build_deployment.py pipe_2026-06-15_001

# 5. 输出
# → 8_deployment.json (schema validated)
# → 部署日志、性能基线、监控链接
```

### 成功标准

- ✅ 零停机部署
- ✅ 所有健康检查通过
- ✅ 数据库迁移成功
- ✅ 监控告警已启用
- ✅ 回滚计划已测试

---

## 📊 Stage 9: 运营 + 增长

**输入** → Production app (已运行 1–4 周)

**输出** → `9_growth_metrics.json` (每周 / 每月更新)

### 关键指标

#### 产品指标
- DAU / MAU / WAU — 活跃用户
- D1 / D7 / D30 留存 — 用户黏性
- 平均会话长度 — 参与度
- 功能采纳率 — 哪些功能被用

#### 商业指标
- 新注册用户 — 增长
- 转化率 — 免费 → 付费
- ARR / MRR — 收入
- CAC (Customer Acquisition Cost) — 获客成本
- CLV (Customer Lifetime Value) — 客户终身价值
- Churn rate — 流失率

#### 获客渠道
- 有机搜索 — SEO / 口碑
- 付费搜索 — Google Ads
- 付费社交 — Facebook / LinkedIn / Twitter
- 推荐 — 用户推荐
- 合作 — 联合营销

#### 增长建议
- 识别 2–5 个高杠杆机会 (impact / effort)
- 优先级排序，建议下步行动

### 周期性更新

```bash
# 每周一次
python3 helpers/build_growth_metrics.py pipe_2026-06-15_001 \
  --period weekly \
  --start-date 2026-06-15 \
  --end-date 2026-06-22

# 每月一次
python3 helpers/build_growth_metrics.py pipe_2026-06-15_001 \
  --period monthly \
  --start-date 2026-06-01 \
  --end-date 2026-06-30

# 输出
# → 9_growth_metrics.json
# → 9_growth_metrics.digest.md (可视化图表)
```

### 🚦 决策点 ④

月度 / 季度复盘：
- 是否达成了 Stage 4 的成功指标？
- 哪个渠道 ROI 最好？
- 应该 SCALE / OPTIMIZE / SUNSET？
- 下个迭代的重点？

**决定** → SCALE (增加投入) / OPTIMIZE (改进转化) / SUNSET (关闭) / PIVOT (方向调整)

---

## 🔄 完整流程示例

```
[发现] (1 周)
  Stage 0 → 1 → 2 → 3
  决策点 ① GO

[设计] (1 周)
  Stage 4 → 5
  决策点 ② PROCEED

[实现] (4–8 周，按 PRD timeline)
  Phase 1: 2 周 (基础)
  Phase 2: 2 周 (核心功能)
  Phase 3: 2 周 (集成)
  Phase 4: 1 周 (优化 + QA)
  
  Stage 6–7 并行，最后合并 PR
  决策点 ③ MERGE

[运营] (持续)
  Stage 8: 1 天 (部署)
  Stage 9: 持续 (每周数据更新)
  决策点 ④ 每月复盘

总周期: 7–17 周 (MVP → Production → 初期增长)
```

---

## 📁 文件结构

所有 Stage 4–9 的 **JSON Schema**：

```
contracts/
├── prd.schema.json                # Stage 4 产出
├── tech_spec.schema.json          # Stage 5 产出
├── code_delivery.schema.json      # Stage 6–7 产出
├── deployment.schema.json         # Stage 8 产出
└── growth_metrics.schema.json     # Stage 9 产出
```

所有 **Helper 脚本**：

```
helpers/
├── build_prd.py                   # Stage 4
├── build_tech_spec.py             # Stage 5
├── init_codebase.py               # Stage 5 后 (新)
├── build_code_delivery.py         # Stage 6–7 (新)
├── build_deployment.py            # Stage 8 (新)
├── build_growth_metrics.py        # Stage 9 (新)
└── digest.py                      # 通用：JSON → Markdown
```

所有 **Skill 指南**：

```
.claude/skills/
├── prd-writer/SKILL.md            # Stage 4 指南
└── tech-architect/SKILL.md        # Stage 5 指南
```

---

## 🎓 学习路径

1. **快速上手** — 读本文，理解流程
2. **深入 Stage 4** — 打开 [`prd-writer/SKILL.md`](../.claude/skills/prd-writer/SKILL.md)，按步骤写 PRD
3. **深入 Stage 5** — 打开 [`tech-architect/SKILL.md`](../.claude/skills/tech-architect/SKILL.md)，设计架构
4. **查阅 Schema** — [`contracts/`](../contracts/) 文件夹中的 JSON Schema
5. **例子运行** — 参考 `runs/pipe_2026-06-15_*/` 中的完整案例

---

## 🚨 常见问题

### Q: Stage 4 PRD 需要多详细？
**A**: 够详细让 Stage 5 architect 明确需求，但不需要所有细节 (那是 PRD 后续版本的事)。关键是：用户故事清晰、优先级明确、成功指标可测量。

### Q: Stage 5 架构能改吗？
**A**: 可以。如果开发中发现架构有问题，可以 raise issue、讨论修改。更新 `5_tech_spec.json` 和相应的代码。

### Q: 如果测试没通过怎么办？
**A**: 回到 Stage 6，修改代码直到测试通过。所有测试必须通过才能合并到 main。

### Q: Stage 9 多久开始？
**A**: Stage 8 部署成功后立即开始，持续收集数据。建议至少跑 1–4 周才有有意义的数据。

### Q: 可以并行运行多个 pipeline 吗？
**A**: 完全可以。每个 pipeline 有独立的 `pipeline_id`，数据不会混淆。可以同时在 Stage 1、3、5、8 分别跑多个产品。

---

## 📚 相关文档

- [docs/flow.md](./flow.md) — Mermaid 完整流程图
- [docs/dependencies.md](./dependencies.md) — 依赖清单 + API 列表
- [docs/contracts.md](./contracts.md) — JSON Schema 人类可读版本
- [README.md](../README.md) — 项目总览

---

**完成** ✅ 希望你享受这条从痛点到产品再到增长的完整旅程！
