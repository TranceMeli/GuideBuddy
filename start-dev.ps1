# Starts GuideBuddy (Django backend + Nuxt frontend) on the next free ports.
#   powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
# Preferred ports are 8000 (backend) and 3000 (frontend); if one is taken, the next free one is used.
# Servers of this project that are already running are stopped first, other projects are left alone.

$root = $PSScriptRoot

function Get-FreePort([int]$start) {
    for ($port = $start; $port -lt $start + 100; $port++) {
        $busy = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $busy) {
            try {
                $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
                $listener.Start(); $listener.Stop()
                return $port
            } catch { }
        }
    }
    throw "No free port found from $start on."
}

# Stop earlier servers of this project only
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($root) -and $_.CommandLine -match 'runserver|nuxi|nuxt' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

$backendPort = Get-FreePort 8000
$frontendPort = Get-FreePort 3000
if ($frontendPort -eq $backendPort) { $frontendPort = Get-FreePort ($frontendPort + 1) }

Start-Process -WindowStyle Hidden -FilePath "$root\.venv\Scripts\python.exe" `
    -ArgumentList 'manage.py', 'runserver', $backendPort -WorkingDirectory $root

$env:NUXT_API_BASE = "http://127.0.0.1:$backendPort/api"
Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' `
    -ArgumentList '/c', "npm run dev -- --port $frontendPort" -WorkingDirectory "$root\frontend"

Write-Host "Backend:  http://localhost:$backendPort"
Write-Host "Frontend: http://localhost:$frontendPort"
