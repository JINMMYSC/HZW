from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jar_intake import write_intake_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an evidence-graded intake report for one HZW candidate JAR."
    )
    parser.add_argument("jar")
    parser.add_argument("--out", required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--claimed-device")
    args = parser.parse_args()
    write_intake_report(
        args.jar,
        args.out,
        source_url=args.source_url,
        claimed_device=args.claimed_device,
    )


if __name__ == "__main__":
    main()
