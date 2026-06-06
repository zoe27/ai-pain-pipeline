# Contracts

跨阶段共享的 JSON Schema 文件。Skill 输出必须经过这里的 schema 校验。

人类可读的契约描述见 [../docs/contracts.md](../docs/contracts.md)。

规划中的 schema：

| 文件 | 用途 |
|------|------|
| `pain_point.schema.json` | 阶段 1 输出 |
| `scored_pain_point.schema.json` | 阶段 2 输出 |
| `opportunity.schema.json` | 阶段 3 输出 ✅ |
| `domain_context.schema.json` | 阶段 0 领域定向 ✅ |
| `prd.schema.json` | 阶段 4 输出 |
| `tech_spec.schema.json` | 阶段 5 输出 |
| `pipeline_state.schema.json` | 全局状态机 |

> 占坑中。第一片实现时再从 `docs/contracts.md` 转出对应 schema。
