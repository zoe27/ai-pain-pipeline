# Cursor Agent：Pipeline 命令自动执行

Agent 跑 Stage 0–3 时会频繁调用 `python3 helpers/*.py`。默认每条命令都要人工点批准，影响流水线效率。

本仓库通过 **项目级 Cursor 配置** 只放行 pipeline 相关命令，危险操作仍拦截或需审批。

## 机制（两层）

| 层 | 文件 | 作用 |
|----|------|------|
| **白名单** | [`.cursor/permissions.json`](../.cursor/permissions.json) | `terminalAllowlist`：列出的命令免审批直接跑 |
| **黑名单 hook** | [`.cursor/hooks.json`](../.cursor/hooks.json) + [`deny-destructive.sh`](../.cursor/hooks/deny-destructive.sh) | 拦截 `git push --force`、`rm -rf` 等 |

另：`autoRun.instructions` 在 **Auto-review** Run Mode 下引导分类器，对未在白名单但安全的命令减少误拦。

## 使用前：Cursor 设置

1. **Cursor Settings → Agents → Run Mode** → 选 **Auto-review**（推荐）或 **Allowlist**
2. 重启 Cursor 或重开项目，使 `.cursor/permissions.json` 生效
3. 若白名单不生效：确认 Run Mode 不是 deprecated 的「Ask Every Time」

> 定义 `terminalAllowlist` 后，IDE 内对应 allowlist 编辑器变为只读；以 repo 内 JSON 为准。

## 已自动放行的命令

- 全部 `helpers/` 下的 pipeline 脚本（fetch / build / digest / eval / smoke）
- 只读 git：`status`、`diff`、`log`、`branch`、`show`
- 创建 run 目录：`mkdir -p runs/*`

## 仍需人工批准（故意未放行）

| 命令 | 原因 |
|------|------|
| `git push` / `gh pr create` | 写远程 |
| `fetch_*` 需外网时 | sandbox 可能仍弹 network 权限 |
| 读/写 `.env` | 凭证 |
| `rm -rf` 等 | hook 直接 deny |

## 扩展白名单

编辑 `.cursor/permissions.json`，按 [Cursor permissions 文档](https://cursor.com/docs/reference/permissions) 语法追加：

```json
"python3 helpers/new_helper.py*"
```

`*` 匹配后续任意参数；`cd helpers && python3 ...*` 形式也要单独加（Agent 常带 `cd`）。

## 安全说明

- Allowlist **不是安全边界**，prompt injection 仍可能绕过；hook 作第二层防护
- 团队共享：配置在 git 里，clone 即得同一策略
- 个人全局策略可叠加 `~/.cursor/permissions.json`（与用户级合并）

## 验证

1. Agent 跑：`python3 helpers/digest.py runs/pipe_xxx/1_pain_points.json` → 应无批准弹窗
2. Agent 跑：`git push --force` → hook 应 deny
3. **Hooks** 输出通道 / Settings → Hooks 查看 hook 是否加载
