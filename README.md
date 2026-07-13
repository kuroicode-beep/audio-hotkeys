# audio-hotkeys

Windows tray app for **Ctrl+Alt+NumPad 0–9** audio snapshots.

Each slot can store:

- output device
- input device
- output volume
- input volume

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

## Usage

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+NumPad 0` … `9` | Apply snapshot slot 0–9 |
| Tray left-click | Open settings |
| Tray right-click | Dark menu (apply slots / settings / quit) |

In settings:

1. Pick a slot
2. Choose output/input device and volumes from lists (`(unchanged)` skips that field)
3. **Capture current** fills from the live defaults
4. **Save slot** / **Apply now**

Config file: `%LOCALAPPDATA%\audio-hotkeys\config.json`

## Notes

- Setting the default endpoint uses the Windows PolicyConfig COM API.
- Volume is applied to the **current default** device after switching.
- Keep NumLock on for the keypad hotkeys.
