---
name: zhihu-cookie-export
description: Guides exporting Zhihu login cookies for DemandRadar fetch_zhihu.py, validates the cookie file without printing secrets, and probes API access. Use when fetch_zhihu is blocked by 403/verification, user asks how to export cookies, or running /zhihu-cookie-export.
---

# zhihu-cookie-export Skill

## Role
帮助用户把**本机浏览器里已登录的知乎 Cookie**导出为项目可用的本地文件，供 `helpers/fetch_zhihu.py --cookies` 抓取真实搜索结果。

## 重要约束

1. **Agent 无法直接读取用户浏览器 Cookie** — 必须由用户在本机浏览器完成导出。
2. **永远不要**把 Cookie 值打印到聊天、日志、commit message 或 PR。
3. **永远不要** `git add` `configs/zhihu.cookies.json` 或任何含 `z_c0` 的真实 Cookie 文件。
4. 验证时只报告「缺哪些 key / probe 是否成功」，不回显 cookie value。

## 何时使用

- `fetch_zhihu.py` 返回 403 /「环境异常」/「需要验证」
- 用户说「导出 cookie」「给 cookie」「知乎登录」
- 准备跑 DemandRadar G1 真实抓取前

## 目标文件

| 文件 | 用途 |
|------|------|
| `configs/zhihu.cookies.example.json` | 模板（可提交） |
| `configs/zhihu.cookies.json` | 真实 Cookie（本地，勿提交） |

## 工作流

复制进度清单并更新：

```
Cookie Export Progress:
- [ ] 1. 用户在浏览器登录知乎并完成验证
- [ ] 2. 用户导出 Cookie 到 configs/zhihu.cookies.json
- [ ] 3. 运行 validate 脚本（不打印密钥）
- [ ] 4. 运行 fetch_zhihu --probe-only
- [ ] 5. probe 成功后继续真实抓取
```

### Step 1 — 告诉用户在浏览器完成登录

请用户：

1. 打开 https://www.zhihu.com 并登录
2. 若出现「环境异常 / 点击验证」，完成验证
3. 确认能正常打开搜索页：https://www.zhihu.com/search?type=content&q=PDF

### Step 2 — 指导用户导出 Cookie

**推荐：Cookie-Editor / EditThisCookie**

1. 安装扩展 Cookie-Editor 或 EditThisCookie
2. 在知乎页面打开扩展 → Export（JSON）
3. 将内容保存为项目根下：`configs/zhihu.cookies.json`

**备选：Chrome DevTools**

1. `F12` → Application → Cookies → `https://www.zhihu.com`
2. 复制至少这些字段的 Value：`z_c0`、`_xsrf`、`d_c0`
3. 写成键值对 JSON：

```json
{
  "z_c0": "...",
  "_xsrf": "...",
  "d_c0": "..."
}
```

扩展导出的数组格式也可以（`[{name,value,domain}, ...]`），`fetch_zhihu.py` 两种都认。

**最低要求：** 必须有 `z_c0`（登录态）。有 `_xsrf`、`d_c0` 更稳。

### Step 3 — 校验文件（不泄露密钥）

用户说「已放好」后，运行：

```bash
python3 .claude/skills/zhihu-cookie-export/scripts/validate_cookies.py configs/zhihu.cookies.json
```

期望输出类似：

```
OK: found required keys: z_c0, _xsrf, d_c0
```

若失败：根据脚本提示缺哪些 key，让用户补齐，**不要**让用户把 value 贴到聊天里。

### Step 4 — Probe 知乎 API

```bash
source .venv/bin/activate
python3 helpers/fetch_zhihu.py <growth_id> --cookies configs/zhihu.cookies.json --probe-only
```

- 成功：`✓ Zhihu search API reachable` → 进入 Step 5
- 失败 403/验证：让用户重新在浏览器过验证并重新导出 Cookie（Cookie 过期或未验证）

### Step 5 — 真实抓取

```bash
python3 helpers/fetch_zhihu.py <growth_id> --cookies configs/zhihu.cookies.json
```

成功后继续 DemandRadar：写 `_judgments/g1.json` → `build_demand_signals.py` → G2/G3/G4。

## Agent 话术模板

用户刚问「cookie 如何给」时，用简短步骤引导，并指向本 skill；不要贴长篇文档。

用户放好文件后，只跑 validate + probe，确认「可用」即可继续 pipeline。

## 安全检查清单

- [ ] `configs/zhihu.cookies.json` 在 `.gitignore` 中
- [ ] 聊天里未出现任何 cookie value
- [ ] 未把 cookie 文件加入 commit
