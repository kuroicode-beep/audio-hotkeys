# audio_hotkeys/hotkeys.py
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

# use_last_error=True is required: ctypes.get_last_error() only tracks the
# Win32 error for DLLs loaded this way. ctypes.windll would always report 0.
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
user32.GetMessageW.restype = ctypes.c_int
user32.PostThreadMessageW.argtypes = (wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.GetKeyState.argtypes = (ctypes.c_int,)
user32.GetKeyState.restype = ctypes.c_short

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_NUMLOCK = 0x90

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

VK_NUMPAD = {i: 0x60 + i for i in range(10)}

# Ctrl+Alt+NumPad N applies slot N; adding Shift saves the live audio state
# into slot N. Two id ranges keep the two actions apart in the message loop.
APPLY_ID_BASE = 1
SAVE_ID_BASE = 11


def numlock_on() -> bool:
    """NumPad VKs only reach RegisterHotKey while NumLock is on."""
    return bool(user32.GetKeyState(VK_NUMLOCK) & 1)


class HotkeyService:
    """Register Ctrl+Alt(+Shift)+NumPad0-9 with Win32 RegisterHotKey.

    Registration is per-slot and best-effort: one conflicting slot must not
    take down the other nine, and every failure is reported to the caller
    instead of killing the message-loop thread silently.
    """

    def __init__(
        self,
        on_slot: Callable[[str], None],
        on_save: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._on_slot = on_slot
        self._on_save = on_save
        self._on_error = on_error
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self.failures: list[tuple[str, str]] = []
        self.save_failures: list[tuple[str, str]] = []
        self.registered: list[int] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self.failures = []
        self.save_failures = []
        self.registered = []
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

    def status_warning(self) -> str:
        """Human-readable problem summary, or '' when every slot is live."""
        lines: list[str] = []
        for failures, label in ((self.failures, "적용"), (self.save_failures, "저장")):
            if not failures:
                continue
            slots = ", ".join(slot for slot, _ in failures)
            lines.append(f"{label} 단축키 등록 실패: NumPad {slots}\n{failures[0][1]}")
        if not numlock_on():
            lines.append("NumLock이 꺼져 있어 NumPad 단축키가 동작하지 않습니다.")
        return "\n".join(lines)

    def _register(self, hotkey_id: int, mods: int, vk: int) -> str:
        """Returns '' on success, else a human-readable reason."""
        if user32.RegisterHotKey(None, hotkey_id, mods | MOD_NOREPEAT, vk):
            self.registered.append(hotkey_id)
            return ""
        err = ctypes.get_last_error()
        if err == ERROR_HOTKEY_ALREADY_REGISTERED:
            return "다른 앱이 같은 조합을 이미 사용 중입니다."
        return ctypes.FormatError(err).strip() or f"WinError {err}"

    def _register_all(self) -> None:
        for slot, vk in VK_NUMPAD.items():
            reason = self._register(APPLY_ID_BASE + slot, MOD_CONTROL | MOD_ALT, vk)
            if reason:
                self.failures.append((str(slot), reason))
            if self._on_save is None:
                continue
            reason = self._register(SAVE_ID_BASE + slot, MOD_CONTROL | MOD_ALT | MOD_SHIFT, vk)
            if reason:
                self.save_failures.append((str(slot), reason))

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        try:
            self._register_all()
        finally:
            # Always release start(); a partial or total failure is reported
            # through self.failures, not by leaving the caller blocked.
            self._ready.set()

        if (self.failures or self.save_failures) and self._on_error:
            try:
                self._on_error(self.status_warning())
            except Exception:
                pass

        try:
            msg = wintypes.MSG()
            while True:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0:  # WM_QUIT
                    break
                if ret == -1:  # GetMessage error — bail instead of spinning
                    break
                if msg.message == WM_HOTKEY:
                    self._dispatch(int(msg.wParam))
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            for hotkey_id in self.registered:
                user32.UnregisterHotKey(None, hotkey_id)
            self.registered = []

    def _dispatch(self, hotkey_id: int) -> None:
        if hotkey_id >= SAVE_ID_BASE:
            handler, slot = self._on_save, hotkey_id - SAVE_ID_BASE
        else:
            handler, slot = self._on_slot, hotkey_id - APPLY_ID_BASE
        if handler is None:
            return
        try:
            handler(str(slot))
        except Exception:
            pass
