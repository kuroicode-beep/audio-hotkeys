# audio-hotkeys v1.1.0 — 단축키 오류 디버깅 및 SVIL 디자인 통합

| 항목 | 내용 |
|------|------|
| 작업일 | 2026-07-16 |
| 작업자 | Claude Code (Opus 4.8) |
| 대상 | audio-hotkeys v1.0.0 → **v1.1.0** |
| 브랜치 | `claude/overlay-shortcuts-skill-svil-9fd8a5` → `main` 병합 완료 |

## 1. 요청

> 단축키가 제대로 작동을 안 하는지 오버레이에 에러가 뜬다. 전체적으로 확인하고 디버깅. SVIL 디자인 적용. 마무리.

## 2. 오버레이 에러의 원인 (재현 완료)

사용자가 본 에러의 정체를 실제로 재현해 확정했다.

```
Apply failed: (-2147023728, '요소가 없습니다.', (None, None, None, 0, None))
```

- `%LOCALAPPDATA%\audio-hotkeys\config.json` 슬롯 0의 `input_id`가 **더 이상 존재하지 않는 장치**를 가리키고 있었다(USB 재열거로 ID 변경). 카카오톡 장치 ID 2개도 동일하게 stale.
- `audio.set_default_device()` → `IPolicyConfig.SetDefaultEndpoint()`가 `COMError(-2147023728 = ERROR_NOT_FOUND)`를 던짐.
- v1.0.0의 `apply_snapshot()`은 예외를 그대로 위로 던져 **스냅샷 적용 전체가 중단**. `apply_slot()`이 이를 잡아 원시 HRESULT 문자열을 토스트로 표시하고, **프로필 OSD는 아예 뜨지 않았다**(단축키의 존재 이유가 사라짐).
- 실제로는 출력 장치·볼륨은 적용 가능한 상태였는데도 첫 실패에서 전부 중단됐다.

## 3. 함께 발견한 결함

조사 중 별도로 확인된 문제들 (모두 재현·수정·검증 완료).

| # | 결함 | 영향 | 근거 |
|---|------|------|------|
| 1 | `hotkeys._run()`이 all-or-nothing 등록. 예외가 `finally`의 `_ready.set()`에 삼켜져 `start()`는 정상 반환 | 슬롯 하나만 충돌해도 **10개 전부 무음 실패**, 앱은 "실행 중" 토스트를 띄움 | 코드 경로 분석 + 재현 |
| 2 | `ctypes.windll` + `ctypes.get_last_error()` 조합 | `get_last_error()`가 **항상 0** → 충돌을 `WinError 0`("작업을 완료했습니다")로 보고 | 실측: `get_last_error()=0` vs 실제 `GetLastError()=1409` |
| 3 | `GetMessageW`가 `-1`(오류) 반환 시 `!= 0` 검사라 무한 루프 | 오류 시 CPU 점유 | 코드 분석 |
| 4 | NumLock 감지 없음 | **NumLock OFF면 NumPad가 다른 VK를 보내 핫키가 아예 안 뜸.** 측정 시점 사용자 NumLock = OFF | 실측 |
| 5 | DPI 비인식 프로세스 | 실제 모니터 2560×1440 @200%. Windows가 2배 비트맵 확대 → **텍스트 흐림**. 저시력 접근성에 직접 타격 | 실측: Tk는 1280×720 보고, ImageGrab은 2560×1440 |
| 6 | `FONT_SIZE_PX`(18)를 양수로 폰트 튜플에 전달 | tkinter가 **pt로 해석** → 의도 18px이 실제 24px | 코드 분석 |
| 7 | 설정 창 `geometry("860x860")` | 화면(논리 720)보다 세로가 커서 **하단 액션 버튼에 접근 불가** | 실측 |

## 4. 수정 내용

### 4.1 스냅샷 부분 실패 허용 (핵심)

- `config`: 모든 `*_id` 옆에 `*_name`을 함께 저장 (PRD **M3** 항목).
- `audio.resolve_device(id, name, flow)`: ID → 실패 시 **이름으로 재매칭** → 실패 시 그 필드만 건너뜀.
- `audio.apply_snapshot()`이 `ApplyResult(summary, warnings)` 반환. **각 필드를 독립 적용**하며 예외를 위로 던지지 않음.
- `app.apply_slot()`: **프로필 OSD는 항상 표시**, 경고 상세는 별도 토스트로 분리.
- 구버전 config 하위호환 유지(`*_name` 없으면 빈 문자열, 한 번 다시 저장하면 자동 복구).

### 4.2 핫키

- 슬롯별 개별 등록 — 하나가 충돌해도 나머지 9개 유지.
- `WinDLL(..., use_last_error=True)`로 **실제 Win32 오류** 확보. 1409는 "다른 앱이 같은 조합을 이미 사용 중"으로 번역.
- `GetMessageW == -1` 처리.
- `numlock_on()` 감지 + 시작 토스트 경고. `status_warning()`으로 실패 슬롯·사유 요약.

### 4.3 SVIL 디자인

