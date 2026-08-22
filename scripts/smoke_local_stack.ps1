$ErrorActionPreference = "Continue"
$processes = @()
try {
    $portalRoot = (Resolve-Path "$PSScriptRoot\..").Path
    $portalPython = Join-Path $portalRoot ".venv\Scripts\python.exe"
    $processes += Start-Process -FilePath $portalPython -ArgumentList "scripts\run_portal_local.py" -WorkingDirectory $portalRoot -WindowStyle Hidden -PassThru
    $processes += Start-Process -FilePath "C:\Users\kvman\PycharmProjects\scientific_calculator\.venv\Scripts\python.exe" -ArgumentList "app.py" -WorkingDirectory "C:\Users\kvman\PycharmProjects\scientific_calculator" -WindowStyle Hidden -PassThru
    $processes += Start-Process -FilePath "C:\Users\kvman\PycharmProjects\unit_converter\.venv\Scripts\python.exe" -ArgumentList "app.py" -WorkingDirectory "C:\Users\kvman\PycharmProjects\unit_converter" -WindowStyle Hidden -PassThru
    $processes += Start-Process -FilePath "C:\Users\kvman\PycharmProjects\pytex\.venv\Scripts\python.exe" -ArgumentList @("-m", "pytex.app", "serve", "--port", "8765") -WorkingDirectory "C:\Users\kvman\PycharmProjects\pytex" -WindowStyle Hidden -PassThru
    $processes += Start-Process -FilePath "C:\Users\kvman\HydrideSegmentation\.venv\Scripts\python.exe" -ArgumentList @("scripts\run_web_server.py", "--host", "127.0.0.1", "--port", "5005", "--no-preload") -WorkingDirectory "C:\Users\kvman\HydrideSegmentation" -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 8
    $urls = @(
        "http://127.0.0.1:5000/",
        "http://127.0.0.1:5000/api/catalog",
        "http://127.0.0.1:5000/pdf_tools/",
        "http://127.0.0.1:5055/",
        "http://127.0.0.1:5055/api/health",
        "http://127.0.0.1:5065/",
        "http://127.0.0.1:5065/api/health",
        "http://127.0.0.1:8765/",
        "http://127.0.0.1:8765/api/health",
        "http://127.0.0.1:5005/",
        "http://127.0.0.1:5005/health"
    )
    foreach ($url in $urls) {
        try { $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8; Write-Output "$url -> $($response.StatusCode)" }
        catch { Write-Output "$url -> ERROR: $($_.Exception.Message)" }
    }
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5055/api/evaluate" -Method Post -ContentType "application/json" -Body '{"expression":"sqrt(3**2 + 4**2)"}' -UseBasicParsing -TimeoutSec 8
        Write-Output "calculator evaluate -> $($response.StatusCode) $($response.Content)"
    } catch { Write-Output "calculator evaluate -> ERROR: $($_.Exception.Message)" }
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5065/api/expressions" -Method Post -ContentType "application/json" -Body '{"expression":"2 kg * 9.81 m/s^2 to N"}' -UseBasicParsing -TimeoutSec 8
        Write-Output "unit expression -> $($response.StatusCode) $($response.Content)"
    } catch { Write-Output "unit expression -> ERROR: $($_.Exception.Message)" }
} finally {
    foreach ($process in $processes) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
}
