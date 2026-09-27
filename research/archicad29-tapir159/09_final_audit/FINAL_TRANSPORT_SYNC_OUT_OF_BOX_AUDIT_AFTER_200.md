# FINAL TRANSPORT / SYNC / OUT-OF-BOX AUDIT — after pass 200

Date: 2026-09-28
Scope: communication between ordinary ChatGPT and Safe BIM/Archicad; webhook alternatives; local vs cloud transport; pre-code fresh-state capture; zero-manual-startup UX.
No product code changes. No Live BIM writes.

---

# 1. Final objective

Daily use should be:

> Start Archicad → Safe BIM is ready → work.

The user should not need to run PowerShell, start Python, open GitHub Desktop, start Ollama, copy code manually, create API keys or manage bridge processes.

For project-dependent AI work, ChatGPT must operate from a fresh task-bound state snapshot and Safe BIM must reject anything stale before a physical BIM write.

---

# 2. Final transport architecture

```text
                         ORDINARY CHATGPT
                              │
                              │ GitHub connector
                              ▼
                 PRIVATE SAFE-BIM BRIDGE REPO
                 ┌────────────────────────────┐
                 │ requests / contexts        │
                 │ jobs / results             │
                 └────────────────────────────┘
                              ▲
                              │ minimal WAN sync
                              ▼
                     SAFE BIM BRIDGE
                 (silent local companion)
                    │              │
            local SQLite       local queue/journal
                    │              │
                    └──────┬───────┘
                           │ Named Pipe
                           ▼
                    SAFE BIM ADD-ON
                           │
                           ▼
                       ARCHICAD
```

**GitHub is only the cross-boundary mailbox.**
It is not the local execution bus and never participates in the physical BIM transaction.

---

# 3. Local vs Internet verdict

## Local is unambiguously preferable for workstation-internal communication
Use local named-pipe IPC for Palette ↔ Bridge. Keep authoritative state, QA cache, receipts, history and execution journal local.

## Pure local cannot currently replace the cloud boundary for ordinary ChatGPT
An unpushed local Git repository is not directly visible to ordinary ChatGPT. Current OpenAI product documentation says local files are accessible in desktop Work when granted, while direct local MCP connection is not the normal ordinary-Chat path; private/local MCP requires a supported tunnel. This project intentionally avoids routing routine BIM work through Work.

Therefore **“ChatGPT simply reads my local GitHub folder” is not a valid primary architecture for the current ordinary-chat workflow**.

## GitHub Desktop is not the transport
GitHub Desktop can coexist and may mean credentials are already available, but Safe BIM must not depend on its UI, background refresh schedule or process being open.

**Final verdict: LOCAL-FIRST HYBRID.**

---

# 4. Remote wake mechanism verdict

## v0.1 primary: conditional polling
Poll one tiny queue-head/manifest endpoint with authenticated `ETag / If-None-Match` semantics.

Properties:
- tiny responses;
- 304 when unchanged;
- serialized requests;
- adaptive cadence;
- no public inbound port;
- no third-party tunnel.

Suggested policy to benchmark, not hard-code yet:
- active task wait: approximately 1–3 s;
- normal Archicad activity: slower;
- idle/background: tens of seconds;
- immediate explicit check on AI/request transitions.

Actual intervals must be measured before production.

## fallback: narrow Git fetch
If standard Git/GCM is already authorized but REST auth is not, fetch only the bridge ref/branch. Do not full-pull the repository.

## webhooks: optional later accelerator
Direct webhook has good latency but requires reachable HTTPS plus signature-secret management. Development proxies such as Smee are not production solutions. Tunnels such as Tailscale/ngrok/Cloudflare add setup, public ingress and another service dependency.

Do not make any of them mandatory for v0.1.

## rejected: self-hosted Actions runner
Too much remote execution authority and setup for a message queue. GitHub explicitly documents hardening risks for self-hosted runners.

---

# 5. Fresh context BEFORE code generation

The strongest improvement over continuous cloud snapshots is a **request-driven context handshake**.

```text
User asks ChatGPT for project work
        ↓
ChatGPT reads low-frequency active project pointer
        ↓
ChatGPT publishes CONTEXT_REQUEST
        ↓
Safe BIM Bridge sees it
        ↓
Palette: "ИИ: считываю проект…"
        ↓
local hot cache + quick reconciliation
        ↓
coherent CONTEXT_READY(snapshot_id, root hash)
        ↓
ChatGPT reads that exact snapshot
        ↓
generates job/recipe bound to it
```

This means Safe BIM does **not** need to publish the whole model continuously.

The local project index remains hot via notifications/reconciliation. Only task-relevant context crosses the Internet.

---

# 6. “Do not change the project” UX

Do not globally lock the designer for the whole AI thinking period.

Use a **Context Lease**:

```text
ИИ: контекст #184 зафиксирован
⚠ Не изменяйте подсвеченные элементы
```

Store:
- logical project ID;
- project modification stamp/root hash;
- snapshot ID;
- target GUIDs;
- target state hashes;
- capture generation.

