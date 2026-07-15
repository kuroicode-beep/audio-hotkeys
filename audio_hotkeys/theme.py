# audio_hotkeys/theme.py
"""SVIL 고대비 다크 디자인 토큰 (tkinter 적용).

색상은 이 모듈의 토큰만 사용한다 — 각 UI 파일에서 하드코딩 금지.
크기는 논리 px로 적으며 px()가 모니터 DPI 배율을 곱한다.
가이드: docs/Design_20260714_SVIL_프론트엔드_디자인가이드_ClaudeCode.md
"""
from __future__ import annotations

import ctypes
import tkinter as tk
import tkinter.font as tkfont

# --- 색상 토큰 -------------------------------------------------------------
BG = "#0d0d12"
SURFACE = "#16161d"
SURFACE_2 = "#1f1f2a"
BORDER = "#3a3a48"
BORDER_STRONG = "#6b6b82"
TEXT = "#f5f5f7"
TEXT_SUB = "#c9c9d4"
ACCENT = "#7ec8ff"
ACCENT_STRONG = "#b3ddff"
ACCENT_MAX = "#d6ecff"
POSITIVE = "#7ee2a8"
WARNING = "#ffd479"
NEGATIVE = "#ff9b9b"
FOCUS = "#ffd479"

# 상태색은 항상 텍스트 라벨과 함께 쓴다 (색상만으로 구분 금지).
LEVEL_COLOR = {"normal": TEXT, "warning": WARNING, "error": NEGATIVE, "positive": POSITIVE}
LEVEL_LABEL = {"normal": "", "warning": "⚠ 주의", "error": "✖ 오류", "positive": "✓ 완료"}

# --- 타이포그래피 ----------------------------------------------------------
# 로컬 설치 폰트만 사용 (CDN 금지). 우선순위대로 실재하는 첫 항목을 고른다.
# 한글 Windows는 Malgun Gothic을 "맑은 고딕"으로 등록하므로 양쪽을 모두 둔다.
UI_FAMILIES = ("KyoboHandwriting2019", "Pretendard", "Malgun Gothic", "맑은 고딕", "Segoe UI")
MONO_FAMILIES = ("Consolas", "D2Coding", "Courier New")

# 본문 기준 18px, 전체 최소선 12px (논리 px).
SIZE_BODY = 18
SIZE_SMALL = 15
SIZE_MICRO = 12
SIZE_H3 = 22
SIZE_H2 = 28
SIZE_OSD_NAME = 96
SIZE_OSD_SLOT = 32

_scale = 1.0
_ui_family: str | None = None
_mono_family: str | None = None


def enable_dpi_awareness() -> None:
    """Tk 창을 만들기 전에 호출한다.

    DPI 비인식 프로세스는 Windows가 비트맵으로 확대해 텍스트가 흐려진다
    (200% 모니터에서 특히). 저시력 사용자에게는 그대로 가독성 손실이라
    per-monitor v2로 선언하고 크기는 px()로 직접 환산한다.
    """
    for fn, arg in (
        ("shcore.SetProcessDpiAwarenessContext", -4),  # PER_MONITOR_AWARE_V2
        ("user32.SetProcessDpiAwarenessContext", -4),
        ("shcore.SetProcessDpiAwareness", 2),
        ("user32.SetProcessDPIAware", None),
    ):
        dll_name, func_name = fn.split(".")
        try:
            dll = getattr(ctypes.windll, dll_name)
            func = getattr(dll, func_name)
            ok = func() if arg is None else func(arg)
            if ok:
                return
        except (AttributeError, OSError):
            continue


def init_scale(root: tk.Misc) -> float:
    """Tk 루트가 생긴 뒤 실제 DPI를 읽어 배율을 고정한다."""
    global _scale
    try:
        _scale = max(1.0, float(root.winfo_fpixels("1i")) / 96.0)
    except Exception:  # noqa: BLE001
        _scale = 1.0
    return _scale


def scale() -> float:
    return _scale


def px(value: int) -> int:
    """논리 px -> 물리 px."""
    return max(1, round(value * _scale))


def _pick(candidates: tuple[str, ...], fallback: str) -> str:
    try:
        available = {name.lower() for name in tkfont.families()}
    except Exception:  # noqa: BLE001 - no Tk root yet
        return fallback
    for name in candidates:
        if name.lower() in available:
            return name
    return fallback


def ui_family() -> str:
    global _ui_family
    if _ui_family is None:
        _ui_family = _pick(UI_FAMILIES, "Segoe UI")
    return _ui_family


def mono_family() -> str:
    global _mono_family
    if _mono_family is None:
        _mono_family = _pick(MONO_FAMILIES, "Courier New")
    return _mono_family


def ui_font(size: int = SIZE_BODY) -> tuple[str, int]:
    """본문 폰트. bold 합성 금지 — 위계는 크기·색으로만 준다.

    tkinter는 음수 크기를 픽셀로 해석한다 (양수는 포인트).
    """
    return (ui_family(), -px(size))


def mono_font(size: int = SIZE_BODY) -> tuple[str, int]:
    """숫자·ID·버전·코드 전용 모노체."""
    return (mono_family(), -px(size))
