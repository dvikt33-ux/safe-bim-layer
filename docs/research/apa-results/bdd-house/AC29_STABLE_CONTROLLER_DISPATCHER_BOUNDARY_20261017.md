# APA AC29 stable production controller / dispatcher boundary

Purpose: connect verified stable APA at C:\LocalAI\APA_AC29_Stable to ordinary GPT ↔ Safe BIM bridge, without rewriting the running AI Dispatcher UI transport.

## Actual routing boundary

- Existing AI Dispatcher 2.2.19 (arena-archicad-project, agent-handoff) routes only target=GPT and target=ARENA. There is no target=APA. It has NOT been edited, restarted, or redirected.
- Existing Safe BIM Mailbox Watcher is pinned to Test MER, dry-run-only. It is NOT a BDD House writer and must not be repointed.
- Archicad production writes continue to require original APA DynamicCommands -> BIM Graph -> SceneWriter and its durable SQLite journal and explicit write scopes.
- New scripts/apa_ac29_production_controller.py is a separate, one-shot GPT bridge companion: not an automatically running dispatcher and not a native executor.

## Minimal working setup

- Verify stable installed selector SHA256 32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce; core and DynamicCommands unchanged; successful stable-install receipt.
- Check protected BDD source PLN SHA256 33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66 and saved working PLN SHA256 e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa.
- The --prepare-block114 action loads already verified source block JSON at commit 8b3bf90d676d6b837312e544d22f289e8dc17991 via authenticated gh API, checks SHA1, and produces a source-qualified but not yet placeable seven-stud local layout.
- The --publish action sends the no-write report to safe-bim-bridge/gpt-live/results, the same GPT evidence route previously used in live AC29 qualification.
- Neither command executes any native Archicad read or write, creates new elements, changes source/working PLN, or activates a background task.

## Current construction gate

Block 1.14 length 2910 mm, seven stud centers at offsets 25, 442, 860, 1272, 1685, 2285 and 2885 mm. Absolute XY and verified reusable parent-Column prototype remain outstanding. No approximate source image coordinates are automatically authorized as BIM placement.

The controller can publish SOURCE BLOCKED / READY evidence; to create anything in BDD House use existing guarded SceneWriter only AFTER native current inventory/prototype, source-verified coordinates, collision checks, and explicit authorization. Preserve previously completed 13 studs, all three Windows, existing walls, roof and structural elements.

No change to main, existing AI Dispatcher, its signal protocol, Arena, AC30, or the stable APA engine. The direct UI Dispatcher target=APA is NOT installed; that would require a separately approved protocol expansion.
