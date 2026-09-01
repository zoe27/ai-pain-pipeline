# 🚀 完整执行命令清单

> 复制粘贴这些命令到终端，逐步执行完整流程

---

## 📋 准备工作

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 设置 Pipeline ID
export PIPE=pipe_2026-08-25_walkthrough
echo "Pipeline ID: $PIPE"

# 3. 创建目录结构
mkdir -p runs/$PIPE/_raw runs/$PIPE/_judgments
```

---

## 📡 Stage 1: 痛点雷达

### 命令 1.1: 抓取数据

```bash
python helpers/fetch_radar.py $PIPE --config configs/radar.example.yaml
```

**预期结果**: 
- `runs/$PIPE/_raw/` 下出现多个 JSON 文件
- 终端显示抓取进度

**如果出错**: 检查 `.env` 文件是否配置（HN 不需要，但 PH/Reddit 需要）

### 命令 1.2: 查看原始数据（可选）

```bash
ls -la runs/$PIPE/_raw/
```

### 命令 1.3: Agent 判断（需要 Kiro）

**在 Kiro 中说**:
```
请执行 Stage 1 的 pain-radar 判断，Pipeline ID 是 pipe_2026-08-25_walkthrough
```

我会生成 `runs/$PIPE/_judgments/stage1.json`

### 命令 1.4: 拼装数据

```bash
python helpers/build_pain_batch.py $PIPE
```

**预期结果**: 
- `runs/$PIPE/1_pain_points.json` 已创建
- 终端显示 "✅ pain_points written"

### 命令 1.5: 生成报告

```bash
python helpers/digest.py runs/$PIPE/1_pain_points.json
```

**预期结果**: 
- `runs/$PIPE/1_pain_points.digest.md` 已创建
- `runs/$PIPE/1_pain_points.digest.zh.md` 已创建（中文版）

### 命令 1.6: 查看结果

```bash
# 查看 JSON（美化输出）
cat runs/$PIPE/1_pain_points.json | python -m json.tool | head -100

# 查看 Digest（可读报告）
cat runs/$PIPE/1_pain_points.digest.md
```

---

## 📊 Stage 2: ICE 评分

### 命令 2.1: Agent 判断（需要 Kiro）

**在 Kiro 中说**:
```
请执行 Stage 2 的 ICE 评分，Pipeline ID 是 pipe_2026-08-25_walkthrough
```

我会生成 `runs/$PIPE/_judgments/stage2.json`

### 命令 2.2: 拼装数据

```bash
python helpers/build_scored_batch.py $PIPE
```

**预期结果**: 
- `runs/$PIPE/2_scored_pain_points.json` 已创建
- 自动添加市场信号和商业预填

### 命令 2.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/2_scored_pain_points.json
```

### 命令 2.4: 查看高分痛点

```bash
# 查看 ICE 评分结果
cat runs/$PIPE/2_scored_pain_points.digest.md

# 或查看前几个高分项
cat runs/$PIPE/2_scored_pain_points.json | python -m json.tool | grep -A 10 '"total"'
```

---

## 🔬 Stage 3: 用户研究 + 商业判断

### 命令 3.1: Agent 判断（需要 Kiro）

**在 Kiro 中说**:
```
请执行 Stage 3 的用户研究，Pipeline ID 是 pipe_2026-08-25_walkthrough
```

我会生成 `runs/$PIPE/_judgments/stage3.json`

### 命令 3.2: 拼装数据

```bash
python helpers/build_opportunity.py $PIPE
```

**预期结果**: 
- `runs/$PIPE/3_opportunity.json` 已创建
- 自动计算 opportunity_score

### 命令 3.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/3_opportunity.json
```

### 命令 3.4: 查看机会评估

```bash
# 查看完整报告
cat runs/$PIPE/3_opportunity.digest.md

# 查看 opportunity_score
cat runs/$PIPE/3_opportunity.json | python -m json.tool | grep -A 5 'opportunity_score'
```

---

## 🚦 决策点 ①: GO / NO-GO

### 审查清单

```bash
# 1. 查看机会评分
cat runs/$PIPE/3_opportunity.json | python -m json.tool | grep -E '(opportunity_score|recommendation|confidence)'

# 2. 查看详细报告
cat runs/$PIPE/3_opportunity.digest.md

# 3. 查看目标用户
cat runs/$PIPE/3_opportunity.json | python -m json.tool | grep -A 20 'target_personas'
```

### 做决策

**如果 opportunity_score > 500 且 recommendation = "build"，继续 Stage 4**

---

## 📝 Stage 4: PRD 撰写

### 命令 4.1: Agent 判断（需要 Kiro）

**在 Kiro 中说**:
```
请执行 Stage 4 的 PRD 撰写，Pipeline ID 是 pipe_2026-08-25_walkthrough
```

我会生成 `runs/$PIPE/_judgments/stage4.json`

### 命令 4.2: 拼装数据

```bash
python helpers/build_prd.py $PIPE
```

**预期结果**: 
- `runs/$PIPE/4_prd.json` 已创建

### 命令 4.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/4_prd.json
```

### 命令 4.4: 查看 PRD

