# Inspector Plugins distribution

This repository distributes three independent, read-only local Codex plugins.
Keep upstream runtime files byte-identical to the pinned release archives.
Do not add runtime downloads, hooks, orchestration, shared caches or databases.
Never alter a user's Codex config, personal marketplace, credentials or policies
from repository scripts. Use isolated test homes for installation checks.

`main` holds documentation, the release lock and offline distribution tooling.
The `macos-arm64`, `linux-x64` and `windows-x64` branches each contain exactly
three self-contained plugin packages and the root Codex marketplace catalog.
Update release pins deliberately. Preserve all upstream licenses and notices.
Do not publish personal paths, credentials, private research or fixture captures.

Required checks: `python3 -m unittest discover -s tests -v`,
`python3 scripts/verify.py`; for each distribution, run the verifier at its root
and run `--smoke` on the matching operating system. Do not execute foreign binaries.
Use standard public GitHub runners, read-only default tokens and full action SHAs.
