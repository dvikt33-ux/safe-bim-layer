# APA Slack Socket Mode launcher (Windows PowerShell 5.1+).
# Runs only on the user's Windows machine after a dedicated Slack App is configured.
# Secrets are prompted locally; do not paste them into ChatGPT or GitHub.
[CmdletBinding()]
param(
    [switch]$InstallDeps,
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvRoot = Join-Path $env:LOCALAPPDATA 'SafeBIM\APA-Sync\venv'
$dataRoot = Join-Path $env:LOCALAPPDATA 'SafeBIM\APA-Sync'
$pythonExe = Join-Path $venvRoot 'Scripts\python.exe'
$requirements = Join-Path $PSScriptRoot 'requirements.txt'
$manifest = Join-Path $PSScriptRoot 'slack_app_manifest.yml'

function Get-ProcessSecret {
    param([Parameter(Mandatory=$true)][string] $Name)
    if ([Environment]::GetEnvironmentVariable($Name, 'Process')) { return }
    Write-Host "Enter $Name locally (characters hidden, nothing written to a file)."
    $secure = Read-Host -Prompt $Name -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plaintext = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        if ([string]::IsNullOrWhiteSpace($plaintext)) {
            throw "$Name was empty."
        }
        [Environment]::SetEnvironmentVariable($Name, $plaintext, 'Process')
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        $secure.Dispose()
    }
}

Write-Host "APA Socket Mode: repository = $repo"
Write-Host "App manifest = $manifest"
Write-Host "Local database directory = $dataRoot"
if (-not (Test-Path -LiteralPath $manifest)) { throw 'Slack manifest not found.' }
if (-not (Test-Path -LiteralPath $requirements)) { throw 'Requirements not found.' }

if ($CheckOnly) {
    Write-Host "VIRTUALENV_READY: $(Test-Path -LiteralPath $pythonExe)"
    Write-Host 'CHECK ONLY: No installation, daemon or Slack session was started.'
    exit 0
}

if (!(Test-Path -LiteralPath $pythonExe)) {
    if (-not $InstallDeps) {
        throw 'Isolated Python venv missing. Run with -InstallDeps to set it up locally.'
    }
    New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
    $launcher = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($null -ne $launcher) {
        & $launcher.Source -3.11 -m venv $venvRoot
    } else {
        & python -m venv $venvRoot
    }
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
}

if ($InstallDeps) {
    & $pythonExe -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) { throw 'Isolated Slack dependency installation failed.' }
}
& $pythonExe -c "import slack_bolt, slack_sdk"
if ($LASTEXITCODE -ne 0) {
    throw 'Slack Python SDK unavailable in isolated venv. Retry with -InstallDeps.'
}

$oldBot = [Environment]::GetEnvironmentVariable('SLACK_BOT_TOKEN', 'Process')
$oldApp = [Environment]::GetEnvironmentVariable('SLACK_APP_TOKEN', 'Process')
try {
    Get-ProcessSecret -Name 'SLACK_BOT_TOKEN'
    Get-ProcessSecret -Name 'SLACK_APP_TOKEN'

    [Environment]::SetEnvironmentVariable('APA_SYNC_CHANNEL_ID', 'C0C886E1PGR', 'Process')
    [Environment]::SetEnvironmentVariable('APA_SYNC_DB', (Join-Path $dataRoot 'events.sqlite3'), 'Process')
    Write-Host 'Starting APA Socket Mode. Keep this PowerShell window open; Ctrl+C stops it.'
    Push-Location $repo
    try {
        & $pythonExe -m scripts.apa_sync.socket_mode
        if ($LASTEXITCODE -ne 0) {
            throw "Coordinator failed with exit code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }
} finally {
    # Secrets must not survive in this PowerShell session after the daemon stops.
    [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', $oldBot, 'Process')
    [Environment]::SetEnvironmentVariable('SLACK_APP_TOKEN', $oldApp, 'Process')
}
