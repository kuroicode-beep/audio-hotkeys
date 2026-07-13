# Register / unregister audio-hotkeys in the current user Startup folder.
param(
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$lnkPath = Join-Path $startup "audio-hotkeys.lnk"

$exe = Join-Path $PSScriptRoot "dist\audio-hotkeys.exe"
$fallback = Join-Path $PSScriptRoot "run.bat"
$target = if (Test-Path $exe) { $exe } else { $fallback }
$workDir = if (Test-Path $exe) { Split-Path $exe -Parent } else { $PSScriptRoot }

if ($Unregister) {
    if (Test-Path $lnkPath) {
        Remove-Item $lnkPath -Force
        Write-Host "Removed startup shortcut: $lnkPath"
    } else {
        Write-Host "No startup shortcut found."
    }
    exit 0
}

if (-not (Test-Path $target)) {
    throw "Nothing to register. Build first (.\build.ps1) or ensure run.bat exists."
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($lnkPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $workDir
$shortcut.WindowStyle = 7  # minimized / hidden for bat; ignored for exe
$shortcut.Description = "audio-hotkeys — Ctrl+Alt+NumPad audio snapshots"
$shortcut.Save()

Write-Host "Startup registered:"
Write-Host "  Shortcut: $lnkPath"
Write-Host "  Target:   $target"
