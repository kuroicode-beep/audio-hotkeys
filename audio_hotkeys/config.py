from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "audio-hotkeys"
CONFIG_DIR = Path.home() / "AppData" / "Local" / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"

SLOT_KEYS = [str(i) for i in range(10)]

# *_name mirrors each *_id so a snapshot survives a device id change
# (USB re-enumeration, driver reinstall). The id is tried first, the name
# is the fallback match.
ID_FIELDS = ("output_id", "input_id", "kakao_output_id", "kakao_input_id",
             "pref_output_id", "pref_input_id", "pref2_output_id")
NAME_FIELDS = ("output_name", "input_name", "kakao_output_name", "kakao_input_name",
               "pref_output_name", "pref_input_name", "pref2_output_name")
VOLUME_FIELDS = ("output_volume", "input_volume", "kakao_output_volume", "kakao_input_volume")

EMPTY_SNAPSHOT: dict[str, Any] = {
    "name": "",
    "output_id": "",
    "output_name": "",
    "input_id": "",
    "input_name": "",
    "output_volume": None,
    "input_volume": None,
    "kakao_output_id": "",
    "kakao_output_name": "",
    "kakao_input_id": "",
    "kakao_input_name": "",
    "kakao_output_volume": None,
    "kakao_input_volume": None,
    "flow8_snapshot": None,   # FLOW 8 믹서 본체 스냅샷 번호(1~15), None이면 안 보냄
    # 헤드셋 우선 장치 — 연결돼 있을 때만 시스템·카카오톡 출력/입력을 이 장치로 바꾼다
    "pref_output_id": "",
    "pref_output_name": "",
    "pref_input_id": "",
    "pref_input_name": "",
    "pref_auto": False,       # True면 연결/해제를 감시해 자동으로 다시 적용
    # 2순위 우선 스피커(출력만) — 헤드셋이 없고 이 장치가 연결돼 있으면 출력만 이쪽으로(블루투스 스피커 등)
    "pref2_output_id": "",
    "pref2_output_name": "",
}


def default_config() -> dict[str, Any]:
    snapshots = {}
    for key in SLOT_KEYS:
        snap = deepcopy(EMPTY_SNAPSHOT)
        snap["name"] = "Default" if key == "0" else f"Slot {key}"
        snapshots[key] = snap
    return {
        "snapshots": snapshots,
        "ui": {
            "font_id": "kyobo-handwriting-2019",
            "font_size": "M",
            "lang": "ko",
        },
    }


def ensure_config() -> dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        data = default_config()
        save_config(data)
        return data
    return load_config()


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return default_config()
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return _normalize(data)


def save_config(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    normalized = _normalize(data)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


# FLOW 8 스냅샷 번호는 1~15 정수만 인정, 그 외는 None
def _flow8(value: Any) -> int | None:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 15 else None


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    base = default_config()
    if not isinstance(data, dict):
        return base
    incoming = data.get("snapshots")
    if isinstance(incoming, dict):
        for key in SLOT_KEYS:
            raw = incoming.get(key, {})
            if not isinstance(raw, dict):
                continue
            snap = deepcopy(EMPTY_SNAPSHOT)
            snap["name"] = str(raw.get("name") or base["snapshots"][key]["name"])
            for field in ID_FIELDS + NAME_FIELDS:
                snap[field] = str(raw.get(field) or "")
            for field in VOLUME_FIELDS:
                snap[field] = _volume(raw.get(field))
            snap["flow8_snapshot"] = _flow8(raw.get("flow8_snapshot"))
            snap["pref_auto"] = bool(raw.get("pref_auto"))
            base["snapshots"][key] = snap
    ui = data.get("ui")
    if isinstance(ui, dict):
        merged = dict(base["ui"])
        for key in ("font_id", "font_size", "lang"):
            if ui.get(key):
                merged[key] = str(ui[key])
        base["ui"] = merged
    return base


def _volume(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, n))
