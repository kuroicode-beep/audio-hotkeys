from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import psutil
from pycaw.pycaw import AudioUtilities

from . import audio as audio_mod

KAKAO_PROCESS_NAMES = ("kakaotalk.exe",)
SVCL_REL = Path("tools") / "svcl" / "svcl.exe"


def find_kakao_pids() -> list[int]:
    pids: list[int] = []
    for proc in psutil.process_iter(["pid", "name"]):
        name = (proc.info.get("name") or "").lower()
        if name in KAKAO_PROCESS_NAMES:
            pids.append(int(proc.info["pid"]))
    return sorted(set(pids))


def svcl_path() -> Path | None:
    candidates: list[Path] = []
    here = Path(__file__).resolve().parent.parent
    candidates.append(here / SVCL_REL)
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", here))
        candidates.append(meipass / "tools" / "svcl" / "svcl.exe")
        candidates.append(Path(sys.executable).resolve().parent / "tools" / "svcl" / "svcl.exe")
        candidates.append(Path(sys.executable).resolve().parent / "svcl.exe")
    for path in candidates:
        if path.is_file():
            return path
    return None


def _run_svcl(*args: str) -> subprocess.CompletedProcess[str]:
    exe = svcl_path()
    if exe is None:
        raise RuntimeError("svcl.exe not found (tools/svcl/svcl.exe)")
    return subprocess.run(
        [str(exe), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def set_kakao_output_device(device_id: str) -> None:
    if not device_id:
        return
    _require_kakao()
    target = _svcl_device_target(device_id, "Render")
    result = _run_svcl("/SetAppDefault", target, "all", "KakaoTalk.exe")
    if result.returncode != 0:
        raise RuntimeError(f"KakaoTalk output device failed ({result.returncode}): {result.stderr or result.stdout}")


def set_kakao_input_device(device_id: str) -> None:
    if not device_id:
        return
    _require_kakao()
    target = _svcl_device_target(device_id, "Capture")
    result = _run_svcl("/SetAppDefault", target, "all", "KakaoTalk.exe")
    if result.returncode != 0:
        raise RuntimeError(f"KakaoTalk input device failed ({result.returncode}): {result.stderr or result.stdout}")


def set_kakao_session_volume(percent: int | None) -> int:
    if percent is None:
        return 0
    clamped = max(0, min(100, int(percent)))
    count = 0
    for session in AudioUtilities.GetAllSessions():
        if not _is_kakao_session(session):
            continue
        volume = session.SimpleAudioVolume
        if volume is None:
            continue
        volume.SetMasterVolume(clamped / 100.0, None)
        if volume.GetMute():
            volume.SetMute(0, None)
        count += 1
    if count:
        return count
    # Fallback: NirSoft app volume (works even without an active session object)
    _require_kakao()
    result = _run_svcl("/SetVolume", "KakaoTalk.exe", str(clamped))
    if result.returncode != 0:
        raise RuntimeError(f"KakaoTalk volume failed ({result.returncode})")
    return 1


def get_kakao_output_volume() -> int | None:
    levels = []
    for session in AudioUtilities.GetAllSessions():
        if not _is_kakao_session(session):
            continue
        volume = session.SimpleAudioVolume
        if volume is None:
            continue
        levels.append(float(volume.GetMasterVolume()) * 100.0)
    if levels:
        return int(round(sum(levels) / len(levels)))
    result = _run_svcl("/Stdout", "/GetPercent", "KakaoTalk.exe")
    text = (result.stdout or "").strip()
    if text:
        try:
            return int(round(float(text)))
        except ValueError:
            return None
    return None


def get_kakao_devices() -> dict[str, str]:
    """Best-effort from svcl CSV export for KakaoTalk application rows."""
    result = {"output_id": "", "input_id": ""}
    rows = _svcl_rows()
    for row in rows:
        if not _row_is_kakao(row):
            continue
        direction = (row.get("Direction") or "").strip()
        item_id = (row.get("Item ID") or "").split("|", 1)[0].strip()
        if direction == "Render" and item_id.startswith("{0.0.0."):
            result["output_id"] = item_id
        elif direction == "Capture" and item_id.startswith("{0.0.1."):
            result["input_id"] = item_id
    return result


def capture_kakao() -> dict:
    """Live KakaoTalk device/volume as snapshot fields.

    Returns {} when KakaoTalk is not running or svcl is missing, so the caller
    keeps whatever the slot already had instead of blanking it.
    """
    if not find_kakao_pids() or svcl_path() is None:
        return {}
    devices = get_kakao_devices()
    fields: dict = {}
    for key, flow, id_field, name_field in (
        ("output_id", "output", "kakao_output_id", "kakao_output_name"),
        ("input_id", "input", "kakao_input_id", "kakao_input_name"),
    ):
        device_id = devices.get(key) or ""
        fields[id_field] = device_id
        name = audio_mod._name_for_id(device_id, flow) if device_id else ""
        # _name_for_id echoes the id back when it cannot resolve a name.
        fields[name_field] = "" if name == device_id else name
    fields["kakao_output_volume"] = get_kakao_output_volume()
    return fields


def apply_kakao_snapshot(snapshot: dict) -> tuple[list[str], list[str]]:
    """Apply the KakaoTalk-only fields. Returns (summary_parts, warnings)."""
    parts: list[str] = []
    warnings: list[str] = []
    out_vol = snapshot.get("kakao_output_volume")
    in_vol = snapshot.get("kakao_input_volume")
    raw_out = snapshot.get("kakao_output_id") or ""
    raw_in = snapshot.get("kakao_input_id") or ""

    wants = bool(raw_out or raw_in or out_vol is not None or in_vol is not None)
    if not wants:
        return parts, warnings
    if not find_kakao_pids():
        parts.append("Kakao: 실행 중 아님")
        return parts, warnings
    if svcl_path() is None:
        warnings.append("svcl.exe를 찾을 수 없어 카카오톡 설정을 건너뛰었습니다.")
        return parts, warnings

    out_id, warn = audio_mod.resolve_device(raw_out, snapshot.get("kakao_output_name") or "", "output")
    if warn:
        warnings.append(f"카카오톡 {warn}")
    in_id, warn = audio_mod.resolve_device(raw_in, snapshot.get("kakao_input_name") or "", "input")
    if warn:
        warnings.append(f"카카오톡 {warn}")

    if out_id:
        try:
            set_kakao_output_device(out_id)
            parts.append(f"KakaoOut: {audio_mod._name_for_id(out_id, 'output')}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"카카오톡 출력 장치 실패: {audio_mod.com_message(exc)}")
    if in_id:
        try:
            set_kakao_input_device(in_id)
            parts.append(f"KakaoIn: {audio_mod._name_for_id(in_id, 'input')}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"카카오톡 입력 장치 실패: {audio_mod.com_message(exc)}")

    vol = out_vol if out_vol is not None else in_vol
    if vol is not None:
        try:
            n = set_kakao_session_volume(int(vol))
            label = "KakaoOutVol" if out_vol is not None else "KakaoVol"
            parts.append(f"{label}: {int(vol)}%×{n}")
            if out_vol is not None and in_vol is not None and int(out_vol) != int(in_vol):
                parts.append("KakaoInVol: (앱 믹서는 출력 볼륨 하나만 사용)")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"카카오톡 볼륨 실패: {audio_mod.com_message(exc)}")
    return parts, warnings


def _require_kakao() -> None:
    if not find_kakao_pids():
        raise RuntimeError("KakaoTalk is not running")


def _is_kakao_session(session) -> bool:
    try:
        proc = session.Process
        if proc is None:
            return False
        return (proc.name() or "").lower() in KAKAO_PROCESS_NAMES
    except Exception:
        return False


def _row_is_kakao(row: dict[str, str]) -> bool:
    name = (row.get("Name") or "").lower()
    path = (row.get("Process Path") or "").lower()
    return "kakaotalk" in name or path.endswith("kakaotalk.exe")


def _svcl_rows() -> list[dict[str, str]]:
    exe = svcl_path()
    if exe is None:
        return []
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        _run_svcl("/scomma", str(path))
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    finally:
        path.unlink(missing_ok=True)


def _svcl_device_target(device_id: str, direction: str) -> str:
    """Resolve a Windows device id to an svcl selector (friendly id or name)."""
    for row in _svcl_rows():
        item_id = (row.get("Item ID") or "").strip()
        row_dir = (row.get("Direction") or "").strip()
        row_type = (row.get("Type") or "").strip()
        if row_type != "Device":
            continue
        if row_dir != direction:
            continue
        if item_id == device_id:
            friendly = (row.get("Command-Line Friendly ID") or "").strip()
            name = (row.get("Name") or "").strip()
            return friendly or name or device_id
    # Fallback to friendly device name from pycaw
    flow = "output" if direction == "Render" else "input"
    return audio_mod._name_for_id(device_id, flow)
