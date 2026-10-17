<#
OpenBIM M2-DA one-time installer for APA Semantic V1.
Upstream .pt uses torch.load(weights_only=False): execution is NOT sandboxed.
Only run -TrustUpstreamCheckpoint if source and official release are trusted.
Original APA sidecar, native Archicad and PLN are never modified.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ImagePath,
  [switch]$TrustUpstreamCheckpoint,
  [switch]$PreflightOnly
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$expectedSrc = '3b6ef1702b835f70b686c98d8a3c8066ec6d6ebd'
$expectedWeight = 'cd7f41460ca1d3cc99bca9c61db8ac83d0381ddec385d55257e3ccb99967ffd7'
$weightUrl = 'https://github.com/Chunling1/OpenBIM-FloorPlan-AI/releases/download/v1.0.0/M2_DA_FT_v2_best.pt'
$oldPy = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe'
$side = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1'
$vendor = Join-Path $env:LOCALAPPDATA 'APA\semantic-ml\openbim-v1'
$project = Join-Path $vendor 'OpenBIM-FloorPlan-AI'
$mlPy = Join-Path $vendor 'venv\Scripts\python.exe'
$model = Join-Path $project 'models\M2_DA_FT_v2_best.pt'
$runner = Join-Path $side 'apa_semantic_entrypoint.py'
$configTool = Join-Path $PSScriptRoot 'configure_apa_semantic_models.py'

if (!(Test-Path -LiteralPath $oldPy -PathType Leaf) -or
    !(Test-Path -LiteralPath $runner -PathType Leaf) -or
    !(Test-Path -LiteralPath $configTool -PathType Leaf)) {
  throw 'ORIGINAL_APA_OR_SEMANTIC_BRIDGE_NOT_INSTALLED'
}
if (!(Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
  throw 'SOURCE_IMAGE_NOT_FOUND'
}
$source = (Resolve-Path -LiteralPath $ImagePath).Path
if ([IO.Path]::GetExtension($source).ToLowerInvariant() -ne '.png') {
  throw 'SOURCE_MUST_BE_PDFPAGERASTER_PNG'
}
if (Test-Path -LiteralPath (Join-Path $side 'models.json')) {
  $settings = Get-Content -LiteralPath (Join-Path $side 'models.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($settings.openbim) { throw 'OPENBIM_ALREADY_CONFIGURED_DO_NOT_REPEAT' }
}
Write-Host "Official source git commit: $expectedSrc"
Write-Host "Official model SHA256: $expectedWeight"
Write-Host "Target: $vendor"
Write-Host "Input: $source"
if ($PreflightOnly) {
  Write-Host 'PREFLIGHT ONLY: no changes or downloads.'
  return
}
if (!$TrustUpstreamCheckpoint) {
  throw 'EXPLICIT_TRUST_REQUIRED_TO_LOAD_UPSTREAM_PICKLE_MODEL'
}
if (Test-Path -LiteralPath $vendor) {
  throw 'OPENBIM_INSTALL_DIR_EXISTS_INSPECT_BEFORE_RETRY'
}

New-Item -ItemType Directory -Path $vendor -Force | Out-Null
git clone --depth 1 --branch v1.0.0 --single-branch https://github.com/Chunling1/OpenBIM-FloorPlan-AI.git $project
if ($LASTEXITCODE -ne 0) { throw 'OPENBIM_GIT_CLONE_FAILED' }
$commit = (git -C $project rev-parse HEAD).Trim().ToLowerInvariant()
if ($commit -ne $expectedSrc) { throw "OPENBIM_GIT_SOURCE_SHA_MISMATCH: $commit" }

& $oldPy -m venv (Join-Path $vendor 'venv')
if ($LASTEXITCODE -ne 0) { throw 'OPENBIM_PYTHON_VENV_FAILED' }

# Keep all dependencies isolated, no changes in original APA Python.
$packages = @(
  'torch==2.6.0',
  'torchvision==0.21.0',
  'segmentation-models-pytorch==0.5.0',
  'albumentations==2.0.8',
  'opencv-python-headless==4.11.0.86',
  'numpy==1.26.4',
  'Pillow==11.3.0'
)
& $mlPy -m pip install --disable-pip-version-check --only-binary=:all: @packages
if ($LASTEXITCODE -ne 0) { throw 'OPENBIM_ISOLATED_DEPENDENCY_INSTALL_FAILED' }
& $mlPy -m pip check
if ($LASTEXITCODE -ne 0) { throw 'OPENBIM_VENDOR_DEPENDENCY_CONFLICT' }

$modelsDir = Join-Path $project 'models'
if (!(Test-Path -LiteralPath $modelsDir)) {
  New-Item -ItemType Directory -Path $modelsDir | Out-Null
}
Invoke-WebRequest -Uri $weightUrl -OutFile $model -MaximumRedirection 10
$actual = (Get-FileHash -LiteralPath $model -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expectedWeight) {
  throw "OFFICIAL_MODEL_HASH_MISMATCH: $actual"
}
Write-Host 'OFFICIAL MODEL HASH: PASS'

# This registers one new external model. It cannot alter existing six tools.
& $oldPy $configTool --vendor openbim --python $mlPy --root $project --model $model --trust-checkpoint
if ($LASTEXITCODE -ne 0) { throw 'APA_OPENBIM_MODEL_REGISTRATION_FAILED' }

$out = Join-Path $env:TEMP ("APA_OpenBIM_" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
& $oldPy $runner --command OpenBIMSegments --a $source --output $out
if ($LASTEXITCODE -ne 0) { throw 'OPENBIM_LIVE_ROUTER_INFERENCE_FAILED' }
if (!(Test-Path -LiteralPath $out -PathType Leaf)) { throw 'EVIDENCE_FILE_MISSING' }
$report = Get-Content -LiteralPath $out -Raw -Encoding UTF8 | ConvertFrom-Json
if ($report.action -ne 'openbim' -or $report.modelWrites -ne 0 -or
    $report.nativeCalls -ne 0 -or !$report.result.classPixelCounts) {
  throw 'OPENBIM_INFERENCE_EVIDENCE_INVALID'
}
Write-Host 'APA OPENBIM: REAL ROUTED INFERENCE PASS' -ForegroundColor Green
Write-Host "EVIDENCE: $out"
$report.result.classPixelCounts | Format-List
