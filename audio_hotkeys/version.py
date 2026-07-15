# audio_hotkeys/version.py
"""Single source of truth for the app version and its release notes."""
from __future__ import annotations

APP_VERSION = "1.1.0"

# (버전, 날짜, 요약) — 최신순
VERSION_HISTORY: list[tuple[str, str, str]] = [
    (
        "1.1.0",
        "2026-07-16",
        "장치 ID가 바뀌어도 이름으로 재매칭. 스냅샷 일부 실패해도 나머지는 적용. "
        "핫키 등록 실패·NumLock 꺼짐을 실제 원인으로 알림. SVIL 고대비 다크 디자인 적용.",
    ),
    (
        "1.0.0",
        "2026-07-13",
        "Ctrl+Alt+NumPad 0–9 오디오 스냅샷, 다크 트레이/설정 UI, 카카오톡 전용 장치·볼륨.",
    ),
]
