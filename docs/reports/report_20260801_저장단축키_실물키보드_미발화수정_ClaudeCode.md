# 완료보고서 — 저장 단축키 실물 키보드 미발화 수정 (v1.4.5)

- 프로젝트: audio-hotkeys
- 작업일: 2026-08-01
- 작업자: Claude Code
- 버전: v1.4.4 → **v1.4.5** (PATCH)
- 커밋: `4699e35` (수정) / `9fdd86d` (main 병합), push 완료

## 요청

"Ctrl+Alt+Shift+키패드로 설정 저장 시 저장 완료 상태를 알 수 없다. 설정 변경 오버레이처럼
'X번 슬롯 저장 완료' 메시지를 띄워달라."

## 진단 — 메시지가 없던 게 아니라 저장 자체가 안 되고 있었다

- 저장 완료 OSD(`✓ 저장됨` 대형 오버레이) + 완료 토스트는 **v1.2.0부터 이미 구현**돼 있었다
  (`app.py` `save_slot()` → `show_profile_osd(..., tag=saved_tag)`).
- 그런데 `%LOCALAPPDATA%\audio-hotkeys\config.json`이 7/18 이후 한 번도 갱신되지 않았다.
  저장 단축키가 발화됐다면 반드시 다시 쓰였을 파일 → **단축키가 실물 키보드에서 한 번도
  발화된 적이 없음**이 확정.
- 근본 원인: Windows 키보드 드라이버는 Shift+NumPad 입력 시 **Shift를 가짜로 해제하고 키의
  NumLock 의미를 뒤집는다** (NumLock 켜짐 + Shift+NumPad8 → Shift 없이 VK_UP 도착).
  따라서 `RegisterHotKey(MOD_SHIFT | VK_NUMPAD*)`는 실물 키보드와 절대 매칭되지 않는다.
- v1.2.0 당시 검증이 통과한 이유: 합성 `keybd_event`(VK 직접 주입)는 드라이버를 우회하기
  때문. 합성 입력 테스트의 맹점이었다.

## 수정 내용

### `audio_hotkeys/hotkeys.py`
- `WH_KEYBOARD_LL` 저수준 키보드 훅 추가 (기존 핫키 스레드에 설치, 메시지 루프 공용).
- 물리 NumPad 식별: **스캔코드 0x47–0x52 + extended 플래그 없음** 기준 — NumLock/Shift와
  무관하게 안정적이고, 메인 키보드 방향키(extended)는 절대 건드리지 않는다
  (CLAUDE.md의 "비-NumLock VK 등록 금지" 함정 회피).
- 가짜 Shift 해제 판별: `_save_combo_down()` — Ctrl+Alt가 눌린 상태에서
  **digit VK ↔ NumLock 상태 불일치 = Shift가 실제로 눌려 있음** 규칙. NumLock ON/OFF 모두 커버.
- 자동 반복 억제(`_save_held` 스캔코드 추적, RegisterHotKey의 MOD_NOREPEAT 대응) +
  keydown/keyup 모두 삼켜서 방향키가 포커스된 앱으로 새지 않게 처리.
- 훅 콜백 참조를 인스턴스에 보관(GC되면 콜백 도중 크래시 — foreground.py와 같은 함정).
- 기존 `RegisterHotKey` 저장 슬롯 등록은 합성 입력 폴백으로 유지. 훅 설치 실패 시
  `status_warning()`에 경고 추가.

### 기타
- `version.py`: v1.4.5 + 히스토리 추가.
- `site/index.html`: 버전 표기 v1.4.5 (gh-pages 배포는 미실행 — 아래 참조).
- `CLAUDE.md`: "Shift+NumPad는 RegisterHotKey로 못 잡는다" 함정 항목 추가.

## 검증 (실제 실행 기준)

1. **하니스 테스트** (Tk 앱 없이 `HotkeyService` 단독 기동, 드라이버가 만드는 것과 동일한
   이벤트 시퀀스를 SendInput으로 주입 — 가짜 Shift 해제(extended 플래그) 포함):
   - 하드웨어형 Ctrl+Alt+Shift+NumPad9 → `save 9` 발화 ✓
   - 자동 반복(keydown 2회) → 1회만 발화 ✓
   - 일반 Ctrl+Alt+NumPad9 → 훅이 통과시키고 RegisterHotKey `apply 9` 정상 ✓
2. **통합 테스트** (새로 빌드한 exe 배포·기동 후 동일 시퀀스 주입):
   - `config.json` 슬롯 9에 현재 장치 저장 확인 → 같은 코드 경로에서 `✓ 저장됨` OSD +
     완료 토스트 표시.
   - 테스트로 바뀐 설정은 백업(`config.backup-20260801.json`)으로 **원복 완료**.

## 배포

- PyInstaller 빌드(스펙 직접 실행) → `dist\audio-hotkeys.exe` 교체, 새 버전 실행 중.
- 구버전 백업: `dist\audio-hotkeys.exe.bak-1.4.4`.
- 시작프로그램 바로가기는 기존 것이 그대로 유효(경로 불변).

## 남은 것

- **gh-pages 배포 보류 지속**: 이전 세션(7/25)부터 후원 QR 공개 건으로 사용자 확인 대기.
  배포 시 v1.4.5 표기도 함께 반영됨 (`publish_site.ps1`).
- 배포페이지 개선 작업지시서 M1~M3 미착수 (Outline `OYR67JpRAi`).
