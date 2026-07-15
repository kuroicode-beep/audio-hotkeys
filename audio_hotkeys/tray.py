from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import Image, ImageDraw

from . import config, prefs, theme
from .i18n import t
from .win_shell import prefers_reduced_motion


def make_icon(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        (4, 4, size - 5, size - 5),
        fill=(13, 13, 18, 255),
        outline=(245, 245, 247, 255),
        width=3,
    )
    draw.polygon(
        [
            (size * 0.28, size * 0.38),
            (size * 0.45, size * 0.38),
            (size * 0.62, size * 0.25),
            (size * 0.62, size * 0.75),
            (size * 0.45, size * 0.62),
            (size * 0.28, size * 0.62),
        ],
        fill=(179, 221, 255, 255),
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
        p = prefs.load_prefs()
        font = prefs.ui_font(self.root, p)
        lang = p["lang"]

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.BORDER_STRONG)
        self._popup = popup

        frame = tk.Frame(popup, bg=theme.BG, highlightthickness=0)
        frame.pack(padx=1, pady=1)

        self._item(frame, t("settings", lang), self._wrap(self.on_settings), font)
        self._sep(frame)

        data = config.load_config()
        for key in config.SLOT_KEYS:
            snap = data["snapshots"][key]
            label = (snap.get("name") or "").strip() or f"Slot {key}"
            text = f"[{key}]  {label}"
            self._item(frame, text, self._wrap(lambda k=key: self.on_apply(k)), font)

        self._sep(frame)
        self._item(frame, t("quit", lang), self._wrap(self.on_quit), font)

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

    def _item(self, parent: tk.Frame, text: str, command: Callable[[], None], font: tuple) -> None:
        btn = tk.Button(
            parent,
            text=text,
            anchor="w",
            command=command,
            bg=theme.BG,
            fg=theme.TEXT,
            activebackground=theme.SURFACE_2,
            activeforeground=theme.ACCENT_STRONG,
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            font=font,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightbackground=theme.BG,
            highlightcolor=theme.FOCUS,
            cursor="hand2",
        )
        btn.pack(fill="x", ipady=4)
        btn.bind("<Enter>", lambda _e: btn.configure(bg=theme.SURFACE_2))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=theme.BG))

    def _sep(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", padx=8, pady=4)


_osd_win: tk.Toplevel | None = None
_osd_job: str | None = None


def toast(root: tk.Tk, message: str, ms: int = 2200) -> None:
    p = prefs.load_prefs()
    font = prefs.ui_font(root, p)
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=theme.BORDER_STRONG)
    frame = tk.Frame(win, bg=theme.SURFACE)
    frame.pack(padx=1, pady=1)
    lbl = tk.Label(
        frame,
        text=message,
        bg=theme.SURFACE,
        fg=theme.TEXT,
        font=font,
        padx=22,
        pady=18,
        justify="left",
        wraplength=420,
    )
    lbl.pack()
    win.update_idletasks()
    x = win.winfo_screenwidth() - win.winfo_reqwidth() - 24
    y = win.winfo_screenheight() - win.winfo_reqheight() - 72
    win.geometry(f"+{x}+{y}")
    win.after(ms, win.destroy)


def show_profile_osd(
    root: tk.Tk,
    slot: str,
    name: str = "",
    *,
    hold_ms: int = 1100,
    fade_ms: int = 280,
    steps: int = 12,
) -> None:
    """Large centered snapshot name with fade-in / fade-out (no bold — size hierarchy)."""
    global _osd_win, _osd_job
    _cancel_osd(root)

    p = prefs.load_prefs()
    family = prefs.resolve_family(p["font_id"], root)
    base = theme.FONT_SIZE_PX.get(p["font_size"], 18)
    # Guide: no bold — use size only. OSD scales from base.
    name_font = (family, max(64, base * 5))
    slot_font = ("Consolas", max(28, base * 2))
    lang = p["lang"]

    title = (name or "").strip() or f"Slot {slot}"

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", 0.0)
    win.configure(bg=theme.BG)

    outer = tk.Frame(win, bg=theme.BG, padx=80, pady=56)
    outer.pack()
    tk.Label(
        outer,
        text=title,
        bg=theme.BG,
        fg=theme.TEXT,
        font=name_font,
        justify="center",
        wraplength=1200,
    ).pack()
    tk.Label(
        outer,
        text=t("numpad", lang, slot=slot),
        bg=theme.BG,
        fg=theme.TEXT_SUB,
        font=slot_font,
        justify="center",
    ).pack(pady=(12, 0))

    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
    x = max(0, (sw - ww) // 2)
    y = max(0, (sh - wh) // 3)
    win.geometry(f"{ww}x{wh}+{x}+{y}")
    win.attributes("-topmost", True)
    try:
        win.lift()
        win.update_idletasks()
    except tk.TclError:
        pass

    _osd_win = win
    if prefers_reduced_motion():
        try:
            win.attributes("-alpha", 0.92)
        except tk.TclError:
            pass
        _osd_job = root.after(hold_ms, lambda: _destroy_osd(win))
        return

    interval = max(12, fade_ms // steps)
    peak = 0.92

    def set_alpha(value: float) -> None:
        if _osd_win is not win:
            return
        try:
            win.attributes("-alpha", max(0.0, min(1.0, value)))
        except tk.TclError:
            pass

    def fade(to: float, done: Callable[[], None] | None = None) -> None:
        nonlocal_state = {"n": 0}

        def tick() -> None:
            global _osd_job
            if _osd_win is not win:
                return
            nonlocal_state["n"] += 1
            progress = nonlocal_state["n"] / steps
            eased = progress * progress * (3 - 2 * progress)
            start = getattr(win, "_osd_alpha", 0.0)
            set_alpha(start + (to - start) * eased)
            if nonlocal_state["n"] >= steps:
                win._osd_alpha = to  # type: ignore[attr-defined]
                set_alpha(to)
                _osd_job = None
                if done:
                    done()
                return
            _osd_job = root.after(interval, tick)

        win._osd_alpha = float(win.attributes("-alpha"))  # type: ignore[attr-defined]
        tick()

    def after_hold() -> None:
        fade(0.0, lambda: _destroy_osd(win))

    def after_in() -> None:
        global _osd_job
        _osd_job = root.after(hold_ms, after_hold)

    fade(peak, after_in)


def _destroy_osd(win: tk.Toplevel) -> None:
    global _osd_win, _osd_job
    if _osd_win is win:
        _osd_win = None
    _osd_job = None
    try:
        win.destroy()
    except tk.TclError:
        pass


def _cancel_osd(root: tk.Tk) -> None:
    global _osd_win, _osd_job
    if _osd_job is not None:
        try:
            root.after_cancel(_osd_job)
        except Exception:
            pass
        _osd_job = None
    if _osd_win is not None:
        try:
            _osd_win.destroy()
        except tk.TclError:
            pass
        _osd_win = None


def run_on_ui(root: tk.Tk, fn: Callable[[], None]) -> None:
    root.after(0, fn)
