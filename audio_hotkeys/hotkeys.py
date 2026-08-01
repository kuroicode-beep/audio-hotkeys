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
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_NUMLOCK = 0x90

WH_KEYBOARD_LL = 13
LLKHF_EXTENDED = 0x01

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

VK_NUMPAD = {i: 0x60 + i for i in range(10)}
VK_DECIMAL = 0x6E  # NumPad "." — needs NumLock, like the digits
VK_OEM_PERIOD = 0xBE  # main-keyboard "." — works with NumLock off

# Physical NumPad digit scan codes. NumLock/Shift never change these, and the
# extended flag is what separates them from the main-keyboard nav cluster.
SC_NUMPAD = {
    0x52: 0, 0x4F: 1, 0x50: 2, 0x51: 3, 0x4B: 4,
    0x4C: 5, 0x4D: 6, 0x47: 7, 0x48: 8, 0x49: 9,
}


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = (
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


_HOOKPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes = (ctypes.c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.UnhookWindowsHookEx.argtypes = (wintypes.HHOOK,)
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.CallNextHookEx.argtypes = (wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.CallNextHookEx.restype = wintypes.LPARAM
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

# Ctrl+Alt+NumPad N applies slot N; adding Shift saves the live audio state
# into slot N; Ctrl+Alt+"." toggles back to the previously applied slot.
# Separate id ranges keep the actions apart in the message loop.
APPLY_ID_BASE = 1
SAVE_ID_BASE = 11
TOGGLE_IDS = (21, 22)


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
        on_toggle: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._on_slot = on_slot
        self._on_save = on_save
        self._on_toggle = on_toggle
        self._on_error = on_error
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._hook: int | None = None
        # The callback ref must live on the instance — if it gets GC'd the
        # process crashes inside the hook dispatch (same trap as foreground.py).
        self._hook_cb = _HOOKPROC(self._ll_keyboard)
        # Scan codes we swallowed on keydown — suppresses hook-level autorepeat
        # (RegisterHotKey's MOD_NOREPEAT does not apply here) and lets us
        # swallow the matching keyup as well.
        self._save_held: set[int] = set()
        self.failures: list[tuple[str, str]] = []
        self.save_failures: list[tuple[str, str]] = []
        self.registered: list[int] = []
        self.toggle_live = False
        self.save_hook_live = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self.failures = []
        self.save_failures = []
        self.registered = []
        self.toggle_live = False
        self.save_hook_live = False
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
        # Save slots ride on the keyboard hook; registration failures for them
        # only matter when the hook could not be installed either.
        save_failures = [] if self.save_hook_live else self.save_failures
        for failures, label in ((self.failures, "적용"), (save_failures, "저장")):
            if not failures:
                continue
            slots = ", ".join(slot for slot, _ in failures)
            lines.append(f"{label} 단축키 등록 실패: NumPad {slots}\n{failures[0][1]}")
        if self._on_save is not None and not self.save_hook_live:
            lines.append("저장 단축키 감지 훅 설치에 실패했습니다. Ctrl+Alt+Shift+NumPad가 동작하지 않을 수 있습니다.")
        if self._on_toggle is not None and not self.toggle_live:
            lines.append("토글 단축키(Ctrl+Alt+.) 등록에 실패했습니다.")
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

        if self._on_toggle is None:
            return
        # Both "." keys drive the same toggle. The main-keyboard one keeps
        # working when NumLock is off, so either alone is enough.
        for hotkey_id, vk in zip(TOGGLE_IDS, (VK_DECIMAL, VK_OEM_PERIOD)):
            if not self._register(hotkey_id, MOD_CONTROL | MOD_ALT, vk):
                self.toggle_live = True

    def _save_combo_down(self, vk: int) -> bool:
        """True when Ctrl+Alt+Shift is physically held for a NumPad keydown.

        The keyboard driver fakes a Shift *release* around Shift+NumPad and
        flips the key's NumLock meaning (Shift+NumPad8 arrives as VK_UP with
        Shift up), which is why RegisterHotKey(MOD_SHIFT, VK_NUMPAD*) never
        fires from a real keyboard. A digit/NumLock mismatch therefore means
        Shift is actually held even when GetAsyncKeyState says otherwise.
        """
        def down(key: int) -> bool:
            return bool(user32.GetAsyncKeyState(key) & 0x8000)

        if not (down(VK_CONTROL) and down(VK_MENU)):
            return False
        if down(VK_SHIFT):
            return True
        is_digit = 0x60 <= vk <= 0x69
        return is_digit != numlock_on()

    def _ll_keyboard(self, n_code: int, w_param: int, l_param: int) -> int:
        if n_code == 0 and self._on_save is not None:
            kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if not kb.flags & LLKHF_EXTENDED and kb.scanCode in SC_NUMPAD:
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    if kb.scanCode in self._save_held:
                        return 1  # autorepeat of a swallowed key
                    if self._save_combo_down(kb.vkCode):
                        self._save_held.add(kb.scanCode)
                        try:
                            self._on_save(str(SC_NUMPAD[kb.scanCode]))
                        except Exception:
                            pass
                        return 1  # swallow — keep the nav key out of the focused app
                elif w_param in (WM_KEYUP, WM_SYSKEYUP) and kb.scanCode in self._save_held:
                    self._save_held.discard(kb.scanCode)
                    return 1  # swallow the matching keyup too
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _run(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        try:
            self._register_all()
            if self._on_save is not None:
                # Save combos need the hook (see _save_combo_down); the
                # RegisterHotKey slots above stay as a synthetic-input fallback.
                self._hook = user32.SetWindowsHookExW(
                    WH_KEYBOARD_LL, self._hook_cb, kernel32.GetModuleHandleW(None), 0
                )
                self.save_hook_live = bool(self._hook)
        finally:
            # Always release start(); a partial or total failure is reported
            # through self.failures, not by leaving the caller blocked.
            self._ready.set()

        if self._on_error:
            warning = self.status_warning()
            # NumLock-off alone is reported by the startup toast, not here.
            if self.failures or self.save_failures or (self._on_toggle and not self.toggle_live):
                try:
                    self._on_error(warning)
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
            if self._hook:
                user32.UnhookWindowsHookEx(self._hook)
                self._hook = None
                self.save_hook_live = False
            for hotkey_id in self.registered:
                user32.UnregisterHotKey(None, hotkey_id)
            self.registered = []

    def _dispatch(self, hotkey_id: int) -> None:
        try:
            if hotkey_id in TOGGLE_IDS:
                if self._on_toggle is not None:
                    self._on_toggle()
                return
            if hotkey_id >= SAVE_ID_BASE:
                handler, slot = self._on_save, hotkey_id - SAVE_ID_BASE
            else:
                handler, slot = self._on_slot, hotkey_id - APPLY_ID_BASE
            if handler is not None:
                handler(str(slot))
        except Exception:
            pass
