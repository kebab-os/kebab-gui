#!/usr/bin/env python3
"""Remove all __pycache__ directories in the repository."""

from __future__ import annotations

import shutil
from pathlib import Path


def remove_pycache_dirs(repo_root: Path) -> int:
    removed = 0
    # Convert to list first so deleting directories does not affect iteration.
    for pycache_dir in list(repo_root.rglob("__pycache__")):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir, ignore_errors=True)
            removed += 1
            print(f"Removed: {pycache_dir}")
    return removed


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    count = remove_pycache_dirs(repo_root)
    print(f"Done. Removed {count} __pycache__ director{'y' if count == 1 else 'ies'}.")


if __name__ == "__main__":
    main()
