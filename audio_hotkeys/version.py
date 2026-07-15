# audio_hotkeys/version.py
"""Single source of truth for the app version and its release notes."""
from __future__ import annotations

APP_VERSION = "1.3.0"

# (버전, 날짜, 요약) — 최신순
VERSION_HISTORY: list[tuple[str, str, str]] = [
    (
        "1.3.0",
        "2026-07-16",
        "직전 슬롯과 오가는 토글 단축키 추가 (Ctrl+Alt+.). "
        "헤드셋↔스피커처럼 두 프로필을 한 키로 왕복합니다. "
        "NumPad `.`와 메인 키보드 `.` 둘 다 동작하며, 메인 쪽은 NumLock이 꺼져 있어도 됩니다.",
    ),
    (
        "1.2.0",
        "2026-07-16",
        "현재 오디오 상태를 슬롯에 바로 저장하는 단축키 추가 (Ctrl+Alt+Shift+NumPad 0–9). "
        "설정 창을 열지 않아도 되고, 장치 이름까지 함께 저장돼 이후 ID가 바뀌어도 자동 복구됩니다. "
        "카카오톡이 실행 중이면 함께 저장하고, 꺼져 있으면 기존 값을 유지합니다.",
    ),
    (
        "1.1.0",
        "2026-07-16",
        "장치 ID가 바뀌어도 이름으로 재매칭. 스냅샷 일부 실패해도 나머지는 적용. "
        "핫키 등록 실패·NumLock 꺼짐을 실제 원인으로 알림. "
        "SVIL 고대비 다크 디자인 + 화면 설정(글꼴 8종·글자 크기·다국어 5종). "
        "고해상도 모니터에서 텍스트가 흐려지던 DPI 문제 해결.",
    ),
    (
        "1.0.0",
        "2026-07-13",
        "Ctrl+Alt+NumPad 0–9 오디오 스냅샷, 다크 트레이/설정 UI, 카카오톡 전용 장치·볼륨.",
    ),
]
