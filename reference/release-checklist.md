# Release checklist

Ordered, language-agnostic. Driven by `.agentstrap/config.json` → `release`.

1. **Determine target version** (arg or next from changelog). Confirm with the user.
2. **Bump every version file** in `release.version_files` — they MUST all match. (`{path, field}` each.)
3. **Finalize the changelog** — move `Unreleased` into a dated `vX.Y.Z` section.
4. **Build** — run `release.build_command`. **Hard gate:** abort on failure.
5. **Test** — run `release.test_command`. **Soft gate:** report failures and ask before proceeding.
6. **Commit + tag** — `release: vX.Y.Z` and tag `vX.Y.Z`. **Never auto-push.**
7. **Checksums** — SHA-256 of release artifacts in `release.artifact_dir` → `SHA256SUMS.txt`.
8. **Final checklist** — print: all version files matched, build clean, tests status, changelog dated, tag created, checksums written. List artifacts with sizes.

The user pushes manually (`git push --tags`) after reviewing.
