**SVIL 표준 디자인 스크립트** — 모든 SVIL 계열 프론트엔드(웹·데스크톱·모바일)의 공통 디자인·접근성 표준.

버전 1.1 · 2026-07-14 · 작성 Claude Code 출처: SVIL 표준 디자인 스크립트(`/design`) · TXTDiary `App.css` · TXTAIMemory v0.9.1 실적용 · inblue_money v1.9.1 실적용 · TXT 패밀리 디자인 가이드 v1.2(`C:\Downloads`)

변경 이력:

* v1.0 (2026-07-14): 최초 작성 (토큰·타이포·컴포넌트·접근성·안티패턴·프레임워크별 적용)
* v1.1 (2026-07-14): TXTAIMemory v0.9.x 실적용 규칙 병합 — 버튼 대비 강화 토큰(accent-strong/accent-max/border-strong), 화면 설정 표준(글꼴 8종·글자 크기 3단계·다국어 5종), 뒤로가기 단축키, 데스크톱 셸(트레이 다크) 규칙


---

## 0. 원칙

* 다크 기본, 고대비, **저시력 접근성 최우선**.
* 색상 하드코딩 금지 — 토큰(CSS 변수 / 상수)만 사용.
* 위계는 **굵기가 아니라 크기·색**으로 (교보손글씨는 단일 굵기).
* 숫자·시간·ID·코드는 **모노체(Consolas)** 예외.
* 컴포넌트를 바꾸면 이 가이드와 토큰도 갱신한다.

## 1. 색상 토큰

| 토큰  | 값   | 용도  |
|-----|-----|-----|
| bg  | `#0d0d12` | 최하단 배경 |
| surface | `#16161d` | 카드·패널 |
| surface-2 | `#1f1f2a` | 입력·버튼 표면 |
| border | `#3a3a48` | 경계선 (⚠ 버튼 테두리엔 금지 — §3.1) |
| border-strong | `#6b6b82` | **버튼 테두리** (배경 대비 ≥3:1, WCAG 1.4.11) |
| text | `#f5f5f7` | 본문 (대비 ≈ 15:1) |
| text-sub | `#c9c9d4` | 보조 텍스트 |
| accent | `#7ec8ff` | 강조·수입·선택·링크 |
| accent-strong | `#b3ddff` | **주 버튼 배경**·제목 하이라이트 (순검정과 ≈15:1) |
| accent-max | `#d6ecff` | 주 버튼 hover (대비 상승 방향) |
| positive | `#7ee2a8` | 긍정·증가 |
| warning | `#ffd479` | 주의  |
| negative | `#ff9b9b` | 지출·초과·오류 |
| focus | `#ffd479` | 포커스 링 |

> 앰버(`#f7c04a`) 계열의 옛 `svil-ai-work` 토큰은 현행 표준이 아님. 현행 강조색은 `accent #7ec8ff`.

## 2. 타이포그래피

* 폰트: **KyoboHandwriting2019** → Pretendard → Malgun Gothic. **로컬 번들 우선**(CDN 의존 금지 — 오프라인 동일 렌더).
* 기준 **18px**, line-height **1.8**, letter-spacing 0.02em, `word-break: keep-all`.
* 위계는 **크기**로: h1 2.0\~2.2rem · h2 1.55\~1.7rem · h3 1.25\~1.35rem.
* **bold 합성 금지**: 교보손글씨는 단일 굵기라 `font-weight:bold`가 faux-bold로 뭉개짐 → 강조는 **크기 + 색(accent)**.
* **숫자·타임스탬프·ID·코드·버전은 Consolas 모노체**: 손글씨는 숫자 판독·정렬이 흐림. `font-family:"Consolas", monospace` (한글 폴백 유지).

## 2.1 화면 설정 표준 (글꼴·크기·언어 — 사용자 설정)

설정 화면에 아래 3종을 제공한다. (TXTAIMemory v0.9.0에서 확립, 테더 패턴 계승)

**글꼴 선택 — 8종 (테더 리스트 기반, 전부 로컬 번들 확보분만)**

