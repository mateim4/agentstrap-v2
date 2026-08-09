# Credentials and secrets

**The single place credentials live.** Link to this note from anywhere that needs one — never copy a password, token, or key into a spec, a handoff, a decision entry, or a chat message.

> ⚠️ **Before adding anything:** this note lives in the docs vault, which is usually a git repository and may be synced across devices. Treat it as *shared-team-visible*, not as a secret store. Production keys, payment credentials and anything whose leak is unrecoverable belong in a real secrets manager — record only a **pointer** to them here (where they live, who has access), never the value.

## What goes here

- Shared test/QA logins for the team.
- Local development defaults (database user, seeded admin account).
- **Pointers** to where real secrets live — the vault/secrets-manager path, the environment variable name, who can grant access.

## What never goes here

- Production credentials, API keys with real spend or real data behind them, signing keys.
- Anything a customer or regulator would consider personal data.

## Accounts

| What | Where it's used | Username | Secret | Notes |
|---|---|---|---|---|
| (none recorded yet) | | | | |

## Pointers to real secrets

| Secret | Lives in | Who can grant access |
|---|---|---|
| (none recorded yet) | | |
