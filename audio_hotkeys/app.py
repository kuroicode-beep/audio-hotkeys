from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from typing import Callable

import pystray
from pystray._win32 import Icon as WinIcon

from . import audio, config
from .hotkeys import HotkeyService
from .settings import open_settings
from .tray import DarkTrayMenu, make_icon, toast

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205


class DarkIcon(WinIcon):
    """pystray Icon that opens a custom dark menu on right-click."""

    dark_menu: DarkTrayMenu | None = None
    ui_root: tk.Tk | None = None
    on_left_click: Callable[[], None] | None = None

    def _on_notify(self, wparam, lparam):  # noqa: ANN001
        if lparam == WM_LBUTTONUP:
            if self.on_left_click and self.ui_root:
                self.ui_root.after(0, self.on_left_click)
            return
        if lparam == WM_RBUTTONUP and self.dark_menu and self.ui_root:
            point = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            self.ui_root.after(0, lambda: self.dark_menu.show(point.x, point.y))
            return
        return super()._on_notify(wparam, lparam)


class App:
    def __init__(self) -> None:
        config.ensure_config()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("audio-hotkeys")

        self.menu = DarkTrayMenu(
            self.root,
            on_settings=self.open_settings,
            on_apply=self.apply_slot,
            on_quit=self.quit,
        )

        self.icon = DarkIcon(
            "audio-hotkeys",
            make_icon(),
            "audio-hotkeys",
            menu=None,
        )
        self.icon.dark_menu = self.menu
        self.icon.ui_root = self.root
        self.icon.on_left_click = self.open_settings

        self.hotkeys = HotkeyService(on_slot=lambda slot: self.root.after(0, lambda s=slot: self.apply_slot(s)))

    def start(self) -> None:
        try:
            self.hotkeys.start()
        except OSError as exc:
            toast(self.root, f"Hotkey register failed: {exc}")

        self.icon.run_detached()
        toast(self.root, "audio-hotkeys running\nCtrl+Alt+NumPad 0–9")
        self.root.mainloop()

    def open_settings(self) -> None:
        open_settings(on_saved=lambda: toast(self.root, "Snapshots saved"))

    def apply_slot(self, slot: str) -> None:
        data = config.load_config()
        snap = data["snapshots"].get(slot)
        if not snap:
            toast(self.root, f"Slot {slot} missing")
            return
        try:
            summary = audio.apply_snapshot(snap)
            toast(self.root, summary)
        except Exception as exc:  # noqa: BLE001
            toast(self.root, f"Apply failed: {exc}")

    def quit(self) -> None:
        try:
            self.hotkeys.stop()
        except Exception:
            pass
        try:
            self.icon.stop()
        except Exception:
            pass
        self.root.after(0, self.root.destroy)


def main() -> int:
    if sys.platform != "win32":
        print("audio-hotkeys supports Windows only", file=sys.stderr)
        return 1
    App().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
