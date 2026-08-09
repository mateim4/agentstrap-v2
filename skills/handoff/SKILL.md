---
name: handoff
description: Force a full handoff refresh now — write a thorough narrative of where work stands into HANDOFF.md so the next session (or device) resumes cleanly. Use when wrapping up, before switching machines, or when asked to checkpoint.
disable-model-invocation: true
---

# Refresh the handoff now

The hooks keep the auto-state block current every turn; this skill refreshes the **narrative** that only you can write.

1. Find `HANDOFF.md` (from `.agentstrap/config.json` → `continuity.handoff_file`, relative to `continuity.vault_path`).
2. Edit the sections **above** the `<!-- AGENTSTRAP:AUTO-STATE -->` marker — leave the marker block to the hooks:
   - **This session** — concrete progress, newest session first. Lead with the bottom line.
   - **What's next** — the immediate next step(s), specific enough to resume cold.
   - **Blockers** — what you're waiting on and who can unblock it.
   - **Files to review first** — the 2–5 files/notes to open on resume.
   - **Open questions in flight** — pointers into the Open Questions register.
3. **Keep the ~2-week window.** The handoff is a working file, not an archive. Before saving, check the oldest session narratives:
   - Anything older than ~2 weeks **moves out** — cut it and append it to the vault-root **Work Log** (permanent, append-only, newest first). Create the Work Log from the AgentStrap template if it does not exist yet.
   - **Durable operational facts do not belong here at all** — machine topology, how to run the stack, ports, known gotchas, environment flags. Move those into their own note (e.g. `40 - Operations/Running the Stack`) and link to it. They are facts about the project, not about a session.
   - **Never put credentials here.** Link to the Credentials and secrets note instead.
4. **Correct what is now false.** The handoff is amend-style and rots fastest. Before saving, verify the claims already in it — branch state, what is pushed, what is committed, what is "awaiting" something that has since landed. Fix anything stale in the same turn; a handoff that lies is worse than one that is thin.
5. Be concrete and concise — write it for "future Claude on another machine with no memory of this chat."
6. Save. The `Stop` hook refreshes the auto-state and syncs it at the end of this turn (subject to the push throttle), and the `SessionEnd` hook guarantees a final push. No manual command is required.
