# DemandRadar 端到端 Walkthrough

完整流程：从产品输入 → 生成知乎回答草稿

## 前置条件

```bash
# 激活虚拟环境
source .venv/bin/activate

# 确认依赖已安装
pip install -q jsonschema pyyaml requests beautifulsoup4 fake-useragent
```

## 完整流程

### Step 0: 创建 Growth Run

```bash
# 生成 growth_id
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001

# 创建目录
mkdir -p runs/$GROWTH/_judgments runs/$GROWTH/_raw

echo "Growth ID: $GROWTH"
```

---

### Step 1: G0 - 产品锚定

#### 1.1 准备产品信息

准备以下信息：
- 产品名称
- 产品 URL 或 GitHub 链接
- 核心功能
- 目标用户

#### 1.2 使用 product-focus Skill

在 Claude 中运行：

```
使用 product-focus skill。

我的产品信息：
- 产品名称：AI PDF 处理工具
- 产品 URL：https://example.com
- 核心功能：PDF 转 Excel、PDF OCR、批量处理、发票识别
- 目标用户：办公人员、财务人员
- 已知竞品：Adobe Acrobat, Smallpdf, iLovePDF

请分析并输出 g0.json
```

#### 1.3 保存 AI 输出

```bash
# 将 Claude 输出的 JSON 保存到：
nano runs/$GROWTH/_judgments/g0.json
# 粘贴 AI 输出，保存退出
```

#### 1.4 运行 Helper

```bash
python3 helpers/build_product_context.py $GROWTH --product-url "https://example.com"
```

**预期输出：**
```
✓ Product context created
Product: AI PDF 处理工具
Keywords: 14
Competitors: 5
```

---

### Step 2: G1 - 知乎信号发现

#### 2.1 爬取知乎问题

```bash
python3 helpers/fetch_zhihu.py $GROWTH
```

**预期输出：**
```
Searching by target keywords...
  Searching keyword: 'PDF 转换工具'...
    Found 20 questions
  ...
✓ Fetched 50 unique questions
Saved to: runs/$GROWTH/_raw/raw_zhihu_questions.json
```

**注意事项：**
- 知乎有反爬限制，可能需要较长时间
- 如果爬取失败，检查网络连接或使用代理
- MVP 阶段：也可以手动创建 mock 数据测试

#### 2.2 使用 demand-radar Skill

在 Claude 中运行：

```
使用 demand-radar skill。

请分析以下知乎问题，过滤出包含真实 Intent 的信号。

原始数据位于：runs/$GROWTH/_raw/raw_zhihu_questions.json

[粘贴 raw 数据的部分内容，或提供文件]

请输出 g1.json
```

#### 2.3 保存 AI 输出

```bash
nano runs/$GROWTH/_judgments/g1.json
# 粘贴 AI filtered_signals 输出
```

#### 2.4 运行 Helper

```bash
python3 helpers/build_demand_signals.py $GROWTH
```

**预期输出：**
```
✓ Demand signals created
Raw questions: 50
Filtered signals: 28
Filter rate: 56.0%
```

---

### Step 3: G2 - 需求聚类

#### 3.1 使用 demand-cluster Skill

在 Claude 中运行：

```
使用 demand-cluster skill。

请将以下需求信号聚类为结构化的需求簇，并计算 Demand Score。

信号数据位于：runs/$GROWTH/g1_demand_signals.json

[粘贴 signals 数据]

请输出 g2.json
```

#### 3.2 保存 AI 输出

```bash
nano runs/$GROWTH/_judgments/g2.json
# 粘贴 AI clusters 输出
```

#### 3.3 运行 Helper

```bash
python3 helpers/build_demand_clusters.py $GROWTH
```

**预期输出：**
```
✓ Demand clusters created

Top 3 clusters by demand score:
  1. PDF → Excel 转换 (Score: 94, Questions: 8)
  2. PDF OCR 识别 (Score: 89, Questions: 6)
  3. PDF 批量处理 (Score: 85, Questions: 5)
```

---

### Step 4: G3 - 增长机会

#### 4.1 使用 growth-opportunity Skill

在 Claude 中运行：

```
使用 growth-opportunity skill。

请分析需求簇，生成可执行的增长机会建议。

输入：
- Clusters: runs/$GROWTH/g2_demand_clusters.json
- Product: runs/$GROWTH/product_context.json

[粘贴数据]

请输出 g3.json
```

#### 4.2 保存 AI 输出

```bash
nano runs/$GROWTH/_judgments/g3.json
# 粘贴 AI zhihu_opportunities 输出
```

#### 4.3 运行 Helper

```bash
python3 helpers/build_growth_opportunities.py $GROWTH
```

**预期输出：**
```
✓ Growth opportunities created

Summary:
  Total clusters: 8
  Zhihu questions to answer: 25
  SEO page opportunities: 12
  Estimated reach: 185,000 views

Top priority clusters:
  • PDF → Excel 转换 (Score: 94)
  • PDF OCR 识别 (Score: 89)
  • PDF 批量处理 (Score: 85)
```