```bash
# 查看 PRD 报告
cat runs/$PIPE/4_prd.digest.md

# 查看核心功能
cat runs/$PIPE/4_prd.json | python -m json.tool | grep -A 50 'core_features'

# 查看成功指标
cat runs/$PIPE/4_prd.json | python -m json.tool | grep -A 20 'success_metrics'
```

---

## 🏗️ Stage 5: 技术架构

### 命令 5.1: Agent 判断（需要 Kiro）

**在 Kiro 中说**:
```
请执行 Stage 5 的技术架构设计，Pipeline ID 是 pipe_2026-08-25_walkthrough
```

我会生成 `runs/$PIPE/_judgments/stage5.json`

### 命令 5.2: 拼装数据

```bash
python helpers/build_tech_spec.py $PIPE
```

**预期结果**: 
- `runs/$PIPE/5_tech_spec.json` 已创建

### 命令 5.3: 生成报告

```bash
python helpers/digest.py runs/$PIPE/5_tech_spec.json
```

### 命令 5.4: 查看技术栈

```bash
# 查看技术规范报告
cat runs/$PIPE/5_tech_spec.digest.md

# 查看技术栈选择
cat runs/$PIPE/5_tech_spec.json | python -m json.tool | grep -A 30 'tech_stack'

# 查看数据库设计
cat runs/$PIPE/5_tech_spec.json | python -m json.tool | grep -A 30 'database_schema'
```

### 命令 5.5: 初始化代码库（可选）

```bash
python helpers/init_codebase.py $PIPE --tech-stack nodejs-react-postgres
```

**预期结果**: 
- `runs/$PIPE/6_codebase/` 目录已创建
- 包含项目骨架

---

## 🚦 决策点 ②: PROCEED / REVISE / CANCEL

### 审查清单

```bash
# 1. 查看 PRD
cat runs/$PIPE/4_prd.digest.md

# 2. 查看技术架构
cat runs/$PIPE/5_tech_spec.digest.md

# 3. 查看时间估算
cat runs/$PIPE/4_prd.json | python -m json.tool | grep 'timeline_estimate_weeks'
```

### 做决策

**如果 PRD 和架构都合理，继续 Stage 6-7（实际开发）**

---

## 💻 Stage 6-7: 编码 + 测试（实际开发）

这个阶段需要真实的开发工作，无法用命令完成。

### 开发流程

1. 进入代码库
   ```bash
   cd runs/$PIPE/6_codebase/
   ```

2. 安装依赖
   ```bash
   npm install  # 或 pip install -r requirements.txt
   ```

3. 开发功能（按照 PRD 和 Tech Spec）

4. 运行测试
   ```bash
   npm test  # 或 pytest
   ```

5. 提交代码
   ```bash
   git add .
   git commit -m "feat: implement MVP"
   git push
   ```

---

## 📊 查看整体进度

```bash
# 查看所有生成的文件
ls -la runs/$PIPE/

# 查看文件树
tree runs/$PIPE/ -L 2

# 查看所有 digest 报告
ls runs/$PIPE/*.digest.md
```

---

## 🔧 故障排查命令

```bash
# 检查 Python 环境
python --version
which python

# 检查依赖
pip list | grep -E "jsonschema|PyYAML|flask"

# 验证 JSON 格式
cat runs/$PIPE/1_pain_points.json | python -m json.tool > /dev/null && echo "✅ JSON 有效"

# 查看错误日志
cat runs/$PIPE/*.log 2>/dev/null || echo "无日志文件"
```

---

## 📚 快速参考

### Pipeline ID
```bash
echo $PIPE
```

### 查看当前进度
```bash
ls runs/$PIPE/*.json
```

### 重新设置 Pipeline
```bash
export PIPE=pipe_2026-08-25_walkthrough
```

---

## 🎯 完整执行流程（复制粘贴版）

```bash
# === 准备 ===
source .venv/bin/activate
export PIPE=pipe_2026-08-25_walkthrough
mkdir -p runs/$PIPE/_raw runs/$PIPE/_judgments

# === Stage 1 ===
python helpers/fetch_radar.py $PIPE --config configs/radar.example.yaml
# 在 Kiro: 请执行 Stage 1
python helpers/build_pain_batch.py $PIPE
python helpers/digest.py runs/$PIPE/1_pain_points.json

# === Stage 2 ===
# 在 Kiro: 请执行 Stage 2
python helpers/build_scored_batch.py $PIPE
python helpers/digest.py runs/$PIPE/2_scored_pain_points.json

# === Stage 3 ===
# 在 Kiro: 请执行 Stage 3
python helpers/build_opportunity.py $PIPE
python helpers/digest.py runs/$PIPE/3_opportunity.json

# === 决策点 ① ===
cat runs/$PIPE/3_opportunity.digest.md

# === Stage 4 ===
# 在 Kiro: 请执行 Stage 4
python helpers/build_prd.py $PIPE
python helpers/digest.py runs/$PIPE/4_prd.json

# === Stage 5 ===
# 在 Kiro: 请执行 Stage 5
python helpers/build_tech_spec.py $PIPE
python helpers/digest.py runs/$PIPE/5_tech_spec.json

# === 决策点 ② ===
cat runs/$PIPE/4_prd.digest.md
cat runs/$PIPE/5_tech_spec.digest.md

# === 完成 ===
ls -la runs/$PIPE/
```

---

**现在开始执行这些命令吧！** 🚀
