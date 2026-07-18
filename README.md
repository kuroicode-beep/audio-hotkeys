# audio-hotkeys

**[웹사이트](https://kuroicode-beep.github.io/audio-hotkeys/)** · **[최신 버전 다운로드](https://github.com/kuroicode-beep/audio-hotkeys/releases/latest/download/audio-hotkeys.exe)** · [릴리스](https://github.com/kuroicode-beep/audio-hotkeys/releases)

Windows tray app for **Ctrl+Alt+NumPad 0–9** audio snapshots. Current version: **v1.4.3**
(the version is shown in the settings header; **업데이트 히스토리** there lists every release).

Each slot can store:

- system output / input device
- system output / input volume
- **KakaoTalk-only** output / input device
- **KakaoTalk-only** output / input volume (Windows app mixer has one volume; output volume is preferred)

KakaoTalk per-app routing uses bundled [SoundVolumeCommandLine (svcl)](https://www.nirsoft.net/utils/sound_volume_command_line.html). KakaoTalk must be running when the snapshot is applied.

Hotkeys are fixed. Configure devices/volumes in the dark settings window.

## Requirements

- Windows 10/11
- Python 3.11+

## Install

```powershell
cd C:\Projects\audio-hotkeys
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe -m audio_hotkeys
```

Or double-click `run.bat`.

## Build

```powershell
.\build.ps1
```

Output: `dist\audio-hotkeys.exe`

## Windows Startup

```powershell
.\install_startup.ps1          # register (prefers dist\audio-hotkeys.exe)
.\install_startup.ps1 -Unregister
```

## Usage

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+NumPad 0` … `9` | Apply snapshot slot 0–9 |
| `Ctrl+Alt+Shift+NumPad 0` … `9` | **Save** the live audio state into slot 0–9 |
| `Ctrl+Alt+.` | **Toggle** back to the previously applied slot |
| Tray left-click | Open settings |
| Tray right-click | Dark menu (apply slots / window-switch overlay / settings / quit) |

**창 전환 표시 (v1.4.0)** — 트레이 우클릭 메뉴 또는 **설정 창의 화면 설정**에서 켜면, 창을 바꿀
때마다(Alt+Tab·클릭·작업표시줄) 화면 중앙에 새 창 이름이 큰 글씨로 잠깐 뜬다. 저시력 사용자가
"지금 어느 창인지"를 놓치지 않도록. Alt+Tab은 Windows 예약 키라 후킹할 수 없어, 포그라운드 창
변경(`SetWinEventHook`)을 감지한다 — 그래서 클릭 전환에도 뜬다. 기본은 꺼짐이고, 켠 상태는 저장된다.

**직전 슬롯 토글 (v1.3.0)** — `Ctrl+Alt+.`을 누르면 마지막으로 적용한 슬롯과 그 직전 슬롯을
한 키로 왕복합니다 (헤드셋↔스피커 등). NumPad `.`와 메인 키보드 `.` 둘 다 동작하며, 메인 키보드
쪽은 **NumLock이 꺼져 있어도** 됩니다. 기록은 메모리에만 두므로 앱을 새로 켠 직후에는 슬롯을
두 개 적용한 뒤부터 동작합니다.

**빠른 저장 (v1.2.0)** — 장치·볼륨을 원하는 대로 맞춰 둔 뒤 `Ctrl+Alt+Shift+NumPad N`을 누르면
설정 창을 열지 않고 그대로 슬롯 N에 저장됩니다. 슬롯 이름은 유지되고, 장치 **이름**까지 함께
저장되므로 이후 장치 ID가 바뀌어도 자동으로 재연결됩니다. KakaoTalk이 실행 중이면 함께 저장하고,
꺼져 있으면 그 슬롯의 기존 KakaoTalk 설정을 지우지 않고 그대로 둡니다.

In settings:

1. Pick a slot
2. Choose output/input devices from lists (`(unchanged)` skips that field)
3. Use volume sliders (check **Set** to apply; unchecked = unchanged)
4. **Capture current** fills from the live defaults
5. **Save slot** / **Apply now**

Config file: `%LOCALAPPDATA%\audio-hotkeys\config.json`

## Notes

- Setting the default endpoint uses the Windows PolicyConfig COM API.
- Volume is applied to the **current default** device after switching.
- Keep NumLock on for the keypad hotkeys.

## Troubleshooting

**단축키를 눌렀는데 아무 일도 없어요**

1. **NumLock이 켜져 있나요?** NumLock이 꺼지면 NumPad 키가 다른 키코드를 보내 핫키가 뜨지 않습니다.
   시작 시 꺼져 있으면 앱이 토스트로 알려 줍니다.
2. **다른 앱이 같은 조합을 선점했나요?** 실패한 슬롯 번호와 이유가 시작 토스트에 표시됩니다.
   슬롯 하나가 실패해도 나머지 아홉 개는 정상 등록됩니다.
3. **audio-hotkeys가 두 번 떠 있나요?** 나중에 뜬 쪽은 핫키를 잡지 못합니다. 트레이 아이콘이
   두 개인지 확인하세요. (PyInstaller onefile은 부트로더 부모/자식 2개 프로세스가 정상입니다.)

**"연결 해제됨" 경고가 떠요**

USB 재연결·드라이버 재설치로 장치 ID가 바뀌면 저장해 둔 ID가 무효가 됩니다. v1.1.0부터는
스냅샷이 장치 **이름**도 함께 저장해 자동으로 재연결하고, 이름까지 못 찾으면 그 필드만 건너뛴 뒤
나머지를 적용합니다.

v1.0.0에서 저장한 스냅샷에는 이름이 없으므로 한 번은 다시 저장해야 합니다. 가장 빠른 방법은
**원하는 장치·볼륨으로 맞춘 뒤 `Ctrl+Alt+Shift+NumPad N`** 을 누르는 것입니다 — 이름까지 함께
저장되어 이후로는 자동 복구됩니다. (설정 창에서 장치를 고르고 **슬롯 저장**을 눌러도 됩니다.)
