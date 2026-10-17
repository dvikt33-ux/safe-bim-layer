# One-time user-local launcher for the existing AC29 APX build chain.
# No elevation, no APX installation, no Archicad or PLN modification.
param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ApprovedSha,
    [string]$TapirPath = $env:APA_TAPIR_REPO,
    [string]$DevKitPath = $env:APA_AC29_DEVKIT,
    [switch]$Healthcheck,
    [switch]$Loop
)
$ErrorActionPreference = "Stop"
$source = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$configHome = Join-Path $env:LOCALAPPDATA "APA_AC29_APX_BuildMailbox"
$config = Join-Path $configHome "paths.json"
if (Test-Path $config) {
    $saved = Get-Content $config -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $TapirPath) { $TapirPath = $saved.tapir }
    if (-not $DevKitPath) { $DevKitPath = $saved.devkit }
}
if (-not $TapirPath) { $TapirPath = Read-Host "Путь к локальному репозиторию Tapir 1.5.10 (папка с .git)" }
if (-not $DevKitPath) { $DevKitPath = Read-Host "Путь к каталогу Support комплекта Archicad 29 DevKit" }
if (-not (Test-Path (Join-Path $source ".git"))) { throw "Нужна обычная Git-копия safe-bim-layer" }
if (-not (Test-Path (Join-Path $TapirPath ".git"))) { throw "Не найден Git-репозиторий Tapir: $TapirPath" }
if (-not (Test-Path $DevKitPath -PathType Container)) { throw "Не найден каталог DevKit: $DevKitPath" }
foreach ($tool in @("gh", "git")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Не установлена программа $tool" }
}
$preferredPython = Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"
if (Test-Path $preferredPython) { $python = $preferredPython }
else {
    $found = Get-Command python -ErrorAction SilentlyContinue
    if (-not $found) { throw "Не найден python.exe в PATH" }
    $python = $found.Source
}
New-Item -ItemType Directory -Force -Path $configHome | Out-Null
@{tapir=$TapirPath;devkit=$DevKitPath} |
    ConvertTo-Json | Set-Content -Path $config -Encoding UTF8
$argsPython = @(
    (Join-Path $PSScriptRoot "apa_ac29_apx_build_mailbox.py"),
    "--source-repo", $source,
    "--tapir-repo", $TapirPath,
    "--devkit", $DevKitPath,
    "--approved-sha", $ApprovedSha
)
if ($Healthcheck) { $argsPython += "--healthcheck" }
if ($Loop) { $argsPython += "--loop" }
Write-Host "APA AC29: только сборка APX. Установка и изменение модели запрещены."
& $python @argsPython
if ($LASTEXITCODE -ne 0) { throw "Локальный канал сборки: EXITCODE=$LASTEXITCODE" }