| id  | 표시명 | font-family | 소스  |
|-----|-----|-------------|-----|
| kyobo-handwriting-2019 | 교보손글씨2019 **(기본)** | `'KyoboHandwriting2019'` | noonfonts/fonts-archive |
| gothic | 고딕  | `'Pretendard', 'Malgun Gothic'` | 시스템(파일 불요) |
| nanum-gothic | 나눔고딕 | `'NanumGothic'` | fonts-archive |
| line-seed | 라인시드체 | `'LINE Seed Sans KR'` | wizfile (woff2) |
| gowun-dodum | 고운돋움체 | `'Gowun Dodum'` | noonfonts |
| cafe24-dongdong | 카페24동동체 | `'Cafe24Dongdong'` | fonts-archive |
| tmoney-round | 티머니둥근바람체 | `'TmoneyRoundWind'` | fonts-archive |
| recipe-korea | 레코체 | `'Recipekorea'` | noonfonts |

* 메이플스토리체·나눔스퀘어라운드는 신뢰 가능한 배포 소스 부재로 **제외**(깨진 옵션 금지).
* 적용: `--app-font-family` CSS 변수 + localStorage 영속, 렌더 전 부트스트랩(깜빡임 방지). `body { font-family: var(--app-font-family, <기본 스택>) }`
* 글꼴 이름은 고유명사 — 번역하지 않는다. 설정 버튼은 해당 글꼴로 미리보기 렌더.

**글자 크기 — 3단계**

| 단계  | 값   | 비고  |
|-----|-----|-----|
| 작음 (S) | 16px | SVIL 최소선 — 이 밑의 옵션은 만들지 않는다 |
| 보통 (M) | 18px | 기본값 |
| 큼 (L) | 20px |     |

* root(`html`) font-size 지정 + rem 기반 → 전 화면 비례 확대. 터치 타겟(50px)·패딩은 px 고정으로 유지.

**다국어 — 5종 (순서 고정)**: 한국어(기본) · English · 日本語 · 中文 · Tiếng Việt

* 모든 UI 문자열 사전 키로 추출(하드코딩 금지), `{변수}` 치환 템플릿(문자열 연결 금지 — 언어별 어순).
* `document.documentElement.lang` 동기화(스크린리더 발음), localStorage 영속.
* 번역 제외: 글꼴 이름·AI/사람 이름(정체성)·사용자 데이터. 백엔드 저장 한국어 상수는 알려진 값만 매핑, 모르는 값은 원문 통과.
* 라이브러리 불요 — 사전 객체 + 치환 함수 + 구독 훅으로 충분 (레퍼런스: TXTAIMemory `ui/src/lib/i18n.ts`).

## 3. 컴포넌트 규격

* **버튼·입력**: min-height 50px, radius 12px, border 2px. focus 3px `#ffd479` 아웃라인.
* **카드**: surface 배경, border 1px, radius 16px, padding 22–24.
* **배지**: pill(radius 999px), 1.5px currentColor, **상태색 + 텍스트 라벨 병행**.
* **탭**: 하단 언더라인 3px accent로 선택 표시 (bold 금지).
* **진행바**: radius 999px.

### 3.1 버튼 대비 규칙 (강화판 — TXTAIMemory v0.9.0 확립)

| 대상  | 조합  | 대비  | 기준  |
|-----|-----|-----|-----|
| **주 버튼** | `accent-strong #b3ddff` 배경 + **#000 순검정** 텍스트 | ≈15:1 | 최대 대비 — AAA(7:1) 2배 이상 |
| 일반 버튼 텍스트 | `text` on `surface-2` | ≈14:1 | AAA |
| **버튼 테두리** | `border-strong #6b6b82` | ≥3:1 | WCAG 1.4.11 — 기존 `border #3a3a48`는 1.5:1로 **버튼엔 금지** |
| hover | 주 버튼 `accent-max`, 일반 버튼 accent 테두리+accent-strong 글자 | —   | **대비가 오르는 방향으로만** 변화 |

* 주 버튼 배경으로 어두운 accent(`#7ec8ff`+`#0d0d12`, ≈10:1)를 쓰지 않는다 — 밝은 배경+순검정이 더 높다.

## 4. 접근성 (필수)

