param(
    [string]$WorkRoot = "$env:USERPROFILE\Documents\Codex\tapir-safe-bim-libpart",
    [string]$DevKitSupport = $env:AC_API_DEVKIT_DIR
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$TapirRepo = "https://github.com/ENZYME-APD/tapir-archicad-automation.git"
$TapirCommit = "d2dfeec7936dd1dbed4e2412f406b30291959c26"
$PatchUrl = "https://raw.githubusercontent.com/dvikt33-ux/safe-bim-layer/research/library-system-v3/tapir-patches/0001-window-door-libraryPartName.patch"

function Find-DevKitSupport {
    param([string]$Explicit)

    $candidates = @()
    if ($Explicit) { $candidates += $Explicit }
    if ($env:AC_API_DEVKIT_DIR) { $candidates += $env:AC_API_DEVKIT_DIR }

    $candidates += @(
        "$env:USERPROFILE\Documents\Archicad API DevKit 29\Support",
        "$env:USERPROFILE\Documents\API Development Kit 29\Support",
        "$env:USERPROFILE\Downloads\Archicad API DevKit 29\Support",
        "$env:USERPROFILE\Downloads\API Development Kit 29\Support",
        "C:\Program Files\GRAPHISOFT\Archicad API DevKit 29\Support",
        "C:\Program Files\GRAPHISOFT\API Development Kit 29\Support"
    )

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (-not $candidate) { continue }
        $acapinc = Join-Path $candidate "Inc\ACAPinc.h"
        if (Test-Path $acapinc) {
            return (Resolve-Path $candidate).Path
        }
    }

    # Bounded fallback search: user Documents/Downloads only, never all of C:\.
    foreach ($root in @("$env:USERPROFILE\Documents", "$env:USERPROFILE\Downloads")) {
        if (-not (Test-Path $root)) { continue }
        $hit = Get-ChildItem -Path $root -Filter ACAPinc.h -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "\\Support\\Inc\\ACAPinc\.h$" } |
            Select-Object -First 1
        if ($hit) {
            return (Split-Path (Split-Path $hit.FullName -Parent) -Parent)
        }
    }

    throw @"
Archicad 29 API DevKit Support folder not found.
Set it once, for example:
  `$env:AC_API_DEVKIT_DIR = 'C:\path\to\DevKit\Support'
Then run this script again.
"@
}

function Find-VSGenerator {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $version = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationVersion
        if ($version) {
            $major = [int](($version -split '\.')[0])
            if ($major -ge 18) { return "Visual Studio 18 2026" }
            if ($major -eq 17) { return "Visual Studio 17 2022" }
            if ($major -eq 16) { return "Visual Studio 16 2019" }
        }
    }

    # Let CMake confirm the exact failure instead of guessing silently.
    return "Visual Studio 17 2022"
}

foreach ($exe in @("git", "cmake")) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        throw "Required executable not found in PATH: $exe"
    }
}

$DevKitSupport = Find-DevKitSupport $DevKitSupport
$Generator = Find-VSGenerator

Write-Host ""
Write-Host "========================================"
Write-Host "SAFE BIM / TAPIR HOSTED LIBPART BUILD"
Write-Host "========================================"
Write-Host "Tapir base : $TapirCommit"
Write-Host "DevKit     : $DevKitSupport"
Write-Host "Generator  : $Generator"
Write-Host "Work root  : $WorkRoot"
Write-Host ""

$src = Join-Path $WorkRoot "tapir"
$patch = Join-Path $WorkRoot "0001-window-door-libraryPartName.patch"
$build = Join-Path $src "archicad-addon\Build\AC29-SafeBIM"

New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null

if (-not (Test-Path (Join-Path $src ".git"))) {
    git clone $TapirRepo $src
}

Push-Location $src
try {
    git fetch origin
    git checkout --detach $TapirCommit

    $dirty = git status --porcelain
    if ($dirty) {
        throw "Dedicated Tapir clone is dirty; refusing to overwrite local changes:`n$dirty"
    }

    Invoke-WebRequest -Uri $PatchUrl -OutFile $patch

    git apply --check $patch
    git apply $patch

    Write-Host "[PASS] Patch applied"

    cmake `
        -S (Join-Path $src "archicad-addon") `
        -B $build `
        -G $Generator `
        -A x64 `
        -T v143 `
        -DAC_VERSION=29 `
        "-DAC_API_DEVKIT_DIR=$DevKitSupport"

    if ($LASTEXITCODE -ne 0) { throw "CMake configure failed." }

    cmake --build $build --config RelWithDebInfo
    if ($LASTEXITCODE -ne 0) { throw "CMake build failed." }

    $apx = Get-ChildItem -Path $build -Filter *.apx -File -Recurse |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $apx) {
        throw "Build completed but no .apx was found under $build"
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host "BUILD PASS"
    Write-Host "========================================"
    Write-Host "Patched Tapir APX:"
    Write-Host $apx.FullName
    Write-Host ""
    Write-Host "Next: install this APX in Archicad 29, restart Archicad, then run the hosted-window smoke test."
}
finally {
    Pop-Location
}
