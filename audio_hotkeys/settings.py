from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from . import audio, config, kakao, prefs, theme
from .i18n import t
from .version import APP_VERSION, VERSION_HISTORY
from .win_shell import apply_dark_titlebar


def _is_text_input(widget: tk.Misc | None) -> bool:
    if widget is None:
        return False
    try:
        cls = widget.winfo_class()
    except tk.TclError:
        return False
    if cls in ("Entry", "TEntry", "Text", "TCombobox", "Spinbox", "TSpinbox"):
        return True
    try:
        if str(widget.cget("state")) == "normal" and isinstance(widget, (tk.Entry, tk.Text)):
            return True
    except Exception:
        pass
    return False


class VolumeSlider:
    """0–100 slider with Set toggle (None when unchecked)."""

    def __init__(
        self,
        parent: tk.Misc,
        label: str,
        font: tuple,
        mono: tuple,
        set_label: str,
        lang: str,
    ) -> None:
        self.enabled = tk.BooleanVar(value=False)
        self.value = tk.IntVar(value=50)
        self._lang = lang
        self._label_var = tk.StringVar(value=t("unchanged", lang))

        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=8)
        tk.Label(row, text=label, width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font).pack(side="left")

        chk = tk.Checkbutton(
            row,
            text=set_label,
            variable=self.enabled,
            command=self._sync,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            activebackground=theme.SURFACE,
            activeforeground=theme.TEXT,
            selectcolor=theme.SURFACE_2,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            font=font,
            padx=8,
            pady=8,
        )
        chk.pack(side="left", padx=(0, 8), ipady=6)

        self.scale = tk.Scale(
            row,
            from_=0,
            to=100,
            orient="horizontal",
            showvalue=0,
            variable=self.value,
            command=lambda _v: self._sync(),
            bg=theme.SURFACE,
            fg=theme.TEXT,
            troughcolor=theme.SURFACE_2,
            activebackground=theme.ACCENT_STRONG,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            bd=0,
            relief="flat",
            sliderrelief="raised",
            length=280,
            width=18,
        )
        self.scale.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=8)

        tk.Label(
            row,
            textvariable=self._label_var,
            width=5,
            bg=theme.SURFACE,
            fg=theme.ACCENT,
            font=mono,
            anchor="e",
        ).pack(side="left")
        self._sync()

    def _sync(self) -> None:
        on = bool(self.enabled.get())
        try:
            self.scale.configure(state=("normal" if on else "disabled"))
        except tk.TclError:
            pass
        self._label_var.set(f"{int(self.value.get())}%" if on else t("unchanged", self._lang))

    def get(self) -> int | None:
        if not self.enabled.get():
            return None
        return max(0, min(100, int(self.value.get())))

    def set(self, value: int | None) -> None:
        if value is None:
            self.enabled.set(False)
        else:
            self.enabled.set(True)
            self.value.set(max(0, min(100, int(value))))
        self._sync()


