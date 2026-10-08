# Safe BIM Mailbox watcher — opt-in dry-run service

Status: offline-tested, Windows live watcher not yet verified. Does not extend
the deployed local writer. The existing guarded \`archicad_mailbox_wall_host.py\`
remains the only component allowed to handle one Mailbox JOB.

## Why not start the existing host's unbounded polling loop

The GitHub inbox retains older requests. The verified local host was used
only with \`--message-id\` and exited after publishing its RESULT.
Do not launch it without that argument on a reused queue.

This watcher makes a one-time durable baseline of EXISTING GitHub inbox names,
then only processes NEW messages. It calls the verified host in bounded
\`--message-id\` mode, with the original \`--data-dir\` and SQLite journals.

## Security boundaries

- **Dry-run only**, \`mode=execute\` is never dispatched.
- Only exact \`create_wall_v1\` protocol and an exact locally inspected
  \`projectPath\`, \`projectName\`, port, instance and logicalProjectId.
- Every proposed JOB is checked for payload hash, createdAt, expiresAt,
  mode, and type before contacting the host.
- Before calling the worker, an intake decision is fsynced to an additional
  \`mailbox-watcher-v1.json\` file in the existing state directory. A crash
  cannot cause automatic resubmission of that message ID.
- Project not running or switched -> watcher pauses and preserves the job
  for later processing, rather than accepting a write to the wrong PLN.
- GitHub errors, malformed input, invalid ledger, collisions or unsupported
  commands fail closed. Never manually delete the new watcher ledger or
  existing \`bridge.sqlite3\`/\`wall-attempts.sqlite3\`.
- The local source pin and actual target are independently validated again
  by the trusted one-shot worker. The watcher never passes \`--enable-execute\`,
  generates a local approval, or executes any Tapir write itself.

## One-time Windows launch

Requires working \`gh auth status\` and the guarded local source delivered by
the previous execution. From the repository root:

\`\`\`powershell
$root = "$env:USERPROFILE\Documents\Codex"
$work = "$root\2026-10-08\referenced-chatgpt-conversation-this-is-an-2"
$python = "$env:APPDATA\uv\tools\archicad-mcp-server\Scripts\python.exe"
$hostFile = "$work\work\delivery\archicad_mailbox_wall_host.py"
$bridge = "$root\safe-bim-chat-bridge-mvp"
$state = "$work\work\mailbox-state"
$watcher = ".\scripts\archicad_mailbox_watch.py"

& $python $watcher --python $python --host-file $hostFile \`
  --bridge-source $bridge --data-dir $state \`
  --expected-project-path 'C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln' \`
  --expected-project-name 'Тест MER ' --expected-port 19723 --loop
\`\`\`

First successful live scan prints \`BASELINE_CREATED\`. Only JOB files added
**AFTER** that point will be processed, and only in \`dry-run\` mode.

During the session leave the watcher running in its dedicated process;
to stop press Ctrl+C. The watcher itself does NOT install any logon task.
Keep process stdout/stderr in an operator log if running unattended.

**Do not** migrate the original SQLite databases into a new data directory,
restart an already active worker with a second competing watcher, or
interpret the initial \`BASELINE_CREATED\` as an actual JOB execution.

To query a single round without entering a background polling loop, omit
\`--loop\`. The first one-shot run also performs baseline initialization.

## Further steps

1. Verify first baseline and one new dry-run RESULT without creating a wall.
2. Optionally install a per-user logon launcher after that successful test.
3. Bring the existing local executor source and safety tests into a reviewed
   GitHub feature branch.
4. Add a narrow, typed, locally permissioned execution protocol before allowing
   unattended writes. Never turn on broad generic \`Create*\` calls.
