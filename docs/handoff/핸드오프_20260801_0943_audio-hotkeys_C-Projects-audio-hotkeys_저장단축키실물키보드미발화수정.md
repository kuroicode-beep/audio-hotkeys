## 대상
- 프로젝트: audio-hotkeys
- 작업 폴더: C:\Projects\audio-hotkeys
- 세션 시각: 2026-08-01 09:43 (KST)

## 세션 요약
"Ctrl+Alt+Shift+키패드 저장 시 완료 표시가 없다"는 보고를 조사한 결과, 완료 OSD는 v1.2.0부터 있었고 **저장 단축키 자체가 실물 키보드에서 한 번도 발화된 적이 없었다**. 원인 수정(v1.4.5), 검증, 빌드·배포, main 병합·push까지 완료.

## 완료된 작업
- **원인 확정**: Windows 키보드 드라이버의 Shift+NumPad 가짜 Shift 해제(키의 NumLock 의미 반전) 때문에 `RegisterHotKey(MOD_SHIFT|VK_NUMPAD*)`가 실물 키보드와 절대 매칭 안 됨. 증거: `%LOCALAPPDATA%\audio-hotkeys\config.json`이 7/18 이후 미갱신. v1.2.0 검증은 합성 keybd_event(VK 주입)가 드라이버를 우회해 통과했던 것.
- **수정** (`audio_hotkeys/hotkeys.py`): `WH_KEYBOARD_LL` 훅 추가 — 물리 NumPad는 스캔코드 0x47–0x52 + extended 아님으로 식별, 가짜 Shift는 "digit VK ↔ NumLock 불일치 = Shift 실제 눌림" 규칙(`_save_combo_down`)으로 판별. 자동반복 억제 + keydown/keyup 삼킴. 훅 콜백 참조 인스턴스 보관(GC 크래시 함정). RegisterHotKey 저장 등록은 합성 입력 폴백으로 유지.
- **검증**: 하니스(HotkeyService 단독)에 드라이버 동일 이벤트 시퀀스(가짜 Shift 해제 포함) 주입 — 저장 발화 / 자동반복 1회 / 적용 단축키 무영향 모두 통과. 새 exe 배포 후 통합 테스트로 config.json 슬롯 저장 확인, 테스트 변경분은 백업(`config.backup-20260801.json`)으로 원복.
- **버전**: v1.4.5 (`version.py` 히스토리 추가), `site/index.html` 표기 v1.4.5, `CLAUDE.md`에 Shift+NumPad 함정 항목 추가.
- **배포**: `dist\audio-hotkeys.exe` v1.4.5 교체·실행 중. 구버전 백업 `dist\audio-hotkeys.exe.bak-1.4.4`. 시작프로그램 바로가기는 경로 불변으로 유효.
- **git**: 수정 `4699e35` → main 병합 `9fdd86d` → 완료보고서 `424c77d`, 전부 push 완료.
- **기록**: 완료보고서 `docs/reports/report_20260801_저장단축키_실물키보드_미발화수정_ClaudeCode.md`, Outline 프로젝트 위키(`/doc/audio-hotkeys-NkvmCKQF5h`, id 0d65ef56)에 2026-08-01 세션 로그 append(rev 8).

## 진행 중 / 미완료 작업
- **gh-pages 배포 보류 지속** (7/25부터): 후원 QR 공개 건 사용자 확인 대기. 확인되면 `publish_site.ps1` 실행 — v1.4.5 표기 함께 반영됨. 배포 후 라이브 URL 재확인 필요.
- **GitHub Release는 v1.4.4가 최신** — v1.4.5 exe를 릴리스에 올리지 않았다. 사이트 다운로드 버튼(`releases/latest/...`)은 여전히 v1.4.4를 준다. 다음 세션에서 릴리스 게시 여부 결정.
- Outline 프로젝트 위키 헤더의 "현재 버전: v1.4.4" 표기는 append 원칙상 미수정(최신 세션 로그에 v1.4.5 명시됨).
- 배포페이지 개선 작업지시서 M1~M3 미착수 (Outline `OYR67JpRAi`).

## 주요 결정사항 / 규칙
- **Shift+NumPad 단축키는 RegisterHotKey로 잡지 말 것** — WH_KEYBOARD_LL 훅 + 스캔코드 식별이 정본 (CLAUDE.md 함정 목록에 기록).
- 합성 keybd_event 검증은 키보드 드라이버 동작을 우회한다 — 단축키 검증 시 드라이버가 실제로 만드는 이벤트 시퀀스(가짜 Shift 등)를 재현해 주입할 것.

## 참고 정보
- 완료보고서: `docs/reports/report_20260801_저장단축키_실물키보드_미발화수정_ClaudeCode.md`
- Outline 프로젝트 위키: `/doc/audio-hotkeys-NkvmCKQF5h` (id 0d65ef56-990f-4937-8bbf-da0f8afbe2d4)
- 배포페이지 개선 작업지시서: Outline `OYR67JpRAi` (id 142b6c11)
- 배포 스크립트: `publish_site.ps1` / 빌드: `python -m PyInstaller --noconfirm audio-hotkeys.spec` (build.ps1은 PS5.1 pip stderr 문제)

## 다음 세션 시작 시 할 일
1. (사용자 확인 시) `publish_site.ps1` gh-pages 배포 → 라이브 URL에서 v1.4.5·후원 QR 확인.
2. GitHub Release v1.4.5 게시 여부 결정(사이트 다운로드 링크 갱신).
3. 여력 되면 배포페이지 개선 작업지시서 M1(히어로 비주얼·OG 메타·다운로드 안심 요소) 착수.
