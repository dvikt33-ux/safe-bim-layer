# APA-P70.A11.S03 — G01 Windows SQLite repair; remaining gaps open

Observed system gapG01 is fixed with actual regression behavior. Legacy SQLite
transaction contexts did not close handles. Eleven fixture connections across
five modules now close after the existing commit/rollback context, and one
read-only suffix-wall diagnostic connection closes on every exit. No assertion,
no-replay protection or cleanup error is suppressed; no forced collection is used.

Local Windows host runs all340tests PASS in57.492seconds, with schema/sample
graph contracts PASS. [CI38191624258](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38191624258) independently
runs all340tests on Ubuntu and all340on Windows, with contracts and PowerShell
syntax validation. Two-platform checks PASS. Restricted Windows sandbox runs
additionally deny atomic replacement of temporary watcher state (WinError5);
these are environmental denials, and the same tests pass on host and CI. The
earlier partial attempts and complete successful logs stay unchanged locally.

[DraftPR54](https://github.com/dvikt33-ux/safe-bim-layer/pull/54), head `2b499730ac4c52b70d796f2857fb15d7e3d3d676`, contains eight allowlisted files and
is stacked on accepted integration draftPR53. New diff additions were scanned
for private paths/secrets. Previously tested code branches remain unchanged.
The repair makes zero native Archicad calls, PLN writes or APX changes. It retains
the22primary/48GUID native system acceptance and save/reopen proof.

S03 remains PARTIAL: only the first observed gap is fixed. Eight gap areas stay
explicit:73Details context adapters; missing manufacturer dimensions/source
commit gate; connected/branched MEP; Shell/Opening/SEO providers; SAM/SAF solver,
loads and norms; full IFC semantics/MCP/Twinmotion; native metadata discrepancies;
large-model performance and installer. Required unsupported scope still blocks
complete engineering/manufacturer/network acceptance. Optimizer/installer stages
must not proceed as if these gaps were complete.

[Selected acceptance](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-012500Z-gap-windows-sqlite-v31/acceptance.json),
[updated gap register](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-012500Z-gap-windows-sqlite-v31/gap-register.json).
Only selected text summaries/hashes are published; full logs remain local. No
local paths, model identities, project catalogs or binary artifacts are uploaded.
Next work remains A11.S03; there is no invented full-product DONE.
