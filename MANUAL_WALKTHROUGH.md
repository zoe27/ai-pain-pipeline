# 🎯 完整手动执行指南（Stage 0-9）

> 在 Kiro 中一步步执行，从痛点到产品的完整流程

---

## 📋 准备工作

### 创建新 Pipeline

```bash
# 生成 Pipeline ID
PIPE=pipe_$(date +%Y-%m-%d)_walkthrough
echo "Pipeline ID: $PIPE"

# 创建目录
mkdir -p runs/$PIPE/_raw runs/$PIPE/_judgments
```

保存这个 Pipeline ID，后面所有步骤都会用到。

---

## 🎯 Stage 0: 领域定向（可选，跳过也行）

Stage 0 是可选的，用于收窄扫描范围。我们**先跳过**，直接从 Stage 1 开始。

---

## 📡 Stage 1: 痛点雷达

### 步骤 1.1: 抓取数据

```bash
python helpers/fetch_radar.py $PIPE --config configs/radar.example.yaml
```

**预期输出**: `runs/$PIPE/_raw/top50.json` 包含抓取的痛点数据

### 步骤 1.2: 查看原始数据（可选）

```bash
cat runs/$PIPE/_raw/top50.json | python -m json.tool | head -50
```

### 步骤 1.3: 在 Kiro 中执行 Agent 判断

**方式 A: 让我执行（推荐）**

告诉我：
```
请执行 Stage 1 的 pain-radar 判断，Pipeline ID 是 <你的PIPE>
```

我会：
1. 读取 `_raw/top50.json`
2. 执行情感分析和关键词提取
3. 写 `_judgments/stage1.json`

**方式 B: 手动执行**

1. 打开 `.claude/skills/pain-radar/SKILL.md`
2. 阅读指南
3. 读取 `runs/$PIPE/_raw/top50.json`
4. 创建 `runs/$PIPE/_judgments/stage1.json`，格式参考已有示例

### 步骤 1.4: 拼装最终输出

```bash
python helpers/build_pain_batch.py $PIPE
```

**预期输出**: 
- `runs/$PIPE/1_pain_points.json`
- 自动调用聚类和外部信号 enrich

### 步骤 1.5: 生成报告

```bash
python helpers/digest.py runs/$PIPE/1_pain_points.json
```

**预期输出**: `runs/$PIPE/1_pain_points.digest.md`

### ✅ Stage 1 完成检查

- [ ] `_judgments/stage1.json` 存在
- [ ] `1_pain_points.json` 存在
- [ ] `1_pain_points.digest.md` 存在

---

## 📊 Stage 2: ICE 评分

### 步骤 2.1: 在 Kiro 中执行 Agent 判断

**方式 A: 让我执行（推荐）**

告诉我：
```
请执行 Stage 2 的 ICE 评分，Pipeline ID 是 <你的PIPE>
```

我会：
1. 读取 `1_pain_points.json`
2. 执行 ICE 评分
3. 写 `_judgments/stage2.json`

**方式 B: 手动执行**

1. 打开 `.claude/skills/score-pain/SKILL.md`
2. 读取 `runs/$PIPE/1_pain_points.json`
3. 创建 `runs/$PIPE/_judgments/stage2.json`

### 步骤 2.2: 拼装最终输出

```bash
python helpers/build_scored_batch.py $PIPE
```

**预期输出**: 
- `runs/$PIPE/2_scored_pain_points.json`
- 自动添加市场信号和商业预填

### 步骤 2.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/2_scored_pain_points.json
```

### ✅ Stage 2 完成检查

- [ ] `_judgments/stage2.json` 存在
- [ ] `2_scored_pain_points.json` 存在
- [ ] `2_scored_pain_points.digest.md` 存在

---

## 🔬 Stage 3: 用户研究 + 商业判断

### 步骤 3.1: 在 Kiro 中执行 Agent 判断

**方式 A: 让我执行（推荐）**

告诉我：
```
请执行 Stage 3 的用户研究，Pipeline ID 是 <你的PIPE>
```

我会：
1. 读取 `2_scored_pain_points.json`
2. 选择高分痛点进行研究
3. 生成用户画像、竞品分析、商业判断
4. 写 `_judgments/stage3.json`

**方式 B: 手动执行**

1. 打开 `.claude/skills/user-research/SKILL.md`
2. 读取 `runs/$PIPE/2_scored_pain_points.json`
3. 创建 `runs/$PIPE/_judgments/stage3.json`

### 步骤 3.2: 拼装最终输出

```bash
python helpers/build_opportunity.py $PIPE
```

**预期输出**: 
- `runs/$PIPE/3_opportunity.json`
- 自动计算 opportunity_score

### 步骤 3.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/3_opportunity.json
```

### ✅ Stage 3 完成检查

- [ ] `_judgments/stage3.json` 存在
- [ ] `3_opportunity.json` 存在
- [ ] `3_opportunity.digest.md` 存在

---

## 🚦 决策点 ①: GO / NO-GO

### 审查内容

