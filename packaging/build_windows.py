"""Build the Windows application folder and installer.

Runs on Windows only.  It is what the release workflow calls, and it can also
be used locally:

    python packaging/build_windows.py

Produces:

    dist/StoryToBook/                          the application folder
    dist/StoryToBook-1.0.0-windows-x64.zip    the portable build
    dist/installer/StoryToBook-1.0.0-...exe   the installer (needs Inno Setup)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
VERSION = "1.0.0"
APP_NAME = "StoryToBook"


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, **kwargs)


def find_iscc() -> Path | None:
    """Locate the Inno Setup compiler, if it is installed.

    Set ``STORYTOBOOK_ISCC`` to point at a specific ``ISCC.exe``.
    """
    override = os.environ.get("STORYTOBOOK_ISCC")
    if override and Path(override).exists():
        return Path(override)

    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    found = shutil.which("ISCC")
    return Path(found) if found else None


def main() -> int:
    if sys.platform != "win32":
        print("This script only runs on Windows.")
        return 1

    # 1. Build the application folder.  A folder build starts instantly,
    #    which matters more than a single file for a desktop application.
    env = dict(os.environ)
    env["STORYTOBOOK_ONEFILE"] = "0"
    env["STORYTOBOOK_BUNDLE_AUDIO"] = "1"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(ROOT / "packaging" / "storytobook.spec"),
            "--noconfirm",
            "--clean",
            "--distpath",
            str(DIST),
            "--workpath",
            str(ROOT / "build"),
        ],
        env=env,
    )

    app_dir = DIST / APP_NAME
    if not (app_dir / f"{APP_NAME}.exe").exists():
        print(f"Expected {app_dir / (APP_NAME + '.exe')} to exist after the build.")
        return 1

    # 2. Verify the frozen build really works.
    report = DIST / "selftest.txt"
    subprocess.run(
        [str(app_dir / f"{APP_NAME}.exe"), "--selftest", "--report", str(report)],
        check=True,
    )
    if report.exists():
        print(report.read_text(encoding="utf-8"))

    # 3. Zip the portable build.
    zip_path = DIST / f"{APP_NAME}-{VERSION}-windows-x64.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(app_dir.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(DIST))
    print(f"wrote {zip_path}")

    # 4. Build the installer when Inno Setup is available.
    iscc = find_iscc()
    if iscc is None:
        print(
            "\nInno Setup was not found, so no installer was produced.\n"
            "Install it with:  choco install innosetup\n"
            "or download it from https://jrsoftware.org/isdl.php"
        )
    else:
        run(
            [
                str(iscc),
                f"/DMyAppDir={app_dir}",
                f"/DMyVersion={VERSION}",
                str(ROOT / "packaging" / "storytobook.iss"),
            ]
        )
        for installer in (DIST / "installer").glob("*.exe"):
            print(f"wrote {installer}")

    print(f"\nBuilt:\n  {app_dir}\n  {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
