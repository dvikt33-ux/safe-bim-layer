# Handoff to Arena

STATUS: TRANSFER REQUIRED — local Arena commits exist, but are not yet on GitHub.

Known Arena state from the latest report:
- local branch: `arena/t0-probes`
- 2 local commits
- bundle commit starts with `97da758`
- exported bundle: `/home/user/handoff/arena-t0-probes.bundle`
- Arena environment has no `gh`, PAT, or SSH push path, and must not receive user secrets.

Shared GitHub target already exists:
- repository: `dvikt33-ux/safe-bim-layer`
- branch: `arena/t0-probes`
- target paths under that branch: `bimexec/probes/`

Required source files:
- `bimexec/probes/probe_t0a.py`
- `bimexec/probes/probe_t0b.py`
- `bimexec/probes/backends.py`
- `bimexec/probes/T0_PLAN.md`
- `bimexec/probes/README_RUN_WINDOWS.txt`
- `bimexec/probes/SHA256SUMS.txt`

## Transfer protocol
Do NOT ask for PAT, SSH keys, or any secret.

Preferred path:
1. Keep the exact local commits and bundle unchanged.
2. Surface `arena-t0-probes.bundle` as a user-visible file attachment/artifact if the environment supports it. Also surface the `.diff`/patches if already exported.
3. Do not regenerate source from prose and do not squash the two local commits.
4. Work/Codex will import the bundle on a machine with repository write access and push the exact commits to GitHub branch `arena/t0-probes`.
5. After push, ChatGPT will compare the remote branch against `main`, review the files, and create/review a PR before any merge.

If file attachment/export is impossible, report that explicitly and provide the exact names and sizes of the exported bundle, diff, and patch files so the transfer blocker is unambiguous. Do not fall back to secrets.

## Safety
- Do not run T0B.
- Do not perform any Archicad write.
- Do not write directly to `main`.
- No production Router integration yet.

Work/Codex separately owns live Windows read-only checks and T0A execution once the probe source is available.
