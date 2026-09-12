# audio_hotkeys/precheck.py
# 방송 직전 점검(Ctrl+Alt+.) — NumLock, 방송 슬롯 적용, FLOW 8 포트, 마이크 신호를 한 번에 확인한다.
from __future__ import annotations

import array
import ctypes
import math
import time

VK_NUMLOCK = 0x90
MIC_THRESHOLD = 0.002   # 피크 -54 dBFS. 48V·레벨이 살아 있으면 방 잡음만으로도 넘고, 죽어 있으면 거의 0이다
MEASURE_SECONDS = 2.0

_user32 = ctypes.WinDLL("user32", use_last_error=True)


def numlock_on() -> bool:
    return bool(_user32.GetKeyState(VK_NUMLOCK) & 1)


def ensure_numlock() -> bool:
    """꺼져 있으면 켠다. 켰으면 True(바뀜), 이미 켜져 있었으면 False."""
    if numlock_on():
        return False
    _user32.keybd_event(VK_NUMLOCK, 0x45, 0x0001, 0)
    _user32.keybd_event(VK_NUMLOCK, 0x45, 0x0003, 0)
    time.sleep(0.15)
    return numlock_on()


def measure_input_peak(seconds: float = MEASURE_SECONDS) -> float | None:
    """기본 입력 장치를 seconds 동안 열어 최대 피크(0~1)를 돌려준다. 열지 못하면 None."""
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001
        return None
    peak = 0.0

    def _cb(indata, frames, t, status) -> None:  # noqa: ANN001
        nonlocal peak
        buf = array.array("h", bytes(indata))
        m = max((abs(x) for x in buf), default=0)
        peak = max(peak, m / 32768.0)

    try:
        info = sd.query_devices(None, "input")
        rate = int(info.get("default_samplerate") or 48000)
        with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16", callback=_cb):
            time.sleep(seconds)
    except Exception:  # noqa: BLE001
        return None
    return peak


def dbfs(peak: float | None) -> str:
    if not peak:
        return "-inf dBFS"
    return f"{20 * math.log10(peak):.0f} dBFS"


def classify(peak: float | None) -> str:
    """'ok' 신호 있음 · 'silent' 열렸지만 무음(48V/레벨 의심) · 'none' 장치 열기 실패."""
    if peak is None:
        return "none"
    return "ok" if peak >= MIC_THRESHOLD else "silent"


def flow8_port() -> tuple[bool, str]:
    try:
        from flow8core import Flow8Controller

        msg = Flow8Controller().port_check()
        return ("정상" in msg), msg
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
