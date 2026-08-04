"""SVIL frontend design tokens (v1.1).

크기는 논리 px로 적는다. px()가 모니터 DPI 배율을 곱하고, 폰트 헬퍼는
tkinter가 픽셀로 해석하도록 음수 크기를 돌려준다 (양수는 포인트).
"""

from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk

# Colors — Outline: SVIL 프론트엔드 · 디자인 가이드 v1.1
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
BLACK = "#000000"

# 상태색은 항상 텍스트 라벨과 함께 쓴다 (색상만으로 구분 금지).
LEVEL_COLOR = {"normal": TEXT, "warning": WARNING, "error": NEGATIVE, "positive": POSITIVE}
LEVEL_LABEL = {"normal": "", "warning": "⚠ 주의", "error": "✖ 오류", "positive": "✓ 완료"}

# Typography
FONT_DEFAULT_ID = "line-seed"
FONT_STACK_DEFAULT = ("LINE Seed Sans KR", "Pretendard", "Malgun Gothic", "Segoe UI")
FONT_MONO = ("Consolas", "Cascadia Mono", "Courier New")

FONT_SIZE_PX = {
    "S": 16,
    "M": 18,
    "L": 20,
}
FONT_SIZE_DEFAULT = "M"

# Layout
TARGET_MIN = 50
RADIUS_BTN = 12
RADIUS_CARD = 16
PAD_CARD = 22
FOCUS_WIDTH = 3
BORDER_WIDTH = 2

# Font catalog (only ids that resolve locally are selectable at runtime)
# 라인시드가 SVIL 표준 기본 — 번들 폰트(assets/fonts)를 load_private_fonts()로 올린다.
FONT_CATALOG: list[dict[str, str]] = [
    {
        "id": "line-seed",
        "label": "라인시드체",
        "family": "LINE Seed Sans KR",
    },
    {
        "id": "kyobo-handwriting-2019",
        "label": "교보손글씨2019",
        "family": "KyoboHandwriting2019",
    },
    {
        "id": "gothic",
        "label": "고딕",
        "family": "Pretendard",  # resolve falls back to Malgun Gothic
    },
    {
        "id": "nanum-gothic",
        "label": "나눔고딕",
        "family": "NanumGothic",
    },
    {
        "id": "gowun-dodum",
        "label": "고운돋움체",
        "family": "Gowun Dodum",
    },
    {
        "id": "cafe24-dongdong",
        "label": "카페24동동체",
        "family": "Cafe24Dongdong",
    },
    {
        "id": "tmoney-round",
        "label": "티머니둥근바람체",
        "family": "TmoneyRoundWind",
    },
    {
        "id": "recipe-korea",
        "label": "레코체",
        "family": "Recipekorea",
    },
]


# --- Bundled fonts ---------------------------------------------------------


def load_private_fonts() -> None:
    """번들 폰트(assets/fonts)를 이 프로세스 전용으로 등록한다.

    FR_PRIVATE라 시스템 설치 없이 이 프로세스에서만 보인다.
    첫 Tk 창을 만들기 전에 호출해야 tkfont.families()에 잡힌다.
    """
    roots = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            roots.append(meipass)
        roots.append(os.path.dirname(os.path.abspath(sys.executable)))
    FR_PRIVATE = 0x10
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    for root in roots:
        folder = os.path.join(root, "assets", "fonts")
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if name.lower().endswith((".ttf", ".otf", ".ttc")):
                gdi32.AddFontResourceExW(os.path.join(folder, name), FR_PRIVATE, 0)


# --- DPI -------------------------------------------------------------------
_scale = 1.0


def enable_dpi_awareness() -> None:
    """Tk 창을 만들기 전에 호출한다.

    DPI 비인식 프로세스는 Windows가 비트맵으로 확대해 텍스트가 흐려진다
    (200% 모니터에서 특히). 저시력 사용자에게는 그대로 가독성 손실이라
    per-monitor v2로 선언하고 크기는 px()로 직접 환산한다.
    """
    for target, arg in (
        ("shcore.SetProcessDpiAwarenessContext", -4),  # PER_MONITOR_AWARE_V2
        ("user32.SetProcessDpiAwarenessContext", -4),
        ("shcore.SetProcessDpiAwareness", 2),
        ("user32.SetProcessDPIAware", None),
    ):
        dll_name, func_name = target.split(".")
        try:
            func = getattr(getattr(ctypes.windll, dll_name), func_name)
            if func() if arg is None else func(arg):
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


def font_tuple(family: str, size: int) -> tuple:
    """size는 논리 px. tkinter는 음수를 픽셀로 해석한다 (양수 = 포인트)."""
    return (family, -px(size))


def mono_tuple(size: int) -> tuple:
    return (FONT_MONO[0], -px(size))
