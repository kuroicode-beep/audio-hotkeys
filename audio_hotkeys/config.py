from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "audio-hotkeys"
CONFIG_DIR = Path.home() / "AppData" / "Local" / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"

SLOT_KEYS = [str(i) for i in range(10)]

EMPTY_SNAPSHOT: dict[str, Any] = {
    "name": "",
    "output_id": "",
    "input_id": "",
    "output_volume": None,
    "input_volume": None,
}


def default_config() -> dict[str, Any]:
    snapshots = {}
    for key in SLOT_KEYS:
        snap = deepcopy(EMPTY_SNAPSHOT)
        snap["name"] = "Default" if key == "0" else f"Slot {key}"
        snapshots[key] = snap
    return {"snapshots": snapshots}


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


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    base = default_config()
    incoming = data.get("snapshots") if isinstance(data, dict) else None
    if not isinstance(incoming, dict):
        return base
    for key in SLOT_KEYS:
        raw = incoming.get(key, {})
        if not isinstance(raw, dict):
            continue
        snap = deepcopy(EMPTY_SNAPSHOT)
        snap["name"] = str(raw.get("name") or base["snapshots"][key]["name"])
        snap["output_id"] = str(raw.get("output_id") or "")
        snap["input_id"] = str(raw.get("input_id") or "")
        snap["output_volume"] = _volume(raw.get("output_volume"))
        snap["input_volume"] = _volume(raw.get("input_volume"))
        base["snapshots"][key] = snap
    return base


def _volume(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, n))
