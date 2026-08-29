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

# 시작 시각을 잡아 둔다. 아래에서 exe가 실제로 이번 실행에 다시 만들어졌는지 판정하는 기준이다.
$startedAt = Get-Date

& $py -m PyInstaller --noconfirm --clean "$PSScriptRoot\audio-hotkeys.spec"
$pyiExit = $LASTEXITCODE

$exe = Join-Path $PSScriptRoot "dist\audio-hotkeys.exe"
if (-not (Test-Path $exe)) {
    throw "Build failed: $exe not found"
}

# 2026-08-30 — 여기서 exe '존재'만 보다가 실패를 성공으로 오판했다.
# --clean이 build\ 삭제에서 PermissionError로 죽었는데도 8/1자 옛 exe가 남아 있어
# "Built:"가 찍혔다. 존재가 아니라 **이번 실행에 갱신됐는지**로 판정한다.
if ($pyiExit -ne 0) {
    throw "Build failed: PyInstaller exit $pyiExit (dist\audio-hotkeys.exe 는 이전 빌드 산출물이다)"
}
$exeItem = Get-Item $exe
if ($exeItem.LastWriteTime -lt $startedAt) {
    throw ("Build failed: exe가 갱신되지 않았다 (LastWriteTime {0} < 시작 {1}). " -f $exeItem.LastWriteTime, $startedAt) +
          "build\ 폴더가 잠겨 --clean이 실패했을 수 있다 — build\ 를 지우고 다시 돌린다."
}
Write-Host "Built: $exe"
Get-Item $exe | Format-List FullName, Length, LastWriteTime
