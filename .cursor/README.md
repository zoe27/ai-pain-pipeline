# Cursor 项目配置

| 文件 | 用途 |
|------|------|
| `permissions.json` | Agent 终端命令白名单（pipeline helpers + 只读 git） |
| `hooks.json` | 执行前 hook：拦截破坏性命令 |
| `hooks/deny-destructive.sh` | 黑名单：`git push --force`、`rm -rf` 等 |

详细说明见 [`docs/cursor_agent_permissions.md`](../docs/cursor_agent_permissions.md)。

**Run Mode**：Cursor Settings → Agents → **Auto-review** 或 **Allowlist**。
