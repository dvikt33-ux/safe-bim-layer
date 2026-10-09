# APA synchronization — Slack step protocol and event coordinator

Scope: Archicad 29 build 5101; `dvikt33-ux/safe-bim-layer`; current APA research.
**No Archicad / PLN write path.** This integration exchanges evidence and state only.

## Architecture

1. **Step-level chat synchronization.** Before every consequential research or
   implementation step, read `#apa-research` (channel `C0C886E1PGR`). Reconcile
   new task states and conflicts; after independently substantiating an outcome,
   publish a short event immediately rather than waiting for the hourly task.
2. **Persistent coordinator.** `coordinator.py` accepts only explicitly marked
   `APA_EVENT_V1` messages, appends immutable events to SQLite, deduplicates
   Slack retries and flags contradictory task/phase transitions for human review.
3. **Event-driven receiver.** `socket_mode.py` uses Slack Events API via
   **Socket Mode**. A separate Slack App receives `message.channels` events and
   updates the ledger promptly. The local read-only HTTP API makes its state
   available to controllable API/local agents.

**Important limit:** ordinary running ChatGPT chats cannot be interrupted or
given new mid-response context by this coordinator. They only see updates on
the next work step when they actually call the Slack connector. API/local
agents can poll the coordinator endpoint or use the Slack SDK directly.

The program is a **prepared implementation** until separately deployed and
tested against live Slack; a source commit alone does not mean it is running.

## Slack workspace

- Workspace: `Проект архикад` / `T0C847UM0A2`
- Event and report channel: `#apa-research` / `C0C886E1PGR`
- GitHub is authoritative for code and test evidence.
- Slack provides notification and an append-only event feed; it is **not**
  a substitute for reviewing source evidence or live BIM acceptance.

## A. Protocol for each parallel ChatGPT chat

Paste this instruction into each **already open** chat once:

> Работаем над APA. Перед каждым новым существенным исследовательским
> проходом, изменением проекта, проверкой кода или техническим решением
> прочитай последние события из подключённого Slack-канала
> `#apa-research` (`C0C886E1PGR`). Учитывай события других чатов,
> конфликтные статусы не считай решёнными. После каждого нового
> подтверждённого результата сразу публикуй `APA_EVENT_V1` в канал,
> а не жди почасового отчёта. До публикации укажи источник, фазу
> SOURCE/OFFLINE/SYNTHETIC/BUILD/LIVE и статус INFO/PASS/BLOCKED/
> NOT_VERIFIED. Не выдавай чужой PASS за собственную проверку.
> Не загружай секреты, личные данные, рабочие PLN и закрытые отчёты
> в публичный канал. Если Slack недоступен, честно укажи, что
> синхронизация не выполнена. Не изменяй main, PLN или рабочие ветки
> без отдельного разрешения.

For each work cycle: `read Slack → reconcile task/phase state → work →
verify → publish event → report link`. The active chat must invoke the
Slack read tool itself; merely knowing this instruction does not start a
background watcher.

## B. Event format (strict)

Only messages starting with `APA_EVENT_V1` and containing one `json`
code fence are ingested. The human-readable middle line is optional.
Example (**replace the event ID with a fresh unique ID**):

    APA_EVENT_V1
    TN-GDL-CREATE-01 | NOT_VERIFIED | BUILD: APX full build not established
    ```json
    {"event_id":"20261010-apa-build-check-001","task_id":"TN-GDL-CREATE-01","status":"NOT_VERIFIED","phase":"BUILD","source":"chatgpt:apa-build","summary":"Full APX build is still unverified; isolated ResConv succeeded","evidence_urls":["https://github.com/dvikt33-ux/safe-bim-layer/pull/20"]}
    ```

Valid phases: `SOURCE`, `OFFLINE`, `SYNTHETIC`, `BUILD`, `LIVE`.
Valid statuses: `INFO`, `PASS`, `BLOCKED`, `NOT_VERIFIED`.
A `PASS` must include at least one HTTPS evidence URL. This is **syntax**
validation, NOT independent proof of PASS.

- One task may have different statuses in different phases: an `OFFLINE PASS`
  never implies a `LIVE PASS`.
