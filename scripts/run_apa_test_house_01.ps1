# Disposable APA_Test_House_01.pln. Reuses the existing Python accelerator.
# Default: read-only preflight. -Execute: one-shot write after successful preflight.
[CmdletBinding()]
param(
    [ValidateRange(1,65535)]
    [int]$Port = 19726,
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$pln = 'C:\LocalAI\APA_Test_House_01.pln'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script = Join-Path $root 'scripts\archicad_project_accelerator.py'
$intent = Join-Path $root 'examples\accelerator\apa-test-house-01.intent.json'
$base = 'C:\LocalAI\APA_Trial_Evidence'
$ledger = Join-Path $base 'persistent-ledger'
$runTag = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,8))
$session = Join-Path $base $runTag

if (-not (Test-Path -LiteralPath $pln -PathType Leaf)) {
    throw "TEST_PLN_NOT_FOUND: $pln"
}
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "ACCELERATOR_NOT_FOUND: $script"
}
if (-not (Test-Path -LiteralPath $intent -PathType Leaf)) {
    throw "BUILDING_INTENT_NOT_FOUND: $intent"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'PYTHON_NOT_INSTALLED'
}
New-Item -ItemType Directory -Path $session -Force | Out-Null
New-Item -ItemType Directory -Path $ledger -Force | Out-Null

$preflight = Join-Path $session 'preflight'
Write-Host "APA: READ-ONLY PREFLIGHT, exact PLN=$pln, port=$Port"
& python $script --intent $intent --scratch-port $Port --output $preflight --preflight
if ($LASTEXITCODE -ne 0) {
    Write-Host "Preflight evidence: $preflight\result.json"
    throw 'APA_PREFLIGHT_BLOCKED: zero write attempts expected'
}
$ticket = Get-Content -LiteralPath (Join-Path $preflight 'result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($ticket.status -ne 'READY_FOR_EXPLICIT_TEST_RUN' -or
    $ticket.binding.path -ine $pln -or
    $ticket.binding.port -ne $Port -or
    $ticket.modelWriteAttempts -ne 0 -or
    $ticket.inventoryUnchanged -ne $true -or
    [string]::IsNullOrWhiteSpace($ticket.confirmPlanHash)) {
    throw 'APA_PREFLIGHT_NOT_ACCEPTED: check result.json, no execution'
}
Write-Host "APA_PREFLIGHT_PASS: scanned=$($ticket.nativeElementsInspected), writes=0"
if (-not $Execute) {
    Write-Host 'READY: invoke with -Execute only for the approved disposable PLN.'
    Write-Host "EVIDENCE: $session"
    return
}

# One-shot guarded executable pass; the native writer rechecks project,
# stories, collision envelope, plan hash and no-retry journal before writing.
$executePath = Join-Path $session 'execute'
$sceneId = 'apa-house-' + $runTag
Write-Host "APA: one-shot native create, unsaved PLN; scene=$sceneId"
& python $script --intent $intent --scratch-port $Port --output $executePath --data-dir $ledger --execute --run-id $sceneId --confirm-plan-hash $ticket.confirmPlanHash
$exitCode = $LASTEXITCODE
$answer = Get-Content -LiteralPath (Join-Path $executePath 'result.json') -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "APA_RESULT: $($answer.status)"
Write-Host "ADDED_GUIDS: $(@($answer.addedGuids).Count)"
Write-Host "MODEL_WRITE_ATTEMPTS: $($answer.modelWriteAttempts)"
Write-Host "EVIDENCE: $session"
if ($exitCode -ne 0 -or $answer.status -ne 'COMPLETE_UNSAVED' -or
    $answer.wholeAssemblyReadback -ne $true) {
    throw 'APA_NOT_COMPLETE: inspect evidence; NEVER auto-retry after partial/unknown writes'
}
Write-Host 'APA_NATIVE_ASSEMBLY_PASS_UNSAVED: inspect the model; SAVE PLN manually only if desired.'
