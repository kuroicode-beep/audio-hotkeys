# audio_hotkeys/foreground.py
from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import threading
from typing import Callable

# Alt+Tab is a Windows-reserved key — RegisterHotKey can't take it without
# breaking the switch itself. Instead we watch EVENT_SYSTEM_FOREGROUND, which
# fires whenever the foreground window changes (Alt+Tab, click, taskbar, …).
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
OBJID_WINDOW = 0
WM_QUIT = 0x0012

_HOOKPROC = ctypes.WINFUNCTYPE(
    None,
    wintypes.HANDLE,  # hWinEventHook
    wintypes.DWORD,   # event
    wintypes.HWND,    # hwnd
    wintypes.LONG,    # idObject
    wintypes.LONG,    # idChild
    wintypes.DWORD,   # idEventThread
    wintypes.DWORD,   # dwmsEventTime
)

user32.SetWinEventHook.restype = wintypes.HANDLE
user32.SetWinEventHook.argtypes = (
    wintypes.DWORD, wintypes.DWORD, wintypes.HMODULE, _HOOKPROC,
    wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
)
user32.UnhookWinEvent.argtypes = (wintypes.HANDLE,)
user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetGUIThreadInfo = user32.GetGUIThreadInfo  # noqa: PLW0127


def _window_title(hwnd: int) -> str:
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


class ForegroundWatcher:
    """Report the title of each newly-foregrounded top-level window.

    Best-effort and self-contained: a failed hook is reported, never crashes
    the app. The callback runs on the UI thread via the caller's marshaller.
    """

    def __init__(
        self,
        on_switch: Callable[[str], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._on_switch = on_switch
        self._on_error = on_error
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._hook = None
        self._proc = _HOOKPROC(self._handle)  # keep a ref — GC'd proc = crash
        self._last_hwnd = 0
        self._own_pid = kernel32.GetCurrentProcessId()
        self.enabled = False
        self.active = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.enabled = True
        self._thread = threading.Thread(target=self._run, name="foreground", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.enabled = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None
        self._thread_id = 0
        self.active = False

    def toggle(self) -> bool:
        if self.enabled:
            self.stop()
        else:
            self.start()
        return self.enabled

    # --- hook thread ------------------------------------------------------
    def _handle(self, hook, event, hwnd, id_object, id_child, thread, ms) -> None:  # noqa: ANN001
        if id_object != OBJID_WINDOW or not hwnd:
            return
        if hwnd == self._last_hwnd:
            return
        self._last_hwnd = hwnd
        title = _window_title(hwnd)
        if not title:
            return
        try:
            self._on_switch(title)
        except Exception:  # noqa: BLE001
            pass

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND,
            0, self._proc, 0, 0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
        )
        if not self._hook:
            self.active = False
            if self._on_error:
                try:
                    self._on_error("창 전환 감지 훅 등록에 실패했습니다.")
                except Exception:  # noqa: BLE001
                    pass
            return
        self.active = True

        msg = wintypes.MSG()
        try:
            while True:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret in (0, -1):  # WM_QUIT or error
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._hook:
                user32.UnhookWinEvent(self._hook)
                self._hook = None
            self.active = False
