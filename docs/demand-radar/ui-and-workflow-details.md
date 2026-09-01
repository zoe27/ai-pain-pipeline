# DemandRadar UI 与工作流详细设计

## 1. 产品锚定输入（G0）

### 1.1 支持的输入方式

| 输入类型 | 示例 | 自动提取信息 |
|---------|------|-------------|
| **Website URL** | `https://example.com` | 产品描述、功能、关键词（通过爬取首页/About） |
| **GitHub Repo** | `https://github.com/user/project` | README、技术栈、star 数、主题标签 |
| **手动描述** | 文本框填写 | 产品描述、核心功能、目标用户 |

### 1.2 输入界面

```
┌────────────────────────────────────────────────────────┐
│  产品锚定                                               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  方式 1: 输入 URL                                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │ https://yourproduct.com                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  或                                                    │
│                                                        │
│  方式 2: GitHub 仓库                                   │
│  ┌──────────────────────────────────────────────────┐ │
│  │ https://github.com/user/project                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  或                                                    │
│                                                        │
│  方式 3: 手动描述                                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 我们是一个 AI PDF 处理 SaaS...                    │ │
│  │                                                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  [ 分析产品 ] →                                        │
└────────────────────────────────────────────────────────┘

分析后展示：
┌────────────────────────────────────────────────────────┐
│  ✓ 产品信息已识别                                       │
├────────────────────────────────────────────────────────┤
│  产品: AI PDF Processing SaaS                          │
│  核心功能: PDF 转换、OCR、批量处理                      │
│  目标关键词: pdf converter, ocr, pdf to excel (8 个)   │
│  识别的竞品: Adobe Acrobat, Smallpdf, ILovePDF         │
│                                                        │
│  [ 编辑 ] [ 继续配置扫描 →]                            │
└────────────────────────────────────────────────────────┘
```

---

## 2. 扫描配置（G0 补充）

### 2.1 渠道选择

```
┌────────────────────────────────────────────────────────┐
│  选择扫描渠道                                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ☑ Reddit              （推荐，intent 信号强）         │
│  ☑ Hacker News         （推荐，技术产品）               │
│  ☐ Quora               （Phase 2）                     │
│  ☐ Product Hunt        （Phase 2）                     │
│  ☐ Twitter/X           （Phase 2）                     │
│  ☐ Google Autocomplete （Phase 1 可选）                │
│                                                        │
│  [ 使用默认配置 ] [ 自定义 →]                          │
└────────────────────────────────────────────────────────┘
```

### 2.2 账号配置（可选，用于后续一键发布）

```
┌────────────────────────────────────────────────────────┐
│  关联社交账号（可选）                                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  连接后可一键发布评论到对应平台                         │
│                                                        │
│  Reddit                                                │
│  [ Connect Reddit Account ]                            │
│                                                        │
│  Twitter/X                                             │
│  [ Connect Twitter Account ]                           │
│                                                        │
│  Hacker News                                           │
│  [ Connect HN Account ]                                │
│                                                        │
│  [ 跳过，稍后配置 ] [ 开始扫描 →]                       │
└────────────────────────────────────────────────────────┘
```

**账号配置数据结构（存储在 `product_context.json`）：**

```json
{
  "connected_accounts": {
    "reddit": {
      "username": "your_reddit_user",
      "auth_token_encrypted": "...",
      "connected_at": "2026-09-01T10:00:00Z",
      "status": "active"
    },
    "twitter": {
      "handle": "@yourhandle",
      "auth_token_encrypted": "...",
      "connected_at": "2026-09-01T10:00:00Z",
      "status": "active"
    }
  }
}
```

---

## 3. 发现结果展示（G1-G3）

### 3.1 Demand Map 总览

```
┌────────────────────────────────────────────────────────┐
│  Demand Map — AI PDF SaaS                              │
│  已发现 147 个需求信号 → 聚类为 12 个机会               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🔥 High Priority                                      │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 1. PDF → Excel          Score: 94   ▲ Trending  │ │
│  │                                                  │ │
│  │ 📊 SEO Opportunities: 3                          │ │
│  │ 💬 Community Posts: 8                            │ │
│  │                                                  │ │
│  │ [ View Details ] [ Quick Actions ▼ ]            │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 2. Invoice OCR          Score: 89   → Stable    │ │
│  │ 📊 SEO: 2  💬 Community: 5                       │ │
│  │ [ View Details ]                                 │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 3. PDF API              Score: 87   ▲ Growing   │ │
│  │ 📊 SEO: 4  💬 Community: 12                      │ │
│  │ [ View Details ]                                 │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  [ View All 12 Clusters ]                              │
└────────────────────────────────────────────────────────┘
```

### 3.2 详情页 — 完整可视化

