# Olympus Desktop (One-Click)

A native desktop wrapper that:

- Loads `.env` (or `.env.dev`) from repo root
- Launches **FastAPI** (`olympus_api.main:app`) and **Worker** (`olympus_worker.main`)
- Shows a small UI with Start/Stop/Status and quick links
- Packages into a double-clickable app via **PyInstaller**

## Prereqs

- Python 3.10+ (3.11 recommended)
- Your repo layout as shipped (`apps/api`, `apps/worker`, `packages/*`, `.env.dev`/`.env`)
- Platform toolchain to run PyInstaller

## Dev run

```bash
cd desktop
python -m pip install -U pip wheel
python -m pip install -e .
python app/main.py
```

## Build (native app)

```bash
python -m pip install pyinstaller
pyinstaller --clean --noconfirm desktop/build.spec
```

Result goes to `dist/OlympusDesktop/`:

- **Windows:** `OlympusDesktop.exe`
- **macOS:** `OlympusDesktop.app`
- **Linux:** `OlympusDesktop` (ELF)

Double-click to run.

## Notes

- The app imports your repo directly (no `pip install -e` needed) by extending `sys.path` to include `apps/*` and `packages/*`.
- Logs go to the parent console when launched from terminal; packaged app swallows the console.
- To quit cleanly, close the window or press **Stop** first (sends SIGTERM, then SIGKILL fallback).
