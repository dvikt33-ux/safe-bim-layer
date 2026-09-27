# PREFINAL AUDIT — DIRECT GITHUB EXECUTION AFTER PASS 176

Date: 2026-09-28

## Goal restated

No copy-paste. User talks to ChatGPT; ChatGPT publishes a job; Safe BIM detects it and starts work automatically.

## What is now sufficiently specified

### Transport
Private GitHub queue is acceptable for v0.1.

### Detection
Conditional polling of one tiny queue head/ref is preferred over webhook relay for the first implementation.

### Execution
GitHub transport never calls Tapir directly. Local Safe BIM admission/runtime remains authoritative.

### Identity
Every job is bound to project ID + snapshot/root hash + recipe hash.

### De-duplication
`job_id + sequence + received commit` are durable local admission keys. Same GitHub job can be observed many times but admitted once.

### UX
Remote write proposal can arrive automatically, validate automatically and prepare Preview/Sandbox automatically. Default physical mutation still requires local confirmation unless the recipe family is explicitly certified for unattended execution later.

## Threat/failure audit

| Failure | Required behavior |
|---|---|
| duplicate GitHub poll | same job ignored after admission |
| rewritten branch/head | immutable received commit pinned; unexpected history change blocks |
| wrong PLN | 0 writes |
| snapshot stale | `STALE_CONTEXT`, 0 writes |
| malformed manifest | reject, 0 writes |
| unknown operation | reject, 0 writes |
| raw arbitrary Python | proposal/review only |
| GitHub outage | no new admission; local admitted job unaffected |
| process restart | resume from local durable state, not from GitHub guess |
| uncertain BIM outcome | existing `UNKNOWN_OUTCOME`; no blind retry |
| token leak | credentials never embedded in APX/UI/repo |

## Auth audit

Prototype can use a fine-grained token restricted to one private repository and minimum contents permission, stored through an OS-protected local service. Do not store token in configuration committed to Git.

Longer-term preferred authentication is a GitHub App because installation tokens are short-lived and repository-scoped, but that is not required for the first prototype.

## Repository design audit

Do not use the current public repositories for actual project state or remote execution jobs containing project-sensitive data.

Create a dedicated private repository, conceptually:

`safe-bim-project-bridge`

Logical areas:

```text
state/       Archicad -> ChatGPT
jobs/        ChatGPT -> Safe BIM
results/     Safe BIM -> ChatGPT
```

A single private repo is simpler for v0.1; later split permissions if needed.

## Prefinal verdict

**ARCHITECTURE READY FOR PROTOTYPE DESIGN: YES**

**FULLY UNATTENDED WRITES AS DEFAULT: NO**

Recommended v0.1 target: automatic delivery + automatic validation/preview + one-click local commit to write. This removes manual code transfer while retaining the final safety boundary in Archicad.
