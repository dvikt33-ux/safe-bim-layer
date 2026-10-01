param(
    [string]$WorkRoot = "$env:USERPROFILE\Documents\Codex\tapir-safe-bim-libpart"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$src = Join-Path $WorkRoot "tapir"
$source = Join-Path $src "archicad-addon\Sources\AddOnMain.cpp"
$hostedSource = Join-Path $src "archicad-addon\Sources\ExtendedElementCommands.cpp"
$build = Join-Path $src "archicad-addon\Build\AC29-SafeBIM"
$patcher = Join-Path $WorkRoot "apply_registration_isolation_patch.py"
$patcherUrl = "https://raw.githubusercontent.com/dvikt33-ux/safe-bim-layer/research/library-system-v3/tapir-patches/apply_registration_isolation_patch.py"

$running = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(ARCHICAD|Archicad)' }
if ($running) {
    Write-Host ""
    Write-Host "Archicad is still running:" -ForegroundColor Yellow
    $running | Select-Object Id, ProcessName, Path | Format-Table -AutoSize
    throw "Close ALL Archicad windows before rebuilding, because the loaded APX can be locked."
}

if (!(Test-Path (Join-Path $src ".git"))) {
    throw "Tapir working clone not found: $src"
}
if (!(Test-Path $source)) {
    throw "AddOnMain.cpp not found: $source"
}
if (!(Test-Path $hostedSource)) {
    throw "ExtendedElementCommands.cpp not found: $hostedSource"
}
if (-not (Select-String -Path $hostedSource -SimpleMatch "SAFE_BIM_HOSTED_LIBRARY_PART_NAME_V1" -Quiet)) {
    throw "Hosted libraryPartName patch is missing. Refusing to build a diagnostic binary that drops the previous work."
}

Invoke-WebRequest -Uri $patcherUrl -OutFile $patcher

$python = (Get-Command python -ErrorAction Stop).Source
& $python $patcher $source
if ($LASTEXITCODE -ne 0) {
    throw "Registration-isolation source patch failed."
}

if (-not (Select-String -Path $source -SimpleMatch "SAFE_BIM_REGISTRATION_ISOLATION_V1" -Quiet)) {
    throw "Registration-isolation marker missing after patch."
}

Write-Host ""
Write-Host "========================================"
Write-Host "REBUILDING DIAGNOSTIC TAPIR AC29"
Write-Host "========================================"
Write-Host ""

cmake --build $build --config RelWithDebInfo
if ($LASTEXITCODE -ne 0) {
    throw "CMake build failed."
}

$apx = Get-ChildItem -Path $build -Filter *.apx -File -Recurse |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $apx) {
    throw "Build completed but no APX was found under $build"
}

Write-Host ""
Write-Host "========================================"
Write-Host "DIAGNOSTIC BUILD PASS"
Write-Host "========================================"
Write-Host "APX replaced in-place:"
Write-Host $apx.FullName
Write-Host ""
Write-Host "The Add-On Manager already points at this path, so do not add another copy."
Write-Host "Start Archicad 29 normally, open the test PLN, keep all modal dialogs closed, then run find_running_tapir_port.py."
