# audio-hotkeys — 배포 페이지 스킬 규격 정합

| 항목 | 내용 |
|------|------|
| 작업일 | 2026-07-25 |
| 작업자 | Claude Code (Opus 4.8) |
| 대상 | `site/index.html` (배포 페이지, 앱 버전 변경 없음 — v1.4.4 유지) |
| 브랜치 | `main` |

## 1. 요청

`svil-landing-page`(배포 페이지) 스킬과 현재 배포 페이지가 일치하는지 확인 후 수정.

## 2. 대조 결과

스킬 템플릿에 이후 추가된 **표준 SVIL 푸터 3링크**가 현재 사이트에 누락돼 있었다. 스킬은 이 3링크(협업 문의·블로그·홈페이지)를 SVIL 공통 상수로 명시하고 "지우지 말 것"으로 규정하는데, 사이트 푸터엔 라이선스·제작자 두 줄만 있었다. 그 외 연락처 이메일 불일치도 발견.

## 3. 수정 (`site/index.html` 단일 파일)

| 항목 | 내용 |
|------|------|
| 표준 푸터 3링크 추가 | 협업 문의(`kuroicode@gmail.com`) · 블로그(인블루의 로그 보관소, `ghost-production-0ec2.up.railway.app/`) · 홈페이지(SVIL, `kuroicode-beep.github.io/svil-homepage/`). CSS `.foot-links` + HTML + i18n 키 `foot_contact`/`foot_blog`/`foot_home` 5개 언어 |
| 연락처 이메일 통일 | Links 섹션 `svil.admin@gmail.com` → 표준 `kuroicode@gmail.com` |
| 블로그 URL | Links 카드 끝 슬래시 추가 |
| JS 폴백 | 누락 키·타이틀을 en으로 폴백(`?? I18N.en[...]`) — 템플릿 개선분 반영 |

폰트(`KyoboHandwriting2019`)·localStorage 키(`ah-lang`)는 프로젝트 고유값이라 유지.

## 4. 검증 (로컬 HTTP 실제 렌더)

`python -m http.server --directory site`로 띄워 확인:

- 푸터 3링크 텍스트·href 정상, 연락처 두 곳 모두 `kuroicode@gmail.com`
- **5개 언어(ko/en/ja/zh/vi) i18n 키 개수 전부 일치**, 언어 버튼별 푸터 라벨 전환 확인
- QR 에셋 `assets/toss-qr.png` HTTP 200·575×575 로드 확인 (인라인 lazy `<img>`의 `naturalWidth=0`은 브라우저 pane 미표시로 컴포지팅이 멈춘 헤드리스 한계 — 실제 결함 아님)

## 5. 남은 것

- **gh-pages 배포 미실행.** 후원 QR 등 공개 정보가 포함돼 스킬 규정상 사용자 확인 후에만 배포. `publish_site.ps1` 실행 대기.
