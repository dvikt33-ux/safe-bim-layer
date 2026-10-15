# Reconstructed read-only source preview; NOT original Work script.
# Usage: powershell -ExecutionPolicy Bypass -File .\native_followon_archive_preview.ps1 -RepoPath C:\path\to\safe-bim-layer
# Does not fetch, checkout, run Archicad, create a ZIP or modify PLN/APX/IFC.

[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
$expected = "744e0bd184a11f1de4a1cf16382d21aec6f8cfca"
$proofPath = Join-Path $PSScriptRoot "native-followon-ci-proof.json"

if (-not (Test-Path -LiteralPath $proofPath -PathType Leaf)) {
    throw "Recovery manifest not found: $proofPath"
}
$proof = Get-Content -LiteralPath $proofPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($proof.source_head -cne $expected) {
    throw "Source commit mismatch"
}
if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) {
    throw "Not a local Git clone: $RepoPath"
}
$kind = (& git -C $RepoPath cat-file -t $expected 2>&1)
if ($LASTEXITCODE -ne 0 -or "$kind".Trim() -cne "commit") {
    throw "PR59 commit unavailable in this clone; no auto-fetch attempted"
}
$items = @($proof.source_blobs)
if ($items.Count -ne 13) {
    throw "Expected exactly 13 published source files"
}
$checked = 0
foreach ($item in $items) {
    $sourcePath = [string]$item.path
    $expectedBlob = [string]$item.blob
    if ($sourcePath -match '(^/|\\|\.\.|\.(pln|apx|ifc|exe|dll)$)') {
        throw "Unsafe source path: $sourcePath"
    }
    $row = (& git -C $RepoPath ls-tree $expected -- $sourcePath 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Git ls-tree failed for $sourcePath"
    }
    $match = [regex]::Match("$row", '^100(?:644|755) blob ([a-f0-9]{40})\s+')
    if (-not $match.Success -or $match.Groups[1].Value -cne $expectedBlob) {
        throw "Published source blob mismatch: $sourcePath"
    }
    $checked++
    Write-Host ("VERIFIED {0}/13 : {1}" -f $checked, $sourcePath)
}
Write-Host ""
Write-Host "PR59 ARCHIVE SOURCE PREVIEW: PASS" -ForegroundColor Green
Write-Host "EXACT COMMIT: $expected"
Write-Host "SOURCE BLOBS VERIFIED: $checked"
Write-Host "LIVE/BUILD RE-RUN: NO"
Write-Host "PLN/APX/IFC MODIFIED: NO"
Write-Host "TO CREATE AN OPTIONAL ZIP: python native_followon_package_setup.py --repo <local-repo-path>"