If the project changes:
- mark lease invalid where relevant;
- never execute the stale job;
- publish `STALE_CONTEXT`;
- regenerate from fresh context.

For broad project-level jobs, any project-root change may invalidate the lease.
For target-scoped jobs, unrelated changes may be allowed if declared preconditions still hold.

Strict optional mode may ask the user not to edit the whole project during preparation, but this should not be the default.

---

# 7. Coherent context capture algorithm

1. read logical/native project identity;
2. read project modification stamp A;
3. freeze local context-index generation;
4. drain/coalesce pending dirty GUIDs;
5. reconcile needed shallow/deep records;
6. read selection / active story / requested scope;
7. read project modification stamp B;
8. if A != B, repeat capture or return `CONTEXT_CHANGED_DURING_CAPTURE`;
9. validate snapshot schema/hashes;
10. publish one coherent context transaction;
11. create context lease.

The network/publisher does not run inside the Archicad event callback.

---

# 8. Mechanical automation must bypass ChatGPT/GitHub

These should remain local and automatic once certified:
- select similar;
- wall-junction/microgap QA;
- highlighting;
- repeat a known deterministic recipe;
- deterministic zone rebuild/recalculation where certified;
- local history/rollback/sandbox operations.

This keeps routine operations effectively instant, offline-capable and free of AI latency.

Remote AI is for novel/ambiguous planning and generation.

---

# 9. Authentication / “no keys” verdict

A private remote repository cannot securely work on a completely fresh machine with literally no authorization relationship.

But the user **does not need to create or copy any API key/PAT**.

Runtime policy:
1. silently test existing standard Git/GCM access;
2. if already authorized, zero setup;
3. otherwise one-time browser authorization through a narrowly scoped GitHub App/OAuth flow;
4. store/refresh credentials through OS-protected mechanisms/helper service;
5. never expose credentials to the Palette web UI;
6. never hardcode a long-lived token in `.apx`, Python, JS or repository.

After this one-time account authorization, daily startup is fully automatic.

For a public/distributed Safe BIM build, GitHub App-style fine-grained permissions and short-lived tokens are preferable to user-generated PATs.

---

# 10. Out-of-box startup contract

```text
Start Archicad
  ↓
Safe BIM Add-On loads
  ↓
Bridge service/process auto-starts or is spawned silently
  ↓
Named-pipe health check
  ↓
SQLite/context cache starts
  ↓
QA/event subscriptions start
  ↓
remote bridge connection starts in background
  ↓
palette READY
```

No console windows.
No PowerShell.
No separate AI app.
No GitHub Desktop interaction.
No manual server start.
No local LLM required for the ChatGPT path.

If Internet/GitHub is unavailable, only remote AI transport is disabled; local Safe BIM stays functional.

---

# 11. Fault-tolerance requirements

- duplicate remote job ID => never duplicate physical write;
- partial remote job => never admit;
- Internet loss after local job admission => local execution can finish if all payload is present;
- result upload failure => durable local result + retry upload;
- stale snapshot => 0 writes;
- wrong project => 0 writes;
- bridge crash => resume from local journal;
- GitHub outage => mechanical/local functions unaffected;
- auth expiry => compact reconnect state, never fallback to public data transport.

---

# 12. Recommended implementation order

### T1 — local transport foundation
- bundled Bridge process/service;
- per-user secured named pipe;
- health/version handshake;
- SQLite queue/journal;
- auto-start lifecycle.

### T2 — local context service
- project identity;
- project/element modification stamps;
- hot context cache;
- dirty GUID reconciliation;
- state hashes.

### T3 — remote bridge read path
- private bridge repo;
- auth bootstrap abstraction;
- conditional queue-head polling;
- local fetch fallback;
- offline queue.

### T4 — task context handshake
- `CONTEXT_REQUEST`;
- `CONTEXT_READY`;
- context lease;
- capture consistency check;
- stale invalidation.

### T5 — remote job path
- job admission;
- automation class policy;
- exact snapshot binding;
- Preview/Checkpoint/Sandbox integration;
- result/evidence publisher.

### T6 — optional latency experiments
- direct webhook with controlled relay;
- measured comparison against ETag polling;
- retain only if benefit justifies setup/security cost.

---

# 13. Final research verdict

**READY FOR PROTOTYPE.**

The best architecture is not “everything through GitHub” and not “everything local”. It is:

> local execution + local authoritative state + request-driven cloud context + minimal private GitHub mailbox.

This satisfies the project's primary goals:
- fastest routine Archicad work;
- minimal manual setup;
- no PowerShell during normal use;
- no user-created API keys;
- no permanent local LLM memory/VRAM load;
- strong stale-context protection;
- GitHub/Internet failure does not threaten the PLN;
- ordinary ChatGPT can still read fresh project context and send Safe BIM jobs.

The remaining questions are benchmark/certification items, not architecture gaps:
- measured network/context round-trip latency;
- credential reuse on the current workstation;
- capture time on small/medium/large PLN files;
- optimal adaptive polling intervals;
- exact UI timing for lease warnings.

Do not start another broad research cycle on transport before these measurements. Move to a narrow prototype and fault-injection audit.