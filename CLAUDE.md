# audio-hotkeys

Windows 트레이 앱. 오디오 입·출력 장치와 볼륨 스냅샷을 전역 단축키로 전환한다.
Python 3.13 + tkinter + pycaw/comtypes + pystray, PyInstaller onefile 배포.

- 사이트: https://kuroicode-beep.github.io/audio-hotkeys/
- 설정 파일: `%LOCALAPPDATA%\audio-hotkeys\config.json`

## 명령

```powershell
.\.venv\Scripts\python.exe -m audio_hotkeys   # 실행 (run.bat 도 동일)
.\build.ps1                                    # dist\audio-hotkeys.exe
.\publish_site.ps1                             # site/ -> gh-pages 배포
.\install_startup.ps1                          # 시작프로그램 등록
```

`build.ps1`은 `$ErrorActionPreference="Stop"` + PowerShell 5.1의 NativeCommandError 조합
때문에 pip가 stderr에 한 줄만 써도 중단된다. 막히면 `python -m PyInstaller --noconfirm
audio-hotkeys.spec`을 직접 실행할 것. (백로그: 스크립트 자체 보완)

## 구조

| 모듈 | 역할 |
|---|---|
| `hotkeys.py` | Win32 `RegisterHotKey` + 메시지 루프 스레드. id 범위로 구분: 적용 1–10 / 저장 11–20 / 토글 21–22 |
| `audio.py` | 장치 열거·볼륨(pycaw), PolicyConfig COM 기본 장치 전환, `resolve_device()`, `ApplyResult` |
| `kakao.py` | KakaoTalk 전용 라우팅 (번들 `tools/svcl/svcl.exe`) |
| `config.py` | 스냅샷 10개 + `ui` 섹션. 필드는 `ID_FIELDS`/`NAME_FIELDS`/`VOLUME_FIELDS` 상수로 관리 |
| `prefs.py` / `i18n.py` | 글꼴·크기·언어 환경설정 / 5개 언어 문자열 |
| `theme.py` | SVIL 디자인 토큰 + DPI 환산 |
| `settings.py` / `tray.py` | 설정 창 / 트레이·OSD·토스트 |
| `version.py` | `APP_VERSION` + `VERSION_HISTORY` |
| `site/index.html` | 배포 페이지 (자체 완결형 단일 파일) |

## 설계 규칙 (어기면 회귀)

**스냅샷은 부분 실패를 허용한다.** `apply_snapshot()`은 예외를 위로 던지지 않고
`ApplyResult(summary, warnings)`를 돌려준다. 장치 하나가 사라져도 그 필드만 건너뛰고 나머지는
적용한다. 프로필 OSD는 **항상** 띄우고 경고는 별도 토스트로 분리한다 — OSD가 단축키의 존재
이유다. (v1.0.0은 첫 실패에서 전체를 중단하고 OSD 대신 원시 HRESULT를 띄웠다.)

**장치는 ID와 이름을 함께 저장한다.** USB 재연결·드라이버 재설치로 ID가 바뀐다.
`audio.resolve_device(id, name, flow)`가 ID → 이름 순으로 해석한다. 스냅샷을 쓰는 코드는
`*_id`만 읽지 말 것.

**핫키 등록은 슬롯별 best-effort.** 하나가 충돌해도 나머지는 살린다. 실패는 삼키지 말고
`on_error`로 보고한다.

## Windows 함정 (전부 실제로 밟은 것)

- **`ctypes.windll` + `ctypes.get_last_error()` = 항상 0.** 반드시
  `ctypes.WinDLL("user32", use_last_error=True)`로 로드할 것. 안 그러면 핫키 충돌(1409)이
  `WinError 0`("작업을 완료했습니다")로 보고된다.
- **NumLock이 꺼지면 NumPad 단축키는 아예 안 뜬다.** 다른 VK가 오기 때문. `numlock_on()`으로
  감지해 알린다. 비-NumLock VK(VK_END 등)를 대신 등록하지 말 것 — Ctrl+Alt+화살표 같은 조합을
  가로챈다. `Ctrl+Alt+.`은 메인 키보드 `.`(VK_OEM_PERIOD)도 등록해서 NumLock과 무관하게 동작.
