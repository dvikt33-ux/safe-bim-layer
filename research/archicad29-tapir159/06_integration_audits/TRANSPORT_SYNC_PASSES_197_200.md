# TRANSPORT / SYNC RESEARCH — passes 197–200

Date: 2026-09-28

## Pass 197 — network-loss and partial-delivery fault model
Remote transport must never be part of a physical BIM transaction.

Failure cases:
- Internet disappears before context upload;
- context upload succeeds but ChatGPT does not generate a job;
- job is written to GitHub but local bridge does not fetch it yet;
- local bridge fetches job, then Internet disappears;
- result cannot be uploaded after successful local execution.

Required semantics:
- local Safe BIM journal is authoritative for execution state;
- no job is considered accepted until its manifest and payload are fully present and validated;
- a job once admitted locally can complete without Internet if all required context/payload is already local;
- result publication is retryable and idempotent;
- remote absence never causes rollback or duplicate execution;
- duplicate remote job IDs are no-ops after durable local receipt.

Conclusion: network failures degrade synchronization, not model integrity.

## Pass 198 — exact context-capture UX
When ChatGPT requests context, the palette should not throw a modal dialog unless strict mode is selected.

Recommended compact state:

```text
ИИ: считываю проект…
Контекст #184
⚠ Не изменяйте подсвеченные элементы  [Отмена]
```

Capture sequence:
1. read project identity / modification stamp;
2. freeze the current local index generation;
3. reconcile dirty GUID queue;
4. read selection + active story + requested details;
5. read project stamp again;
6. if stamp changed during capture, repeat once or return `CONTEXT_CHANGED_DURING_CAPTURE`;
7. publish coherent context;
8. create a context lease.

For a broad operation with no target GUID set, show `Не изменяйте проект до получения задания` only during the short strict-capture window. After snapshot publication, edits may continue, but they invalidate the lease and force regeneration before write.

This is safer than trying to physically disable Archicad editing for the entire AI thinking period.

## Pass 199 — fastest daily-work data path
Separate fast local work from remote AI work:

```text
MECHANICAL / CERTIFIED
Palette → local Safe BIM → Archicad
(no GitHub, no AI, works offline)

NOVEL / AI
ChatGPT ↔ private GitHub mailbox ↔ local Bridge
                       ↓
                 local Safe BIM
                       ↓
                   Archicad
```

Local bridge keeps a hot project mirror, so AI context capture does not rebuild the entire project on demand.

Remote data should be demand-scoped:
- project identity;
- story structure / active story;
- selection;
- project/profile summary;
- relevant GUID records;
- relevant relations;
- QA around target neighborhood;
- recent changes needed to interpret the task.

Do not upload full floor-plan polygons, large images, full attributes or all element geometry unless requested by task scope.

## Pass 200 — out-of-box installation contract
The final user-facing contract should be:

### Normal daily startup
1. Start Archicad.
2. Safe BIM loads.
3. The bundled Bridge starts/is already running silently.
4. Local IPC connects automatically.
5. Local cache and QA start automatically.
6. Remote ChatGPT bridge connects in background.
7. User works.

No PowerShell, terminal, manual Python process, Ollama launch, GitHub Desktop interaction or token copying.

### First installation exception
A private cloud mailbox cannot be securely accessed on a new machine without an authorization relationship. Safe BIM must therefore hide credential mechanics behind either:
- silent reuse of existing standard Git/GCM credentials; or
- one-time browser authorization (`Подключить GitHub`) through OAuth/GitHub App.

The product must never ask the user to create/copy a PAT or embed a long-lived token in the Add-On.

### Runtime when remote bridge is down
Safe BIM stays fully usable for:
- deterministic recipes;
- similar selection;
- QA;
- history;
- sandbox;
- local code/recipe execution.

Only external ChatGPT transport becomes unavailable.

**Pass-200 conclusion:** the design can meet the intended “out of the box” daily UX. The only unavoidable setup boundary is one-time secure account authorization on a machine where no reusable GitHub credential already exists.