点击 "View Details" 后：

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Demand Map                                        │
├──────────────────────────────────────────────────────────────┤
│  Demand Cluster: PDF → Excel                                 │
│  Score: 94 (High) | Trend: ▲ Growing                        │
├──────────────────────────────────────────────────────────────┤
│  信号来源:                                                    │
│  • Reddit discussions: 47 (90 days)                          │
│  • HN threads: 12                                            │
│  • Search volume: ~8,100/month (Trends)                      │
│  • Commercial intent: High                                   │
│  • Competition: Medium                                       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  📊 SEO Opportunities (3)                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. /pdf-to-excel — Converter Landing Page             │ │
│  │                                                        │ │
│  │ Rationale: 47 Reddit threads 询问 PDF→Excel 工具      │ │
│  │                                                        │ │
│  │ [ Preview Page ▼ ]                                     │ │
│  │                                                        │ │
│  │ ┌────────────────── Page Mockup ────────────────────┐ │ │
│  │ │                                                    │ │ │
│  │ │  # PDF to Excel Converter — Free Online           │ │ │
│  │ │                                                    │ │ │
│  │ │  Convert PDF tables to Excel spreadsheets         │ │ │
│  │ │  instantly with AI-powered OCR.                   │ │ │
│  │ │                                                    │ │ │
│  │ │  [Upload PDF] [Try Demo]                          │ │ │
│  │ │                                                    │ │ │
│  │ │  ## How It Works                                  │ │ │
│  │ │  1. Upload your PDF                               │ │ │
│  │ │  2. Our AI extracts tables...                     │ │ │
│  │ │                                                    │ │ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │ [ Generate Full HTML ] [ Edit ] [ Publish ]            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. /guides/how-to-convert-pdf-to-excel                │ │
│  │                                                        │ │
│  │ Type: How-to Guide                                     │ │
│  │ Rationale: 长尾搜索意图 + 教程缺口                      │ │
│  │                                                        │ │
│  │ [ Preview Outline ▼ ]                                  │ │
│  │                                                        │ │
│  │ ┌────────────────── Article Outline ────────────────┐ │ │
│  │ │                                                    │ │ │
│  │ │  # How to Convert PDF to Excel (2026 Guide)       │ │ │
│  │ │                                                    │ │ │
│  │ │  ## Introduction                                  │ │ │
│  │ │  ## Method 1: Using Online Converters             │ │ │
│  │ │  ## Method 2: Manual Copy-Paste                   │ │ │
│  │ │  ## Method 3: OCR for Scanned PDFs                │ │ │
│  │ │  ## Best Practices                                │ │ │
│  │ │  ## FAQ                                           │ │ │
│  │ │                                                    │ │ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │ [ Generate Full Article ] [ Edit Outline ]             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. /api/pdf-to-excel — API Documentation Page         │ │
│  │ [ Preview ] [ Generate ]                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  💬 Community Opportunities (8)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Reddit • r/productivity • 2 days ago • 34 upvotes      │ │
│  │                                                        │ │
│  │ 原帖标题:                                               │ │
│  │ "Anyone know a good PDF to Excel converter?"          │ │
│  │                                                        │ │
│  │ [ View Full Thread → ]                                 │ │
│  │                                                        │ │
│  │ 原帖内容预览:                                           │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │ I have a bunch of monthly reports in PDF that I  │ │ │
│  │ │ need to convert to Excel for analysis. Most      │ │ │
│  │ │ tools I tried mess up the formatting. Any recs?  │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │ AI 生成的回复:                                          │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │ I've been using [YourProduct] for exactly this.  │ │ │
│  │ │ It handles complex tables really well and keeps  │ │ │
│  │ │ the formatting intact. They have a free tier     │ │ │
│  │ │ that should work for your use case.              │ │ │
│  │ │                                                  │ │ │
│  │ │ For batch processing, their API is also great.   │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │ Commercial Intent: ⚠️ Medium (求推荐，但非购买意图)    │ │
│  │ Relevance: 95%                                         │ │
│  │                                                        │ │
│  │ [ Edit Reply ] [ Post to Reddit ] ✓ 账号已连接        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ HN • Ask HN • 5 days ago • 128 points                 │ │
│  │                                                        │ │
│  │ "Best tools for extracting tables from PDF?"          │ │
│  │                                                        │ │
│  │ [ View Thread ] [ See Reply ]                          │ │
│  │                                                        │ │
│  │ AI 生成的回复:                                          │ │
│  │ ┌──────────────────────────────────────────────────┐ │ │
│  │ │ For complex tables, we built [YourProduct] to    │ │ │
│  │ │ handle exactly this problem. The key challenges  │ │ │
│  │ │ are: 1) merged cells, 2) multi-line headers...   │ │ │
│  │ └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │ Commercial Intent: 🟢 High (技术讨论 + 工具对比)       │ │
│  │                                                        │ │
│  │ ⚠️ HN 账号未连接 [ Connect HN Account ]               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [ View All 8 Posts ]                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. 一键发布工作流

