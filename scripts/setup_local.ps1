$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    python -m venv (Join-Path $root ".venv")
}
& $python -m pip install -r (Join-Path $root "requirements.txt")
& $python -m pip install -e (Join-Path $root "..\pdf_tools")
& $python -m pip install -e (Join-Path $root "..\tabular_ml")
& $python -m pip install -r (Join-Path $root "requirements-test.txt")
$calculatorRoot = (Resolve-Path (Join-Path $root "..\scientific_calculator")).Path
$calculatorPython = Join-Path $calculatorRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $calculatorPython)) {
    python -m venv (Join-Path $calculatorRoot ".venv")
}
& $calculatorPython -m pip install -r (Join-Path $calculatorRoot "requirements.txt")
& $calculatorPython -m pip install -r (Join-Path $calculatorRoot "requirements-test.txt")
$unitRoot = (Resolve-Path (Join-Path $root "..\unit_converter")).Path
$unitPython = Join-Path $unitRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $unitPython)) {
    python -m venv (Join-Path $unitRoot ".venv")
}
& $unitPython -m pip install -r (Join-Path $unitRoot "requirements.txt")
Write-Host "Local portal environment is ready. Run .\start_platform.ps1 to launch the stack."
