## 대상
- 프로젝트: audio-hotkeys
- 작업 폴더: C:\Projects\audio-hotkeys
- 세션 시각: 2026-08-04 11:59 (KST)

## 세션 요약
v1.4.5 체크포인트 이후 증분 두 건을 구현·배포·병합했다: ① 설정 창 열기 단축키 Ctrl+Alt+Shift+. (v1.5.0) ② 기본 글꼴 라인시드 번들 + 설정 창 3탭 재정렬 (v1.6.0). main 병합 `a6a77d1`, push 완료, v1.6.0 exe 실행 중.

## 완료된 작업
- **v1.5.0 설정 열기 단축키**: NumPad `.`(스캔코드 0x53)는 가짜 Shift 해제 대상이라 기존 `WH_KEYBOARD_LL` 훅을 확장(`hotkeys.py` `_hooked_action`/`_shift_combo_down`), 메인 키보드 `.`는 `RegisterHotKey(MOD_SHIFT|VK_OEM_PERIOD)` 등록(id 23–24). 이미 열려 있으면 앞으로. 하니스 6개 시나리오 + 배포 exe 실주입 검증. 커밋 `6d4a104`.
- **v1.6.0 라인시드 번들**: `assets/fonts/LINESeedKR-Rg.ttf` 번들 + 기동 시 `theme.load_private_fonts()`(AddFontResourceExW FR_PRIVATE). 번들 폰트가 "LINE Seed Sans KR Regular"로 잡혀 `prefs.py`에 접두 일치 해석 추가. `FONT_DEFAULT_ID`=line-seed, 사용자 config `ui.font_id`도 전환. spec datas에 assets/fonts 추가, `_MEI*` 추출 확인. 커밋 `9ffe7e1`.
- **v1.6.0 설정 창 3탭**: 스냅샷(슬롯+장치+액션) / 화면 설정(글꼴·크기·언어) / 정보(단축키·버전·히스토리). 닫기·상태 표시는 공통 하단. 언어 변경 리빌드 시 탭 유지. clam 선택 탭 축소 expand 보정, 상태 wraplength `theme.px(660)`. i18n 4키 추가(62키 ×5). 소스 실행 3탭 스크린샷 검증.
- main 병합 `a6a77d1` → 완료보고서 커밋 `de4bb56`, push 완료.
- 기록: `docs/reports/report_20260801_설정단축키_라인시드_탭재정렬_ClaudeCode.md`, Outline 위키 세션 로그 append(rev 10).
- 배포: `dist\audio-hotkeys.exe` v1.6.0 실행 중 (백업 `.bak-1.4.4`).

## 진행 중 / 미완료 작업
- **gh-pages 배포 보류 지속**(7/25부터, 후원 QR 공개 건 사용자 확인 대기). 사이트 표기는 저장소에서 v1.6.0.
- **GitHub Release v1.4.4가 최신** — v1.5.0/v1.6.0 릴리스 미게시. 사이트 다운로드 버튼은 여전히 v1.4.4를 준다.
- Outline 위키 헤더 "현재 버전: v1.4.4" 표기 stale (append 원칙, 최신 로그에 v1.6.0 명시).
- 배포페이지 개선 작업지시서 M1~M3 미착수 (Outline `OYR67JpRAi`).

## 주요 결정사항 / 규칙
- Shift+NumPad 계열 단축키(저장·설정 열기)는 전부 `WH_KEYBOARD_LL` 훅 + 스캔코드 식별이 정본. RegisterHotKey는 합성 입력 폴백.
- 앱 번들 폰트는 FR_PRIVATE 프로세스 전용 등록 + 접두 일치 해석 — 굵기 접미사가 붙은 패밀리명("... Regular") 대응.
- 창 캡처 검증 시 캡처 프로세스도 `SetProcessDpiAwareness` 필수 — 멀티모니터+DPI 비인식이면 좌표가 어긋나 엉뚱한 영역을 찍는다(이번에 실제로 발생, 파일 즉시 삭제).

## 참고 정보
- 완료보고서: `docs/reports/report_20260801_설정단축키_라인시드_탭재정렬_ClaudeCode.md`
- Outline 프로젝트 위키: `/doc/audio-hotkeys-NkvmCKQF5h` (id 0d65ef56-990f-4937-8bbf-da0f8afbe2d4)
- 빌드: `python -m PyInstaller --noconfirm audio-hotkeys.spec` / 배포 페이지: `publish_site.ps1`
- 폰트 원본: `C:\Projects\SingPromfterApp\...\assets\fonts\LINESeedKR-Rg.ttf`에서 복사

## 다음 세션 시작 시 할 일
1. (사용자 확인 시) gh-pages 배포 → 라이브에서 v1.6.0·후원 QR 확인.
2. GitHub Release v1.6.0 게시 여부 결정(사이트 다운로드 링크 갱신).
3. 여력 되면 배포페이지 개선 작업지시서 M1 착수.
