from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from typing import Callable

import pystray
from pystray._win32 import Icon as WinIcon

from . import audio, config, theme
from .hotkeys import HotkeyService
from .i18n import t
from .settings import open_settings
from .tray import DarkTrayMenu, make_icon, show_profile_osd, toast
from .version import APP_VERSION
from .win_shell import force_app_dark_mode

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
        theme.enable_dpi_awareness()  # must precede the first Tk window
        self.root = tk.Tk()
        theme.init_scale(self.root)
        self.root.withdraw()
        self.root.title(f"audio-hotkeys v{APP_VERSION}")

        self.menu = DarkTrayMenu(
            self.root,
            on_settings=self.open_settings,
            on_apply=self.apply_slot,
            on_quit=self.quit,
        )

        self.icon = DarkIcon(
            "audio-hotkeys",
            make_icon(),
            f"audio-hotkeys v{APP_VERSION}",
            menu=None,
        )
        self.icon.dark_menu = self.menu
        self.icon.ui_root = self.root
        self.icon.on_left_click = self.open_settings

        self.hotkeys = HotkeyService(
            on_slot=lambda slot: self.root.after(0, lambda s=slot: self.apply_slot(s)),
            on_error=lambda text: self.root.after(0, lambda x=text: toast(self.root, x, level="warning")),
        )

    def start(self) -> None:
        try:
            self.hotkeys.start()
        except Exception as exc:  # noqa: BLE001
            toast(self.root, t("hotkey_failed", error=exc), level="error")

        self.icon.run_detached()
        self.root.after(400, self._startup_toast)
        self.root.mainloop()

    def _startup_toast(self) -> None:
        warning = self.hotkeys.status_warning()
        if warning:
            toast(self.root, warning, level="warning", ms=6000)
            return
        toast(self.root, t("running_toast"))

    def open_settings(self) -> None:
        open_settings(on_saved=lambda: toast(self.root, t("snapshots_saved")))

    def apply_slot(self, slot: str) -> None:
        data = config.load_config()
        snap = data["snapshots"].get(slot)
        if not snap:
            toast(self.root, t("slot_missing", slot=slot), level="error")
            return
        name = str(snap.get("name") or "").strip() or f"Slot {slot}"
        try:
            result = audio.apply_snapshot(snap)
        except Exception as exc:  # noqa: BLE001
            show_profile_osd(self.root, slot, name, level="error")
            toast(self.root, t("apply_failed", error=audio.com_message(exc)), level="error")
            return
        # The profile OSD is the whole point of the hotkey — show it even when a
        # single device is stale, and route the detail to its own toast.
        show_profile_osd(self.root, slot, name, level="warning" if result.warnings else "normal")
        if result.warnings:
            toast(self.root, "\n".join(result.warnings), level="warning", ms=5000)

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
    force_app_dark_mode()
    App().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
