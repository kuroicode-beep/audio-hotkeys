"""Windows shell helpers for SVIL §4.2 dark desktop shell."""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from ctypes import wintypes


def force_app_dark_mode() -> None:
    """uxtheme SetPreferredAppMode(ForceDark) + FlushMenuThemes (harmless if missing)."""
    if sys.platform != "win32":
        return
    try:
        uxtheme = ctypes.WinDLL("uxtheme")
        set_preferred = uxtheme[135]
        flush = uxtheme[136]
        set_preferred.argtypes = [ctypes.c_int]
        set_preferred.restype = ctypes.c_int
        flush.argtypes = []
        flush.restype = None
        set_preferred(2)  # ForceDark
        flush()
    except Exception:
        pass


def apply_dark_titlebar(window: tk.Misc) -> None:
    """OS-agnostic dark titlebar via DwmSetWindowAttribute (Win10 1903+ / Win11)."""
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = wintypes.HWND(int(window.wm_frame(), 16))
        value = ctypes.c_int(1)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (Win10 1903+); 19 used on older builds
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attr,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
    except Exception:
        pass


def prefers_reduced_motion() -> bool:
    """Best-effort Windows stand-in for CSS prefers-reduced-motion."""
    if sys.platform != "win32":
        return False
    try:
        SPI_GETCLIENTAREAANIMATION = 0x1042
        enabled = ctypes.c_bool(True)
        ok = ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETCLIENTAREAANIMATION,
            0,
            ctypes.byref(enabled),
            0,
        )
        if ok and not enabled.value:
            return True
    except Exception:
        pass
    return False
