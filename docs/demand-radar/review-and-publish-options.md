# Review & 发布方案设计

## 背景

流水线（G0-G4）可以自动运行，生成知乎回答草稿。
核心需求：**人工 review 草稿，确认后一键发布到知乎。**

两个子需求：
1. **Review UI**：直观查看原贴内容 + 回答草稿，支持编辑
2. **一键发布**：调用知乎 API 提交回答，记录发布状态

发布使用知乎 Cookie 方案（非官方 OAuth），Cookie 从已登录浏览器导出。

---

## 方案对比

### 方案 A：Telegram Bot

**流程：**
```
流水线跑完 → Bot 发消息给你 → 你回复 /publish ans_001 → Bot 调用知乎发布
```

**优点：**
- 无需部署服务，Bot API 轻量
- 手机随时操作，有通知推送

**缺点：**
- 只能发文字消息，编辑体验差
- 不够直观，看不到格式化排版
- 不适合需要调整文案的场景

**适合：** 回答质量很稳定，基本不需要修改，只需要确认发布

---

### 方案 B：部署轻量 Web App（Railway/Render）

**流程：**
```
流水线跑完 → Web App 读取最新 run → 你打开固定 URL → 在页面上 review/编辑/发布
```

**技术：** Flask + 部署到 Railway/Render 免费套餐

**优点：**
- ✅ 随时随地，任意设备浏览器访问
- ✅ 完整 UI：格式化排版、编辑框、发布按钮
- ✅ 发布状态持久化

**缺点：**
- 需要部署配置（约 30 分钟）
- 知乎 Cookie 需要放到云端环境变量（有安全风险）
- Cookie 过期需要重新配置

**安全注意：** Cookie 泄露 = 知乎账号被盗，需确认是否可接受

**适合：** 长期使用，需要完整 review 体验

---

### 方案 C：GitHub Actions + Issue 作为 Review 界面

**流程：**
```
流水线跑完 → 自动创建 GitHub Issue（包含所有草稿）
→ 你在 Issue 评论 /approve ans_001 → GitHub Actions 触发发布脚本
```

**优点：**
- 不需要额外服务，复用 GitHub
- 有版本记录，审计友好

**缺点：**
- 体验生硬，Issue 不适合长文本编辑
- 触发发布链路复杂（Actions → 本机/服务器）
- 发布仍需要有机器执行，结构复杂

**适合：** 团队场景，需要审计记录

---

### 方案 D：本地 Flask Server（当前实现）✅

**流程：**
```
跑完 G4 后手动启动 → python3 review_dashboard.py GROWTH_ID
→ 自动打开浏览器 → review/编辑/发布 → 关闭即止
```

**优点：**
- ✅ 立即可用，无需部署
- ✅ 完整 UI 体验
- ✅ Cookie 在本地，安全
- ✅ 用完即关，不常驻

**缺点：**
- 必须在运行了流水线的机器旁边
- 不适合「流水线自动跑 + 人不在机器旁」的场景

**适合：** MVP 阶段，本地验证流程

---

## 当前决策

**Phase 1（现在）**：方案 D — 本地 Flask Server
- 验证完整流程
- Cookie 本地安全
- 快速实现

**Phase 2（后续）**：方案 B — 部署 Web App
- 需要讨论：Cookie 放云端的安全策略
- 可选：加密存储、短期 token 代替 Cookie

---

## Cookie 安全说明

知乎 Cookie 关键字段：`z_c0`（认证 token）

| 存储方式 | 风险 |
|---------|------|
| 本地文件 `.env` / `configs/` | 低，只在本机 |
| 云端环境变量（Render/Railway） | 中，依赖平台安全 |
| 代码仓库 | 🚨 严禁，会泄露 |

**规则：**
- `configs/zhihu.cookies.json` 加入 `.gitignore`
- 云端部署时通过环境变量注入，不写文件

---

## 知乎发布 API

知乎内部 API（非官方，通过 Cookie 调用）：

```
POST https://www.zhihu.com/api/v4/answers
Content-Type: application/json
Cookie: z_c0=...

{
  "question_id": "123456789",
  "content": "<p>回答内容（富文本）</p>",
  "reshipment_settings": "allowed"
}
```

**注意：**
- content 需要是 HTML 富文本，不是 Markdown
- 需要 `x-zse-96` 签名头（知乎反爬），可能需要逆向
- 发布频率不能太高，建议间隔 > 30 秒