```bash
# 查看机会报告
cat runs/$PIPE/3_opportunity.digest.md

# 或查看 JSON
cat runs/$PIPE/3_opportunity.json | python -m json.tool
```

### 关键指标

- `opportunity_score`: 总分（high ≥ 2000, medium ≥ 500, low ≥ 100）
- `recommendation`: build / validate / skip / partner
- `confidence`: high / medium / low

### 做决策

**如果决定 GO，继续 Stage 4。如果 NO-GO，流程结束。**

---

## 📝 Stage 4: PRD 撰写

### 步骤 4.1: 在 Kiro 中执行 Agent 判断

**方式 A: 让我执行（推荐）**

告诉我：
```
请执行 Stage 4 的 PRD 撰写，Pipeline ID 是 <你的PIPE>
```

我会：
1. 读取 `3_opportunity.json`
2. 撰写完整 PRD
3. 写 `_judgments/stage4.json`

**方式 B: 手动执行**

1. 打开 `.claude/skills/prd-writer/SKILL.md`
2. 按照指南撰写 PRD
3. 创建 `runs/$PIPE/_judgments/stage4.json`

### 步骤 4.2: 拼装最终输出

```bash
python helpers/build_prd.py $PIPE
```

**预期输出**: `runs/$PIPE/4_prd.json`

### 步骤 4.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/4_prd.json
```

### ✅ Stage 4 完成检查

- [ ] `_judgments/stage4.json` 存在
- [ ] `4_prd.json` 存在
- [ ] `4_prd.digest.md` 存在

---

## 🏗️ Stage 5: 技术架构

### 步骤 5.1: 在 Kiro 中执行 Agent 判断

**方式 A: 让我执行（推荐）**

告诉我：
```
请执行 Stage 5 的技术架构设计，Pipeline ID 是 <你的PIPE>
```

我会：
1. 读取 `4_prd.json`
2. 设计系统架构
3. 写 `_judgments/stage5.json`

**方式 B: 手动执行**

1. 打开 `.claude/skills/tech-architect/SKILL.md`
2. 按照指南设计架构
3. 创建 `runs/$PIPE/_judgments/stage5.json`

### 步骤 5.2: 拼装最终输出

```bash
python helpers/build_tech_spec.py $PIPE
```

**预期输出**: `runs/$PIPE/5_tech_spec.json`

### 步骤 5.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/5_tech_spec.json
```

### ✅ Stage 5 完成检查

- [ ] `_judgments/stage5.json` 存在
- [ ] `5_tech_spec.json` 存在
- [ ] `5_tech_spec.digest.md` 存在

---

## 🚦 决策点 ②: PROCEED / REVISE / CANCEL

### 审查内容

- PRD 是否清晰？
- 技术架构是否合理？
- 时间估算是否现实？

**如果决定 PROCEED，继续 Stage 6-7。**

---

## 💻 Stage 6-7: 编码 + 测试

### 步骤 6.1: 初始化代码库（可选）

```bash
python helpers/init_codebase.py $PIPE --tech-stack nodejs-react-postgres
```

### 步骤 6.2: 开发

这个阶段需要真实的开发工作：
- 在生成的代码库中编写代码
- 运行测试
- 提交 PR

### 步骤 6.3: 生成交付报告（手动）

开发完成后，手动创建：
- `runs/$PIPE/7_code_delivery.json`

参考 Schema: `contracts/code_delivery.schema.json`

---

## 🚦 决策点 ③: MERGE / REQUEST_CHANGES

审查：
- 测试是否通过？
- 代码质量如何？
- 安全扫描结果？

---

## 🚀 Stage 8: 部署

手动部署到 staging/production，然后创建：
- `runs/$PIPE/8_deployment.json`

参考 Schema: `contracts/deployment.schema.json`

---

## 📊 Stage 9: 运营 + 增长

持续收集数据，定期生成：
- `runs/$PIPE/9_growth_metrics.json`

参考 Schema: `contracts/growth_metrics.schema.json`

---

## 🚦 决策点 ④: SCALE / OPTIMIZE / SUNSET

每月复盘，决定下一步策略。

---

## 🎯 总结

### 在 Kiro 中的执行流程

每个 Stage 你只需要说：
```
请执行 Stage N，Pipeline ID 是 pipe_xxx
```

我会自动完成：
1. 读取上一阶段数据
2. 执行 Agent 逻辑
3. 生成 `_judgments/stageN.json`
4. 提示你运行 helper 拼装

然后你运行：
```bash
python helpers/build_*.py pipe_xxx
python helpers/digest.py runs/pipe_xxx/N_*.json
```

### 预计时间

- Stage 1-3: 每个 10-15 分钟 (在 Kiro 中)
- Stage 4-5: 每个 15-20 分钟 (在 Kiro 中)
- Stage 6-7: 4-8 周 (实际开发)
- Stage 8-9: 持续运行

---

## 🚀 现在开始

告诉我：
```
创建新 Pipeline，从 Stage 1 开始
```

我会引导你完成整个流程！