- Conflicting statuses for the same `task_id:phase` are flagged
  `CONFLICT`; the new message is preserved but not silently accepted.
- To supersede the latest status, include
  `"supersedes":"<latest_event_id>"`, with newly verified evidence.
- Reusing an `event_id` or Slack message timestamp with different contents
  is rejected. Retries of an identical event are idempotent.
- The coordinator only sees new Slack events **after** its listener starts.
  For historic events, bootstrap via `step_sync before` (manual review) or
  a separately verified backfill procedure; no live backfill is claimed.

## C. Optional local event coordinator on Windows

The currently connected ChatGPT Slack connector **does not** expose
`SLACK_BOT_TOKEN` or `SLACK_APP_TOKEN` to this independent application.
A separate Slack App must be configured by the workspace owner:

1. Visit https://api.slack.com/apps and create an app in `Проект архикад`.
2. Enable **Socket Mode**; create an app-level token (`xapp-`) with
   `connections:write`. Do not share tokens in ChatGPT or GitHub.
3. Under OAuth scopes, grant the bot `channels:history` (receive/read
   public channel messages). The optional step-level CLI also needs
   `chat:write` to publish, and read access to the channel.
4. Under **Event Subscriptions**, enable `message.channels`.
   Install the app to the workspace, obtain bot token (`xoxb-`),
   and invite the bot to `#apa-research`.
5. From the repository checkout, in a *separate isolated environment*,
   install `slack-bolt` (only when you explicitly authorize installation)
   and set `SLACK_APP_TOKEN` and `SLACK_BOT_TOKEN` securely in the
   process environment. Never put tokens in a tracked `.env` file.
6. Start using `python -m scripts.apa_sync.socket_mode`.
   Leave the process running for realtime event delivery.
7. Verify `http://127.0.0.1:8765/health` and
   `http://127.0.0.1:8765/v1/state` locally. Publish an explicit
   sample event in Slack, then verify that its sequence appears in
   `/v1/changes?after=0`.

The HTTP API intentionally binds **only to 127.0.0.1**, never to a public
network address. A remote agent requires an authenticated, separately
secured tunnel or an agent colocated on the coordinator machine.

### Optional work-step CLI for local agents

Requires bot token and `slack_sdk` (provided by `slack-bolt`):

```powershell
python -m scripts.apa_sync.step_sync before --limit 100
python -m scripts.apa_sync.step_sync after --event-file .\event.json
# The previous command is a dry-run preview, with no Slack write.
python -m scripts.apa_sync.step_sync after --event-file .\event.json --publish
```

The explicit `--publish` flag prevents accidental Slack writes.
A bot may lack `conversations.history` or `chat.postMessage` permissions
until scopes and channel membership are configured.

### Local read API for an agent

- `GET /health` — process-local API health.
- `GET /v1/state` — latest state per `task_id:phase`; conflicts explicit.
- `GET /v1/changes?after=123&limit=100` — chronological event changes,
  `next_cursor` for subsequent polling (cursor is SQLite sequence).
- `before --oldest=<Slack-message-ts>` — step CLI cursor is **different**:
  a Slack message timestamp, not a SQLite sequence.

This API does not write back to Archicad or automatically approve model
changes. Local agents may poll every few seconds; that cadence is not a
capability of the built-in ChatGPT automation scheduler.

## Testing and privacy

Offline tests (no Slack access):

```powershell
python -m unittest discover -s tests -p 'test_apa_slack_sync.py' -v
```

Requires a separate live acceptance to claim event delivery:

- A new Slack App connects and receives a genuine channel event.
- A repeated Slack delivery produces exactly one database record.
- Two contradictory task/phase reports expose `CONFLICT`.
- Local read API exposes updated sequence and payload.
- An independent agent reads that sequence before doing more work.
- Previously open ChatGPT conversations still need an explicit Slack
  read at their next execution step.

Never commit DB files, tokens, client model contents, personal information,
private filesystem paths or unreviewed artifacts to the public repository
or public Slack channel. Restrict the Slack app to the minimum permissions.

Sources: https://docs.slack.dev/apis/events-api/using-socket-mode/
and https://docs.slack.dev/tools/bolt-python/concepts/socket-mode/
