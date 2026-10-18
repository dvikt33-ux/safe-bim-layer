# One high-level test from the existing GitHub queue. Only port 19724 / copied test PLN.
param([switch]$Healthcheck, [switch]$Loop)
$ErrorActionPreference = 'Stop'
$src = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$branch = 'feature/apa-ac29-group-acceptance-mailbox-20261018'
$expected = 'C:\LocalAI\APA_Functional_Test_House_01.pln'
if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw 'Исходный тестовый PLN не найден' }
if (Get-Process -Name 'Archicad*' -ErrorAction SilentlyContinue) {
    Write-Host 'Archicad может оставаться открытым — тест выполняется в экземпляре на порту 19724.'
}
$actualBranch = (& git -C $src branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $actualBranch -ne $branch) {
    throw "Ожидается локальная ветка $branch; текущая ветка $actualBranch"
}
$revision = (& git -C $src rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[0-9a-f]{40}$') { throw 'Не удалось определить SHA локального исполнителя' }
$changes = & git -C $src status --porcelain
if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Рабочее дерево локального исполнителя должно быть чистым' }
$python = (Get-Command python -ErrorAction Stop).Source
$params = @((Join-Path $PSScriptRoot 'apa_ac29_group_acceptance_mailbox.py'), '--source-repo', $src, '--approved-sha', $revision)
if ($Healthcheck) { $params += '--healthcheck' }
if ($Loop) { $params += '--loop' }
Write-Host 'APA AC29: один комплексный тест групп, только копия APA_Functional_Test_House_01.pln, порт 19724.'
& $python @params
if ($LASTEXITCODE -ne 0) { throw "Локальный исполнитель завершился с кодом $LASTEXITCODE" }
