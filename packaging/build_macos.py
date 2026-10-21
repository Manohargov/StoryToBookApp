"""Build the macOS application bundle and a disk image.

Runs on macOS only.  It is what the release workflow calls, and it can also
be used locally:

    python packaging/build_macos.py

Produces:

    dist/StoryToBook.app          the application bundle
    dist/StoryToBook-<version>-macos-<arch>.dmg
    dist/StoryToBook-<version>-macos-<arch>.zip
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
VERSION = "1.0.0"


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, **kwargs)


def main() -> int:
    if sys.platform != "darwin":
        print("This script only runs on macOS.")
        return 1

    arch = platform.machine()  # arm64 or x86_64
    app_name = "StoryToBook"
    bundle = DIST / f"{app_name}.app"

    # 1. Build the bundle.  A macOS build is always a folder bundle.
    env = dict(os.environ)
    env["STORYTOBOOK_ONEFILE"] = "0"
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

    if not bundle.exists():
        print(f"Expected {bundle} to exist after the build.")
        return 1

    # 2. Ad-hoc sign the bundle.  Without a Developer ID this does not satisfy
    #    Gatekeeper, but it does stop macOS from refusing to start the app at
    #    all on Apple silicon.
    run(["codesign", "--force", "--deep", "--sign", "-", str(bundle)], capture_output=True)

    # 3. Zip for direct download.
    zip_path = DIST / f"{app_name}-{VERSION}-macos-{arch}.zip"
    if zip_path.exists():
        zip_path.unlink()
    run(["ditto", "-c", "-k", "--keepParent", str(bundle), str(zip_path)])

    # 4. Disk image.
    dmg_path = DIST / f"{app_name}-{VERSION}-macos-{arch}.dmg"
    if dmg_path.exists():
        dmg_path.unlink()

    staging = DIST / "dmg-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    shutil.copytree(bundle, staging / bundle.name)
    # A symlink to /Applications is what makes the "drag to install" work.
    os.symlink("/Applications", staging / "Applications")

    readme = staging / "README.txt"
    readme.write_text(
        "StoryToBook\n"
        "===========\n\n"
        "Drag StoryToBook.app into your Applications folder.\n\n"
        "macOS may show a warning the first time you open the app because it\n"
        "is not signed with an Apple Developer ID. Use right click -> Open,\n"
        "or run:  xattr -cr /Applications/StoryToBook.app\n",
        encoding="utf-8",
    )

    run(
        [
            "hdiutil",
            "create",
            "-volname",
            "StoryToBook",
            "-srcfolder",
            str(staging),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]
    )
    shutil.rmtree(staging, ignore_errors=True)

    print(f"\nBuilt:\n  {bundle}\n  {zip_path}\n  {dmg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
