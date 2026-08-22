$ErrorActionPreference = "Stop"
Write-Host "Starting Scientific Tools platform..."
$portalPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; & '$portalPython' scripts\run_portal_local.py"
$pytexPython = 'C:\Users\kvman\PycharmProjects\pytex\.venv\Scripts\python.exe'
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\kvman\PycharmProjects\pytex'; & '$pytexPython' -m pytex.app serve --port 8765"
$calculatorPython = 'C:\Users\kvman\PycharmProjects\scientific_calculator\.venv\Scripts\python.exe'
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\kvman\PycharmProjects\scientific_calculator'; & '$calculatorPython' app.py"
$unitPython = 'C:\Users\kvman\PycharmProjects\unit_converter\.venv\Scripts\python.exe'
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\kvman\PycharmProjects\unit_converter'; & '$unitPython' app.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'C:\Users\kvman\HydrideSegmentation'; .\.venv\Scripts\python.exe scripts\run_web_server.py --host 127.0.0.1 --port 5005 --no-preload"
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5000"
