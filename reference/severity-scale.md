# Severity scale (unified P0–P3)

Every AgentStrap auditor reports findings on **one** scale, so the consolidator never has to translate vocabularies.

| Tier | Meaning | Examples |
| --- | --- | --- |
| **P0 — Critical** | Exploitable now, data loss, or build/ship blocker. Fix before anything else. | RCE, auth bypass, secret leak, data corruption, broken build. |
| **P1 — High** | Serious correctness/security/UX defect; fix this cycle. | Injection behind a flag, N+1 on a hot path, WCAG blocker, missing error handling on a critical path. |
| **P2 — Medium** | Real issue, not urgent; schedule it. | Missing tests, moderate perf waste, inconsistent patterns, weak validation. |
| **P3 — Low** | Polish, nits, opportunistic cleanup. | Naming, dead code, doc gaps, minor a11y. |

### Mapping legacy vocabularies

- Generic audits (CRITICAL / MAJOR / MINOR): CRITICAL→P0, MAJOR→P1, MINOR→P2/P3 by judgement.
- Security (CRITICAL / HIGH / MEDIUM / LOW): CRITICAL→P0, HIGH→P1, MEDIUM→P2, LOW→P3.

## Security: STRIDE + deployment context

Tag each security finding with a **STRIDE** category: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.

Adjust severity by the project's `audit.deployment_context` using a badge:

| Badge | Meaning |
| --- | --- |
| 🔴 APPLIES | Full severity. |
| 🟡 REDUCED | A compensating control lowers it (e.g. air-gapped network eliminates a remote attacker). |
| ⚪ N/A | Not reachable in this deployment. |

- **air-gapped** — external attackers eliminated; network eavesdropping needs physical access. Many remote threats → 🟡/⚪.
- **internal** — trusted network, authenticated users; remote-internet threats reduced, insider/lateral threats full.
- **internet-facing** — all threats at full severity (🔴). Default when unset.

## UI/UX acceptance thresholds (for the ux-accessibility auditor)

- **Accessibility:** WCAG 2.2 AA — contrast ≥ 4.5:1 (normal text) / 3:1 (large); visible focus; keyboard-operable; touch targets ≥ 24×24 CSS px (prefer 44×44).
- **Core Web Vitals:** LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1.
- **States:** every view has loading / empty / error states; forms have inline validation and labels.
