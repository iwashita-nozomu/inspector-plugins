# Security

Do not post credentials, private repository contents, research or personal paths
in public issues. Public issues are suitable for non-sensitive reproduction steps
using synthetic examples. Use GitHub private vulnerability reporting when enabled
for a confidential vulnerability report.

This catalog contains pinned, unsigned native executables from the linked public
upstream releases. `releases.lock.json` records their archive SHA256 and source
commits. The per-platform `distribution.json` records every extracted file hash.
Hashes prove consistency with those reviewed pins; they are not author signatures.

Distribution scripts do not install plugins, alter Codex settings or credentials,
download dependencies, run analyzed code, or enable plugins. Installation is an
explicit Codex action. Each MCP server runs as a local host process with the
user's OS access; its read-only annotations are descriptive, not an OS sandbox.
GitHub access reuses the user's `gh` authentication and never grants access.

Update the release lock only after reviewing the source commit, upstream tests,
release digests and license notices. Use standard public CI runners and pinned
official Actions. Do not add runtime fetchers, lifecycle hooks or auto-updaters.
