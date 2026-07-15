"""SVIL frontend design tokens (v1.1)."""

from __future__ import annotations

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

# Typography
FONT_DEFAULT_ID = "kyobo-handwriting-2019"
FONT_STACK_DEFAULT = ("KyoboHandwriting2019", "Pretendard", "Malgun Gothic", "Segoe UI")
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
FONT_CATALOG: list[dict[str, str]] = [
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
        "id": "line-seed",
        "label": "라인시드체",
        "family": "LINE Seed Sans KR",
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


def font_tuple(family: str, size: int) -> tuple:
    return (family, size)


def mono_tuple(size: int) -> tuple:
    return (*FONT_MONO, size)