* WCAG: 본문 대비 ≥ **4.5:1**, UI 요소 ≥ **3:1**.
* **색상만으로 상태 구분 금지** — 텍스트 라벨 병행 (`⚠ 초과`, `+`/`-`, `남음`).
* 최소 폰트 16px(본문 18px 권장), 터치·클릭 타겟 ≥ **50px**.
* 포커스 링 항상 노출(`#ffd479` 3px), `prefers-reduced-motion` 존중.

## 4.1 키보드 단축키 (뒤로가기 — 전 앱 공통)

| 입력  | 동작  |
|-----|-----|
| `Alt + ←` / `Alt + →` | 뒤로 / 앞으로 |
| `Backspace` | 뒤로 — **입력 중 절대 발동 금지** |
| 마우스 뒤로/앞으로 버튼(button 3/4) | 뒤로 / 앞으로 |

* **입력 가드 필수**: 포커스가 `input`/`textarea`/`select`/`contentEditable`이면 Backspace 무시(글자 지우기 충돌 = 데이터 손실급 버그로 취급).
* 구현: window 레벨 keydown/mouseup + 라우터 `navigate(-1/1)` (레퍼런스: TXTAIMemory `ui/src/App.tsx`).

## 4.2 데스크톱 셸 (트레이·네이티브 메뉴)

* **트레이 우클릭 메뉴도 반드시 다크** — 앱만 다크이고 트레이 메뉴가 흰색이면 가족이 아니다.
* Windows 트레이 메뉴는 CSS가 아니라 OS 테마를 따름 → 프로세스 단위 강제: `uxtheme.dll` ordinal **135** `SetPreferredAppMode(2 /*ForceDark*/)` + ordinal **136** `FlushMenuThemes()` 를 트레이 생성 전 호출(Notepad++ 검증 기법, 실패 무해). (레퍼런스: TXTAIMemory `ui/src-tauri/src/lib.rs`)
* 창 자체도 OS 테마 무관 다크 고정: Tauri `windows[].theme: "Dark"` (타이틀바 포함).

## 5. 안티패턴

* `font-weight`로 강조 ✗ → 크기·색으로.
* 숫자를 손글씨로 ✗ → Consolas 모노체.
* 색상 하드코딩 ✗ → 토큰만.
* CDN 폰트 의존 ✗ → 로컬 번들.
* 버튼 테두리에 `border` 토큰 ✗ → `border-strong`(3:1 미달 방지).
* 입력 가드 없는 Backspace 뒤로가기 ✗ → 데이터 손실급 버그.
* 앰버 옛 토큰과 혼동 ✗.

## 6. 프레임워크별 적용

* **웹(React/Vite)**: `App.css`/`styles.css` `@font-face` 로컬 번들 + `:root` CSS 변수. 클래스·변수명 유지해 컴포넌트 무변경.
* **PySide6/Qt**: QSS에 토큰 주입. 숫자 열 `QFont("Consolas")` setFont, `QDateEdit`/`QSpinBox`에 Consolas 폴백. bold 대신 색으로 강조.
* **Flutter**: `ThemeData` 다크 + 동일 팔레트, 숫자 `TextStyle` 모노.
* **Tauri**: 창 `theme: "Dark"`, 트레이는 §4.2, 폰트는 `public/fonts/` 번들.

## 7. 레퍼런스 구현

* **TXTAIMemory v0.9.1** (React+Tauri) — `ui/src/styles.css`(토큰·컴포넌트), `ui/src/lib/prefs.ts`(글꼴·크기), `ui/src/lib/i18n.ts`(다국어 5종), `ui/src/App.tsx`(단축키), `ui/src-tauri/src/lib.rs`(트레이 다크). **가장 완전한 기준 구현.**
* **inblue_money v1.9.1** (PySide6) — `main.py`의 `DARK_QSS`, `MONO_CSS`, `mono_font()`, 색상 상수 `COL_*`.
* **TXTDiary** (React) — `App.css`.
* 문서: TXT 패밀리 디자인 가이드 v1.2 — `C:\Downloads\디자인가이드_20260713_TXT패밀리_ClaudeCode.md` (+ Vault `03_PRJ`)
* 스킬: `/svil-frontend-design` · 메모리: `design-guide-default`, `txt-series-design-tokens`.
