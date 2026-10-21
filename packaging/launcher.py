"""Entry point used by PyInstaller.

Keeping the launcher in its own file avoids the quirks that ``__main__.py``
brings to the frozen build, and gives PyInstaller a single, obvious script to
analyse.
"""

from __future__ import annotations

import multiprocessing
import sys


def main() -> int:
    from storytobook.__main__ import main as run

    return run()


if __name__ == "__main__":
    # Required so that a frozen build can spawn child processes safely.
    multiprocessing.freeze_support()
    sys.exit(main())
