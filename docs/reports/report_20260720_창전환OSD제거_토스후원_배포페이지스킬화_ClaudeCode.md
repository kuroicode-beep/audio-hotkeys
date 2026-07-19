# audio-hotkeys — 창 전환 OSD 제거, 토스 후원, 배포 페이지 스킬화

| 항목 | 내용 |
|------|------|
| 작업일 | 2026-07-19 ~ 2026-07-20 |
| 작업자 | Claude Code (Fable 5 / Sonnet 5) |
| 대상 | audio-hotkeys v1.4.3 → **v1.4.4** |
| 브랜치 | `claude/remove-window-switch-osd-1cbf69` → `main` 병합 완료 (squash, `9efada9`) |
| 공개 | 사이트 https://kuroicode-beep.github.io/audio-hotkeys/ · [릴리스 v1.4.4](https://github.com/kuroicode-beep/audio-hotkeys/releases/tag/v1.4.4) · [PR #1](https://github.com/kuroicode-beep/audio-hotkeys/pull/1) |

## 1. 요청 흐름

이전 세션이 남긴 인수인계문("창 전환 OSD 제거")으로 시작해, 대화 중 후원 방식 문의 → 후원 섹션 제작 → 후원 스킬 등록 → 배포 페이지 자체를 스킬로 일반화 → PRD 작성 → 머지 → 정리·마무리까지 이어졌다. 다음 세션이 참고할 수 있도록 각 갈래를 순서대로 기록한다.

## 2. 창 전환(Alt+Tab) OSD 제거

### 2.1 발견한 문제 — main에 깨진 미커밋 작업

작업 시작 전 `git -C C:\Projects\audio-hotkeys status`로 확인한 결과, main 작업트리에 **이미 같은 리팩터의 절반**(`app.py`·`tray.py`는 온전히 제거, `settings.py`는 `__init__` 파라미터만 지우고 `_prefs_body`의 체크박스 블록은 안 지워 `AttributeError`로 깨진 중간 상태)이 미커밋으로 남아 있었다. CLAUDE.md의 "main이 클린하다고 가정하지 말 것" 규칙이 실제로 발동한 경우. 사용자 확인 후 이 워크트리에서 전체를 새로 처리하고 main의 깨진 잔재는 폐기했다.

### 2.2 제거 범위

인수인계문은 `config.py`·`settings.py`·`foreground.py`·`i18n.py`·`version.py`만 언급했지만, 실제로는 `app.py`·`tray.py`도 OSD 관련 코드(`ForegroundWatcher` 배선, `show_switch_osd`, 트레이 토글 메뉴)를 갖고 있어 함께 정리했다.

- `foreground.py` 삭제(유일한 소비자가 사라짐)
- `app.py`/`tray.py`/`settings.py`/`config.py`에서 창 전환 OSD 관련 코드 전부 제거
- `i18n.py`: 5개 언어에서 `on`/`off`/`window_switch_osd*` 키 정리 (언어별 57개로 일치 확인)
- `version.py`: v1.4.4 + 히스토리

### 2.3 검증

소스 임포트·헤드리스 SettingsWindow 빌드·소스 앱 실행(크래시 없음), PyInstaller 빌드 성공 후 프로즌 exe 실행까지 확인했다. 프로필 OSD(오디오 전환 시 표시)는 이번 제거 대상이 아니며 그대로 유지된다.

## 3. 토스 QR 후원 섹션

### 3.1 방식 선정 과정

토스아이디(toss.me) 송금 링크는 서비스 종료 확인(공식 종료 공지). Buy Me a Coffee는 Stripe 정산이라 **한국 미지원**으로 배제. Ko-fi/PayPal.me도 검토했으나 사용자의 PayPal 계정이 재가입(여권/국제면허 필요)·기존 계정 비번 재설정(전화번호 변경) 둘 다 막힌 상태라 **무기한 보류**. 최종적으로 토스 QR(계좌 텍스트 노출 없이 이미지만)로 결정.

### 3.2 구현

`site/index.html`에 SVIL 고대비 다크 카드 + 5개 언어 i18n(`support_*` 4키)으로 후원 섹션 추가. QR은 사용자가 보낸 폰 스크린샷(`C:\downloads\qr.png`, 904×2316)에서 자동 크롭 스크립트로 메인 QR만(파란 테두리·썸네일 제외) 잘라 `site/assets/toss-qr.png`(575×575)로 저장. 로컬 HTTP 서버로 실렌더 검증(이미지 200, `naturalWidth` 로드 확인) 후 gh-pages 배포, 라이브에서 재확인.

## 4. 재사용 스킬 2종 등록

