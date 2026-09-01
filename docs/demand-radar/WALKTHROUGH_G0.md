# DemandRadar G0 Walkthrough

测试 G0（产品锚定）阶段。

## 前置条件

```bash
# 安装依赖
pip install requests beautifulsoup4 fake-useragent pyyaml jsonschema
```

## Step 1: 创建 Growth Run

```bash
# 设置 growth_id
GROWTH=growth_zhihu_$(date +%Y-%m-%d)_001

# 创建目录
mkdir -p runs/$GROWTH/_judgments runs/$GROWTH/_raw
```

## Step 2: 使用 product-focus Skill 生成判断

在 Claude 中：

**Prompt:**
```
使用 product-focus skill。

我的产品信息：
- 产品名称：AI PDF 处理工具
- 产品 URL：https://example.com
- 描述：使用 AI 技术处理 PDF，支持表格提取、OCR、批量转换等功能
- 目标用户：办公人员、财务人员
- 核心功能：PDF 转 Excel、PDF 转 Word、智能 OCR、批量处理

请分析并输出 g0.json
```

**输出示例：**
Claude 会生成类似这样的 JSON：

```json
{
  "product_info": {
    "name": "AI PDF 处理工具",
    "description": "一款基于 AI 的 PDF 处理 SaaS 工具...",
    "core_capabilities": [
      "PDF 转 Excel",
      "PDF 转 Word",
      "智能 OCR 识别",
      "批量文档处理"
    ],
    "target_keywords": [
      "PDF 转换工具",
      "PDF 转 Excel",
      "PDF 转 Word",
      "PDF OCR",
      "扫描件识别",
      "发票识别工具",
      "PDF 批量处理",
      "在线 PDF 工具"
    ],
    "competitors": [
      "Adobe Acrobat",
      "Smallpdf",
      "iLovePDF"
    ],
    "target_user": "办公人员、财务人员、数据分析师"
  },
  "scan_config": {
    "sources": ["zhihu"],
    "date_range": "90_days",
    "max_questions_per_keyword": 20,
    "custom_keywords": []
  },
  "reasoning": "..."
}
```

## Step 3: 保存判断文件

```bash
# 将 Claude 输出的 JSON 保存到：
cat > runs/$GROWTH/_judgments/g0.json << 'EOF'
{
  "product_info": {
    ...
  },
  "scan_config": {
    ...
  }
}
EOF
```

或者直接复制粘贴到文件中。

## Step 4: 运行 Helper 拼装

```bash
python3 helpers/build_product_context.py $GROWTH \
  --product-url "https://example.com"
```

**预期输出：**
```
Loading judgment from runs/growth_zhihu_2026-09-01_001/_judgments/g0.json...
Assembling product context...
Validating against schema...

✓ Product context created: runs/growth_zhihu_2026-09-01_001/product_context.json

Product: AI PDF 处理工具
Keywords: 8
Competitors: 3

Next: python3 helpers/fetch_zhihu.py growth_zhihu_2026-09-01_001
```

## Step 5: 验证输出

```bash
# 查看生成的文件
cat runs/$GROWTH/product_context.json | jq .

# 检查 schema 验证
python3 -c "
import json, jsonschema
with open('contracts/product_context.schema.json') as f:
    schema = json.load(f)
with open('runs/$GROWTH/product_context.json') as f:
    data = json.load(f)
jsonschema.validate(instance=data, schema=schema)
print('✓ Schema validation passed')
"
```

## 故障排除

### 1. ModuleNotFoundError: No module named 'jsonschema'

```bash
pip install jsonschema
```

### 2. Judgment file not found

确保 `runs/$GROWTH/_judgments/g0.json` 存在，且包含 `product_info` 和 `scan_config` 字段。

### 3. Schema validation failed

检查 g0.json 中：
- `target_keywords` 至少有 3 个
- `core_capabilities` 至少有 1 个
- `description` 长度 20-500 字

## 完整示例

```bash
# 1. 创建 run
GROWTH=growth_zhihu_2026-09-01_001
mkdir -p runs/$GROWTH/_judgments runs/$GROWTH/_raw

# 2. 创建 judgment（使用 Claude + product-focus skill）
# 然后保存到 runs/$GROWTH/_judgments/g0.json

# 3. 运行 helper
python3 helpers/build_product_context.py $GROWTH \
  --product-url "https://example.com"

# 4. 查看输出
cat runs/$GROWTH/product_context.json | jq .product_info.name
cat runs/$GROWTH/product_context.json | jq .product_info.target_keywords
```

## 下一步

G0 完成后，进入 G1（知乎信号发现）：

```bash
python3 helpers/fetch_zhihu.py $GROWTH
```

参见 `WALKTHROUGH_G1.md`（待创建）。
