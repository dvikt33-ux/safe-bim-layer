# APA AC29: local build-only mailbox launcher, compatible with Windows PowerShell 5.1.
# Does not install APX, open Archicad, modify PLN, or execute remote shell commands.
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

function Get-ApprovedCandidates([string]$Kind) {
    # Bounded, read-only discovery. Never download or auto-install a different Tapir or DevKit.
    $roots = @(
        "C:\LocalAI",
        (Join-Path $env:USERPROFILE "Documents"),
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:USERPROFILE "source\repos"),
        (Join-Path $env:LOCALAPPDATA "APA")
    ) | Select-Object -Unique

    $found = New-Object System.Collections.Generic.List[string]
    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        $directories = @((Get-Item -LiteralPath $root)) + @(
            Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue
        )
        foreach ($directory in $directories) {
            if ($Kind -eq "Tapir") {
                if ($directory.Name -notmatch '(?i)tapir|additional.json.commands|archicad.json') { continue }
                if ((Test-Path -LiteralPath (Join-Path $directory.FullName ".git")) -and
                    (Test-Path -LiteralPath (Join-Path $directory.FullName "archicad-addon\Sources\AddOnMain.cpp"))) {
                    $found.Add($directory.FullName)
                }
            }
            elseif ($Kind -eq "DevKit") {
                if ($directory.Name -notmatch '(?i)Support|Dev.?Kit') { continue }
                $support = $directory.FullName
                if ($directory.Name -ne "Support") { $support = Join-Path $directory.FullName "Support" }
                if ((Test-Path -LiteralPath (Join-Path $support "Inc") -PathType Container) -and
                    (Test-Path -LiteralPath (Join-Path $support "Lib") -PathType Container)) {
                    $found.Add($support)
                }
            }
        }
    }
    return @($found | Select-Object -Unique)
}

function Resolve-ToolPath([string]$Kind, [string]$CurrentPath, [string]$Question) {
    if (-not [string]::IsNullOrWhiteSpace($CurrentPath)) { return $CurrentPath.Trim('"') }
    $options = @(Get-ApprovedCandidates $Kind)
    if ($options.Count -eq 1) {
        Write-Host ("Найден автоматически " + $Kind + ": " + $options[0])
        return [string]$options[0]
    }
    if ($options.Count -gt 1) {
        Write-Host ("Найдено несколько вариантов " + $Kind + ":")
        for ($index = 0; $index -lt $options.Count; $index++) {
            Write-Host ("  " + ($index + 1) + ". " + $options[$index])
        }
        Write-Host "Для точности укажите нужный путь вручную."
    }
    else {
        Write-Host ("Автоматический поиск " + $Kind + " не нашёл подходящего каталога.")
    }
    $value = Read-Host $Question
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw ("Путь к " + $Kind + " пуст. Скрипт остановлен без сборки. Укажите путь в запросе или параметре запуска.")
    }
    return $value.Trim().Trim('"')
}

if (Test-Path -LiteralPath $config -PathType Leaf) {
    $saved = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $TapirPath) { $TapirPath = $saved.tapir }
    if (-not $DevKitPath) { $DevKitPath = $saved.devkit }
}

$TapirPath = Resolve-ToolPath "Tapir" $TapirPath "Путь к Git-репозиторию Tapir 1.5.10"
$DevKitPath = Resolve-ToolPath "DevKit" $DevKitPath "Путь к каталогу Support комплекта Archicad 29 DevKit"

if (-not (Test-Path -LiteralPath (Join-Path $source ".git"))) {
    throw "Не найдена обычная Git-копия safe-bim-layer."
}
if (-not (Test-Path -LiteralPath (Join-Path $TapirPath ".git"))) {
    throw "Не найден Git-репозиторий Tapir (папка с .git): $TapirPath"
}
if (-not (Test-Path -LiteralPath (Join-Path $TapirPath "archicad-addon\Sources\AddOnMain.cpp"))) {
    throw "Это не исходный репозиторий Tapir с archicad-addon: $TapirPath"
}
if (-not ((Test-Path -LiteralPath (Join-Path $DevKitPath "Inc") -PathType Container) -and
          (Test-Path -LiteralPath (Join-Path $DevKitPath "Lib") -PathType Container))) {
    throw "Нужна папка DevKit\Support с подкаталогами Inc и Lib: $DevKitPath"
}
foreach ($tool in @("gh", "git")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Не установлена программа: $tool"
    }
}
$preferredPython = Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"
if (Test-Path -LiteralPath $preferredPython) { $python = $preferredPython }
else {
    $found = Get-Command python -ErrorAction SilentlyContinue
    if (-not $found) { throw "Не найден python.exe в PATH" }
    $python = $found.Source
}

New-Item -ItemType Directory -Force -Path $configHome | Out-Null
@{tapir=$TapirPath;devkit=$DevKitPath} |
    ConvertTo-Json | Set-Content -LiteralPath $config -Encoding UTF8

$argsPython = @(
    (Join-Path $PSScriptRoot "apa_ac29_apx_build_mailbox.py"),
    "--source-repo", $source,
    "--tapir-repo", $TapirPath,
    "--devkit", $DevKitPath,
    "--approved-sha", $ApprovedSha
)
if ($Healthcheck) { $argsPython += "--healthcheck" }
if ($Loop) { $argsPython += "--loop" }
Write-Host "APA AC29: только сборка APX; установка и изменение модели запрещены."
& $python @argsPython
if ($LASTEXITCODE -ne 0) {
    throw "Локальный канал сборки завершился с ошибкой: $LASTEXITCODE"
}
