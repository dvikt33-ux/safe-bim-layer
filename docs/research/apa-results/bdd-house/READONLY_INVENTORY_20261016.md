# BDD house — guarded read-only native Archicad inventory (2026-10-16)

## Purpose / evidence grading

- Target: Archicad 29.2.1 (5101) / Tapir 1.5.10, port **19727**.
- Exact project identity: \`C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln\` (note trailing space in project name).
- Last proven remote context: \`CONTEXT_READY\` for instance \`archicad-19727\`, project hash \`live-local-466106906936337060ca\`, current selection 0. Selection count **does not** establish whether the PLN is empty.
- Stage for this new collector: **IMPLEMENTED / NOT_LIVE_TESTED**. Do not claim model inventory numbers before real execution and GitHub readback.
- Do not manipulate PLN, project selection, source models, or Archicad 30.

## Collector

\`scripts/apa_bdd_inventory_readonly.py\`

- Explicit read allowlist: GetProjectInfo, GetAddOnVersion, GetStories, GetAllElements, GetDetailsOfElements, Get3DBoundingBoxes.
- Fail-closed: exact PLN path/name and port before reads, re-check identity throughout, and verify all element GUIDs again after capture.
- Details/bounding-box retrieval in batches of 48 with per-element read fallback if a batch cannot be read.
- Local full evidence and compact report under \`%TEMP%\APA_BDD_Readonly\`.
- \`--publish\` explicitly creates a new unique report JSON in the **private** \`dvikt33-ux/safe-bim-bridge\` mailbox results directory using the existing \`gh\` credentials. It never deletes or replaces historical messages.
- This tool **does not** generate a PLN, does not export IFC, and does not write or save BIM elements.

## Windows invocation

Download the script from this research branch using the user's authenticated GitHub CLI, then run it with the Python already used for Archicad. Example:

\`\`\`powershell
$b = gh api "repos/dvikt33-ux/safe-bim-layer/contents/scripts/apa_bdd_inventory_readonly.py?ref=research/bdd-house-readonly-inventory-20261016" --jq .content
$p = Join-Path $env:TEMP "apa_bdd_inventory_readonly.py"
[IO.File]::WriteAllBytes($p, [Convert]::FromBase64String(($b -replace '\s','')))
$py = "$env:APPDATA\uv\tools\archicad-mcp-server\Scripts\python.exe"
& $py $p --port 19727 --publish
\`\`\`

If this fails, retain the diagnostic output; never try other model ports automatically.

## Next

After a verified GitHub report appears, quantify existing walls, slabs, roofs, openings and 2D data; calculate model-wide extents from actual bounding boxes; compare against 2022 project drawings before creating any native elements. Source drawing discrepancy between the stated axes 14.18 × 9.28 m and repeated structural dimensions 14.28 × 9.38 m remains unresolved until validated. Write discrepancies and specific construction plan back to \`docs/research/apa-results/\` on a separate branch or draft PR.

## Local bridge scope crash

The installed \`sync_bridge\` host originally crashed on a malformed-for-current-provider \`requestedScope="project"\` request. A local-only defensive quarantine patch restored operation, but is **not persisted in this research branch** and must not be assumed permanent. Do not rerun the old bootstrap script because it checks out commit \`7469b77\` and can erase that local patch.
