---
name: handoff
description: Force a full handoff refresh now — write a thorough narrative of where work stands into HANDOFF.md so the next session (or device) resumes cleanly. Use when wrapping up, before switching machines, or when asked to checkpoint.
disable-model-invocation: true
---

# Refresh the handoff now

The hooks keep the auto-state block current every turn; this skill refreshes the **narrative** that only you can write.

1. Find `HANDOFF.md` (from `.agentstrap/config.json` → `continuity.handoff_file`, relative to `continuity.vault_path`).
2. Edit the sections **above** the `<!-- AGENTSTRAP:AUTO-STATE -->` marker — leave the marker block to the hooks:
   - **What was done** — concrete progress this session.
   - **What's next** — the immediate next step(s), specific enough to resume cold.
   - **Blockers** — what you're waiting on and who can unblock it.
   - **Files to review first** — the 2–5 files/notes to open on resume.
   - **Open questions in flight** — pointers into the Open Questions register.
3. Be concrete and concise — write it for "future Claude on another machine with no memory of this chat."
4. Save. The `Stop` hook refreshes the auto-state and syncs it at the end of this turn (subject to the push throttle), and the `SessionEnd` hook guarantees a final push. No manual command is required.
