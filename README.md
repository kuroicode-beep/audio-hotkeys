# audio-hotkeys

Windows tray app for **Ctrl+Alt+NumPad 0–9** audio snapshots. Current version: **v1.1.0**
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
| Tray left-click | Open settings |
| Tray right-click | Dark menu (apply slots / settings / quit) |

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
나머지를 적용합니다. 설정에서 장치를 다시 고르고 **슬롯 저장**을 누르면 이후로는 자동 복구됩니다.
(v1.0.0에서 저장한 스냅샷에는 이름이 없으므로 한 번은 다시 저장해 주셔야 합니다.)
