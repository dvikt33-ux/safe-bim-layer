# APA AC29 — task-scoped runtime selection and stable promotion (2026-10-17)

Scope: close the specific remaining gap after PR #135 **without** changing existing APA core, DynamicCommands, SceneWriter, working PLN, APX, AC30, or \`main\`.

## Implemented

- Existing \`prepare_current_runtime_catalog_task(writer,intent)\` still binds the real current live export, matching current PLN, Tapir and runtime identity, attaches reviewed catalog policies and probes only valid task candidates. It reuses **the same** DynamicCommands router, BIM Graph, and native-plan preview.
- After recompiling the verified candidates, \`select_uniquely_registered_read_alternative\` may pick a **unique** candidate with strictly better **task-scoped registration confidence**, **only** if every operation in every eligible competing graph is independently reviewed as \`READ_ONLY\`. Actual native add-on registration outranks a weaker official-API *product version only* check; missing probe status is not evidence. Ties remain unresolved. \`CREATE/MODIFY\` stay excluded from this heuristic. No automatic native execution or permission is granted; all runs still require existing SceneWriter guards.
- **Registration confidence is NOT speed optimization**: selection method explicitly says \`NOT_COST_OPTIMAL\`, while existing Fast Downward cost selection takes precedence when actual comparable end-to-end measurements exist.
- For namespaced live native Grid/Stair contracts, the original \`verify_native_runtime_identity\` now recognizes the command's bare suffix, preventing a missing APX identity check.

## Release process (two distinct actions)

1. \`scripts/apa_ac29_stable_selector_install.py\`: guarded **offline** promotion from the previously confirmed local working checkout (currently under \`%TEMP%\APA_BDD_NorthPair_20261016_174054\`) to **new, independent** \`C:\LocalAI\APA_AC29_Stable\`. It fails if destination already exists, if any known core/router/discovery digest changed, if required source assets are absent, or if the new sidecar source Git blob differs from its pinned revision. Only \`scripts\`, \`schemas\`, and \`archicad-addon\` are copied; excludes *.pln, temp ledgers, logs and previous updates. It imports the released sidecar in the installed Python interpreter and retains a manifest receipt. **No local deployment is claimed until the user executes and provides a receipt.** It does not switch any running process or silently replace a canonical prior installation.
2. \`scripts/apa_ac29_live_selector_qualification.py\`: run **after** stable promotion with BDD House open in Archicad 29. Reuses the already recovered 2-step READ_ONLY \`apa-capability-task/1\` source, refreshes a current real Tapir schema export into a **new temp folder**, checks the saved source and working PLN hashes and 290-GUID scope, probes only the **eligible selected task command registrations**, makes a preview selection, and publishes a sanitized report to \`safe-bim-bridge\`. It **does not dispatch** \`GetDetailsOfElements\`/\`Get3DBoundingBoxes\`, \`Create*\`, \`Modify*\` or \`SaveProject\`, so it is not a repeat of the earlier live wall-geometry read.

## Existing actual evidence, not a new PASS

The earlier BDD report \`safe-bim-bridge/safe-bim-mailbox/gpt-live/results/apa-bdd-selected-tapir-20261017-133000.json\` already proves six live walls read, 290 GUID retained, zero native writes, and an explicitly chosen Tapir alternative. It did **not** independently prove this new task-scoped runtime registration selection or a permanent deployment.

## Final acceptance

Report must contain \`STABLE_SELECTOR_DEPLOYED_IMPORT_VERIFIED_NO_NATIVE_CALLS\` from step 1, and step 2 must publish real runtime \`RUNTIME_AVAILABLE\` evidence plus \`AUTO_SELECTED_READ_ONLY_BY_RUNTIME_REGISTRATION\` and \`selectedCommands\` with no model writes. Otherwise status is \`PARTIAL\` with the exact blocking reason. Even after that, unexported add-ons, 33 historical source-only contracts and six UNKNOWN effects are **not** all live-enabled and must remain excluded.

No hundreds of repeated functional tests. Five focused unit tests cover only the new tie-break gate. GitHub drafts remain unmerged unless explicitly authorized.
