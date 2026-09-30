from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jar_diff import write_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inventory and compare two or more HZW candidate JAR files."
    )
    parser.add_argument("jars", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if len(args.jars) < 2:
        parser.error("at least two JAR files are required")
    write_report(args.jars, args.out)
    print(args.out)
