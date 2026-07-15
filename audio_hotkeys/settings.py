# audio_hotkeys/settings.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from . import audio, config, kakao, theme
from .version import APP_VERSION, VERSION_HISTORY

UNCHANGED = "(unchanged)"


class VolumeSlider:
    """0–100 slider with an Unchanged toggle (None when unchecked)."""

    def __init__(self, parent: ttk.LabelFrame, label: str) -> None:
        self.enabled = tk.BooleanVar(value=False)
        self.value = tk.IntVar(value=50)
        self._label_var = tk.StringVar(value="—")

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=theme.px(8))
        ttk.Label(row, text=label, width=12).pack(side="left")

        chk = tk.Checkbutton(
            row,
            text="설정",
            variable=self.enabled,
            command=self._sync,
            bg=theme.BG,
            fg=theme.TEXT,
            activebackground=theme.BG,
            activeforeground=theme.ACCENT_STRONG,
            selectcolor=theme.SURFACE_2,
            highlightthickness=2,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            font=theme.ui_font(theme.SIZE_SMALL),
            padx=theme.px(6),
            pady=theme.px(6),
            cursor="hand2",
        )
        chk.pack(side="left", padx=(0, theme.px(10)))

        self.scale = tk.Scale(
            row,
            from_=0,
            to=100,
            orient="horizontal",
            showvalue=0,
            variable=self.value,
            command=lambda _v: self._sync(),
            bg=theme.BG,
            fg=theme.TEXT,
            troughcolor=theme.SURFACE_2,
            activebackground=theme.ACCENT_MAX,
            highlightthickness=2,
            highlightbackground=theme.BORDER_STRONG,
            highlightcolor=theme.FOCUS,
            bd=0,
            relief="flat",
            sliderrelief="flat",
            length=theme.px(280),
            width=theme.px(18),
            sliderlength=theme.px(34),
        )
        self.scale.pack(side="left", fill="x", expand=True, padx=(0, theme.px(10)))

        # 숫자는 모노체 (가이드: 숫자·ID·버전은 Consolas)
        tk.Label(
            row,
            textvariable=self._label_var,
            bg=theme.BG,
            fg=theme.ACCENT,
            font=theme.mono_font(theme.SIZE_BODY),
            width=5,
            anchor="e",
        ).pack(side="left")
        self._sync()

    def _sync(self) -> None:
        on = bool(self.enabled.get())
        try:
            self.scale.configure(
                state="normal" if on else "disabled",
                troughcolor=theme.SURFACE_2 if on else theme.SURFACE,
            )
        except tk.TclError:
            pass
        self._label_var.set(f"{int(self.value.get())}%" if on else "—")

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
        self.slot = tk.StringVar(value="0")
        self.name_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.kakao_output_var = tk.StringVar()
        self.kakao_input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")
        self.status_level = tk.StringVar(value="normal")

        self.output_choices = audio.device_choices("output")
        self.input_choices = audio.device_choices("input")
        self._output_map = {name: did for name, did in self.output_choices}
        self._input_map = {name: did for name, did in self.input_choices}

        self._build()
        self._load_slot("0")

    # --- theme ------------------------------------------------------------
    def _build(self) -> None:
        self.root.title(f"audio-hotkeys v{APP_VERSION} — 스냅샷")
        self.root.configure(bg=theme.BG)
        # 창이 화면보다 커지면 하단 액션 버튼에 닿을 수 없다. 폼은 스크롤되므로
        # 화면에 맞춰 줄이는 쪽이 안전하다.
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(theme.px(880), screen_w - theme.px(40))
        height = min(theme.px(820), screen_h - theme.px(60))
        self.root.minsize(min(theme.px(720), width), min(theme.px(560), height))
        self.root.geometry(f"{width}x{height}+{max(0, (screen_w - width) // 2)}+{max(0, (screen_h - height) // 2)}")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        font = theme.ui_font()

        self.root.option_add("*TCombobox*Listbox.background", theme.SURFACE_2)
        self.root.option_add("*TCombobox*Listbox.foreground", theme.TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", theme.ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        self.root.option_add("*TCombobox*Listbox.font", font)

        style.configure(".", background=theme.BG, foreground=theme.TEXT, fieldbackground=theme.SURFACE_2, font=font)
        style.configure("TFrame", background=theme.BG)
        style.configure("TLabel", background=theme.BG, foreground=theme.TEXT, font=font)
        style.configure("TLabelframe", background=theme.BG, foreground=theme.TEXT, bordercolor=theme.BORDER)
        style.configure(
            "TLabelframe.Label",
            background=theme.BG,
            foreground=theme.ACCENT_STRONG,
            font=theme.ui_font(theme.SIZE_H3),
        )
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
            padding=theme.px(8),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme.SURFACE_2), ("!disabled", theme.SURFACE_2)],
            foreground=[("readonly", theme.TEXT), ("!disabled", theme.TEXT)],
            background=[("readonly", theme.SURFACE_2), ("active", theme.SURFACE_2)],
            bordercolor=[("focus", theme.FOCUS), ("hover", theme.ACCENT)],
            selectbackground=[("readonly", theme.SURFACE_2)],
            selectforeground=[("readonly", theme.TEXT)],
            arrowcolor=[("readonly", theme.ACCENT), ("disabled", theme.TEXT_SUB)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=theme.SURFACE_2,
            troughcolor=theme.BG,
            bordercolor=theme.BG,
            arrowcolor=theme.TEXT,
        )
        style.map("Vertical.TScrollbar", background=[("active", theme.ACCENT)])

        outer = ttk.Frame(self.root, padding=theme.px(20))
        outer.pack(fill="both", expand=True)

        self._header(outer)

        slot_row = ttk.Frame(outer)
        slot_row.pack(fill="x", pady=(0, theme.px(14)))
        ttk.Label(slot_row, text="슬롯").pack(side="left")
        self.slot_box = ttk.Combobox(
            slot_row,
            textvariable=self.slot,
            values=config.SLOT_KEYS,
            state="readonly",
            width=5,
            font=theme.mono_font(),
        )
        self.slot_box.pack(side="left", padx=theme.px(12))
        self.slot_box.bind("<<ComboboxSelected>>", lambda _e: self._load_slot(self.slot.get()))
        self._darken_combobox_popdown(self.slot_box)
        ttk.Label(
            slot_row,
            text="단축키 고정 · Ctrl+Alt+NumPad 0–9 (NumLock ON 필요)",
            foreground=theme.TEXT_SUB,
            font=theme.ui_font(theme.SIZE_SMALL),
        ).pack(side="left", padx=theme.px(8))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg=theme.BG, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        form_host = ttk.Frame(canvas)
        form_host.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=form_host, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        system = ttk.LabelFrame(form_host, text="시스템", padding=theme.px(18))
        system.pack(fill="x", pady=(0, theme.px(14)))
        self._entry(system, "스냅샷 이름", self.name_var)
        self._combo(system, "출력 장치", self.output_var, [n for n, _ in self.output_choices])
        self._combo(system, "입력 장치", self.input_var, [n for n, _ in self.input_choices])
        self.out_vol = VolumeSlider(system, "출력 볼륨")
        self.in_vol = VolumeSlider(system, "입력 볼륨")

        kakao_box = ttk.LabelFrame(form_host, text="카카오톡 전용", padding=theme.px(18))
        kakao_box.pack(fill="x", pady=(0, theme.px(14)))
        ttk.Label(
            kakao_box,
            text="KakaoTalk.exe 가 실행 중일 때만 적용됩니다. 앱 믹서는 볼륨이 하나뿐입니다.",
            foreground=theme.TEXT_SUB,
            font=theme.ui_font(theme.SIZE_SMALL),
        ).pack(anchor="w", pady=(0, theme.px(10)))
        self._combo(kakao_box, "출력 장치", self.kakao_output_var, [n for n, _ in self.output_choices])
        self._combo(kakao_box, "입력 장치", self.kakao_input_var, [n for n, _ in self.input_choices])
        self.kakao_out_vol = VolumeSlider(kakao_box, "출력 볼륨")
        self.kakao_in_vol = VolumeSlider(kakao_box, "입력 볼륨")

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=theme.px(16))
        self._button(actions, "슬롯 저장", self._save_slot, primary=True).pack(side="left")
        self._button(actions, "지금 적용", self._apply_now).pack(side="left", padx=theme.px(8))
        self._button(actions, "현재 상태 가져오기", self._capture_current).pack(side="left")
        self._button(actions, "카카오톡 가져오기", self._capture_kakao).pack(side="left", padx=theme.px(8))
        self._button(actions, "닫기", self.root.destroy).pack(side="right")

        self.status_label = tk.Label(
            outer,
            textvariable=self.status_var,
            bg=theme.BG,
            fg=theme.TEXT_SUB,
            font=theme.ui_font(theme.SIZE_SMALL),
            anchor="w",
            justify="left",
            wraplength=theme.px(820),
        )
        self.status_label.pack(fill="x", anchor="w")

    def _header(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, theme.px(16)))
        ttk.Label(row, text="audio-hotkeys", font=theme.ui_font(theme.SIZE_H2)).pack(side="left")
        # 버전은 상시 표시 + 모노체
        tk.Label(
            row,
            text=f"v{APP_VERSION}",
            bg=theme.BG,
            fg=theme.ACCENT,
            font=theme.mono_font(theme.SIZE_SMALL),
        ).pack(side="left", padx=(theme.px(10), 0), pady=(theme.px(8), 0))
        self._button(row, "업데이트 히스토리", self._show_history).pack(side="right")

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        primary: bool = False,
    ) -> tk.Frame:
        """§3.1 대비 규칙: 주 버튼은 accent-strong 배경 + 검정 글자.

        tk.Button의 highlightbackground는 Windows에서 테두리를 그려주지 않아
        (WCAG 1.4.11 위반) 프레임으로 2px 테두리를 직접 만든다.
        반환값은 래퍼 프레임이므로 호출부에서 그대로 pack 하면 된다.
        """
        bg = theme.ACCENT_STRONG if primary else theme.SURFACE_2
        fg = "#000000" if primary else theme.TEXT
        hover_bg = theme.ACCENT_MAX if primary else theme.SURFACE_2
        hover_fg = "#000000" if primary else theme.ACCENT_STRONG
        border = theme.ACCENT_STRONG if primary else theme.BORDER_STRONG

        wrap = tk.Frame(parent, bg=border, highlightthickness=0)
        btn = tk.Button(
            wrap,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=hover_fg,
            disabledforeground=theme.TEXT_SUB,
            font=theme.ui_font(theme.SIZE_SMALL),
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=theme.px(16),
            pady=theme.px(10),
            cursor="hand2",
        )
        btn.pack(padx=theme.px(2), pady=theme.px(2))

        def enter(_e: tk.Event) -> None:
            btn.configure(bg=hover_bg, fg=hover_fg)
            wrap.configure(bg=theme.ACCENT)

        def leave(_e: tk.Event) -> None:
            btn.configure(bg=bg, fg=fg)
            wrap.configure(bg=border)

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        # 포커스 링은 상시 보이게 (키보드 이동)
        btn.bind("<FocusIn>", lambda _e: wrap.configure(bg=theme.FOCUS))
        btn.bind("<FocusOut>", lambda _e: wrap.configure(bg=border))
        return wrap

    def _entry(self, parent: ttk.LabelFrame, label: str, var: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=theme.px(8))
        ttk.Label(row, text=label, width=12).pack(side="left")
        entry = tk.Entry(
            row,
            textvariable=var,
            bg=theme.SURFACE_2,
            fg=theme.TEXT,
            insertbackground=theme.ACCENT,
            font=theme.ui_font(),
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightcolor=theme.FOCUS,
            highlightbackground=theme.BORDER_STRONG,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=theme.px(8))

    def _combo(self, parent: ttk.LabelFrame, label: str, var: tk.StringVar, values: list[str]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=theme.px(8))
        ttk.Label(row, text=label, width=12).pack(side="left")
        box = ttk.Combobox(row, textvariable=var, values=values, state="readonly", font=theme.ui_font())
        box.pack(side="left", fill="x", expand=True, ipady=theme.px(8))
        self._darken_combobox_popdown(box)

    def _darken_combobox_popdown(self, box: ttk.Combobox) -> None:
        def _on_open(_event: tk.Event | None = None) -> None:
            try:
                popdown = box.tk.call("ttk::combobox::PopdownWindow", box)
                listbox = f"{popdown}.f.l"
                box.tk.call(listbox, "configure", "-background", theme.SURFACE_2)
                box.tk.call(listbox, "configure", "-foreground", theme.TEXT)
                box.tk.call(listbox, "configure", "-selectbackground", theme.ACCENT)
                box.tk.call(listbox, "configure", "-selectforeground", "#000000")
                box.tk.call(listbox, "configure", "-font", theme.ui_font())
            except tk.TclError:
                pass

        box.bind("<Button-1>", lambda _e: self.root.after(1, _on_open), add="+")
        box.bind("<Down>", lambda _e: self.root.after(1, _on_open), add="+")

    # --- state ------------------------------------------------------------
    def _set_status(self, text: str, level: str = "normal") -> None:
        tag = theme.LEVEL_LABEL.get(level, "")
        self.status_var.set(f"{tag}  {text}".strip() if tag else text)
        self.status_label.configure(fg=theme.LEVEL_COLOR.get(level, theme.TEXT_SUB))

    def _load_slot(self, key: str) -> None:
        snap = self.data["snapshots"][key]
        self.name_var.set(snap.get("name") or "")

        lost: list[str] = []
        rematched: list[str] = []
        for var, choices, flow, id_field, name_field, field_label in (
            (self.output_var, self.output_choices, "output", "output_id", "output_name", "시스템 출력"),
            (self.input_var, self.input_choices, "input", "input_id", "input_name", "시스템 입력"),
            (self.kakao_output_var, self.output_choices, "output", "kakao_output_id", "kakao_output_name", "카카오톡 출력"),
            (self.kakao_input_var, self.input_choices, "input", "kakao_input_id", "kakao_input_name", "카카오톡 입력"),
        ):
            saved_name = snap.get(name_field) or ""
            device_id, _ = audio.resolve_device(snap.get(id_field) or "", saved_name, flow)
            if device_id:
                display = audio.find_display(choices, device_id)
                var.set(display)
                if snap.get(id_field) and snap.get(id_field) != device_id:
                    rematched.append(f"{field_label}: 이름으로 재연결됨 ({display})")
            else:
                var.set(UNCHANGED)
                if snap.get(id_field) or saved_name:
                    lost.append(f"{field_label}: 연결 해제됨{f' ({saved_name})' if saved_name else ''}")

        self.out_vol.set(snap.get("output_volume"))
        self.in_vol.set(snap.get("input_volume"))
        self.kakao_out_vol.set(snap.get("kakao_output_volume"))
        self.kakao_in_vol.set(snap.get("kakao_input_volume"))

        running = "실행 중" if kakao.find_kakao_pids() else "실행 중 아님"
        base = f"슬롯 {key} 편집 중 · Ctrl+Alt+NumPad{key} · 카카오톡 {running}"
        notes = lost + rematched
        if lost:
            self._set_status(base + "\n" + "\n".join(notes) + "\n장치를 다시 고른 뒤 [슬롯 저장]을 누르세요.", "warning")
        elif rematched:
            self._set_status(base + "\n" + "\n".join(notes), "positive")
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
        self._set_status(f"슬롯 {key} 저장했습니다", "positive")
        if self.on_saved:
            self.on_saved()

    def _apply_now(self) -> None:
        result = audio.apply_snapshot(self._read_form())
        if result.warnings:
            self._set_status(result.summary + "\n" + "\n".join(result.warnings), "warning")
        else:
            self._set_status(result.summary, "positive")

    def _capture_current(self) -> None:
        out = audio.get_default_device("output")
        inp = audio.get_default_device("input")
        self.output_var.set(out.name if out else UNCHANGED)
        self.input_var.set(inp.name if inp else UNCHANGED)
        self.out_vol.set(audio.get_volume("output"))
        self.in_vol.set(audio.get_volume("input"))
        self._set_status("현재 시스템 장치·볼륨을 가져왔습니다", "positive")

    def _capture_kakao(self) -> None:
        if not kakao.find_kakao_pids():
            self._set_status("카카오톡이 실행 중이 아닙니다", "warning")
            return
        devices = kakao.get_kakao_devices()
        self.kakao_output_var.set(audio.find_display(self.output_choices, devices.get("output_id") or ""))
        self.kakao_input_var.set(audio.find_display(self.input_choices, devices.get("input_id") or ""))
        self.kakao_out_vol.set(kakao.get_kakao_output_volume())
        self.kakao_in_vol.set(None)
        self._set_status("카카오톡 장치·볼륨을 가져왔습니다", "positive")

    def _show_history(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("업데이트 히스토리")
        win.configure(bg=theme.BG)
        win.geometry(f"{theme.px(640)}x{theme.px(460)}")
        win.transient(self.root)

        frame = tk.Frame(win, bg=theme.BG, padx=theme.px(22), pady=theme.px(22))
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="업데이트 히스토리",
            bg=theme.BG,
            fg=theme.ACCENT_STRONG,
            font=theme.ui_font(theme.SIZE_H2),
            anchor="w",
        ).pack(fill="x", pady=(0, theme.px(14)))

        for version, date, summary in VERSION_HISTORY:
            card = tk.Frame(frame, bg=theme.SURFACE, highlightthickness=1, highlightbackground=theme.BORDER)
            card.pack(fill="x", pady=(0, theme.px(12)))
            head = tk.Frame(card, bg=theme.SURFACE)
            head.pack(fill="x", padx=theme.px(18), pady=(theme.px(14), theme.px(4)))
            # 버전·날짜는 숫자 → 모노체
            tk.Label(
                head,
                text=f"v{version}",
                bg=theme.SURFACE,
                fg=theme.ACCENT,
                font=theme.mono_font(theme.SIZE_BODY),
            ).pack(side="left")
            tk.Label(
                head,
                text=date,
                bg=theme.SURFACE,
                fg=theme.TEXT_SUB,
                font=theme.mono_font(theme.SIZE_SMALL),
            ).pack(side="right")
            tk.Label(
                card,
                text=summary,
                bg=theme.SURFACE,
                fg=theme.TEXT,
                font=theme.ui_font(theme.SIZE_SMALL),
                justify="left",
                anchor="w",
                wraplength=theme.px(540),
            ).pack(fill="x", padx=theme.px(18), pady=(0, theme.px(16)))

        self._button(frame, "닫기", win.destroy).pack(anchor="e")
        win.bind("<Escape>", lambda _e: win.destroy())


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
