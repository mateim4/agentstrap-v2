# Audit personas

The `/agentstrap:audit` swarm. Each persona is a subagent in `agents/`. All report findings on the unified **P0–P3** scale (`reference/severity-scale.md`) and stay strictly read-only.

| Persona (`agents/…`) | Lens | Default model |
| --- | --- | --- |
| `audit-code-quality` | Correctness, readability, dead code, error handling, duplication. | sonnet |
| `audit-security` | Vulnerabilities; STRIDE + deployment-context severity. | opus |
| `audit-architecture` | Boundaries, coupling, data flow, scalability of the design. | sonnet |
| `audit-performance` | Hot paths, queries (N+1), rendering, bundle size, memory. | sonnet |
| `audit-documentation` | README/setup accuracy, API docs, changelog, misleading comments. | sonnet |
| `audit-testing` | Coverage gaps, missing edge cases, flaky patterns, test quality. | sonnet |
| `audit-ux-accessibility` | WCAG 2.2 AA, keyboard, states, Core Web Vitals. | sonnet |
| `audit-adversarial` | Red-team: chains weaknesses into concrete abuse scenarios. | opus |

A separate `research-delegate` is **not** an auditor — it's the worker the main thread uses to keep its own context clean (working rule 9).

## Finding format (every auditor emits this)

```
### <P0|P1|P2|P3> — <title>
- File: <path:line>
- Lens: <persona>
- What happens: <concrete description>
- Why it matters: <impact>
- Fix: <specific recommendation>
- [security only] STRIDE: <category> · Context: <🔴|🟡|⚪>
```
