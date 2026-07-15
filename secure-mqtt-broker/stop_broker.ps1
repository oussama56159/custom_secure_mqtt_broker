$connections = Get-NetTCPConnection -LocalPort 8883 -State Listen -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "Secure MQTT broker is not running on port 1884."
    exit 0
}

$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $processIds) {
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue

    if ($process -and $process.ProcessName -eq "mosquitto") {
        Stop-Process -Id $processId
        Write-Host "Stopped secure MQTT broker on port 8883."
    } else {
        Write-Host "Port 8883 is used by another process. Not stopping it."
    }
}
