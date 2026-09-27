# TRANSPORT / SYNC RESEARCH — passes 191–196

Date: 2026-09-28

## Pass 191 — authentication without user-created keys
A private GitHub repository necessarily needs authentication. The user requirement should therefore be interpreted as **no manual PAT/API-key creation and no recurring login/setup**, not as “no authentication can exist”.

Strong options:
- existing standard Git credentials/Git Credential Manager if already configured;
- a Safe BIM GitHub App/OAuth bootstrap using PKCE or device flow;
- short-lived GitHub App installation tokens managed automatically by a helper service.

GitHub recommends GitHub Apps over broad personal tokens and supports fine-grained permissions and short-lived installation tokens. A native client cannot safely ship a reusable secret; token material belongs in OS-protected storage/helper service, never in the Archicad palette/JS.

Decision for v0.1 on the current workstation:
1. probe silently whether standard Git/GCM can access the bridge repo;
2. if yes, use it with no extra user action;
3. if not, provide one `Подключить GitHub` OAuth authorization, never ask the user to create/copy a token;
4. after that, normal startup is zero-touch.

A truly fresh machine cannot access a private repository with literally zero account authorization. That is a hard security constraint, not a UX failure.

## Pass 192 — fresh-context handshake before code generation
Continuous cloud mirroring is unnecessary if ChatGPT can request a fresh coherent context on demand.

Proposed protocol:

```text
ChatGPT receives user task
  ↓
read active project pointer
  ↓
create CONTEXT_REQUEST(job_id, required_scope)
  ↓
Safe BIM bridge detects request
  ↓
freeze local cached snapshot boundary
  ↓
quick reconcile project stamp / selection / dirty GUIDs
  ↓
UI shows context-capture banner
  ↓
publish CONTEXT_READY snapshot
  ↓
ChatGPT reads exact snapshot and generates Safe Recipe
```

This has two benefits:
- the cloud no longer needs every edit;
- ChatGPT is explicitly bound to a task-specific snapshot.

The local cache is kept hot using Archicad notifications/reconciliation, so CONTEXT_REQUEST should usually publish from already-known local state with only targeted refresh.

## Pass 193 — “do not change the project” warning vs productivity
A hard global lock while AI thinks would unnecessarily slow architectural work and may be impossible to enforce cleanly for all Archicad UI actions.

Better model: **Context Lease**.

When context is captured:
- palette shows `Контекст задания #184 зафиксирован`;
- selected/target elements may be highlighted;
- optional strict mode shows `Не изменяйте отмеченные элементы до готовности задания`;
- Safe BIM records project stamp + target state hashes.

If user changes anything relevant during generation:
- lease becomes `INVALIDATED`;
- incoming job is never written to BIM;
- bridge publishes `STALE_CONTEXT` + changed GUIDs;
- regeneration can occur automatically.

For broad operations with no known targets, project root stamp changes invalidate the lease. For target-scoped work, unrelated edits can be allowed if the recipe's declared preconditions are still unchanged.

Decision: default should be non-blocking safety, not forcibly freezing the whole designer.

## Pass 194 — mechanical actions should stay local and automatic
Operations such as:
- select similar elements;
- recompute/rebuild zones where certified;
- deterministic QA;
- highlight junction/microgap warnings;
- run a previously certified recipe;

should not travel through ChatGPT or GitHub at all. They execute locally through Safe BIM and remain usable offline.

AI/cloud path is only for novel intent/planning or remote recipe generation.

This reduces latency, network traffic and failure surface.

## Pass 195 — auto-regeneration on stale context
The bridge can turn staleness into a normal protocol state instead of an error dialog.

```text
job arrives
  ↓
precondition mismatch
  ↓
0 writes
  ↓
STALE_CONTEXT result
  ↓
new task context snapshot
  ↓
request/regenerate recipe
```

For ordinary ChatGPT, fully automatic regeneration requires a machine conversation transport/dispatcher to wake the assistant again. If that machine route is unavailable, the palette can show `Задание устарело — требуется обновление` and the user's next chat turn resumes it.

The existing AI Dispatcher/GitHub turn-id design proves that a de-duplicated wake protocol is feasible, but it is UI-automation based and should remain an optional orchestration layer rather than the BIM safety boundary.

## Pass 196 — startup / out-of-box lifecycle
Target startup behavior:

```text
Start Archicad
  ↓
Safe BIM Add-On loads
  ↓
Bridge process/service is already running OR spawned silently
  ↓
named-pipe health handshake
  ↓
local SQLite context opened
  ↓
remote bridge auth checked in background
  ↓
palette ready
```

User does not run PowerShell, Ollama, Git, Python or a helper manually.

If remote GitHub is unavailable:
- local mechanical functions, QA, history, sandbox and recipes keep working;
- AI remote state shows `Офлайн`;
- outbound result/context jobs queue locally and sync later.

If authentication expires:
- do not block Archicad startup;
- show one compact `Требуется переподключение GitHub` action;
- never downgrade to a public repo or embed credentials.

**Pass-196 conclusion:** near-zero-touch runtime is achievable after a one-time secure account authorization or successful reuse of existing credentials. No user-created API keys are required.