작업 도중 "다음에도 재사용 가능하게 스킬로 만들어달라"는 요청에 따라 사용자 홈(`~/.claude/skills/`)에 등록.

- **`svil-donation-section`**: 후원 QR 섹션만 붙이는 절차. 표준 QR을 스킬 자체에 보관(`assets/toss-qr.png`)해 다음 프로젝트는 복사만 하면 됨. 검증된 크롭 코드(파랑 제외, 가장 긴 흰 밴드로 썸네일 QR 회피) 포함.
- **`svil-landing-page`**: 이번 배포 페이지 스펙 전체(자체 완결형 단일 파일·SVIL 다크·영어 디폴트 5개 언어 i18n·후원 섹션·gh-pages 배포)를 일반화한 템플릿(`templates/index.html`, `templates/publish_site.ps1`). 로컬 HTTP로 i18n 전환·콘솔 에러 0 검증 완료. `svil-donation-section`(부품)과 `svil-frontend-design`(디자인 정본)을 내장·참조하는 조립 지점임을 두 스킬 모두에 명시했다.

## 5. 배포 페이지 디자인 개선 PRD

`docs/PRD_20260720_배포페이지_디자인개선_ClaudeCode.md`. 현재 페이지의 약점 3가지(히어로에 제품 비주얼 없음·OG/Twitter 공유 메타 없음·다운로드 안심 요소 없음)를 진단하고 P0/P1/P2 요구사항·마일스톤(M1→M2→M3, M3에서 `svil-landing-page` 스킬 역반영)을 정리했다. **이번 세션에서 구현은 하지 않았고 문서만 작성했다** — 다음 착수 대상.

## 6. 머지 및 정리

- PR #1을 squash merge (`9efada9`)로 main에 반영.
- 로컬 main이 origin에 **한 번도 push되지 않은 v1.4.2/v1.4.3 커밋**을 갖고 있어 머지 후 `ahead 2, behind 1`로 갈라짐 — diff로 해당 코드가 squash 커밋에 전부 흡수됐음을 확인한 뒤(유실 없음) origin에 맞춰 재설정.
- 워크트리·브랜치 정리: 로컬/원격 feature 브랜치 삭제. **워크트리 디렉터리 자체는 이 세션 안에서 삭제 불가** — 세션의 기본 작업 디렉터리로 하니스가 계속 물고 있어(폴더가 비어 있는데도 "다른 프로세스가 사용 중" 오류) `git worktree remove`/`Remove-Item` 모두 실패. `.git/worktrees/` 메타데이터는 제거해 git 레벨에서는 완전히 unregister됨. **다음에 Claude Code로 이 폴더를 열지 않을 때, 사용자가 직접 `C:\Projects\audio-hotkeys\.claude\worktrees\remove-window-switch-osd-1cbf69` 폴더를 지우면 된다** (빈 폴더, 데이터 없음).
- GitHub Release가 v1.4.1에 멈춰 있어(사이트 다운로드 버튼이 옛 빌드를 가리키는 상태) main 기준으로 재빌드해 **v1.4.4 릴리스 게시**, 다운로드 링크 실제 200 응답 확인.
- 시작프로그램에 이미 등록된 바로가기(`audio-hotkeys.lnk`)는 이전 세션 산물이라 그대로 두고 건드리지 않음 — 다만 그 바로가기가 가리키는 `C:\Projects\audio-hotkeys\dist\audio-hotkeys.exe`는 세션 시작 시점부터 **이미 실행 중이던 v1.4.1-era 빌드 그대로**다(사용자의 라이브 오디오 라우팅을 건드리지 않기 위해 강제 종료·교체하지 않음). **다음에 편한 시점에 앱을 재시작하면 시작프로그램이 다시 켜질 때 최신 코드를 반영하려면 `dist\audio-hotkeys.exe`를 v1.4.4로 갱신해야 한다** — 원하면 `.\build.ps1`(또는 `python -m PyInstaller --noconfirm audio-hotkeys.spec`) 한 번 실행 후 재시작 권장.

## 7. 남은 것 / 다음 세션 참고

- PRD 기반 배포 페이지 개선(M1: 히어로 비주얼·OG메타·다운로드 안심 요소) 미착수.
- 로컬 `dist\audio-hotkeys.exe` 갱신 + 앱 재시작 (사용자 편한 시점에).
- 후원 QR 실사용 스캔 확인은 사용자에게 요청했으나 이 세션 안에서 결과 확인은 못 함.
- `svil-donation-section`/`svil-landing-page` 스킬은 이번이 첫 실사용 — 다음 프로젝트에 적용하며 다듬을 것.