class SettingsWindow:
    def __init__(self, root: tk.Tk, on_saved: Callable[[], None] | None = None) -> None:
        self.root = root
        self.on_saved = on_saved
        self.data = config.load_config()
        self.prefs = prefs.load_prefs()
        self.lang = self.prefs["lang"]

        self.slot = tk.StringVar(value="0")
        self.name_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.kakao_output_var = tk.StringVar()
        self.kakao_input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")
        self.font_id_var = tk.StringVar()
        self.font_size_var = tk.StringVar()
        self.lang_var = tk.StringVar()
        self._font_preview_var = tk.StringVar()

        self.output_choices = audio.device_choices("output")
        self.input_choices = audio.device_choices("input")
        self._output_map = {name: did for name, did in self.output_choices}
        self._input_map = {name: did for name, did in self.input_choices}
        self._fonts = prefs.available_fonts(root)
        self._font_map = {f["label"]: f["id"] for f in self._fonts}
        self._font_labels = {f["id"]: f["label"] for f in self._fonts}

        self._build()
        self._load_slot("0")

    def _font(self) -> tuple:
        return prefs.ui_font(self.root, self.prefs)

    def _mono(self) -> tuple:
        return prefs.mono_font(self.prefs)

    def _build(self) -> None:
        font = self._font()
        mono = self._mono()
        self.root.title(f'{t("app_title", self.lang)} — v{APP_VERSION}')
        self.root.configure(bg=theme.BG)
        # 창이 화면보다 커지면 하단 액션 버튼에 닿을 수 없다. 폼은 스크롤되므로
        # 화면에 맞춰 줄이는 쪽이 안전하다.
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(theme.px(880), screen_w - theme.px(40))
        height = min(theme.px(860), screen_h - theme.px(60))
        self.root.minsize(min(theme.px(720), width), min(theme.px(560), height))
        self.root.geometry(
            f"{width}x{height}+{max(0, (screen_w - width) // 2)}+{max(0, (screen_h - height) // 2)}"
        )
        apply_dark_titlebar(self.root)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.option_add("*TCombobox*Listbox.background", theme.SURFACE_2)
        self.root.option_add("*TCombobox*Listbox.foreground", theme.TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", theme.ACCENT_STRONG)
        self.root.option_add("*TCombobox*Listbox.selectForeground", theme.BLACK)
        self.root.option_add("*TCombobox*Listbox.font", font)
        self.root.option_add("*Font", font)

        style.configure(".", background=theme.BG, foreground=theme.TEXT, fieldbackground=theme.SURFACE_2, font=font)
        style.configure("TFrame", background=theme.BG)
        style.configure("TLabel", background=theme.BG, foreground=theme.TEXT, font=font)
        style.configure(
            "TCombobox",
            fieldbackground=theme.SURFACE_2,
            background=theme.SURFACE_2,
            foreground=theme.TEXT,
            arrowcolor=theme.TEXT,
            bordercolor=theme.BORDER_STRONG,
            lightcolor=theme.SURFACE_2,
            darkcolor=theme.SURFACE_2,
            insertcolor=theme.TEXT,
            font=font,
            padding=8,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme.SURFACE_2)],
            foreground=[("readonly", theme.TEXT)],
            background=[("readonly", theme.SURFACE_2), ("active", theme.SURFACE_2)],
            selectbackground=[("readonly", theme.ACCENT_STRONG)],
            selectforeground=[("readonly", theme.BLACK)],
            arrowcolor=[("readonly", theme.TEXT)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=theme.SURFACE_2,
            troughcolor=theme.BG,
            bordercolor=theme.BG,
            arrowcolor=theme.TEXT,
        )

        outer = tk.Frame(self.root, bg=theme.BG, padx=theme.PAD_CARD, pady=theme.PAD_CARD)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=theme.BG)
        header.pack(fill="x", pady=(0, theme.px(12)))
        tk.Label(
            header,
            text=t("hotkeys_fixed", self.lang),
            bg=theme.BG,
            fg=theme.TEXT_SUB,
            font=font,
            anchor="w",
            justify="left",
        ).pack(side="left")
        # 버전은 상시 표시 + 숫자이므로 모노체
        tk.Label(
            header,
            text=f"v{APP_VERSION}",
            bg=theme.BG,
            fg=theme.ACCENT,
            font=mono,
        ).pack(side="left", padx=(theme.px(12), 0))
        self._secondary_button(header, t("update_history", self.lang), self._show_history).pack(side="right")

        slot_row = tk.Frame(outer, bg=theme.BG)
        slot_row.pack(fill="x", pady=(0, 12))
        tk.Label(slot_row, text=t("slot", self.lang), bg=theme.BG, fg=theme.TEXT, font=font).pack(side="left")
        self.slot_box = ttk.Combobox(
            slot_row,
            textvariable=self.slot,
            values=config.SLOT_KEYS,
            state="readonly",
            width=6,
            font=mono,
        )
        self.slot_box.pack(side="left", padx=12, ipady=12)
        self.slot_box.bind("<<ComboboxSelected>>", lambda _e: self._load_slot(self.slot.get()))
        self._darken_combobox_popdown(self.slot_box)

        body = tk.Frame(outer, bg=theme.BG)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg=theme.BG, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        form_host = tk.Frame(canvas, bg=theme.BG)
        form_host.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=form_host, anchor="nw")

        def _sync_width(event: tk.Event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        canvas.bind("<Configure>", _sync_width)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        self._card(form_host, t("display", self.lang), font, self._prefs_body)
        self._card(form_host, t("system", self.lang), font, self._system_body)
        self._card(form_host, t("kakao_section", self.lang), font, self._kakao_body)

        actions = tk.Frame(outer, bg=theme.BG)
        actions.pack(fill="x", pady=16)
        self._primary_button(actions, t("save_slot", self.lang), self._save_slot).pack(side="left")
        self._primary_button(actions, t("apply_now", self.lang), self._apply_now).pack(side="left", padx=8)
        self._secondary_button(actions, t("capture_current", self.lang), self._capture_current).pack(side="left")
        self._secondary_button(actions, t("capture_kakao", self.lang), self._capture_kakao).pack(side="left", padx=8)
        self._secondary_button(actions, t("close", self.lang), self.root.destroy).pack(side="right")

        self._status = tk.Label(
            outer,
            textvariable=self.status_var,
            bg=theme.BG,
            fg=theme.TEXT_SUB,
            font=font,
            anchor="w",
            justify="left",
            wraplength=780,
        )
        self._status.pack(anchor="w")

        self.root.bind("<Alt-Left>", lambda _e: self._go_back())
        self.root.bind("<Alt-Right>", lambda _e: "break")
        self.root.bind("<BackSpace>", self._back_guard)
        self.root.bind("<Button-4>", lambda _e: self._go_back())  # XBUTTON1 back
        self.root.bind("<Button-5>", lambda _e: "break")  # XBUTTON2 forward (no-op)

    def _go_back(self) -> str:
        self.root.destroy()
        return "break"

    def _back_guard(self, event: tk.Event) -> str | None:
        if _is_text_input(event.widget):
            return None
        return self._go_back()

    def _card(self, parent: tk.Misc, title: str, font: tuple, body_fn: Callable) -> None:
        outer = tk.Frame(
            parent,
            bg=theme.BORDER,
            highlightthickness=0,
        )
        outer.pack(fill="x", pady=(0, 12))
        card = tk.Frame(outer, bg=theme.SURFACE, padx=theme.PAD_CARD, pady=theme.PAD_CARD)
        card.pack(fill="x", padx=1, pady=1)
        tk.Label(card, text=title, bg=theme.SURFACE, fg=theme.ACCENT, font=font, anchor="w").pack(anchor="w", pady=(0, 10))
        body_fn(card, font)

    def _prefs_body(self, parent: tk.Misc, font: tuple) -> None:
        mono = self._mono()
        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=t("font", self.lang), width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font).pack(
            side="left"
        )
        labels = [f["label"] for f in self._fonts]
        self.font_id_var.set(self._font_labels.get(self.prefs["font_id"], labels[0] if labels else ""))
        box = ttk.Combobox(row, textvariable=self.font_id_var, values=labels, state="readonly", font=font)
        box.pack(side="left", fill="x", expand=True, ipady=12)
        self._darken_combobox_popdown(box)
        box.bind("<<ComboboxSelected>>", lambda _e: self._on_font_preview())

        preview_font = self._font()
        self._font_preview = tk.Label(
            parent,
            textvariable=self._font_preview_var,
            bg=theme.SURFACE,
            fg=theme.ACCENT,
            font=preview_font,
            anchor="w",
            pady=8,
        )
        self._font_preview.pack(fill="x", pady=(0, 8))
        self._on_font_preview(apply=False)

        row2 = tk.Frame(parent, bg=theme.SURFACE)
        row2.pack(fill="x", pady=4)
        tk.Label(
            row2, text=t("font_size", self.lang), width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font
        ).pack(side="left")
        size_map = {"S": t("size_s", self.lang), "M": t("size_m", self.lang), "L": t("size_l", self.lang)}
        self._size_ids = {v: k for k, v in size_map.items()}
        self.font_size_var.set(size_map.get(self.prefs["font_size"], size_map["M"]))
        sbox = ttk.Combobox(
            row2, textvariable=self.font_size_var, values=list(size_map.values()), state="readonly", font=font
        )
        sbox.pack(side="left", fill="x", expand=True, ipady=12)
        self._darken_combobox_popdown(sbox)
        sbox.bind("<<ComboboxSelected>>", lambda _e: self._apply_prefs())

        row3 = tk.Frame(parent, bg=theme.SURFACE)
        row3.pack(fill="x", pady=4)
        tk.Label(
            row3, text=t("language", self.lang), width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font
        ).pack(side="left")
        lang_labels = [prefs.LANG_LABELS[c] for c in prefs.LANGS]
        self._lang_ids = {prefs.LANG_LABELS[c]: c for c in prefs.LANGS}
        self.lang_var.set(prefs.LANG_LABELS.get(self.prefs["lang"], "한국어"))
        lbox = ttk.Combobox(row3, textvariable=self.lang_var, values=lang_labels, state="readonly", font=font)
        lbox.pack(side="left", fill="x", expand=True, ipady=12)
        self._darken_combobox_popdown(lbox)
        lbox.bind("<<ComboboxSelected>>", lambda _e: self._apply_prefs(rebuild=True))

        # Apply font change without full rebuild when only font/size (size triggers apply)
        box.bind("<<ComboboxSelected>>", lambda _e: self._apply_prefs(), add="+")

    def _system_body(self, parent: tk.Misc, font: tuple) -> None:
        mono = self._mono()
        self._field(parent, t("snapshot_name", self.lang), self.name_var, font)
        self._combo(parent, t("output_device", self.lang), self.output_var, [n for n, _ in self.output_choices], font)
        self._combo(parent, t("input_device", self.lang), self.input_var, [n for n, _ in self.input_choices], font)
        self.out_vol = VolumeSlider(
            parent, t("output_volume", self.lang), font, mono, t("set", self.lang), self.lang
        )
        self.in_vol = VolumeSlider(parent, t("input_volume", self.lang), font, mono, t("set", self.lang), self.lang)

    def _kakao_body(self, parent: tk.Misc, font: tuple) -> None:
        mono = self._mono()
        tk.Label(
            parent,
            text=t("kakao_hint", self.lang),
            bg=theme.SURFACE,
            fg=theme.TEXT_SUB,
            font=font,
            anchor="w",
            justify="left",
            wraplength=720,
        ).pack(anchor="w", pady=(0, 8))
        self._combo(
            parent, t("output_device", self.lang), self.kakao_output_var, [n for n, _ in self.output_choices], font
        )
        self._combo(parent, t("input_device", self.lang), self.kakao_input_var, [n for n, _ in self.input_choices], font)
        self.kakao_out_vol = VolumeSlider(
            parent, t("output_volume", self.lang), font, mono, t("set", self.lang), self.lang
        )
        self.kakao_in_vol = VolumeSlider(
            parent, t("input_volume", self.lang), font, mono, t("set", self.lang), self.lang
        )

    def _on_font_preview(self, apply: bool = True) -> None:
        label = self.font_id_var.get()
        font_id = self._font_map.get(label, self.prefs["font_id"])
        family = prefs.resolve_family(font_id, self.root)
        size = theme.FONT_SIZE_PX.get(self.prefs["font_size"], 18)
        self._font_preview_var.set(label)
        try:
            self._font_preview.configure(font=(family, size), fg=theme.ACCENT)
        except tk.TclError:
            pass
        if apply:
            pass  # preview only; `_apply_prefs` handles persistence

    def _apply_prefs(self, rebuild: bool = False) -> None:
        font_id = self._font_map.get(self.font_id_var.get(), self.prefs["font_id"])
        size = self._size_ids.get(self.font_size_var.get(), self.prefs["font_size"])
        lang = self._lang_ids.get(self.lang_var.get(), self.prefs["lang"])
        changed = font_id != self.prefs["font_id"] or size != self.prefs["font_size"] or lang != self.prefs["lang"]
        self.prefs = {"font_id": font_id, "font_size": size, "lang": lang}
        prefs.save_prefs(self.prefs)
        if rebuild or changed:
            self.lang = lang
            geom = self.root.geometry()
            for child in self.root.winfo_children():
                child.destroy()
            self._build()
            self._load_slot(self.slot.get())
            self.root.geometry(geom)
        else:
            self._on_font_preview(apply=False)

    def _primary_button(self, parent: tk.Misc, text: str, command: Callable[[], None]) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=theme.ACCENT_STRONG,
            fg=theme.BLACK,
            activebackground=theme.ACCENT_MAX,
            activeforeground=theme.BLACK,
            disabledforeground=theme.BORDER,
            font=self._font(),
            relief="solid",
            bd=theme.BORDER_WIDTH,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            padx=16,
            pady=14,
            cursor="hand2",
        )
        btn.configure(height=1)
        return btn

    def _secondary_button(self, parent: tk.Misc, text: str, command: Callable[[], None]) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=theme.SURFACE_2,
            fg=theme.TEXT,
            activebackground=theme.SURFACE,
            activeforeground=theme.ACCENT_STRONG,
            font=self._font(),
            relief="solid",
            bd=theme.BORDER_WIDTH,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            padx=16,
            pady=14,
            cursor="hand2",
        )

        def on_enter(_e: tk.Event) -> None:
            btn.configure(fg=theme.ACCENT_STRONG, highlightbackground=theme.ACCENT, bg=theme.SURFACE)

        def on_leave(_e: tk.Event) -> None:
            btn.configure(fg=theme.TEXT, highlightbackground=theme.BORDER_STRONG, bg=theme.SURFACE_2)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _field(self, parent: tk.Misc, label: str, var: tk.StringVar, font: tuple) -> None:
        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=8)
        tk.Label(row, text=label, width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font).pack(side="left")
        e = tk.Entry(
            row,
            textvariable=var,
            bg=theme.SURFACE_2,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            font=font,
            relief="solid",
            bd=theme.BORDER_WIDTH,
            highlightthickness=theme.FOCUS_WIDTH,
            highlightcolor=theme.FOCUS,
            highlightbackground=theme.BORDER_STRONG,
        )
        e.pack(side="left", fill="x", expand=True, ipady=14)

    def _combo(self, parent: tk.Misc, label: str, var: tk.StringVar, values: list[str], font: tuple) -> None:
        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=8)
        tk.Label(row, text=label, width=14, anchor="w", bg=theme.SURFACE, fg=theme.TEXT, font=font).pack(side="left")
        box = ttk.Combobox(row, textvariable=var, values=values, state="readonly", font=font)
        box.pack(side="left", fill="x", expand=True, ipady=12)
        self._darken_combobox_popdown(box)

    def _darken_combobox_popdown(self, box: ttk.Combobox) -> None:
        def _on_open(_event: tk.Event | None = None) -> None:
            try:
                popdown = box.tk.call("ttk::combobox::PopdownWindow", box)
                listbox = f"{popdown}.f.l"
                box.tk.call(listbox, "configure", "-background", theme.SURFACE_2)
                box.tk.call(listbox, "configure", "-foreground", theme.TEXT)
                box.tk.call(listbox, "configure", "-selectbackground", theme.ACCENT_STRONG)
                box.tk.call(listbox, "configure", "-selectforeground", theme.BLACK)
                box.tk.call(listbox, "configure", "-font", self._font())
            except tk.TclError:
                pass

        box.bind("<Button-1>", lambda _e: self.root.after(1, _on_open), add="+")
        box.bind("<Down>", lambda _e: self.root.after(1, _on_open), add="+")

    def _set_status(self, message: str, *, error: bool = False, level: str | None = None) -> None:
        state = level or ("error" if error else "normal")
        tag = theme.LEVEL_LABEL.get(state, "")
        self.status_var.set(f"{tag}  {message}".strip() if tag else message)
        self._status.configure(fg=theme.LEVEL_COLOR.get(state, theme.TEXT_SUB))

    def _load_slot(self, key: str) -> None:
        snap = self.data["snapshots"][key]
        self.name_var.set(snap.get("name") or "")

        lost: list[str] = []
        rematched: list[str] = []
        for var, choices, flow, id_field, name_field, field_key in (
            (self.output_var, self.output_choices, "output", "output_id", "output_name", "field_sys_out"),
            (self.input_var, self.input_choices, "input", "input_id", "input_name", "field_sys_in"),
            (self.kakao_output_var, self.output_choices, "output", "kakao_output_id", "kakao_output_name", "field_kakao_out"),
            (self.kakao_input_var, self.input_choices, "input", "kakao_input_id", "kakao_input_name", "field_kakao_in"),
        ):
            saved_id = snap.get(id_field) or ""
            saved_name = snap.get(name_field) or ""
            field = t(field_key, self.lang)
            device_id, _ = audio.resolve_device(saved_id, saved_name, flow)
            if device_id:
                display = audio.find_display(choices, device_id)
                var.set(display)
                if saved_id and saved_id != device_id:
                    rematched.append(t("device_rematched", self.lang, field=field, name=display))
            else:
                var.set(t("unchanged", self.lang))
                if saved_id or saved_name:
                    lost.append(
                        t("device_disconnected_named", self.lang, field=field, name=saved_name)
                        if saved_name
                        else t("device_disconnected", self.lang, field=field)
                    )

        self.out_vol.set(snap.get("output_volume"))
        self.in_vol.set(snap.get("input_volume"))
        self.kakao_out_vol.set(snap.get("kakao_output_volume"))
        self.kakao_in_vol.set(snap.get("kakao_input_volume"))

        kakao_state = t("running", self.lang) if kakao.find_kakao_pids() else t("not_running", self.lang)
        base = t("editing", self.lang, slot=key, kakao=kakao_state)
        notes = lost + rematched
        if lost:
            hint = t("reselect_hint", self.lang, save=t("save_slot", self.lang))
            self._set_status("\n".join([base, *notes, hint]), level="warning")
        elif rematched:
            self._set_status("\n".join([base, *notes]), level="positive")
        else:
            self._set_status(base)

    def _pick(self, var: tk.StringVar, mapping: dict[str, str]) -> tuple[str, str]:
        """Combobox 선택을 (id, name)으로. 이름도 저장해야 ID 변경 시 재매칭된다."""
        display = var.get()
        device_id = mapping.get(display, "")
        return device_id, (display if device_id else "")

    def _read_form(self) -> dict:
        out_id, out_name = self._pick(self.output_var, self._output_map)
        in_id, in_name = self._pick(self.input_var, self._input_map)
        k_out_id, k_out_name = self._pick(self.kakao_output_var, self._output_map)
        k_in_id, k_in_name = self._pick(self.kakao_input_var, self._input_map)
        return {
            "name": self.name_var.get().strip() or f"Slot {self.slot.get()}",
            "output_id": out_id,
            "output_name": out_name,
            "input_id": in_id,
            "input_name": in_name,
            "output_volume": self.out_vol.get(),
            "input_volume": self.in_vol.get(),
            "kakao_output_id": k_out_id,
            "kakao_output_name": k_out_name,
            "kakao_input_id": k_in_id,
            "kakao_input_name": k_in_name,
            "kakao_output_volume": self.kakao_out_vol.get(),
            "kakao_input_volume": self.kakao_in_vol.get(),
        }

    def _save_slot(self) -> None:
        key = self.slot.get()
        self.data["snapshots"][key] = self._read_form()
        config.save_config(self.data)
        self._set_status(t("saved_slot", self.lang, slot=key), level="positive")
        if self.on_saved:
            self.on_saved()

    def _apply_now(self) -> None:
        result = audio.apply_snapshot(self._read_form())
        if result.warnings:
            self._set_status("\n".join([result.summary, *result.warnings]), level="warning")
        else:
            self._set_status(result.summary, level="positive")

    def _capture_current(self) -> None:
        out = audio.get_default_device("output")
        inp = audio.get_default_device("input")
        unchanged = t("unchanged", self.lang)
        self.output_var.set(out.name if out else unchanged)
        self.input_var.set(inp.name if inp else unchanged)
        self.out_vol.set(audio.get_volume("output"))
        self.in_vol.set(audio.get_volume("input"))
        self._set_status(t("captured_system", self.lang))

    def _show_history(self) -> None:
        win = tk.Toplevel(self.root)
        win.title(t("update_history", self.lang))
        win.configure(bg=theme.BG)
        win.geometry(f"{theme.px(660)}x{theme.px(480)}")
        win.transient(self.root)
        apply_dark_titlebar(win)

        font = self._font()
        mono = self._mono()
        frame = tk.Frame(win, bg=theme.BG, padx=theme.px(22), pady=theme.px(22))
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=t("update_history", self.lang),
            bg=theme.BG,
            fg=theme.ACCENT_STRONG,
            font=theme.font_tuple(font[0], theme.FONT_SIZE_PX.get(self.prefs["font_size"], 18) + 10),
            anchor="w",
        ).pack(fill="x", pady=(0, theme.px(14)))

        for version, date, summary in VERSION_HISTORY:
            card = tk.Frame(frame, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
            card.pack(fill="x", pady=(0, theme.px(12)))
            head = tk.Frame(card, bg=theme.SURFACE)
            head.pack(fill="x", padx=theme.px(18), pady=(theme.px(14), theme.px(4)))
            # 버전·날짜는 숫자 → 모노체
            tk.Label(head, text=f"v{version}", bg=theme.SURFACE, fg=theme.ACCENT, font=mono).pack(side="left")
            tk.Label(head, text=date, bg=theme.SURFACE, fg=theme.TEXT_SUB, font=mono).pack(side="right")
            tk.Label(
                card,
                text=summary,
                bg=theme.SURFACE,
                fg=theme.TEXT,
                font=font,
                justify="left",
                anchor="w",
                wraplength=theme.px(560),
            ).pack(fill="x", padx=theme.px(18), pady=(0, theme.px(16)))

        self._secondary_button(frame, t("close", self.lang), win.destroy).pack(anchor="e")
        win.bind("<Escape>", lambda _e: win.destroy())

    def _capture_kakao(self) -> None:
        if not kakao.find_kakao_pids():
            self._set_status(t("kakao_not_running", self.lang), error=True)
            return
        devices = kakao.get_kakao_devices()
        self.kakao_output_var.set(audio.find_display(self.output_choices, devices.get("output_id") or ""))
        self.kakao_input_var.set(audio.find_display(self.input_choices, devices.get("input_id") or ""))
        self.kakao_out_vol.set(kakao.get_kakao_output_volume())
        self.kakao_in_vol.set(None)
        self._set_status(t("captured_kakao", self.lang))


def open_settings(on_saved: Callable[[], None] | None = None) -> None:
    existing = getattr(open_settings, "_win", None)
    if existing is not None:
        try:
            existing.lift()
            existing.focus_force()
            apply_dark_titlebar(existing)
            return
        except tk.TclError:
            pass

    win = tk.Toplevel() if tk._default_root else tk.Tk()
    win.title(t("app_title"))
    apply_dark_titlebar(win)
    SettingsWindow(win, on_saved=on_saved)
    open_settings._win = win

    def _on_close() -> None:
        open_settings._win = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)