### 4.1 发布按钮状态

| 状态 | 界面显示 | 操作 |
|------|---------|------|
| **账号已连接** | [ Post to Reddit ] ✓ 账号已连接 | 点击后弹出确认框 → 立即发布 |
| **账号未连接** | ⚠️ Reddit 账号未连接 [ Connect ] | 跳转到 OAuth 授权 |
| **已发布** | ✓ Posted 2 hours ago [ View Post ] | 查看已发布的评论 |
| **发布失败** | ❌ Failed to post [ Retry ] | 显示错误信息 + 重试 |

### 4.2 发布确认弹窗

```
┌────────────────────────────────────────────────────────┐
│  确认发布到 Reddit                                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  目标: r/productivity                                  │
│  原帖: "Anyone know a good PDF to Excel converter?"    │
│                                                        │
│  你的回复:                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │ I've been using [YourProduct] for exactly this.  │ │
│  │ It handles complex tables really well...         │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ☐ 同时关注该帖子后续讨论                               │
│                                                        │
│  [ 取消 ] [ 确认发布 ]                                 │
└────────────────────────────────────────────────────────┘
```

### 4.3 发布后跟踪

```json
{
  "post_id": "comm_001",
  "platform": "reddit",
  "thread_url": "https://reddit.com/r/productivity/...",
  "posted_at": "2026-09-01T12:00:00Z",
  "posted_by": "your_reddit_user",
  "reply_url": "https://reddit.com/r/productivity/.../comment_id",
  "status": "published",
  "metrics": {
    "upvotes": 12,
    "replies": 3,
    "clicks": 47
  }
}
```

---

## 5. 数据结构补充

### 5.1 `product_context.json` 扩展

```json
{
  "growth_id": "growth_2026-09-01_001",
  "product_input": {
    "type": "url",  // "url" | "github" | "manual"
    "value": "https://example.com",
    "github_repo": null,
    "manual_description": null
  },
  "product_info": {
    "name": "YourProduct",
    "description": "AI PDF processing SaaS",
    "core_capabilities": ["pdf-to-excel", "ocr", "batch"],
    "target_keywords": ["pdf converter", "pdf ocr"],
    "competitors": ["Adobe", "Smallpdf"]
  },
  "scan_config": {
    "sources": ["reddit", "hackernews"],
    "custom_keywords": [],
    "date_range": "90_days"
  },
  "connected_accounts": {
    "reddit": {
      "username": "user",
      "status": "active",
      "connected_at": "2026-09-01T10:00:00Z"
    }
  }
}
```

### 5.2 `g4_content_drafts.json` 中的 community reply

```json
{
  "community_replies": [
    {
      "reply_id": "reply_001",
      "cluster_id": "pdf-to-excel",
      "platform": "reddit",
      "source": {
        "url": "https://reddit.com/r/productivity/...",
        "subreddit": "r/productivity",
        "title": "Anyone know a good PDF to Excel converter?",
        "author": "user123",
        "posted_at": "2026-08-30T10:00:00Z",
        "upvotes": 34,
        "full_text": "I have a bunch of monthly reports..."
      },
      "generated_reply": {
        "text": "I've been using [YourProduct] for exactly this...",
        "tone": "helpful",
        "mentions_product": true,
        "commercial_intent": "medium"
      },
      "relevance_score": 95,
      "commercial_intent": "medium",
      "post_status": "pending",  // "pending" | "published" | "failed"
      "published_at": null,
      "published_url": null
    }
  ]
}
```

---

## 6. MVP 实现优先级

| 优先级 | 功能 | Phase |
|-------|------|-------|
| P0 | 产品 URL/GitHub 输入 | 1 |
| P0 | 渠道默认配置（Reddit + HN） | 1 |
| P0 | Demand Map 总览 | 1 |
| P0 | SEO 页面预览（mockup/outline） | 1 |
| P0 | Community 原帖显示 + 生成回复 | 1 |
| P1 | 渠道自定义选择 | 1 |
| P1 | 账号连接（OAuth） | 2 |
| P1 | 一键发布到 Reddit | 2 |
| P2 | SEO 页面完整生成 + HTML 导出 | 2 |
| P2 | 发布后跟踪（metrics） | 2 |
| P3 | 多账号管理 | 3 |
| P3 | 发布日程排期 | 3 |

---

## 7. 核心设计原则

1. **来源可追溯** — 每条建议都关联原始数据源（帖子链接、搜索词）
2. **内容可预览** — 发布前必须能看到完整效果（页面 mockup、评论文本）
3. **账号可选配** — MVP 可不连接账号，手动复制粘贴；连接后一键发布
4. **审核必经** — 自动生成，但人工 Approve 后才真正发布
5. **反馈闭环** — 记录发布后的 metrics，反哺 Demand Score（Phase 3）