- **DPI**: `theme.enable_dpi_awareness()`를 **첫 Tk 창 생성 전에** 호출하고
  `theme.init_scale(root)`로 배율을 고정한다. 크기는 논리 px로 적고 `theme.px()`로 환산.
  안 하면 고DPI에서 Windows가 비트맵 확대해 텍스트가 흐려진다(저시력 접근성 직격).
- **tkinter 폰트 크기는 음수가 픽셀, 양수가 포인트.** `theme.font_tuple()`/`mono_tuple()`이
  처리하므로 직접 튜플을 만들지 말 것.
- **`tk.Button`의 `highlightbackground`는 Windows에서 테두리를 안 그린다.** 프레임 래퍼로
  2px 테두리를 직접 만든다 (`settings.py`의 `_button` 참고).
- **창 크기는 화면에 맞춰 클램프.** 화면보다 크면 하단 버튼에 닿을 수 없다.
- **한글 주석이 든 `.ps1`은 UTF-8 BOM으로 저장.** 없으면 PowerShell 5.1이 CP949로 읽어 깨진다.

## 컨벤션

- **버전**: SemVer. `version.py`의 `APP_VERSION` + `VERSION_HISTORY`(버전, 날짜, 요약)를
  기능 추가·수정 때마다 갱신. 버전은 설정 헤더·트레이에 상시 표시, 설정에 업데이트 히스토리 뷰.
- **i18n**: 문자열은 전부 `i18n.py` 사전 키. 하드코딩 금지. **5개 언어 동시 반영 —
  ko / en / ja / zh / vi**(Tiếng Việt). 키 개수가 5개 언어 모두 같아야 한다.
  글꼴 이름·사람/AI 이름·사용자 데이터는 번역 제외.
- **색상 하드코딩 금지.** `theme.py` 토큰만 사용.
- 기존 코드 관례를 먼저 읽고 맞출 것.

## 접근성 (SVIL 공통, 예외 없음)

전체 기준은 `/svil-frontend-design` 스킬이 정본이다. `docs/svil-design-guide.md`는 07-14
사본이라 **최소 폰트가 구판(16px)으로 남아 있다 — 스킬(12px)을 따를 것.**

- 본문 18px 기본, **전체 최소선 12px**(컴팩트 UI·배지 등). 위계는 크기·색으로만 —
  **bold 합성 금지**(단일 굵기 폰트라 뭉개진다).
- 다크 배경 + 고대비. 본문 대비 ≥ 4.5:1, UI ≥ 3:1.
- **색상만으로 상태 구분 금지** — 텍스트 라벨 병행 (`theme.LEVEL_LABEL`: `⚠ 주의` / `✖ 오류` /
  `✓ 완료`).
- 터치 타겟 ≥ 50px(본문 영역), 컴팩트 컨트롤 ≥ 34px. 포커스 링 상시(`#ffd479` 3px).
- **숫자·ID·버전·코드는 Consolas 모노체** (`theme.mono_font()` / `mono_tuple()`).
- `prefers_reduced_motion()` 존중 — 참이면 OSD 페이드를 건너뛴다. 표시 시간을 계산할 때
  페이드를 더하지 말 것(그 경우 표시 시간 = `hold_ms`).

## 작업 방식

- 코드 수정 전 **수정할 파일 목록을 먼저 보고**한다.
- **작업 시작 전 `git -C C:\Projects\audio-hotkeys status`로 main 작업트리의 미커밋 상태를
  확인할 것.** 워크트리에서 일한다고 main이 깨끗하다고 가정하지 말 것 — 2026-07-16에 이틀 묵은
  미커밋 §2.1 작업(i18n·글꼴 8종·화면설정)을 병합 직전에야 발견했다. git이 막아줘서 살았다.
- 검증은 **실제 실행 기준**으로. 이 앱은 단축키·COM·트레이라 단위 테스트만으로는 부족하다.
  합성 키 입력(`keybd_event`)으로 진짜 단축키를 눌러보고, 장치가 실제로 바뀌는지 확인한다.
  테스트로 바꾼 슬롯·기본 장치는 **반드시 원복**한다.
- 표시 시간·크기 같은 건 계산하지 말고 **재본다**.

## 참고

- PRD: `docs/PRD.md` (마일스톤·수용 기준)
- 완료보고서: `docs/reports/`
- 아웃라인 위키: SVIL Main / audio-hotkeys
