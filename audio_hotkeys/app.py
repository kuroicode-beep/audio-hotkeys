from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from copy import deepcopy
from ctypes import wintypes
from typing import Callable

import pystray
from pystray._win32 import Icon as WinIcon

from . import audio, config, kakao, theme
from .hotkeys import HotkeyService
from .i18n import t
from .settings import open_settings
from .tray import DarkTrayMenu, make_icon, show_profile_osd, toast
from .version import APP_VERSION
from .win_shell import force_app_dark_mode

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
PREF_POLL_MS = 3000  # 헤드셋 연결/해제 감시 주기
ECHO_CHANNEL = "1"   # 에코 단축키가 만지는 FLOW 8 입력 채널(1번 마이크)
ECHO_STEP = 8        # FX1 센드 한 단계(0~127 중 8 ≈ 6%)


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
        theme.load_private_fonts()  # bundled fonts, also before the first Tk window
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

        # Ctrl+Alt+"." ping-pongs between these two. In memory only — a fresh
        # start has nothing to go back to yet.
        self._last_slot: str | None = None
        self._prev_slot: str | None = None

        # 헤드셋 자동 전환 감시 — 감시 중인 슬롯, 마지막으로 본 연결 여부, after 잡 id
        self._auto_slot: str | None = None
        self._auto_present: tuple[bool, bool] | None = None
        self._auto_job: str | None = None
        # 헤드셋 신뢰 — 동글형은 꺼도 '연결됨'으로 남으므로, 붙거나 떨어지는 순간을 한 번 본 뒤에만 믿는다
        self._headset_trusted = False

        self.hotkeys = HotkeyService(
            on_slot=lambda slot: self.root.after(0, lambda s=slot: self.apply_slot(s)),
            on_save=lambda slot: self.root.after(0, lambda s=slot: self.save_slot(s)),
            on_toggle=lambda: self.root.after(0, self.toggle_slot),
            on_settings=lambda: self.root.after(0, self.open_settings),
            on_error=lambda text: self.root.after(0, lambda x=text: toast(self.root, x, level="warning")),
            on_echo=lambda delta: self.root.after(0, lambda d=delta: self.nudge_echo(d)),
        )

    def nudge_echo(self, delta: int) -> None:
        """Ctrl+Alt+NumPad +/- — FLOW 8 1번 마이크의 FX1(에코) 센드를 한 단계 올리거나 내린다."""
        try:
            from flow8core import Flow8Controller

            value = Flow8Controller().nudge(ECHO_CHANNEL, "send_fx1", delta * ECHO_STEP)
        except Exception as exc:  # noqa: BLE001
            toast(self.root, t("echo_failed", error=exc), level="error")
            return
        pct = round(value * 100 / 127)
        show_profile_osd(self.root, "+" if delta > 0 else "-", t("echo_level", pct=pct), tag="FX1",
                         level="positive" if delta > 0 else "normal", hold_ms=1200)

    def start(self) -> None:
        try:
            self.hotkeys.start()
        except Exception as exc:  # noqa: BLE001
            toast(self.root, t("hotkey_failed", error=exc), level="error")

        self.icon.run_detached()
        self.root.after(400, self._startup_toast)
        self.root.after(1500, self._arm_auto_from_config)
        self.root.mainloop()

    # ── 헤드셋 자동 전환 ──
    def _arm_auto_from_config(self) -> None:
        """시작 시 자동 전환이 켜진 첫 슬롯을 감시한다. 바로 적용하진 않고 변화만 본다."""
        data = config.load_config()
        for key in config.SLOT_KEYS:
            snap = data["snapshots"][key]
            if snap.get("pref_auto") and audio.presence_key(snap) is not None:
                self._arm_auto(key, snap)
                return

    def _arm_auto(self, slot: str, snap: dict) -> None:
        self._auto_slot = slot
        try:
            self._auto_present = audio.presence_key(snap)
        except Exception:  # noqa: BLE001
            self._auto_present = None
        if self._auto_job is None:
            self._auto_job = self.root.after(PREF_POLL_MS, self._auto_tick)

    def _disarm_auto(self) -> None:
        self._auto_slot = None
        self._auto_present = None

    def _auto_tick(self) -> None:
        self._auto_job = None
        if self._auto_slot is None:
            return
        data = config.load_config()
        snap = data["snapshots"].get(self._auto_slot)
        if not snap or not snap.get("pref_auto"):
            self._disarm_auto()
            return
        try:
            present = audio.presence_key(snap)
        except Exception:  # noqa: BLE001
            present = self._auto_present
        if present is not None and present != self._auto_present:
            before = self._auto_present or (False, False)
            self._auto_present = present
            h, s = present
            if h != before[0]:
                # 헤드셋이 실제로 붙거나 떨어졌다 — 이제부터 헤드셋 존재 여부를 믿는다
                self._headset_trusted = True
                tier = "headset" if h else ("speaker" if s else "")
                key = "auto_switched_on" if h else "auto_switched_off"
            else:
                # 스피커가 붙으면 스피커(마지막에 붙은 쪽이 이긴다), 떨어지면 믿을 수 있는 헤드셋이 있을 때만 헤드셋
                tier = "speaker" if s else ("headset" if (h and self._headset_trusted) else "")
                key = "auto_spk_on" if s else "auto_spk_off"
            self.apply_slot(self._auto_slot, tier=tier)
            toast(self.root, t(key), level="positive")
        if self._auto_job is None:
            self._auto_job = self.root.after(PREF_POLL_MS, self._auto_tick)

    def _startup_toast(self) -> None:
        warning = self.hotkeys.status_warning()
        if warning:
            toast(self.root, warning, level="warning", ms=6000)
            return
        toast(self.root, t("running_toast"))

    def open_settings(self) -> None:
        open_settings(on_saved=lambda: toast(self.root, t("snapshots_saved")))

    def apply_slot(self, slot: str, tier: str | None = None) -> None:
        data = config.load_config()
        snap = data["snapshots"].get(slot)
        if not snap:
            toast(self.root, t("slot_missing", slot=slot), level="error")
            return
        name = str(snap.get("name") or "").strip() or f"Slot {slot}"
        try:
            result = audio.apply_snapshot(snap, tier=tier, headset_trusted=self._headset_trusted)
        except Exception as exc:  # noqa: BLE001
            show_profile_osd(self.root, slot, name, level="error")
            toast(self.root, t("apply_failed", error=audio.com_message(exc)), level="error")
            return
        self._remember(slot)
        # 자동 전환이 켜진 슬롯이면 감시 시작(기준 = 지금 연결 상태), 아니면 감시 해제
        if snap.get("pref_auto") and audio.presence_key(snap) is not None:
            self._arm_auto(slot, snap)
        else:
            self._disarm_auto()
        # The profile OSD is the whole point of the hotkey — show it even when a
        # single device is stale, and route the detail to its own toast.
        show_profile_osd(self.root, slot, name, level="warning" if result.warnings else "normal")
        if result.warnings:
            toast(self.root, "\n".join(result.warnings), level="warning", ms=5000)

    def _remember(self, slot: str) -> None:
        """Track the last two distinct slots so toggle_slot() can ping-pong."""
        if slot == self._last_slot:
            return
        self._prev_slot = self._last_slot
        self._last_slot = slot

    def toggle_slot(self) -> None:
        """Ctrl+Alt+"." — go back to the slot applied before the current one."""
        if self._prev_slot is None:
            toast(self.root, t("no_previous_slot"), level="warning")
            return
        # apply_slot -> _remember swaps last/prev, so pressing again comes back.
        self.apply_slot(self._prev_slot)

    def save_slot(self, slot: str) -> None:
        """Ctrl+Alt+Shift+NumPad N — snapshot the live audio state into slot N."""
        data = config.load_config()
        snap = data["snapshots"].get(slot) or deepcopy(config.EMPTY_SNAPSHOT)
        # Keep the label the user gave this slot; only the devices change.
        name = str(snap.get("name") or "").strip() or f"Slot {slot}"
        try:
            captured = audio.capture_system()
            kakao_fields = kakao.capture_kakao()
        except Exception as exc:  # noqa: BLE001
            toast(self.root, t("save_failed", error=audio.com_message(exc)), level="error")
            return

        snap.update(captured)
        # An empty dict means KakaoTalk is not running — leave the slot's
        # existing KakaoTalk fields alone rather than wiping them.
        snap.update(kakao_fields)
        snap["name"] = name
        data["snapshots"][slot] = snap
        try:
            config.save_config(data)
        except OSError as exc:
            toast(self.root, t("save_failed", error=exc), level="error")
            return

        show_profile_osd(self.root, slot, name, level="positive", tag=t("saved_tag"))
        detail = t("captured_kakao_too") if kakao_fields else t("captured_no_kakao")
        toast(self.root, t("saved_current", slot=slot, summary=detail), level="positive", ms=3000)

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
