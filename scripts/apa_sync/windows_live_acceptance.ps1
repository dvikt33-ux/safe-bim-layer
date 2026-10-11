# APA receipt -> Slack -> local SQLite, isolated opt-in acceptance.
# No Archicad/PLN/APX, repository checkout, service stop/start or package install.
[CmdletBinding()]
param(
    [switch]$Publish,
    [string]$PythonExe = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$defaultVenv = Join-Path $env:LOCALAPPDATA 'SafeBIM\APA-Sync\venv\Scripts\python.exe'
if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    if (Test-Path -LiteralPath $defaultVenv) {
        $PythonExe = $defaultVenv
    } else {
        $PythonExe = (Get-Command python -ErrorAction Stop).Source
    }
}
if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw 'Python interpreter missing; nothing sent or changed.'
}

$planCommit = '4e821c96a3cd94184bbad78f566eb037ff578c52'
$receipt = 'docs/research/apa-results/receipts/APA-RUN-20261011-091905Z-p70-source-integration-map.json'
$args = @(
    '-m', 'scripts.apa_sync.live_receipt_probe',
    '--plan-commit', $planCommit,
    '--task-id', 'APA-P70.A01.S01',
    '--receipt-path', $receipt
)

if ($Publish) {
    Write-Host 'APA LIVE PROBE: explicit Slack send enabled.'
    Write-Host 'No controller status write, PLN/APX edit or service restart.'
    $args += '--publish'
} else {
    Write-Host 'APA PREFLIGHT: read-only; no Slack send.'
}

Push-Location $repo
try {
    & $PythonExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "APA bridge acceptance NOT_VERIFIED (exit $LASTEXITCODE)."
    }
} finally {
    Pop-Location
}
