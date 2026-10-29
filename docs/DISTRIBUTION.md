# Distribution design

The installed Codex CLI 0.164.0 and current official documentation support a Git
marketplace selected with `--ref`, a root `.agents/plugins/marketplace.json`, and
local plugin entries relative to that marketplace root. Git-backed plugin entries
also support `url` and `git-subdir` with `ref` / full commit `sha` selectors.
No documented release-ZIP source or platform selector was found. This project
does not invent either field.

References checked on 2026-10-29:

- [Official package and marketplace documentation](https://developers.openai.com/plugins/build/plugins)
- [Official marketplace source documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management)
- `codex plugin marketplace add --help`, `upgrade --help`, `plugin add --help`, `remove --help`
- Host-bundled Plugin Creator skill and its marketplace sample

The upstream Git source folders contain manifests/skills but do not contain the
built binary. Pointing directly at those folders would install an incomplete MCP
package. Instead, each OS distribution branch vendors all three complete release
packages byte-for-byte. Catalog sources use only the supported local form:

```json
{"name":"code-structure-inspector","source":{"source":"local","path":"./plugins/code-structure-inspector"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Developer Tools"}
```

The user chooses an OS branch or immutable version tag at registration. The Git
marketplace snapshot binds catalog and binaries together. `releases.lock.json`
pins the upstream source SHA, release URL, archive size and SHA256; `distribution.json`
records each extracted file's digest. All license files are preserved.
The root `.gitattributes` disables text conversion for every file, preserving both
LF and CRLF bytes even when a user's global Git setting enables autocrlf.
The moving OS branch is a manual update channel. Version tags and complete Git
commit SHAs provide fixed snapshots. Git tags are not cryptographic signatures.

There is no launcher, install hook, lifecycle script, runtime download, updater,
cross-plugin call or shared runtime state. Existing upstream installers are retained
as part of the exact release but are not invoked by the catalog or Codex install.

## Maintainer workflow

1. Review upstream source/tests/releases, then deliberately edit `releases.lock.json`.
2. Download the exact public archive URLs in that lock into a staging directory,
   using an ordinary reviewed download tool. Do not replace pins with `latest`.
3. Run the offline assembler once per OS, using an output directory that does not exist:

```sh
python3 scripts/assemble.py --platform macos-arm64 --archives downloads --output build/macos-arm64
python3 scripts/verify.py --root build/macos-arm64 --smoke
```

Use `linux-x64` / `windows-x64` on their native hosts. The assembler validates all
archive digests before writing packages, rejects links/traversal/duplicate entries,
and executes nothing. The verifier checks exact file inventories, both manifest
identities/versions, both MCP commands and native binary headers.
Native smoke tests initialize each MCP server, discover its precise read-only tool
set and make a bounded synthetic call. The Git test rejects an invalid repository
identifier before any network request. Foreign binaries are never executed.

4. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/verify.py`.
5. Commit each distribution to its OS branch with its matching catalog. Run native
   CI on the three standard public runners. Preserve the original file bytes.
6. In an isolated, empty Codex test home, use the official CLI to register the
   published branch/tag, list all three entries and install each. Read back the
   installed packages and check tools. Test upgrade/removal there as well.
7. Review changes, publish version tags, record readback/CI evidence. Changing a
   catalog is not permission to migrate a user's existing plugin identities.

Repository Actions default to read-only tokens and use full-SHA-pinned official
Actions. Only the trusted-main CodeQL job receives `security-events: write` to
upload its scan; PR CodeQL has a read-only token and does not upload. There are no
pull-request-target workflows, artifact uploads, stored credentials, contents-write
tokens, self-hosted runners, paid larger runners or automatic publishing.
Dependabot checks Actions pins only; the Python tooling uses the standard library.
Upstream Rust dependencies remain managed in each source repository.
