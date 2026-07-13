from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from . import audio, config, kakao

BG = "#121212"
FG = "#FFFFFF"
PANEL = "#1A1A1A"
BTN_BG = "#000000"
BTN_FG = "#FFFFFF"
BTN_BORDER = "#FFFFFF"
FOCUS = "#FFFF00"
MUTED = "#B0B0B0"
LIST_BG = "#000000"
LIST_FG = "#FFFFFF"
LIST_SEL_BG = "#333333"
FONT = ("KyoboHandwriting2019", 12)
FONT_FALLBACK = ("Segoe UI", 12)


class SettingsWindow:
    def __init__(self, root: tk.Tk, on_saved: Callable[[], None] | None = None) -> None:
        self.root = root
        self.on_saved = on_saved
        self.data = config.load_config()
        self.slot = tk.StringVar(value="0")
        self.name_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.out_vol_var = tk.StringVar()
        self.in_vol_var = tk.StringVar()
        self.kakao_output_var = tk.StringVar()
        self.kakao_input_var = tk.StringVar()
        self.kakao_out_vol_var = tk.StringVar()
        self.kakao_in_vol_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")

        self.output_choices = audio.device_choices("output")
        self.input_choices = audio.device_choices("input")
        self.vol_choices = audio.volume_choices()
        self._output_map = {name: did for name, did in self.output_choices}
        self._input_map = {name: did for name, did in self.input_choices}

        self._build()
        self._load_slot("0")

    def _font(self) -> tuple[str, int]:
        try:
            probe = tk.Label(self.root, font=FONT)
            probe.destroy()
            return FONT
        except tk.TclError:
            return FONT_FALLBACK

    def _build(self) -> None:
        self.root.title("audio-hotkeys — Snapshots")
        self.root.configure(bg=BG)
        self.root.minsize(760, 720)
        self.root.geometry("820x780")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        font = self._font()

        # Dark combobox dropdown (native Listbox under ttk.Combobox)
        self.root.option_add("*TCombobox*Listbox.background", LIST_BG)
        self.root.option_add("*TCombobox*Listbox.foreground", LIST_FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground", LIST_SEL_BG)
        self.root.option_add("*TCombobox*Listbox.selectForeground", LIST_FG)
        self.root.option_add("*TCombobox*Listbox.font", font)

        style.configure(".", background=BG, foreground=FG, fieldbackground=PANEL, font=font)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=font)
        style.configure("TLabelframe", background=BG, foreground=FG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG, font=font)
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=FG,
            arrowcolor=FG,
            bordercolor=BTN_BORDER,
            lightcolor=PANEL,
            darkcolor=PANEL,
            insertcolor=FG,
            font=font,
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", PANEL), ("!disabled", PANEL)],
            foreground=[("readonly", FG), ("!disabled", FG)],
            background=[("readonly", PANEL), ("active", PANEL)],
            selectbackground=[("readonly", LIST_SEL_BG)],
            selectforeground=[("readonly", LIST_FG)],
            arrowcolor=[("readonly", FG), ("disabled", MUTED)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=PANEL,
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=FG,
        )

        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Hotkeys fixed: Ctrl+Alt+NumPad 0–9").pack(anchor="w", pady=(0, 12))

        slot_row = ttk.Frame(outer)
        slot_row.pack(fill="x", pady=(0, 12))
        ttk.Label(slot_row, text="Slot").pack(side="left")
        self.slot_box = ttk.Combobox(
            slot_row,
            textvariable=self.slot,
            values=config.SLOT_KEYS,
            state="readonly",
            width=6,
        )
        self.slot_box.pack(side="left", padx=12)
        self.slot_box.bind("<<ComboboxSelected>>", lambda _e: self._load_slot(self.slot.get()))
        self._darken_combobox_popdown(self.slot_box)

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        form_host = ttk.Frame(canvas)
        form_host.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=form_host, anchor="nw")

        def _sync_width(event: tk.Event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        canvas.bind("<Configure>", _sync_width)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        system = ttk.LabelFrame(form_host, text="System", padding=16)
        system.pack(fill="x", pady=(0, 12))
        self._field(system, "Snapshot name", self.name_var, entry=True)
        self._combo(system, "Output device", self.output_var, [n for n, _ in self.output_choices])
        self._combo(system, "Input device", self.input_var, [n for n, _ in self.input_choices])
        self._combo(system, "Output volume", self.out_vol_var, self.vol_choices)
        self._combo(system, "Input volume", self.in_vol_var, self.vol_choices)

        kakao_box = ttk.LabelFrame(form_host, text="KakaoTalk (app-only)", padding=16)
        kakao_box.pack(fill="x", pady=(0, 12))
        ttk.Label(
            kakao_box,
            text="Applies only to KakaoTalk.exe (must be running). App mixer has one volume.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 8))
        self._combo(kakao_box, "Output device", self.kakao_output_var, [n for n, _ in self.output_choices])
        self._combo(kakao_box, "Input device", self.kakao_input_var, [n for n, _ in self.input_choices])
        self._combo(kakao_box, "Output volume", self.kakao_out_vol_var, self.vol_choices)
        self._combo(kakao_box, "Input volume", self.kakao_in_vol_var, self.vol_choices)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=16)
        self._action_button(actions, "Save slot", self._save_slot).pack(side="left")
        self._action_button(actions, "Apply now", self._apply_now).pack(side="left", padx=8)
        self._action_button(actions, "Capture current", self._capture_current).pack(side="left")
        self._action_button(actions, "Capture KakaoTalk", self._capture_kakao).pack(side="left", padx=8)
        self._action_button(actions, "Close", self.root.destroy).pack(side="right")

        ttk.Label(outer, textvariable=self.status_var, foreground=MUTED).pack(anchor="w")

        for child in self.root.winfo_children():
            self._force_focus_style(child)

    def _action_button(self, parent: ttk.Frame, text: str, command: Callable[[], None]) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=BTN_BG,
            fg=BTN_FG,
            activebackground="#1A1A1A",
            activeforeground=BTN_FG,
            disabledforeground=MUTED,
            font=self._font(),
            relief="solid",
            bd=2,
            highlightthickness=2,
            highlightbackground=BTN_BORDER,
            highlightcolor=FOCUS,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        return btn

    def _force_focus_style(self, widget: tk.Misc) -> None:
        try:
            widget.configure(highlightthickness=2, highlightcolor=FOCUS, highlightbackground=BG)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._force_focus_style(child)

    def _field(self, parent: ttk.LabelFrame, label: str, var: tk.StringVar, entry: bool = False) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text=label, width=16).pack(side="left")
        if entry:
            e = tk.Entry(
                row,
                textvariable=var,
                bg=PANEL,
                fg=FG,
                insertbackground=FG,
                font=self._font(),
                relief="solid",
                bd=1,
                highlightthickness=2,
                highlightcolor=FOCUS,
                highlightbackground=BTN_BORDER,
            )
            e.pack(side="left", fill="x", expand=True, ipady=4)

    def _combo(self, parent: ttk.LabelFrame, label: str, var: tk.StringVar, values: list[str]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text=label, width=16).pack(side="left")
        box = ttk.Combobox(row, textvariable=var, values=values, state="readonly", font=self._font())
        box.pack(side="left", fill="x", expand=True, ipady=4)
        self._darken_combobox_popdown(box)

    def _darken_combobox_popdown(self, box: ttk.Combobox) -> None:
        def _on_open(_event: tk.Event | None = None) -> None:
            try:
                popdown = box.tk.call("ttk::combobox::PopdownWindow", box)
                listbox = f"{popdown}.f.l"
                box.tk.call(listbox, "configure", "-background", LIST_BG)
                box.tk.call(listbox, "configure", "-foreground", LIST_FG)
                box.tk.call(listbox, "configure", "-selectbackground", LIST_SEL_BG)
                box.tk.call(listbox, "configure", "-selectforeground", LIST_FG)
                box.tk.call(listbox, "configure", "-font", self._font())
            except tk.TclError:
                pass

        box.bind("<<ComboboxSelected>>", lambda _e: None)
        box.bind("<Button-1>", lambda _e: self.root.after(1, _on_open), add="+")
        box.bind("<Down>", lambda _e: self.root.after(1, _on_open), add="+")

    def _vol_label(self, value) -> str:
        return "(unchanged)" if value is None else str(int(value))

    def _load_slot(self, key: str) -> None:
        snap = self.data["snapshots"][key]
        self.name_var.set(snap.get("name") or "")
        self.output_var.set(audio.find_display(self.output_choices, snap.get("output_id") or ""))
        self.input_var.set(audio.find_display(self.input_choices, snap.get("input_id") or ""))
        self.out_vol_var.set(self._vol_label(snap.get("output_volume")))
        self.in_vol_var.set(self._vol_label(snap.get("input_volume")))
        self.kakao_output_var.set(audio.find_display(self.output_choices, snap.get("kakao_output_id") or ""))
        self.kakao_input_var.set(audio.find_display(self.input_choices, snap.get("kakao_input_id") or ""))
        self.kakao_out_vol_var.set(self._vol_label(snap.get("kakao_output_volume")))
        self.kakao_in_vol_var.set(self._vol_label(snap.get("kakao_input_volume")))
        running = "running" if kakao.find_kakao_pids() else "not running"
        self.status_var.set(f"Editing slot {key}  ·  Ctrl+Alt+NumPad{key}  ·  KakaoTalk {running}")

    def _parse_vol(self, raw: str) -> int | None:
        return None if raw == "(unchanged)" else int(raw)

    def _read_form(self) -> dict:
        return {
            "name": self.name_var.get().strip() or f"Slot {self.slot.get()}",
            "output_id": self._output_map.get(self.output_var.get(), ""),
            "input_id": self._input_map.get(self.input_var.get(), ""),
            "output_volume": self._parse_vol(self.out_vol_var.get()),
            "input_volume": self._parse_vol(self.in_vol_var.get()),
            "kakao_output_id": self._output_map.get(self.kakao_output_var.get(), ""),
            "kakao_input_id": self._input_map.get(self.kakao_input_var.get(), ""),
            "kakao_output_volume": self._parse_vol(self.kakao_out_vol_var.get()),
            "kakao_input_volume": self._parse_vol(self.kakao_in_vol_var.get()),
        }

    def _save_slot(self) -> None:
        key = self.slot.get()
        self.data["snapshots"][key] = self._read_form()
        config.save_config(self.data)
        self.status_var.set(f"Saved slot {key}")
        if self.on_saved:
            self.on_saved()

    def _apply_now(self) -> None:
        snap = self._read_form()
        summary = audio.apply_snapshot(snap)
        self.status_var.set(summary)

    def _capture_current(self) -> None:
        out = audio.get_default_device("output")
        inp = audio.get_default_device("input")
        out_vol = audio.get_volume("output")
        in_vol = audio.get_volume("input")
        self.output_var.set(out.name if out else "(unchanged)")
        self.input_var.set(inp.name if inp else "(unchanged)")
        self.out_vol_var.set(str(_nearest_five(out_vol)) if out_vol is not None else "(unchanged)")
        self.in_vol_var.set(str(_nearest_five(in_vol)) if in_vol is not None else "(unchanged)")
        self.status_var.set("Captured system devices/volumes")

    def _capture_kakao(self) -> None:
        if not kakao.find_kakao_pids():
            self.status_var.set("KakaoTalk is not running")
            return
        devices = kakao.get_kakao_devices()
        self.kakao_output_var.set(audio.find_display(self.output_choices, devices.get("output_id") or ""))
        self.kakao_input_var.set(audio.find_display(self.input_choices, devices.get("input_id") or ""))
        vol = kakao.get_kakao_output_volume()
        self.kakao_out_vol_var.set(str(_nearest_five(vol)) if vol is not None else "(unchanged)")
        self.kakao_in_vol_var.set("(unchanged)")
        self.status_var.set("Captured KakaoTalk devices/volume")


def _nearest_five(value: int) -> int:
    return int(round(value / 5) * 5)


def open_settings(on_saved: Callable[[], None] | None = None) -> None:
    existing = getattr(open_settings, "_win", None)
    if existing is not None:
        try:
            existing.lift()
            existing.focus_force()
            return
        except tk.TclError:
            pass

    win = tk.Toplevel() if tk._default_root else tk.Tk()
    win.title("audio-hotkeys")
    SettingsWindow(win, on_saved=on_saved)
    open_settings._win = win

    def _on_close() -> None:
        open_settings._win = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)