- `theme.py`에 토큰 중앙화(하드코딩 금지), 상태는 **색 + 텍스트 라벨 병행**(`⚠ 주의` / `✖ 오류` / `✓ 완료`).
- 교보손글씨2019 본문, **숫자·ID·버전은 Consolas**, bold 합성 없음.
- **per-monitor-v2 DPI 인식** + `theme.px()` 환산 → 고해상도에서 선명.
- 설정 창을 화면 크기에 맞춰 클램프.
- 버전 상시 표시(헤더·트레이) + **업데이트 히스토리** 뷰.

## 5. 07-14 미커밋 작업 통합 (중요)

배포 직전 `main` 작업트리에서 **2026-07-14자 커밋되지 않은 작업**을 발견했다. `git merge`가 자동 중단되어 유실은 없었다.

- 내용: `i18n.py`(다국어 5종), `prefs.py`, `theme.py`(글꼴 8종 카탈로그), `win_shell.py`(§4.2 uxtheme 다크), `settings.py` 화면 설정 UI — 즉 **SVIL 가이드 §2.1 전체**.
- 양쪽이 같은 UI 파일(`app/config/settings/tray/theme`)을 각각 재작성한 상태였다.
- **소장님 결정: 07-14 UI를 베이스로 유지하고 v1.1.0 수정을 얹는다.**
- 처리: 07-14 작업을 먼저 `a092b2d`로 커밋해 보존 → 병합 → UI 5개 파일은 07-14 버전 채택 후 수정 이식.
- 버그 수정 핵심(`hotkeys.py`·`audio.py`·`kakao.py`)은 07-14가 건드리지 않아 **충돌 없이 그대로 반영**됐다.
- 07-14 쪽에 없던 DPI 인식·pt/px 오류·창 클램프도 함께 고쳐 얹었다.
- 새 문구는 **5개 언어 전부**에 추가(각 49키로 균일 확인).

## 6. 검증 (실제 실행 기준)

| 항목 | 방법 | 결과 |
|------|------|------|
| 오버레이 에러 재현 | stale ID로 `set_default_device()` 직접 호출 | `COMError(-2147023728)` 재현 ✅ |
| 수정 후 동일 스냅샷 | 실제 슬롯 0에 `apply_snapshot()` | **예외 없음.** 출력·볼륨 적용 + 경고 1건 ✅ |
| 이름 재매칭 | stale ID + 유효 이름 | live ID로 재연결 ✅ |
| 구버전 config | `*_name` 없는 dict 정규화 | 정상 ✅ |
| 핫키 등록 | 실행 중 앱 상대로 외부 프로브 | 10/10 점유(1409) ✅ |
| **실제 키 입력** | `Ctrl+Alt+NumPad0` 합성 후 화면 캡처 | **"기본 환경" OSD 표시 + ⚠ 주의 토스트** ✅ |
| Win32 오류 문구 | `get_last_error()` 비교 | 0 → 1409 실측 개선 ✅ |
| 통합 후 재검증 | 병합본으로 전체 재실행 | 전 항목 통과 ✅ |
| 빌드 exe | `dist\audio-hotkeys.exe` 실행 후 프로브 | 10/10 핫키 점유 ✅ |

## 7. 산출물

- `dist\audio-hotkeys.exe` (21.9 MB, 2026-07-16 02:24)
- 바탕화면 바로가기: `C:\Users\kuroi\OneDrive\Desktop\audio-hotkeys.lnk` (검증됨)
- 시작프로그램: `%APPDATA%\...\Startup\audio-hotkeys.lnk` (검증됨 — 트레이 상주형이라 등록 대상)
- 신규 스크립트: `install_desktop_shortcut.ps1` (UTF-8 BOM 저장)

## 8. 남은 것 / 사용자 조치 필요

1. **슬롯 0을 한 번 다시 저장해 주세요.** v1.0.0에 저장된 스냅샷에는 장치 이름이 없어 자동 재매칭이 불가합니다. 설정에서 입력 장치·카카오톡 장치를 다시 고르고 **[슬롯 저장]** 하면 이후로는 ID가 바뀌어도 자동 복구됩니다.
2. **NumLock을 켜 두세요.** 확인 시점에 꺼져 있었고, 꺼진 상태로는 NumPad 단축키가 동작하지 않습니다(앱이 시작 시 경고합니다).
3. 백로그: 단일 인스턴스 가드(M1), 슬롯별 토스트 위치·시간(M2).
4. `build.ps1`은 PowerShell 5.1에서 pip의 stderr를 오류로 취급해 중단됩니다(`$ErrorActionPreference="Stop"` + NativeCommandError). 이번엔 우회 실행했고, 스크립트 자체 보완은 백로그로 둡니다.

## 9. 참고

- PRD: [docs/PRD.md](../PRD.md) — M3·M4 완료 반영, 부분 실패 규칙 추가
- README: 트러블슈팅 섹션 신설(NumLock/충돌/연결 해제)
- 커밋: `25854a2`(수정) · `a092b2d`(07-14 보존) · `ebb3f53`(통합) · `a485249`(히스토리)
