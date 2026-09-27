# DIRECT GITHUB EXECUTION — PASSES 177–180

Date: 2026-09-28

## Pass 177 — safest automation split

The best split is:

```text
ChatGPT responsibilities
- understand user intent
- read published project context
- compile a typed Safe Recipe/job
- publish immutable job envelope
- later read result/evidence

Local Safe BIM responsibilities
- authenticate queue source
- de-duplicate/admit once
- check current project identity
- check state hashes/preconditions
- compile against local capabilities
- create checkpoint/sandbox
- perform physical BIM mutation
- read-back/reconcile
- publish terminal result
```

ChatGPT never holds authority to bypass local guards.

## Pass 178 — automatic vs user-confirmed execution

A useful system does not need to choose between “manual copy-paste” and “fully autonomous remote code execution”.

Recommended graduated mode:

### Mode A — Receive only
Remote job appears in palette; user opens it.

### Mode B — Auto-prepare
Remote job is fetched, validated, context-checked and preview/sandbox prepared automatically. User presses one `Применить` button.

### Mode C — Trusted recipe auto-run
Only future certified recipe families can execute without the click, and only when:
- exact project matches;
- snapshot/preconditions match;
- capability version matches;
- checkpoint/sandbox policy succeeds;
- job declares a bounded mutation budget;
- no unsupported operation is present.

For v0.1 choose Mode B.

## Pass 179 — UI behavior

Compact palette state:

```text
SAFE BIM
Контекст: ✓
Удалённое задание: #184
Статус: готово к проверке

[Посмотреть]
[Применить]
[Отклонить]
```

If main panel is collapsed, arrival should use a small non-modal indicator/badge, not steal Archicad focus.

After automatic preparation:

```text
#184 Дом: коробка + перекрытия + крыша
Создать: 43
Изменить: 0
Удалить: 0
QA: PASS
Sandbox: готов
Checkpoint: готов

[ПРИМЕНИТЬ]
```

AI/chat panel remains manually toggled open/closed as previously specified.

## Pass 180 — final implementation decomposition

Prototype can be implemented in five bounded components:

1. `BridgeQueueClient`
   - reads one queue-head object with conditional HTTP request;
   - fetches exact immutable job commit/files only when head changes;
   - owns GitHub auth outside APX.

2. `RemoteJobAdmission`
   - validates JSON schema/hash/protocol;
   - persists once-only admission in SQLite;
   - checks project/snapshot/capability.

3. `SafeRecipeInbox`
   - exposes `RECEIVED`, `STALE_CONTEXT`, `WAITING_USER`, `READY_TO_APPLY` to palette.

4. Existing `Safe Runtime`
   - unchanged safety kernel remains the only write path.

5. `ResultPublisher`
   - asynchronously publishes coalesced external status/result/evidence;
   - never blocks or changes a BIM transaction.

This minimizes overlap with geometry/runtime work and can be prototyped first using read-only or fake execution.
