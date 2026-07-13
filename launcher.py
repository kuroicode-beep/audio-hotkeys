"""PyInstaller / direct entrypoint (absolute import, no package-relative)."""

from audio_hotkeys.app import main

if __name__ == "__main__":
    raise SystemExit(main())
