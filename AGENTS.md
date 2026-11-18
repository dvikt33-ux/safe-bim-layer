# CURRENT PRODUCT DELIVERY RULE — 2026-11-16 (DIRECT USER INSTRUCTION)

**Priority: finish usable APA capabilities, not administrative routines.** This newer directive supersedes conflicting historical CHAT-FIRST / WORK-MINIMAL allocations and any interpretation of FULL INTEGRATION that makes reports, hashes, test-counts, CI maintenance or repeated audits the primary deliverable. Work/Codex is authorized as the substantive engineering executor for complex new functionality; connected tools, scripts and CI should handle routine operations.

1. **Product-first acceptance.** Each substantial Work run must target an explicit user-visible capability or the completion of an already-started capability. Define its observable Archicad/PLN result and acceptance evidence before implementation. Count progress in accepted capabilities, not number of commits, tests, documents or SHA-256 receipts.
2. **Close whole vertical slices.** Reuse existing APA, Tapir Bridge, DynamicCommands, SceneWriter, BIM Graph, model-first, documentation and verification machinery. Finish creation/editing, readback and needed Save/Close/Reopen for one capability before calling it COMPLETE. Temporary coexistence of working overlapping modules is acceptable; do not remove one until its replacement is proven.
3. **Routine is supporting work.** Run existing automated tests, CI, hashes, packaging and receipts as necessary gates, preferably in batches. Do not spend a major Work run reauditing stable subsystems, repairing unrelated test infrastructure, authoring extensive reports or re-checking already accepted evidence unless a reproducible blocker directly affects the target feature.
4. **Blocker response.** Record an exact blocker and the minimum operator action. If GUI startup, elevated-process integrity, native API availability or a required local write approval blocks execution, do not circumvent it, attempt indefinite recovery or claim native success; continue permitted independent product implementation and automated tests, with native acceptance remaining PENDING/BLOCKED.
5. **Reuse before building.** Check installed native Archicad/Tapir functions and existing APA implementations first; inspect external C++/MCP/IFC code only for a proven feature gap. Do not introduce a second MCP, SceneWriter or BIM Graph. Preserve license and provenance requirements.
6. **Compact handoff.** Report the capability gained, direct run command, full working GitHub URLs and verified absolute local paths, native test evidence, precise remaining blockers and next usable task. Keep routine log detail in artifacts rather than expanding the user-facing report.
7. **Safety is not reduced.** Live writes require exact project identity, authorized test-copy scope, current operator approval, idempotency/no-replay protection, independent native readback and preserved production PLN. CI PASS alone is not native acceptance. Never merge protected branches or modify originals without authorization.

**Current product priority:** connect the full APA cycle for creating and continuing projects through the existing brief, graph, writer, validation and documentation interfaces. Develop primarily against AC30 / Tapir 2.0 and preserve the working AC29 / Tapir 1.5.10 routes. Use R07 and a distinct design to check the shared workflow. Stair, Wall, persistence and Publisher are acceptance scenarios. When a native operation is blocked, continue independent integration work and preserve the actual acceptance status.

---
 
# Current execution priority — FULL INTEGRATION / NATIVE VALIDATION

Direct user instruction 2026-10-14 supersedes the historical CHAT-FIRST / WORK-MINIMAL allocation below. Work develops and integrates the existing Archicad/Tapir/SDK contracts, runs native Windows tests and publishes one main draft PR. Broad offline audit runs independently against published commits and Windows CI. Reuse BIM Graph, Knowledge Graph, SceneWriter and SQLite; no parallel executor or search implementation. Native permissions remain explicit per project/scope. This does not authorize production projects. MORPH LAST RESORT, identity, retention, UNKNOWN no-replay and publication gates remain binding.

# Historical CHAT-FIRST / WORK-MINIMAL allocation (superseded where conflicting)

# MORPH LAST RESORT — обязательное постоянное правило APA

Действует для создания и редактирования любых конструкций во всех дальнейших задачах, а не только для текущего узла. В первую очередь выбирать штатные параметрические BIM-инструменты Archicad по конструктивному назначению: Wall, Slab, Beam, Column, Roof, Shell, Stair, Railing, Opening, MEP и другие подходящие инструменты.

Morph разрешён только в крайнем случае: подходящие нативные инструменты и доступные API проверены; они не позволяют достоверно реализовать требуемую геометрию; конкретная причина отказа документирована; обязательные BIM-свойства и связи не потеряны. Отсутствие адаптера APA не оправдывает Morph — сначала проверяется и подключается доступный штатный элемент.

Для обрешётки25×150мм и контробрешётки50×50мм приоритет — настоящий нативный Beam. Классификация Beam/IfcBeam не превращает Morph в нативную балку. Проверенный существующий узел сохраняется; новые альтернативы проверяются отдельно с нативным readback и IFC. Текущий цикл поверх PR63 сохраняет все109принятых GUID/геометрию, включая ранее принятые107/96. Четыре исходных стыка Wall/Roof анализируются read-only; их изменения требуют прямого разрешения на конкретные операции в отдельно разрешённой копии. Неполное перекрытие фактической нижней грани не считать полным исправлением. Переименованная тестовая копия разрешается только по прямому указанию пользователя, с точной идентичностью, хешем сохранённого файла и независимой сверкой принятой геометрии до записи.

Applies to the entire `safe-bim-layer` repository, all subdirectories, and subsequent development work using these instructions.

## Primary workflow

- **ChatGPT conversation is the primary development environment.** Perform architecture, research, design, algorithms, writing and reviewing Python/C++/API code, preparing patches, tests, and debugging in ordinary ChatGPT chat whenever possible.
- **Work/Codex is a narrow execution helper, not the default developer.** Use it only for small, necessary actions that require a local computer, running builds/tests, inspecting local files or interacting with software, or other operations unavailable in the chat's connected tools.
- **Prefer connected GitHub actions directly from the chat** for inspecting and updating repositories when available. Do not hand off a whole feature or long research effort merely to edit one file.
- Aim for roughly **90–95% of substantive work in chat and 5–10% in Work**, as a prioritization guideline rather than a mechanical limit.
- If Work is unavoidable, scope it to a single minimal, verifiable action with explicit inputs, outputs and acceptance criteria. Bring the result back to the main chat before planning the next action.
- Preserve the existing project and code; prioritize the smallest working end-to-end vertical slice, then add functionality, performance, validation and security incrementally. Reuse existing proven implementation.
- Minimize Work-credit consumption. Never use Work for tasks that can be accurately completed in normal chat.

## Installed Archicad runtime

- Latest user-confirmed installation (2026-10-09): **Archicad 29.2.1 (5101) RUS FULL (x86-64)**; reference [docs/ARCHICAD_RUNTIME_CURRENT.md](docs/ARCHICAD_RUNTIME_CURRENT.md) for the canonical current build.
- Keep `Archicad 29 DevKit`, `AC29` and Tapir-specific versions as their own API compatibility identifiers; update only the installed application version, not past tests or historical research.


- Writes to production/other PLN require explicit separate approval. The user granted continuing authorization for **only** the exact test PLN `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln` (including trailing space in the project name). The local executor must still enforce scoped operation approval records, live project identity, replay protection, and readback; no new permission question is needed within that scope.
- Before any live write, verify the exact currently open project/instance, not a stale port. Read back what actually changed; do not claim success from an unverified command.
- A read-only bridge is not a write-capable bridge. Preserve project identity checks, replay protection, and audit evidence when enabling write execution.

This rule supplements existing project documentation and does not weaken restrictions on licensed tools, data privacy, or live-model modifications.
