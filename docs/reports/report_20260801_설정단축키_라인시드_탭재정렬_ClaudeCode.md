# 완료보고서 — 설정 열기 단축키 + 라인시드 번들 + 설정 창 3탭 재정렬

- 프로젝트: audio-hotkeys
- 작업일: 2026-08-01 (v1.4.5 체크포인트 이후 증분)
- 작업자: Claude Code
- 버전: v1.4.5 → **v1.5.0** → **v1.6.0**
- 커밋: `6d4a104` (v1.5.0) / `9ffe7e1` (v1.6.0) / 병합 `a6a77d1` (main), push 완료

## v1.5.0 — 설정 창 열기 단축키 (Ctrl+Alt+Shift+.)

- NumPad `.`(스캔코드 0x53)는 숫자 키패드와 동일한 가짜 Shift 해제 대상 →
  기존 `WH_KEYBOARD_LL` 훅을 0x53까지 확장 (`_hooked_action`), 판별 규칙은
  `_shift_combo_down`으로 일반화(digit VK 범위 0x60–0x6F, VK_DECIMAL 포함).
- 메인 키보드 `.`는 `RegisterHotKey(MOD_SHIFT|VK_OEM_PERIOD)`로 등록 —
  NumLock과 무관하게 동작 (id 23–24).
- 이미 설정 창이 열려 있으면 새로 만들지 않고 앞으로 가져온다(기존 `open_settings` 싱글턴).
- 설정 창 단축키 안내에 "설정 창 열기" 줄 추가, i18n `hotkeys_settings` 5개 언어.
- 검증: 하니스 6개 시나리오(설정 NumPad 하드웨어 시퀀스 / 메인 키보드 / 저장·자동반복·
  적용·토글 무영향) 통과 + 배포 exe에 실제 키 시퀀스 주입해 설정 창 열림 확인.

## v1.6.0 — 기본 글꼴 라인시드 번들 + 설정 창 3탭

### 라인시드 글꼴
- 라인시드는 `FONT_CATALOG`에 있었지만 시스템 미설치라 `available_fonts()`에서
  걸러져 옵션에 안 보였다. `assets/fonts/LINESeedKR-Rg.ttf`를 앱에 번들하고
  기동 시 `theme.load_private_fonts()`(AddFontResourceExW, FR_PRIVATE)로
  프로세스 전용 등록 — 시스템 설치 없이 동작.
- 번들 폰트는 tkinter에 "LINE Seed Sans KR Regular"처럼 **굵기 접미사가 붙은
  패밀리명**으로 잡힌다 → `prefs.resolve_family`/`available_fonts`에 접두 일치 추가.
- 기본 글꼴 `FONT_DEFAULT_ID`를 line-seed로 변경(카탈로그 첫 번째), 사용자
  설정(config.json `ui.font_id`)도 line-seed로 전환. 기존 글꼴은 옵션 유지.
- PyInstaller spec `datas`에 `assets/fonts` 추가. frozen exe의 `_MEI*` 추출
  폴더에 폰트가 실제로 풀리는 것 확인.

### 설정 창 재정렬 (산만함 해소)
- 기존: 단축키 안내 4줄 + 화면설정/시스템/카카오 카드 3장 + 버튼 5개가 한 화면.
- 변경: `ttk.Notebook` 3탭 —
  - **스냅샷**: 슬롯 선택 + 시스템/카카오 카드(스크롤) + 슬롯 저장·지금 적용·현재 캡처·카카오 캡처
  - **화면 설정**: 글꼴·글자 크기·언어 (+글꼴 미리보기)
  - **정보**: 단축키 안내 + 버전(모노) + 업데이트 히스토리
- 닫기 버튼·상태 표시는 공통 하단으로. 언어 변경 리빌드 시 보고 있던 탭 유지.
- clam 테마가 선택 탭을 좁게 그리는 문제를 `expand` 맵으로 보정, 상태 문구
  wraplength를 논리 px(`theme.px(660)`)로 바꿔 고DPI 조기 줄바꿈 해소.
- 탭 선택은 색(accent) + 탭 라벨 텍스트로 구분(색상만 구분 금지 준수).
- i18n 신규 키: `tab_snapshot` / `tab_info` / `hotkeys_title` / `version_label` ×5 언어
  (총 62키 ×5 동일 확인).

## 검증

- 소스 실행으로 3탭 각각 스크린샷 확인(라인시드 렌더링 포함), 사용자에게 전달.
- 배포 exe(v1.6.0)에서 설정 단축키 → 창 열림 확인, 테스트로 연 창은 닫아 원복.
- 주의: 검증 중 창 캡처가 멀티모니터 + DPI 비인식 프로세스 좌표 불일치로 화면의
  다른 영역을 찍는 실수가 있었음(해당 파일 즉시 삭제). 캡처 프로세스도
  `SetProcessDpiAwareness`가 필요하다 — 이 앱 CLAUDE.md의 DPI 함정이 검증
  도구에도 그대로 적용된다는 교훈.

## 배포

- `dist\audio-hotkeys.exe` v1.6.0 교체·실행 중. 시작프로그램 경로 불변.
- gh-pages 배포 보류 지속(후원 QR 공개 건 사용자 확인 대기). 사이트 버전 표기는
  저장소에서 v1.6.0으로 갱신됨.
- GitHub Release는 여전히 v1.4.4 — 게시 여부 미결.

## 남은 것

- gh-pages 배포(사용자 확인 시), GitHub Release 갱신 결정.
- 배포페이지 개선 작업지시서 M1~M3 미착수.
