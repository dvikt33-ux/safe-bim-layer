# Archicad 29.2.1 (5101) — read-only version check and logon autostart

**Status (2026-10-09): scripts committed; GitHub Actions offline checks passed.
Actual Windows Scheduled Task installation and local API version inventory are
NOT yet verified.** This runbook deliberately does not enable model writes.

## 1. Read-only runtime probe

The existing Archicad Python environment provides Graphisoft \`ACConnection\`.
Run \`scripts/archicad_runtime_version_probe.py\` with exact target:

- Project: \`C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln\`
- Project name (including trailing space): \`Тест MER \`
- JSON API port: \`19723\`

The script calls **only** Graphisoft official \`GetProductInfo\` and Tapir
\`GetProjectInfo\`, \`GetAddOnVersion\` and \`GetStories\`. It does not modify
objects, attributes, libraries, favorites, PLN, or the Mailbox journal.

The current application release **29.2.1 (5101) RUS FULL (x86-64)** is
grounded in the UI screenshot, not inferred from the Python API.
An actual product build mismatch must be reported rather than re-labelled.
Do not assume old \`tapir-1.5.8.json\` exactly describes the loaded add-on.

## 2. Autostart installer

\`scripts/install_mailbox_watch_autostart.ps1\` is a human-invoked, opt-in
Task Scheduler setup script. It registers ONE scheduled task under the
currently logged-in Windows user:

- Name: \`SafeBIM-Mailbox-DryRun\`
- Trigger: user logon (not system boot, not SYSTEM, not elevated)
- Multiple instances: IgnoreNew
- Code: \`work\delivery\start_archicad_mailbox_watch.ps1\`; downloads this
  small reviewed wrapper from the project GitHub feature branch.
- Client: the **already-installed** Python
  \`archicad_mailbox_watch.py\`, calling
  \`archicad_mailbox_wall_host.py --message-id\` one job at a time.
- Policy: strictly dry-run; no \`--approval\`, no \`--enable-execute\`.
- Target: the exact test PLN, only \`19723\`.
- State: the **existing**
  \`work\mailbox-state\bridge.sqlite3\`,
  \`wall-attempts.sqlite3\`, and \`mailbox-watcher-v1.json\`.
- Logging: \`mailbox-watch-autostart.log\`. No credentials in command line.

The installer refuses to overwrite a task of the same name or to initialize
fresh state if original journals are missing. It registers for the **NEXT**
logon, **does not start** a second watcher now, and does not terminate the
current foreground session. The wrapper checks for an existing process
using the same watcher path; if present, it skips startup.

If Archicad is not open at login, the watcher remains in \`PAUSED\` and
waits. Opening an unrelated PLN must not authorize it. After the correct
test PLN opens, it resumes with the persistent baseline journal. **Never**
erase the baseline journal to replay an old job.

### Stop or remove

Manual foreground watcher: Ctrl+C in its original PowerShell window.

After logon-based installation:

\`\`\`powershell
Get-ScheduledTask -TaskName "SafeBIM-Mailbox-DryRun"
Stop-ScheduledTask -TaskName "SafeBIM-Mailbox-DryRun"
Disable-ScheduledTask -TaskName "SafeBIM-Mailbox-DryRun"
# To remove the task only (keeps all local scripts, SQLite and PLN):
Unregister-ScheduledTask -TaskName "SafeBIM-Mailbox-DryRun" -Confirm:$false
\`\`\`

Installation does **not** make the watcher execute BIM writes. The
next phase must port the already-proven local wall writer source into
reviewable GitHub code and add explicit typed recipes, collision checks,
per-operation authorization and fresh read-back, not an unrestricted API bus.
