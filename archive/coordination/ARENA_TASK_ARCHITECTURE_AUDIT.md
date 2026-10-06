# Safe BIM Layer: architecture audit (read-only first pass)

You are reviewing a Python project that acts as a safety layer around Archicad/Tapir MCP-style operations.

## Scope

- Review the repository only. Do not access a live Archicad instance.
- Do not open, modify, save, or create `.pln`, `.pla`, `.bpn`, or other real Archicad project files.
- Do not use credentials, API keys, personal data, model files, GGUFs, or machine-specific logs.
- Do not change the default branch and do not push directly to it.
- If you propose code, work in a separate branch and return a pull request or a unified diff only after the review findings are clear.

## Goal

Perform an architecture audit of Safe BIM Layer. Compare its guardrails and operation flow with publicly documented Archicad/Tapir MCP-style approaches where relevant. Focus on safe validation, idempotency, error handling, and prevention of real-project mutation.

## Deliverable

Return a concise report containing:

1. Current architecture: entry points, inputs/outputs, safety boundaries, and dependencies.
2. Top risks, ordered by severity, with concrete file/function references.
3. A comparison to relevant Archicad/Tapir MCP patterns. Clearly label any inference or uncertainty.
4. The smallest worthwhile patch proposal. It must preserve the read-only/no-real-project constraint, avoid new dependencies unless essential, and include tests or a test plan.
5. A unified diff or PR in a new branch only if the patch is genuinely minimal and can be validated without Archicad. Otherwise, stop at the proposal.

Do not perform any external publishing, package installation, secret scanning that exposes values, or live-project operations.
