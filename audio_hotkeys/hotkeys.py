from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

VK_NUMPAD = {i: 0x60 + i for i in range(10)}


class HotkeyService:
    """Register Ctrl+Alt+NumPad0-9 with Win32 RegisterHotKey."""

    def __init__(self, on_slot: Callable[[str], None]) -> None:
        self._on_slot = on_slot
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="hotkeys", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("Hotkey thread failed to start")

    def stop(self) -> None:
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None
        self._thread_id = 0

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        registered: list[int] = []
        try:
            for slot, vk in VK_NUMPAD.items():
                hotkey_id = slot + 1
                ok = user32.RegisterHotKey(
                    None,
                    hotkey_id,
                    MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
                    vk,
                )
                if not ok:
                    raise ctypes.WinError(ctypes.get_last_error())
                registered.append(hotkey_id)
            self._ready.set()

            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    hotkey_id = int(msg.wParam)
                    slot = str(hotkey_id - 1)
                    try:
                        self._on_slot(slot)
                    except Exception:
                        pass
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            for hotkey_id in registered:
                user32.UnregisterHotKey(None, hotkey_id)
            self._ready.set()
