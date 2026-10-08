# Creates a CURRENT-USER, LOGON-ONLY Task Scheduler entry for the
# existing dry-run-only Safe BIM Mailbox watcher. Does not start a second worker.
# Preserves existing bridge.sqlite3, wall-attempts.sqlite3 and watcher ledger.
param([switch]$ShowTaskOnly)

$ErrorActionPreference = "Stop"
$taskName = "SafeBIM-Mailbox-DryRun"
$root = Join-Path $env:USERPROFILE "Documents\Codex"
$work = Join-Path $root "2026-10-08\referenced-chatgpt-conversation-this-is-an-2"
$delivery = Join-Path $work "work\delivery"
$state = Join-Path $work "work\mailbox-state"
$launcher = Join-Path $delivery "start_archicad_mailbox_watch.ps1"
$watcher = Join-Path $delivery "archicad_mailbox_watch.py"
$python = Join-Path $env:APPDATA "uv\tools\archicad-mcp-server\Scripts\python.exe"
$hostFile = Join-Path $delivery "archicad_mailbox_wall_host.py"
$bridge = Join-Path $root "safe-bim-chat-bridge-mvp"

if ($ShowTaskOnly) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) { $task | Select-Object TaskName, State, Actions, Triggers }
    else { Write-Host "TASK_NOT_INSTALLED" }
    exit 0
}

foreach ($f in @($python, $hostFile, $watcher)) {
    if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { throw "MISSING_REQUIRED_FILE: $f" }
}
foreach ($f in @("bridge.sqlite3", "wall-attempts.sqlite3", "mailbox-watcher-v1.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $state $f) -PathType Leaf)) {
        throw "MISSING_EXISTING_JOURNAL: $f"
    }
}
if (-not (Test-Path -LiteralPath $bridge -PathType Container)) {
    throw "MISSING_PINNED_BRIDGE: $bridge"
}
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw "TASK_EXISTS: refusing to overwrite; inspect with -ShowTaskOnly"
}
$gh = (Get-Command gh -ErrorAction Stop).Source
& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI is not authenticated" }

# Fetch only the reviewed launcher, not a new worker or live mutation extension.
$endpoint = "repos/dvikt33-ux/safe-bim-layer/contents/scripts/start_archicad_mailbox_watch.ps1?ref=chatgpt/schema-driven-batch-20261008"
$encoded = @(& $gh api $endpoint --jq '.content')
if ($LASTEXITCODE -ne 0 -or -not $encoded) { throw "Could not fetch launcher" }
$bytes = [Convert]::FromBase64String(($encoded -join ""))
if ($bytes.Length -lt 200) { throw "Downloaded launcher is unexpectedly short" }
$temporary = "$launcher.new"
[System.IO.File]::WriteAllBytes($temporary, $bytes)
Move-Item -LiteralPath $temporary -Destination $launcher -Force

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
$arguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "' + $launcher + '"'
$action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Safe BIM dry-run Mailbox watcher only; no Archicad write approval."
Register-ScheduledTask -TaskName $taskName -InputObject $task | Out-Null

Write-Host "AUTOSTART_REGISTERED: $taskName" -ForegroundColor Green
Write-Host "User: $identity"
Write-Host "Mode: at user logon; interactive token; low privilege"
Write-Host "Current foreground watcher remains untouched; NO second process started."
Write-Host "Original SQLite journals and PLN are unchanged."
Write-Host "At next login the launcher will wait for the exact Test MER PLN."
Write-Host "Logs: $(Join-Path $state 'mailbox-watch-autostart.log')"
