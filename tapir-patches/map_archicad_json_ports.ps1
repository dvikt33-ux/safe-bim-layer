$ErrorActionPreference = 'Stop'

Write-Host 'SAFE BIM / ARCHICAD JSON PORT MAP'
Write-Host ''

$archicad = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(ARCHICAD|Archicad)' }

if (-not $archicad) {
    throw 'No running Archicad process found.'
}

Write-Host 'ARCHICAD PROCESSES'
$archicad | Select-Object Id, ProcessName, StartTime, Path | Format-Table -AutoSize

$pids = @($archicad.Id)
$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $pids -contains $_.OwningProcess } | Sort-Object OwningProcess, LocalPort

Write-Host ''
Write-Host 'LISTENING PORTS OWNED BY ARCHICAD'
if (-not $listeners) {
    Write-Host 'None.'
} else {
    $listeners | Select-Object OwningProcess, LocalAddress, LocalPort | Format-Table -AutoSize
}

# Also show every listener in the traditional Archicad JSON range and its owner.
Write-Host ''
Write-Host 'PORTS 19723..19743 AND THEIR OWNERS'
$range = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -ge 19723 -and $_.LocalPort -le 19743 } | Sort-Object LocalPort
foreach ($conn in $range) {
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    [pscustomobject]@{
        Port = $conn.LocalPort
        PID = $conn.OwningProcess
        Process = if ($proc) { $proc.ProcessName } else { '<unknown>' }
        Path = if ($proc) { $proc.Path } else { '' }
    }
} | Format-Table -AutoSize

function Invoke-JsonPost {
    param(
        [int]$Port,
        [hashtable]$Payload,
        [int]$TimeoutMs = 1500
    )

    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout = [TimeSpan]::FromMilliseconds($TimeoutMs)
    try {
        $json = $Payload | ConvertTo-Json -Depth 12 -Compress
        $content = New-Object System.Net.Http.StringContent($json, [Text.Encoding]::UTF8, 'application/json')
        $response = $client.PostAsync("http://127.0.0.1:$Port", $content).GetAwaiter().GetResult()
        $text = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        return [pscustomobject]@{ Ok = $true; Status = [int]$response.StatusCode; Body = $text }
    } catch {
        return [pscustomobject]@{ Ok = $false; Status = $null; Body = $_.Exception.Message }
    } finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

$candidates = @($listeners.LocalPort | Sort-Object -Unique)
Write-Host ''
Write-Host 'PROBING ARCHICAD-OWNED PORTS WITH NATIVE API.GetProductInfo'

$validJsonPorts = @()
foreach ($port in $candidates) {
    $native = Invoke-JsonPost -Port $port -Payload @{ command = 'API.GetProductInfo' }
    if (-not $native.Ok) {
        Write-Host "$port : no JSON API response -> $($native.Body)"
        continue
    }

    Write-Host "$port : HTTP $($native.Status)"
    Write-Host $native.Body

    try {
        $parsed = $native.Body | ConvertFrom-Json
        if ($parsed.succeeded -eq $true -or $parsed.result) {
            $validJsonPorts += $port
        }
    } catch {}
}

Write-Host ''
Write-Host 'NATIVE ARCHICAD JSON PORTS:' ($validJsonPorts -join ', ')

foreach ($port in $validJsonPorts) {
    Write-Host ''
    Write-Host "TAPIR PROBE ON PORT $port"
    $payload = @{
        command = 'API.ExecuteAddOnCommand'
        parameters = @{
            addOnCommandId = @{
                commandNamespace = 'TapirCommand'
                commandName = 'GetAddOnVersion'
            }
            addOnCommandParameters = @{}
        }
    }
    $tapir = Invoke-JsonPost -Port $port -Payload $payload -TimeoutMs 3000
    Write-Host $tapir.Body
}

Write-Host ''
Write-Host 'DONE'