---

### Step 5: G4 - 知乎回答生成

#### 5.1 使用 zhihu-answer-writer Skill

在 Claude 中运行：

```
使用 zhihu-answer-writer skill。

请为 top 20 个知乎问题生成高质量回答草稿。

输入：
- Opportunities: runs/$GROWTH/g3_growth_opportunities.json
- Product: runs/$GROWTH/product_context.json

[粘贴数据]

请为每个问题生成回答草稿，输出 g4.json
```

#### 5.2 保存 AI 输出

```bash
nano runs/$GROWTH/_judgments/g4.json
# 粘贴 AI answers 输出
```

#### 5.3 运行 Helper

```bash
python3 helpers/build_zhihu_answers.py $GROWTH
```

**预期输出：**
```
✓ Zhihu answer drafts created

Summary:
  Total answers: 20
  By priority:
    • urgent: 3
    • high: 8
    • medium: 7
    • low: 2
  Avg word count: 485
  Estimated reach: 185,000 views

✅ All done! Review answers and copy-paste to Zhihu.
```

---

### Step 6: 生成可读 Digest

```bash
# 查看生成的回答（JSON 格式）
cat runs/$GROWTH/g4_zhihu_answers.json | jq '.zhihu_answers[0].generated_answer.text'

# 或者生成 Markdown digest（如果实现了）
python3 helpers/digest.py runs/$GROWTH/g4_zhihu_answers.json
```

---

## 查看结果

### 查看产品锚点
```bash
cat runs/$GROWTH/product_context.json | jq .product_info
```

### 查看需求簇
```bash
cat runs/$GROWTH/g2_demand_clusters.json | jq '.clusters[] | {label, demand_score, question_count}'
```

### 查看回答草稿（第一条）
```bash
cat runs/$GROWTH/g4_zhihu_answers.json | jq '.zhihu_answers[0] | {
  question_title,
  opportunity_score,
  answer_preview: .generated_answer.text[:200]
}'
```

### 查看所有问题标题
```bash
cat runs/$GROWTH/g4_zhihu_answers.json | jq -r '.zhihu_answers[] | "\(.question_title) (Score: \(.opportunity_score))"'
```

---

## 人工 Review 与发布

### 1. 导出回答到文本文件

```bash
cat runs/$GROWTH/g4_zhihu_answers.json | jq -r '
.zhihu_answers[] | 
"## [\(.question_title)](\(.question_url))
\n
Opportunity Score: \(.opportunity_score)
Priority: \(.metadata.publish_recommendation.priority)
\n
\(.generated_answer.text)
\n
---
\n"
' > runs/$GROWTH/answers_for_review.md
```

### 2. Review

打开 `runs/$GROWTH/answers_for_review.md`，逐条 review：
- 检查回答质量
- 修改不合适的措辞
- 调整产品提及方式

### 3. 发布到知乎

**手动发布（MVP）：**
1. 打开知乎问题链接
2. 复制回答草稿
3. 粘贴到知乎回答框
4. 发布

**记录发布状态：**
```bash
# 手动更新 publish_status
# 或创建一个简单的 tracking 表格
```

---

## 故障排除

### 1. fetch_zhihu.py 失败
```
Error: Status 429, skipping page
```
**解决**：知乎限流，等待几分钟后重试，或使用代理

### 2. Schema validation 失败
```
❌ Schema validation failed: Missing required field
```
**解决**：检查 AI 输出的 JSON 格式，确保包含所有必需字段

### 3. Judgment file not found
```
❌ Judgment file not found: _judgments/g1.json
```
**解决**：确保已经用 Claude + Skill 生成了对应的 judgment 文件

---

## 快速命令汇总

```bash
# 完整流程（需要手动填充 _judgments/*.json）
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001
mkdir -p runs/$GROWTH/_judgments runs/$GROWTH/_raw

# G0
python3 helpers/build_product_context.py $GROWTH --product-url "URL"

# G1
python3 helpers/fetch_zhihu.py $GROWTH
python3 helpers/build_demand_signals.py $GROWTH

# G2
python3 helpers/build_demand_clusters.py $GROWTH

# G3
python3 helpers/build_growth_opportunities.py $GROWTH

# G4
python3 helpers/build_zhihu_answers.py $GROWTH

# View results
cat runs/$GROWTH/g4_zhihu_answers.json | jq -r '.zhihu_answers[] | "\(.question_title)\n\(.generated_answer.text)\n---\n"'
```

---

## 预期时间

- G0：5 分钟
- G1：10-30 分钟（取决于爬虫速度）
- G2：10 分钟
- G3：10 分钟
- G4：15 分钟

**总计**：50-80 分钟完成首次 run

后续 runs 会更快（熟悉流程后 30 分钟以内）。
