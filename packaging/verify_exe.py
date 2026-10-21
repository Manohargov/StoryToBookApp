"""Screenshot a running frozen executable to verify the bundle works.

Usage:  python packaging/verify_exe.py <path-to-exe> <output.png>
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab


def find_window(title: str) -> tuple[int, int, int, int] | None:
    """Locate a top level window by its title, using ctypes."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found: list[tuple[int, int, int, int]] = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    def callback(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title.lower() in buffer.value.lower() and user32.IsWindowVisible(hwnd):
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            found.append((rect.left, rect.top, rect.right, rect.bottom))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found[0] if found else None


def main() -> int:
    exe = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/StoryToBook.exe").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "exe-check.png").resolve()

    env = dict(os.environ)
    env["STORYTOBOOK_HOME"] = os.environ.get(
        "STORYTOBOOK_HOME", str(Path.home() / "AppData" / "Local" / "Temp" / "stb-exe-verify")
    )

    process = subprocess.Popen([str(exe)], env=env)
    try:
        time.sleep(14)

        rect = find_window("Story to Book")
        if rect is None:
            print("ERROR: the application window never appeared")
            return 1

        left, top, right, bottom = rect
        shot = ImageGrab.grab()
        shot.crop((left, top, right, bottom)).save(output)
        print(f"saved {output} ({right - left}x{bottom - top})")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
