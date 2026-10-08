# CHAT-FIRST / WORK-MINIMAL — binding development rule

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


- Writes to production/other PLN require explicit separate approval. The user granted continuing authorization for **only** the exact test PLN `C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\Тест MER .pln` (including trailing space in the project name). The local executor must still enforce scoped operation approval records, live project identity, replay protection, and readback; no new permission question is needed within that scope.
- Before any live write, verify the exact currently open project/instance, not a stale port. Read back what actually changed; do not claim success from an unverified command.
- A read-only bridge is not a write-capable bridge. Preserve project identity checks, replay protection, and audit evidence when enabling write execution.

This rule supplements existing project documentation and does not weaken restrictions on licensed tools, data privacy, or live-model modifications.
