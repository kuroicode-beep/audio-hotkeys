"""UI preferences: font / size / language (SVIL screen-settings standard)."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Any

from . import config, theme

LANGS = ("ko", "en", "ja", "zh", "vi")
LANG_LABELS = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
    "vi": "Tiếng Việt",
}

DEFAULT_PREFS: dict[str, str] = {
    "font_id": theme.FONT_DEFAULT_ID,
    "font_size": theme.FONT_SIZE_DEFAULT,
    "lang": "ko",
}


def _normalize_prefs(raw: Any) -> dict[str, str]:
    prefs = dict(DEFAULT_PREFS)
    if not isinstance(raw, dict):
        return prefs
    font_id = str(raw.get("font_id") or prefs["font_id"])
    if font_id not in {f["id"] for f in theme.FONT_CATALOG}:
        font_id = prefs["font_id"]
    size = str(raw.get("font_size") or prefs["font_size"]).upper()
    if size not in theme.FONT_SIZE_PX:
        size = prefs["font_size"]
    lang = str(raw.get("lang") or prefs["lang"])
    if lang not in LANGS:
        lang = prefs["lang"]
    return {"font_id": font_id, "font_size": size, "lang": lang}


def load_prefs() -> dict[str, str]:
    data = config.load_config()
    return _normalize_prefs(data.get("ui"))


def save_prefs(prefs: dict[str, str]) -> None:
    data = config.load_config()
    data["ui"] = _normalize_prefs(prefs)
    config.save_config(data)


def resolve_family(font_id: str, root: tk.Misc | None = None) -> str:
    families = None
    owns = False
    if root is None:
        root = tk.Tk()
        root.withdraw()
        owns = True
    try:
        families = {name.lower(): name for name in tkfont.families(root)}
        if font_id == "gothic":
            for candidate in ("Pretendard", "Malgun Gothic", "Segoe UI"):
                if candidate.lower() in families:
                    return families[candidate.lower()]
            return "Malgun Gothic"
        for entry in theme.FONT_CATALOG:
            if entry["id"] == font_id:
                fam = entry["family"]
                if fam.lower() in families:
                    return families[fam.lower()]
                # try without spaces / common aliases
                compact = fam.replace(" ", "").lower()
                for key, original in families.items():
                    if key.replace(" ", "") == compact:
                        return original
                break
        return "Malgun Gothic"
    finally:
        if owns:
            root.destroy()


def available_fonts(root: tk.Misc | None = None) -> list[dict[str, str]]:
    """Return catalog entries that tkinter can resolve (gothic always available)."""
    owns = False
    if root is None:
        root = tk.Tk()
        root.withdraw()
        owns = True
    try:
        families = {name.lower().replace(" ", "") for name in tkfont.families(root)}
        out: list[dict[str, str]] = []
        for entry in theme.FONT_CATALOG:
            if entry["id"] == "gothic":
                out.append(entry)
                continue
            fam = entry["family"].lower().replace(" ", "")
            if fam in families:
                out.append(entry)
        if not any(e["id"] == theme.FONT_DEFAULT_ID for e in out):
            out.insert(0, theme.FONT_CATALOG[0])
        return out
    finally:
        if owns:
            root.destroy()


def ui_font(root: tk.Misc | None = None, prefs: dict[str, str] | None = None) -> tuple:
    p = prefs or load_prefs()
    family = resolve_family(p["font_id"], root)
    size = theme.FONT_SIZE_PX.get(p["font_size"], 18)
    return (family, size)


def mono_font(prefs: dict[str, str] | None = None) -> tuple:
    p = prefs or load_prefs()
    size = theme.FONT_SIZE_PX.get(p["font_size"], 18)
    return ("Consolas", size)
