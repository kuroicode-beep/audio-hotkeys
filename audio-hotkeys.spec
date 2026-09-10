# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["comtypes.stream", "psutil"]
hiddenimports += collect_submodules("comtypes")
hiddenimports += collect_submodules("pycaw")
# FLOW 8 믹서 연동(v1.7.0) — flow8core는 editable 설치라 경로를 직접 준다
hiddenimports += collect_submodules("flow8core") + ["rtmidi", "rtmidi._rtmidi"]

a = Analysis(
    ["launcher.py"],
    pathex=[".", "C:/Projects/svil-flow8-mcp"],
    binaries=[],
    datas=[
        ("tools/svcl/svcl.exe", "tools/svcl"),
        ("assets/fonts", "assets/fonts"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="audio-hotkeys",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
