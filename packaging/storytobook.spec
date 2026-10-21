# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for StoryToBook.

Build a one-file executable::

    pyinstaller packaging/storytobook.spec --noconfirm

Build a one-folder bundle (faster start-up, ships as a zip)::

    STORYTOBOOK_ONEFILE=0 pyinstaller packaging/storytobook.spec --noconfirm

Set ``STORYTOBOOK_BUNDLE_AUDIO=0`` to leave ``sounddevice`` out, which drops
the bundled PortAudio library and the microphone feature.
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

SPEC_DIR = Path(SPECPATH).resolve()
ROOT = SPEC_DIR.parent
SRC = ROOT / "src"
ASSETS = SPEC_DIR / "assets"

ONEFILE = os.environ.get("STORYTOBOOK_ONEFILE", "1") == "1"
BUNDLE_AUDIO = os.environ.get("STORYTOBOOK_BUNDLE_AUDIO", "1") == "1"

APP_NAME = "StoryToBook"
VERSION = "1.0.0"

# The heavy optional engines are deliberately excluded: the application reports
# them as "not installed" and falls back to the built-in cover designer.
EXCLUDES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "whisper",
    "openai",
    "matplotlib",
    "pandas",
    "scipy",
    "IPython",
    "notebook",
    "pytest",
    "setuptools",
    "pip",
    "sqlite3",
    "xmlrpc",
    "pydoc_data",
    "tkinter.test",
    "test",
]
# Note: "unittest" is deliberately NOT excluded - fpdf2 imports
# unittest.mock from fpdf.sign, so removing it breaks PDF export.

datas: list = []
binaries: list = []
hiddenimports: list = []

# --- customtkinter ------------------------------------------------------
# The themes live in the package as JSON files and are needed at runtime.
try:
    ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")
    datas += ctk_datas
    binaries += ctk_binaries
    hiddenimports += ctk_hidden
except Exception:  # pragma: no cover - the hook is a convenience only
    pass

# --- sounddevice --------------------------------------------------------
# Pulls in the PortAudio shared library, which the recorder needs.
if BUNDLE_AUDIO:
    try:
        sd_datas, sd_binaries, sd_hidden = collect_all("sounddevice")
        datas += sd_datas
        binaries += sd_binaries
        hiddenimports += sd_hidden
    except Exception:  # pragma: no cover
        pass

# --- icon ---------------------------------------------------------------
if sys.platform == "darwin":
    icon_path = ASSETS / "StoryToBook.icns"
else:
    icon_path = ASSETS / "StoryToBook.ico"
if not icon_path.exists():
    icon_path = None

block_cipher = None


a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(icon_path) if icon_path else None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        icon=str(icon_path) if icon_path else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

    if sys.platform == "darwin":
        # macOS needs a real application bundle.
        app = BUNDLE(
            coll,
            name=f"{APP_NAME}.app",
            icon=str(icon_path) if icon_path else None,
            bundle_identifier="com.storytobook.app",
            version=VERSION,
            info_plist={
                "CFBundleName": APP_NAME,
                "CFBundleDisplayName": APP_NAME,
                "CFBundleShortVersionString": VERSION,
                "CFBundleVersion": VERSION,
                "CFBundleGetInfoString": "Turn a spoken story into a finished book.",
                "NSHighResolutionCapable": True,
                "LSMinimumSystemVersion": "10.13",
                "NSHumanReadableCopyright": "MIT licensed.",
            },
        )
