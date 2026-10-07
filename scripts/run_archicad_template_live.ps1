param(
    [int]$Port = 19723,
    [ValidateSet("preflight","core","materials-data","navigator-master","autotext","master-smoke","layout-autotext-smoke","coordinate-calibration","all-safe")]
    [string]$Stage = "all-safe",
    [string]$OutDir = "outputs/archicad-template-live"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Builder = Join-Path $Root "scripts/archicad_template_builder.py"

if (-not (Test-Path $Builder)) {
    throw "Builder not found: $Builder"
}

$RunId = Get-Date -Format "yyyyMMdd-HHmmss"
$RunDir = Join-Path $Root (Join-Path $OutDir $RunId)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Invoke-BuilderStep {
    param(
        [Parameter(Mandatory=$true)][string]$Action,
        [switch]$AllowNonempty
    )

    $OutFile = Join-Path $RunDir ("{0}.json" -f $Action)
    $args = @($Builder, $Action, "--port", "$Port", "--out", $OutFile)
    if ($AllowNonempty) {
        $args += "--allow-nonempty"
    }

    Write-Host "==> $Action"
    & python @args
    $exitCode = $LASTEXITCODE

    if (-not (Test-Path $OutFile)) {
        throw "$Action did not produce expected evidence file: $OutFile"
    }

    $result = Get-Content -Raw -Encoding UTF8 $OutFile | ConvertFrom-Json
    $status = [string]$result.status

    if ($exitCode -ne 0) {
        throw "$Action exited with code $exitCode (status=$status). Evidence: $OutFile"
    }

    if ($status -ne "PASS") {
        throw "$Action stopped fail-closed with status=$status. Evidence: $OutFile"
    }

    return $result
}

$preflight = @("font-preflight","validate","inspect","plan")
$core = @("apply-core","inspect")
$materialsData = @(
    "apply-surfaces",
    "plan-materials",
    "apply-ready-materials",
    "plan-data-schema",
    "apply-data-schema"
)
$navigatorMaster = @(
    "plan-navigator",
    "apply-navigator-shell",
    "plan-master-layouts",
    "apply-master-layout-shell",
    "inspect"
)
$autotext = @("plan-autotext")
$masterSmoke = @("apply-master-layout-smoke")
$layoutAutoTextSmoke = @("apply-layout-autotext-smoke")
$coordinateCalibration = @("apply-master-coordinate-calibration")

switch ($Stage) {
    "preflight" {
        $steps = $preflight
    }
    "core" {
        $steps = $core
    }
    "materials-data" {
        $steps = $materialsData
    }
    "navigator-master" {
        $steps = $navigatorMaster
    }
    "autotext" {
        $steps = $autotext
    }
    "master-smoke" {
        $steps = $masterSmoke
    }
    "layout-autotext-smoke" {
        $steps = $layoutAutoTextSmoke
    }
    "coordinate-calibration" {
        $steps = $coordinateCalibration
    }
    "all-safe" {
        $steps = $preflight + $core + $materialsData + $navigatorMaster
    }
    default {
        throw "Unsupported stage: $Stage"
    }
}

$summary = [ordered]@{
    status = "PASS"
    runId = $RunId
    stage = $Stage
    port = $Port
    evidenceDirectory = $RunDir
    steps = @()
    productionGeometryCreated = $false
    autotextGateExecuted = ($Stage -eq "autotext" -or $Stage -eq "master-smoke" -or $Stage -eq "layout-autotext-smoke")
    coordinateCalibrationExecuted = ($Stage -eq "coordinate-calibration")
}

foreach ($step in $steps) {
    $result = Invoke-BuilderStep -Action $step
    $summary.steps += [ordered]@{
        action = $step
        status = [string]$result.status
        evidence = Join-Path $RunDir ("{0}.json" -f $step)
    }
}

$SummaryPath = Join-Path $RunDir "summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $SummaryPath

Write-Host ""
Write-Host "PASS: $Stage"
Write-Host "Evidence: $RunDir"
Write-Host "Summary:  $SummaryPath"
