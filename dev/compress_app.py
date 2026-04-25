#!/usr/bin/env python3
"""Pack a directory into a plain-text .kbapp stack."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path

PACKAGE_HEADER = "KBAPP 1"
FILE_PREFIX = "---FILE:"
FILE_SUFFIX = "---"
END_MARKER = "---ENDFILE---"


def _encode_file(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    try:
        return "utf-8", raw.decode("utf-8")
    except UnicodeDecodeError:
        return "base64", base64.b64encode(raw).decode("ascii")


def build_package(source_dir: Path) -> str:
    entries: list[str] = [PACKAGE_HEADER]
    for file_path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        rel_path = file_path.relative_to(source_dir).as_posix()
        encoding, payload = _encode_file(file_path)
        entries.append(f"{FILE_PREFIX} {rel_path} {FILE_SUFFIX}")
        entries.append(f"encoding={encoding}")
        entries.append("")
        entries.append(payload)
        entries.append(END_MARKER)
    return "\n".join(entries) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack a folder into a plain-text .kbapp file.")
    parser.add_argument("source", help="Path to the app folder to package")
    parser.add_argument("output", nargs="?", help="Optional output .kbapp path")
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Source folder not found: {source_dir}")

    output_path = Path(args.output).resolve() if args.output else source_dir.with_suffix(".kbapp")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_package(source_dir), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
