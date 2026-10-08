# Windows logon launcher for the verified, dry-run-only Safe BIM watcher.
# Not an Archicad write launcher. No --enable-execute or --approval flag.
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE "Documents\Codex"
$work = Join-Path $root "2026-10-08\referenced-chatgpt-conversation-this-is-an-2"
$python = Join-Path $env:APPDATA "uv\tools\archicad-mcp-server\Scripts\python.exe"
$hostFile = Join-Path $work "work\delivery\archicad_mailbox_wall_host.py"
$watcher = Join-Path $work "work\delivery\archicad_mailbox_watch.py"
$bridge = Join-Path $root "safe-bim-chat-bridge-mvp"
$state = Join-Path $work "work\mailbox-state"
$log = Join-Path $state "mailbox-watch-autostart.log"

# Never create an alternate journal or silently pick another script.
foreach ($file in @($python, $hostFile, $watcher)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file missing: $file" }
}
foreach ($dir in @($bridge, $state)) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Required directory missing: $dir" }
}
foreach ($file in @("bridge.sqlite3", "wall-attempts.sqlite3", "mailbox-watcher-v1.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $state $file))) {
        throw "Original journal missing: $file; refusing to create new state"
    }
}
$gh = (Get-Command gh -ErrorAction Stop).Source

# Guard manual watcher already running. Scheduler independently has IgnoreNew.
$existing = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains("archicad_mailbox_watch.py") -and
        $_.CommandLine.Contains($watcher) })
if ($existing.Count -gt 0) {
    Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) ALREADY_RUNNING: manual watcher remains active"
    exit 0
}

while ($true) {
    try {
        $args = @(
            "-u", $watcher, "--python", $python, "--host-file", $hostFile,
            "--bridge-source", $bridge, "--data-dir", $state,
            "--expected-project-path", 'C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln',
            "--expected-project-name", 'Тест MER ',
            "--expected-port", "19723", "--gh", $gh, "--loop"
        )
        Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) START dry-run-only watcher"
        & $python @args 2>&1 | ForEach-Object {
            Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) $_"
            if ((Get-Item -LiteralPath $log).Length -gt 5242880) {
                $archive = "$log.previous"
                if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
                Move-Item -LiteralPath $log -Destination $archive
            }
        }
        Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) WATCHER_EXIT code=$LASTEXITCODE; restart in 30 sec"
    }
    catch {
        Add-Content -LiteralPath $log -Encoding UTF8 -Value "$(Get-Date -Format o) WATCHER_ERROR $($_.Exception.GetType().Name); restart in 30 sec"
    }
    Start-Sleep -Seconds 30
}
