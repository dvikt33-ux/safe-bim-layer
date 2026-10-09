# Separate checkout + optional AC29 build. No APX installation, Archicad launch or PLN edits.
[CmdletBinding()]
param(
  [string]$Destination = (Join-Path $env:USERPROFILE 'Documents\APA_SyncGuids_Build_20261009'),
  [string]$DevKitPath = '',
  [switch]$AllowDevKitDownload,
  [switch]$SourceOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$upstream = 'https://github.com/kuvbur/AddOn_SomeStuff.git'
$upstreamSha = 'bc371d9ee4b602315b1045e2ff1f71ea1e3b808c'
$overlaySha = 'd3350a86d21203403543626f5bb204022b051b28'
$overlayPrefix = "https://raw.githubusercontent.com/dvikt33-ux/safe-bim-layer/$overlaySha/integrations/somestuff-syncguids"
$source = Join-Path $Destination 'SomeStuff-source'
$downloads = Join-Path $Destination 'overlay'
$phase = 'PREFLIGHT'
function Assert-Ok([bool]$ok, [string]$reason) {
  if (-not $ok) { throw $reason }
}
function Write-Json([string]$path, [object]$obj) {
  $obj | ConvertTo-Json -Depth 12 | Set-Content -Path $path -Encoding UTF8
}
if (Test-Path -LiteralPath $Destination) {
  throw "BLOCKED: destination exists, refusing to replay: $Destination"
}
Assert-Ok ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) 'Windows required'
foreach ($name in @('git','python')) {
  Assert-Ok ($null -ne (Get-Command $name -ErrorAction SilentlyContinue)) "Missing command: $name"
}
if (-not $SourceOnly) {
  Assert-Ok ($null -ne (Get-Command cmake -ErrorAction SilentlyContinue)) 'Missing command: cmake'
}
New-Item -Path $Destination -ItemType Directory | Out-Null
New-Item -Path $downloads -ItemType Directory | Out-Null
try {
  Write-Host '=== CLONE PINNED UPSTREAM ==='
  $phase = 'CLONE'
  & git clone --depth 1 --branch test-latest --single-branch $upstream $source
  Assert-Ok ($LASTEXITCODE -eq 0) 'git clone failed'
  $got = (& git -C $source rev-parse HEAD).Trim()
  Assert-Ok ($LASTEXITCODE -eq 0 -and $got -eq $upstreamSha) "Pinned tag moved: expected $upstreamSha got $got"
  Write-Host '=== DOWNLOAD PINNED OVERLAY ==='
  $phase = 'DOWNLOAD_OVERLAY'
  $files = @(
    @{ From='Sources/AddOn/json_commands/SyncGuidsCommand.cpp'; Name='SyncGuidsCommand.cpp' },
    @{ From='Sources/AddOn/json_commands/SyncGuidsCommand.hpp'; Name='SyncGuidsCommand.hpp' },
    @{ From='patches/registrar.diff'; Name='registrar.diff' }
  )
  foreach ($f in $files) {
    $target = Join-Path $downloads $f.Name
    Invoke-WebRequest -Uri "$overlayPrefix/$($f.From)" -UseBasicParsing -OutFile $target
    Assert-Ok ((Get-Item $target).Length -gt 100) "Empty overlay: $($f.Name)"
  }
  Write-Host '=== PATCH CHECK ==='
  $phase = 'APPLY_PATCH'
  $patch = Join-Path $downloads 'registrar.diff'
  & git -C $source apply --check $patch
  Assert-Ok ($LASTEXITCODE -eq 0) 'Registrar patch does not apply to pinned source'
  foreach ($name in @('SyncGuidsCommand.cpp','SyncGuidsCommand.hpp')) {
    $target = Join-Path $source "Sources\AddOn\json_commands\$name"
    Assert-Ok (-not (Test-Path -LiteralPath $target)) "File already exists: $name"
    Copy-Item -LiteralPath (Join-Path $downloads $name) -Destination $target
  }
  & git -C $source apply $patch
  Assert-Ok ($LASTEXITCODE -eq 0) 'Patch application failed'
  $formatter = Get-Command clang-format -ErrorAction SilentlyContinue
  $formatStatus = 'NOT_AVAILABLE'
  if ($null -ne $formatter) {
    $targets = @(
      (Join-Path $source 'Sources\AddOn\json_commands\SyncGuidsCommand.cpp'),
      (Join-Path $source 'Sources\AddOn\json_commands\SyncGuidsCommand.hpp'),
      (Join-Path $source 'Sources\AddOn\json_commands\JsonCommandRegistrar.cpp')
    )
    & clang-format -i @targets
    Assert-Ok ($LASTEXITCODE -eq 0) 'clang-format failed'
    $formatStatus = 'RAN'
  }
  & git -C $source diff --check
  Assert-Ok ($LASTEXITCODE -eq 0) 'git diff --check failed'
  $status = @(& git -C $source status --porcelain)
  Assert-Ok ($LASTEXITCODE -eq 0) 'git status failed'
  Assert-Ok ($status.Count -eq 3) "Expected exactly 3 changed files, found $($status.Count)"
  $statusText = [string]::Join([Environment]::NewLine, $status)
  foreach ($expected in @('SyncGuidsCommand.cpp','SyncGuidsCommand.hpp','JsonCommandRegistrar.cpp')) {
    Assert-Ok ($statusText.Contains($expected)) "Missing source: $expected"
  }
  Write-Json (Join-Path $Destination 'source-report.json') @{
    status='SOURCE_APPLIED'; upstreamCommit=$upstreamSha; overlayCommit=$overlaySha
    sourcePath=$source; sourceChanges=@($status); clangFormat=$formatStatus
    apxInstalled=$false; plnModified=$false
  }
  Write-Host 'SOURCE PATCH: PASS'
  if ($SourceOnly) {
    Write-Host "SOURCE ONLY: $source"
    return
  }
  Write-Host '=== BUILD EXPERIMENTAL AC29 ==='
  $phase = 'BUILD'
  $arguments = @('Tools\BuildAddOn.py','-c','config.json','-v','29')
  if ($DevKitPath -ne '') {
    $kit = (Resolve-Path -LiteralPath $DevKitPath).Path
    if (Test-Path (Join-Path $kit 'Inc\ACAPinc.h')) {
      $kit = Split-Path $kit -Parent
    }
    Assert-Ok (Test-Path (Join-Path $kit 'Support\Inc\ACAPinc.h')) 'DevKitPath must contain Support\Inc\ACAPinc.h'
    $arguments += @('-d',$kit)
  } elseif (-not $AllowDevKitDownload) {
    Write-Host 'BUILD BLOCKED: supply -DevKitPath or explicitly -AllowDevKitDownload'
    Write-Json (Join-Path $Destination 'build-report.json') @{
      status='BLOCKED_NO_DEVKIT'; sourcePath=$source
      instruction='Run python Tools\BuildAddOn.py -c config.json -v 29 with an appropriate DevKit'
    }
    return
  }
  Push-Location $source
  try {
    & python @arguments *>&1 | Tee-Object -FilePath (Join-Path $Destination 'build.log')
    $exitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  Assert-Ok ($exitCode -eq 0) "Build failed, exit $exitCode; see build.log"
  $apx = Join-Path $source 'Build\SomeStuff\29\Debug\SomeStuff.apx'
  Assert-Ok (Test-Path -LiteralPath $apx) "Build returned success but output missing: $apx"
  $file = Get-Item -LiteralPath $apx
  $report = @{
    status='BUILD_RETURNED_SUCCESS'; apxPath=$file.FullName
    apxBytes=$file.Length; apxSha256=(Get-FileHash $apx -Algorithm SHA256).Hash
    upstreamCommit=$upstreamSha; overlayCommit=$overlaySha
    apxInstalled=$false; runtimeTested=$false
  }
  Write-Json (Join-Path $Destination 'build-report.json') $report
  Write-Host '=== BUILD REPORT ==='
  $report | ConvertTo-Json -Depth 12
  Write-Host 'DO NOT REPLACE THE INSTALLED APX.'
} catch {
  $report = @{
    status='STOP'; phase=$phase; reason=$_.Exception.Message
    destination=$Destination; apxInstalled=$false; plnModified=$false
  }
  Write-Json (Join-Path $Destination 'stop.json') $report
  Write-Host '=== BUILD PREPARATION STOP ==='
  $report | ConvertTo-Json -Depth 12
  Write-Host 'Do not delete the evidence before investigating.'
}
