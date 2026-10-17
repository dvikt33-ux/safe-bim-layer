<#
APA Raster2Seq V1: pinned, opt-in model installer and real APA Router inference.
First use -PreflightOnly (no writes). The checkpoint is 1.45 GB.
Untrusted .pth uses torch.load(weights_only=False); operator must explicitly
approve pinned source with -TrustUpstreamCheckpoint. This is NOT a sandbox.
No PLN, Archicad/SDK or original six-tool APA modifications.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ImagePath,
    [switch]$PreflightOnly,
    [switch]$TrustUpstreamCheckpoint
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$rev = '5c8245b4b62971cae212d64f503a469c722523d7'
$sha = 'f7c0ef9379aa8cf11349da8b2179214e0d495af758383984a2361a1309aab3b7'
$url = 'https://huggingface.co/haopt/Raster2Seq/resolve/c9a9c439ba66594dab701b77b7df52a5f75a5fce/cubicasa5k/checkpoint.pth'
$oldPy = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe'
$side = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1'
$vendor = Join-Path $env:LOCALAPPDATA 'APA\semantic-ml\raster2seq-v1'
$project = Join-Path $vendor 'floorplan-back'
$venv = Join-Path $vendor 'venv'
$mlPy = Join-Path $venv 'Scripts\python.exe'
$model = Join-Path $project 'models\raster2seq\cubicasa5k\checkpoint.pth'
$runner = Join-Path $side 'apa_semantic_entrypoint.py'
$configTool = Join-Path $PSScriptRoot 'configure_apa_semantic_models.py'

if (!(Test-Path -LiteralPath $ImagePath -PathType Leaf)) { throw 'SOURCE_IMAGE_NOT_FOUND' }
$inputPng = (Resolve-Path -LiteralPath $ImagePath).Path
if ([IO.Path]::GetExtension($inputPng).ToLowerInvariant() -ne '.png') {
    throw 'RASTER2SEQ_REQUIRES_PNG_FROM_A_FLOORPLAN_SHEET'
}
if (!(Test-Path -LiteralPath $oldPy -PathType Leaf) -or
    !(Test-Path -LiteralPath $runner -PathType Leaf) -or
    !(Test-Path -LiteralPath $configTool -PathType Leaf)) {
    throw 'ORIGINAL_APA_OR_SEMANTIC_BRIDGE_MISSING'
}
$config = Join-Path $side 'models.json'
if (!(Test-Path -LiteralPath $config -PathType Leaf)) {
    throw 'OPENBIM_MODEL_CONFIGURATION_NOT_PRESENT'
}
$configJson = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
if (!$configJson.openbim) { throw 'OPENBIM_BASELINE_NOT_REGISTERED' }
if ($configJson.raster2seq) { throw 'RASTER2SEQ_ALREADY_REGISTERED_INSPECT_INSTEAD' }

Write-Host "Source revision: $rev"
Write-Host "Official checkpoint SHA256: $sha"
Write-Host "Model source: $url"
Write-Host "Expected download size: 1.45 GB"
Write-Host "New isolated directory: $vendor"
Write-Host "PNG for floorplan inference: $inputPng"
Write-Host 'CUDA / Archicad / PLN will not be used or modified.'
if ($PreflightOnly) {
    Write-Host 'RASTER2SEQ PREFLIGHT ONLY: no installation or downloads.'
    return
}
if (!$TrustUpstreamCheckpoint) {
    throw 'EXPLICIT_CHECKPOINT_TRUST_REQUIRED'
}
if (Test-Path -LiteralPath $vendor) {
    throw 'RASTER2SEQ_VENDOR_DESTINATION_EXISTS_INSPECT_BEFORE_RETRY'
}

New-Item -Path $vendor -ItemType Directory -Force | Out-Null
git clone --depth 1 https://github.com/Takheer/floorplan-back.git $project
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_UPSTREAM_CLONE_FAILED' }
$actualRev = (git -C $project rev-parse HEAD).Trim().ToLowerInvariant()
if ($actualRev -ne $rev) { throw "RASTER2SEQ_UPSTREAM_REVISION_MISMATCH: $actualRev" }

& $oldPy -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_VENV_FAILED' }
& $mlPy -m pip install --disable-pip-version-check -e $project
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_VENDOR_DEPENDENCIES_FAILED' }
& $mlPy -m pip check
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_VENDOR_DEPENDENCY_CONFLICT' }

Push-Location $project
try {
    & $mlPy -c "from app.inference.raster2seq import Raster2SeqModel; from app.settings import Settings; m=Raster2SeqModel(Settings(model_device='cpu')); print('RASTER2SEQ_VENDOR_IMPORT_PASS',m.device)"
    if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_IMPORT_FAILED' }
}
finally { Pop-Location }

$dir = Split-Path -Parent $model
New-Item -Path $dir -ItemType Directory -Force | Out-Null
# curl.exe supports resumable 1.45GB HTTPS downloads and preserves the file
# on failure for manual review. Never silently replace an existing checkpoint.
if (Test-Path -LiteralPath $model) { throw 'CHECKPOINT_ALREADY_EXISTS_INSPECT' }
& curl.exe --fail --location --retry 4 --retry-delay 5 --continue-at - --output $model $url
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_CHECKPOINT_DOWNLOAD_FAILED_DO_NOT_RETRY_INSTALL' }
$actualSha = (Get-FileHash -LiteralPath $model -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha -ne $sha) { throw "RASTER2SEQ_OFFICIAL_CHECKPOINT_SHA_MISMATCH: $actualSha" }
Write-Host 'RASTER2SEQ OFFICIAL CHECKPOINT SHA256: PASS' -ForegroundColor Green

# Register model without overwriting the existing OpenBIM model configuration.
& $oldPy $configTool --vendor raster2seq --python $mlPy --root $project --model $model --trust-checkpoint
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_MODEL_REGISTRATION_FAILED' }

$out = Join-Path $env:TEMP ("APA_Raster2Seq_" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
& $oldPy $runner --command RasterFloorplan --a $inputPng --output $out
if ($LASTEXITCODE -ne 0) { throw 'RASTER2SEQ_ROUTER_INFERENCE_FAILED' }
if (!(Test-Path -LiteralPath $out -PathType Leaf)) { throw 'RASTER2SEQ_EVIDENCE_MISSING' }
$report = Get-Content -LiteralPath $out -Raw -Encoding UTF8 | ConvertFrom-Json
if ($report.action -ne 'raster2seq' -or
    $report.modelWrites -ne 0 -or $report.nativeCalls -ne 0 -or
    $null -eq $report.result.counts -or $null -eq $report.result.floorplan) {
    throw 'RASTER2SEQ_EVIDENCE_CONTRACT_FAILED'
}
Write-Host 'APA RASTER2SEQ: REAL ROUTED SOURCE INFERENCE PASS' -ForegroundColor Green
Write-Host "REPORT: $out"
Write-Host 'Detected candidates, NOT confirmed BIM building components:'
$report.result.counts | Format-List
