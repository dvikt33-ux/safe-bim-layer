<#
APA AC29 stage 2: exact AP2 PDF -> PyMuPDF crop -> existing APA OpenBIM
-> source-qualified candidates for repeat/mass operations. READ-ONLY.
No calls to Archicad and no PLN writes. Do not run twice in same target dir.
#>
[CmdletBinding()]
param(
  [string]$PDF = "C:\Users\Admin\Documents\Codex\2026-10-16\referenced-chatgpt-conversation-this-is-an-2\outputs\2_этап_АП_КОМФОРТ_без_замазок.pdf"
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$expected = '2cf28450e868a5c742511fe40e6d0f061c9210744cb4f43875e0d7839725c55b'
$side = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-semantic-v1'
$py = Join-Path $side 'venv\Scripts\python.exe'
$basePy = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe'
$router = Join-Path $side 'apa_semantic_entrypoint.py'
$mlConfig = Join-Path $side 'models.json'
$preparer = Join-Path $PSScriptRoot 'apa_arch_plan_benchmark.py'
$planner = Join-Path $PSScriptRoot 'apa_ap2_massops_preflight.py'
foreach($path in @($PDF,$py,$basePy,$router,$mlConfig,$preparer,$planner)){
  if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw "MISSING_REQUIRED_FILE: $path"}
}
$sourceSHA = (Get-FileHash -LiteralPath $PDF -Algorithm SHA256).Hash.ToLowerInvariant()
if($sourceSHA -ne $expected){throw "AP2_SOURCE_SHA_MISMATCH: $sourceSHA"}
$models = Get-Content -LiteralPath $mlConfig -Raw -Encoding UTF8 | ConvertFrom-Json
if(!$models.openbim){throw 'OPENBIM_NOT_CONFIGURED'}
$runRoot = Join-Path $env:TEMP ('APA_AP2_MassOps_' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
if(Test-Path -LiteralPath $runRoot){throw 'RESULT_FOLDER_ALREADY_EXISTS'}
New-Item -ItemType Directory -Path $runRoot -ErrorAction Stop | Out-Null
$planFolder = Join-Path $runRoot 'plan16'
Write-Host '1/3: source PDF page16, structural layer evidence and PNG' -ForegroundColor Cyan
& $py $preparer --pdf $PDF --page 16 --clip 125 95 685 595 --out $planFolder
if($LASTEXITCODE -ne 0){throw 'SOURCE_PREPARATION_FAILED'}
Write-Host '2/3: real existing APA Router -> OpenBIM inference (CPU)' -ForegroundColor Cyan
$png = Join-Path $planFolder 'floorplan.png'
$mlResult = Join-Path $planFolder 'openbim.json'
& $basePy $router --command OpenBIMSegments --a $png --output $mlResult
if($LASTEXITCODE -ne 0){throw 'APA_OPENBIM_INFERENCE_FAILED'}
Write-Host '3/3: verify source/model receipts and decide candidate operations' -ForegroundColor Cyan
$finalResult = Join-Path $planFolder 'massops.json'
& $py $planner --pdf $PDF --crop-receipt (Join-Path $planFolder 'evidence.json') --openbim-report $mlResult --output $finalResult
if($LASTEXITCODE -ne 0){throw 'MASSOPS_SOURCE_QUALIFICATION_FAILED'}
$result = Get-Content -LiteralPath $finalResult -Raw -Encoding UTF8 | ConvertFrom-Json
if($result.nativeCalls -ne 0 -or $result.modelWrites -ne 0 -or $result.readyForModelWrite -or !$result.semantic.evidenceAccepted){throw 'READ_ONLY_RESULT_VALIDATION_FAILED'}
Write-Host 'APA AP2: ROUTED INFERENCE + MASSOPS PREFLIGHT PASS' -ForegroundColor Green
Write-Host ('Mark placements: {0}; repeat groups: {1}; repeated placements: {2}' -f $result.markPlacementCount,$result.repeatGroups,$result.repeatPlacementCount)
$result.candidateBatches | Sort-Object placements -Descending | Select-Object mark,placements,candidateStrategy | Format-Table -AutoSize
Write-Host 'OpenBIM pixel classification:'
$result.semantic.classPixelCounts | Format-List
Write-Host 'Actual copied groups: 0; native calls: 0; PLN writes: 0'
Write-Host "REPORTS: $runRoot"
