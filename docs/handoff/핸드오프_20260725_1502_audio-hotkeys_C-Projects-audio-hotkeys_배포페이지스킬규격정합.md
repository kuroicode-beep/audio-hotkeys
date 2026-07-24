## 대상
- 프로젝트: audio-hotkeys
- 작업 폴더: C:\Projects\audio-hotkeys
- 세션 시각: 2026-07-25 15:02 (KST)

## 세션 요약
배포 페이지(`site/index.html`)가 `svil-landing-page` 스킬 최신 규격과 일치하는지 대조하고, 누락분을 맞췄다. 앱 로직 변경 없이 배포 페이지 단일 파일만 수정.

## 완료된 작업
- **표준 SVIL 푸터 3링크 추가** (스킬이 "지우지 말 것"으로 규정한 공통 상수인데 사이트에 누락돼 있었음):
  - 협업 문의 → `mailto:kuroicode@gmail.com`
  - 블로그 → `https://ghost-production-0ec2.up.railway.app/` (표기 "인블루의 로그 보관소")
  - 홈페이지 → `https://kuroicode-beep.github.io/svil-homepage/` (표기 "SVIL")
  - CSS `.foot-links` 블록 + footer HTML + i18n 키 `foot_contact`/`foot_blog`/`foot_home` 5개 언어(ko/en/ja/zh/vi) 추가.
- **연락처 이메일 통일**: Links 섹션 "Contact us" 카드 `svil.admin@gmail.com` → 표준 `kuroicode@gmail.com`.
- 블로그 Links 카드 URL 끝 슬래시 보정, JS `applyLang`에 누락 키·타이틀 en 폴백(`?? I18N.en[...]`) 반영(템플릿 개선분).
- 검증(로컬 HTTP 실렌더): 푸터 3링크 텍스트·href 정상, 연락처 두 곳 모두 kuroicode@gmail.com, 5개 언어 i18n 키 개수 전부 일치, 언어별 푸터 라벨 전환 확인, QR 에셋 `assets/toss-qr.png` HTTP 200·575×575.
- 완료보고서: `docs/reports/report_20260725_배포페이지_스킬규격정합_ClaudeCode.md`.
- Outline 작업지시서(`OYR67JpRAi`, id 142b6c11)에 "증분(2026-07-25)" 섹션 append(rev 8).
- 커밋 `097d2b9` (main), push 완료.

## 진행 중 / 미완료 작업
- **gh-pages 배포 미실행.** 후원 QR 등 공개 정보 포함이라 스킬 규정상 사용자 확인 후에만 배포. `publish_site.ps1` 실행 대기 중. 배포 후 라이브 URL(https://kuroicode-beep.github.io/audio-hotkeys/)에서 푸터·에셋 200 재확인 필요.

## 주요 결정사항 / 규칙
- 폰트(`KyoboHandwriting2019`)·localStorage 키(`ah-lang`)는 프로젝트 고유값 → 스킬 템플릿 기본값(LINESeedKR/site-lang)으로 바꾸지 않고 유지.
- 이 작업은 별도 "배포페이지 개선 PRD"의 M1~M3 스프린트와 무관한 규격 정합 증분.

## 참고 정보
- 배포 페이지 개선 작업지시서(미착수 M1~M3): Outline `OYR67JpRAi` (id 142b6c11)
- 배포페이지 개선 PRD: Outline `4VQwpPYfSv`
- 스킬: `svil-landing-page`(페이지 정본), `svil-donation-section`(후원), `svil-frontend-design`(디자인 정본)
- 배포 스크립트: `publish_site.ps1` (UTF-8 BOM)

## 다음 세션 시작 시 할 일
1. (사용자 확인 시) `publish_site.ps1`로 gh-pages 배포 → 라이브 URL 재확인.
2. 여력 되면 배포페이지 개선 작업지시서 M1(P0-1 히어로 비주얼·P0-2 OG 메타·P0-3 다운로드 안심 요소) 착수.
