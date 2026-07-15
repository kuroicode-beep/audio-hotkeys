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
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_NUMLOCK = 0x90

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

VK_NUMPAD = {i: 0x60 + i for i in range(10)}


def numlock_on() -> bool:
    """NumPad VKs only reach RegisterHotKey while NumLock is on."""
    return bool(user32.GetKeyState(VK_NUMLOCK) & 1)


class HotkeyService:
    """Register Ctrl+Alt+NumPad0-9 with Win32 RegisterHotKey.

    Registration is per-slot and best-effort: one conflicting slot must not
    take down the other nine, and every failure is reported to the caller
    instead of killing the message-loop thread silently.
    """

    def __init__(
        self,
        on_slot: Callable[[str], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._on_slot = on_slot
        self._on_error = on_error
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self.failures: list[tuple[str, str]] = []
        self.registered_slots: list[str] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self.failures = []
        self.registered_slots = []
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
        if self.failures:
            slots = ", ".join(slot for slot, _ in self.failures)
            reason = self.failures[0][1]
            lines.append(f"단축키 등록 실패: NumPad {slots}\n{reason}")
        if not numlock_on():
            lines.append("NumLock이 꺼져 있어 NumPad 단축키가 동작하지 않습니다.")
        return "\n".join(lines)

    def _register_all(self) -> None:
        for slot, vk in VK_NUMPAD.items():
            hotkey_id = slot + 1
            ok = user32.RegisterHotKey(None, hotkey_id, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk)
            if ok:
                self.registered_slots.append(str(slot))
                continue
            err = ctypes.get_last_error()
            if err == ERROR_HOTKEY_ALREADY_REGISTERED:
                reason = "다른 앱이 같은 조합을 이미 사용 중입니다."
            else:
                reason = ctypes.FormatError(err).strip() or f"WinError {err}"
            self.failures.append((str(slot), reason))

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        try:
            self._register_all()
        finally:
            # Always release start(); a partial or total failure is reported
            # through self.failures, not by leaving the caller blocked.
            self._ready.set()

        if self.failures and self._on_error:
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
                    slot = str(int(msg.wParam) - 1)
                    try:
                        self._on_slot(slot)
                    except Exception:
                        pass
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            for slot in self.registered_slots:
                user32.UnregisterHotKey(None, int(slot) + 1)
            self.registered_slots = []
