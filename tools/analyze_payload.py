from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from payload_stream import payload_analysis_json, write_payload_analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse one decoded V860 mixed server payload."
    )
    parser.add_argument("payload", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.out:
        write_payload_analysis(args.payload, args.out)
        print(args.out)
    else:
        print(payload_analysis_json(args.payload.read_bytes()), end="")
