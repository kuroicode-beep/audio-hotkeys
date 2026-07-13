from __future__ import annotations

import threading
import tkinter as tk
from typing import Callable

from PIL import Image, ImageDraw

from . import config

BG = "#121212"
FG = "#F2F2F2"
HOVER = "#2A2A2A"
FOCUS = "#FFFF00"
BORDER = "#3A3A3A"
FONT = ("Segoe UI", 16)


def make_icon(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, size - 5, size - 5), fill=(30, 30, 30, 255), outline=(242, 242, 242, 255), width=3)
    # simple speaker wedge
    draw.polygon(
        [
            (size * 0.28, size * 0.38),
            (size * 0.45, size * 0.38),
            (size * 0.62, size * 0.25),
            (size * 0.62, size * 0.75),
            (size * 0.45, size * 0.62),
            (size * 0.28, size * 0.62),
        ],
        fill=(242, 242, 242, 255),
    )
    return img


class DarkTrayMenu:
    """Custom dark popup menu (Windows native tray menus follow OS theme only)."""

    def __init__(
        self,
        root: tk.Tk,
        on_settings: Callable[[], None],
        on_apply: Callable[[str], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.root = root
        self.on_settings = on_settings
        self.on_apply = on_apply
        self.on_quit = on_quit
        self._popup: tk.Toplevel | None = None

    def show(self, x: int, y: int) -> None:
        self.close()
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=BORDER)
        self._popup = popup

        frame = tk.Frame(popup, bg=BG, highlightthickness=0)
        frame.pack(padx=1, pady=1)

        self._item(frame, "Settings…", self._wrap(self.on_settings))
        self._sep(frame)

        data = config.load_config()
        for key in config.SLOT_KEYS:
            snap = data["snapshots"][key]
            label = snap.get("name") or f"Slot {key}"
            text = f"Ctrl+Alt+Num{key}  {label}"
            self._item(frame, text, self._wrap(lambda k=key: self.on_apply(k)))

        self._sep(frame)
        self._item(frame, "Quit", self._wrap(self.on_quit))

        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        px = min(x, screen_w - w - 8)
        py = min(y - h, screen_h - h - 8)
        popup.geometry(f"+{max(0, px)}+{max(0, py)}")
        popup.focus_force()
        popup.bind("<Escape>", lambda _e: self.close())
        popup.bind("<FocusOut>", lambda _e: self.root.after(150, self._close_if_unfocused))

    def close(self) -> None:
        if self._popup is not None:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass
            self._popup = None

    def _close_if_unfocused(self) -> None:
        if self._popup is None:
            return
        try:
            if self._popup.focus_displayof() is None:
                self.close()
        except tk.TclError:
            self.close()

    def _wrap(self, fn: Callable[[], None]) -> Callable[[], None]:
        def runner() -> None:
            self.close()
            fn()

        return runner

    def _item(self, parent: tk.Frame, text: str, command: Callable[[], None]) -> None:
        btn = tk.Button(
            parent,
            text=text,
            anchor="w",
            command=command,
            bg=BG,
            fg=FG,
            activebackground=HOVER,
            activeforeground=FG,
            relief="flat",
            bd=0,
            padx=16,
            pady=12,
            font=FONT,
            highlightthickness=2,
            highlightbackground=BG,
            highlightcolor=FOCUS,
            cursor="hand2",
        )
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda _e: btn.configure(bg=HOVER))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=BG))

    def _sep(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)


def toast(root: tk.Tk, message: str, ms: int = 2200) -> None:
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=BORDER)
    frame = tk.Frame(win, bg=BG)
    frame.pack(padx=1, pady=1)
    lbl = tk.Label(
        frame,
        text=message,
        bg=BG,
        fg=FG,
        font=FONT,
        padx=18,
        pady=14,
        justify="left",
        wraplength=420,
    )
    lbl.pack()
    win.update_idletasks()
    x = win.winfo_screenwidth() - win.winfo_reqwidth() - 24
    y = win.winfo_screenheight() - win.winfo_reqheight() - 72
    win.geometry(f"+{x}+{y}")
    win.after(ms, win.destroy)


def run_on_ui(root: tk.Tk, fn: Callable[[], None]) -> None:
    root.after(0, fn)
