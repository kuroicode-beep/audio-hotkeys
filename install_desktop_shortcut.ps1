# 바탕화면에 audio-hotkeys 바로가기를 만든다 / 지운다.
param(
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "audio-hotkeys.lnk"

if ($Unregister) {
    if (Test-Path $lnkPath) {
        Remove-Item $lnkPath -Force
        Write-Host "Removed desktop shortcut: $lnkPath"
    } else {
        Write-Host "No desktop shortcut found."
    }
    exit 0
}

$exe = Join-Path $PSScriptRoot "dist\audio-hotkeys.exe"
if (-not (Test-Path $exe)) {
    throw "exe가 없습니다. 먼저 .\build.ps1 을 실행하세요: $exe"
}

$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut($lnkPath)
$lnk.TargetPath = $exe
$lnk.WorkingDirectory = Split-Path $exe -Parent
$lnk.Description = "audio-hotkeys — Ctrl+Alt+NumPad 오디오 스냅샷"
$lnk.Save()

if (-not (Test-Path $lnkPath)) {
    throw "바로가기 생성에 실패했습니다: $lnkPath"
}
Write-Host "Desktop shortcut created:"
Write-Host "  Shortcut: $lnkPath"
Write-Host "  Target:   $exe"
