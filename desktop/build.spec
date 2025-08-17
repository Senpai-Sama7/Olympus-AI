# Build with:  pyinstaller --clean --noconfirm desktop/build.spec
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

repo_root = Path(__file__).resolve().parents[1]
desktop_dir = repo_root / "desktop"
ui_dir = desktop_dir / "app" / "ui"

# Include olympus packages by path (no pip -e needed)
pathex = [
    str(desktop_dir),
    str(repo_root / "apps" / "api"),
    str(repo_root / "apps" / "worker"),
    str(repo_root / "packages" / "plan"),
    str(repo_root / "packages" / "memory"),
    str(repo_root / "packages" / "llm"),
    str(repo_root / "packages" / "tools"),
    str(repo_root / "packages" / "automation"),
]

hiddenimports = []
# hiddenimports += collect_submodules("olympus_api")
# hiddenimports += collect_submodules("olympus_worker")

block_cipher = None

a = Analysis(
    [str(desktop_dir / "app" / "main.py")],
    pathex=pathex,
    binaries=[],
    datas=[
        (str(ui_dir / "index.html"), "app/ui"),
        (str(ui_dir / "app.js"), "app/ui"),
        (str(ui_dir / "styles.css"), "app/ui"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OlympusDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OlympusDesktop",
)
