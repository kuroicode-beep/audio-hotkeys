# Build audio-hotkeys.exe with PyInstaller (windowed, onefile).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating venv..."
    py -3.13 -m venv .venv
    & $py -m pip install -r requirements.txt
}

& $py -m pip install -q pyinstaller
& $py -m PyInstaller --noconfirm --clean "$PSScriptRoot\audio-hotkeys.spec"

$exe = Join-Path $PSScriptRoot "dist\audio-hotkeys.exe"
if (-not (Test-Path $exe)) {
    throw "Build failed: $exe not found"
}
Write-Host "Built: $exe"
Get-Item $exe | Format-List FullName, Length, LastWriteTime
