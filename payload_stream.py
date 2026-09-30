from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextLine:
    offset: int
    raw: bytes
    text: str


@dataclass(frozen=True)
class NormalRecord:
    offset: int
    record_type: int
    payload: bytes
    raw: bytes


@dataclass(frozen=True)
class MapDownloadRecord:
    offset: int
    cache_key: str
    map_bytes: bytes
    raw: bytes


@dataclass(frozen=True)
class UnknownSpecialRecord:
    offset: int
    marker: int
    raw: bytes


@dataclass(frozen=True)
class TruncatedRecord:
    offset: int
    reason: str
    raw: bytes


@dataclass(frozen=True)
class AmbiguousRecord:
    offset: int
    reason: str
    raw: bytes


PayloadRecord = (
    TextLine
    | NormalRecord
    | MapDownloadRecord
    | UnknownSpecialRecord
    | TruncatedRecord
    | AmbiguousRecord
)


def _truncated(data: bytes, offset: int, reason: str) -> list[PayloadRecord]:
    return [TruncatedRecord(offset, reason, data[offset:])]


def parse_payload_stream(data: bytes) -> list[PayloadRecord]:
    """Split a decoded V860 server payload without guessing unknown framing.

    Confirmed text commands begin with ``<`` and end in LF. Confirmed normal
    binary records have a two-byte big-endian body length followed by a record
    type in the range 0..123. Marker 127 has its recovered map-download shape.
    Markers 124..126 are deliberately returned as one opaque remainder because
    their length/framing is not yet established from a real capture or client
    branch. Continuing after one would risk inventing record boundaries.
    """
    records: list[PayloadRecord] = []
    offset = 0

    while offset < len(data):
        body_length = None
        record_type = None
        record_end = None
        normal_complete = False
        if len(data) - offset >= 3:
            body_length = int.from_bytes(data[offset : offset + 2], "big")
            record_type = data[offset + 2]
            record_end = offset + 2 + body_length
            normal_complete = (
                body_length >= 1
                and record_type <= 123
                and record_end <= len(data)
            )

        if data[offset] == ord("<"):
            newline = data.find(b"\n", offset)
            if newline >= 0 and normal_complete:
                records.append(
                    AmbiguousRecord(
                        offset,
                        "angle-bracket prefix is valid as both text and a normal record",
                        data[offset:],
                    )
                )
                break
            if newline >= 0:
                raw = data[offset : newline + 1]
                records.append(
                    TextLine(offset, raw, raw[:-1].decode("utf-8", errors="replace"))
                )
                offset = newline + 1
                continue
            if not normal_complete:
                records.extend(_truncated(data, offset, "text command has no LF terminator"))
                break

        if len(data) - offset < 3:
            records.extend(_truncated(data, offset, "record header needs three bytes"))
            break

        assert body_length is not None
        assert record_type is not None

        if body_length == 0 and 124 <= record_type <= 127:
            if record_type in (124, 125, 126):
                records.append(UnknownSpecialRecord(offset, record_type, data[offset:]))
                break

            key_start = offset + 3
            key_end = data.find(b"\x00", key_start)
            if key_end < 0:
                records.extend(_truncated(data, offset, "marker 127 cache key has no NUL terminator"))
                break
            length_start = key_end + 1
            if len(data) - length_start < 2:
                records.extend(_truncated(data, offset, "marker 127 map length is truncated"))
                break
            map_length = int.from_bytes(data[length_start : length_start + 2], "little")
            record_end = length_start + 2 + map_length
            if record_end > len(data):
                records.extend(_truncated(data, offset, "marker 127 map payload is truncated"))
                break
            raw = data[offset:record_end]
            records.append(
                MapDownloadRecord(
                    offset,
                    data[key_start:key_end].decode("utf-8", errors="replace"),
                    data[length_start + 2 : record_end],
                    raw,
                )
            )
            offset = record_end
            continue

        if body_length < 1:
            records.extend(_truncated(data, offset, "normal record body length must include its type"))
            break
        assert record_end is not None
        if record_end > len(data):
            records.extend(_truncated(data, offset, "normal record body is truncated"))
            break
        if record_type > 123:
            records.append(UnknownSpecialRecord(offset, record_type, data[offset:]))
            break

        raw = data[offset:record_end]
        records.append(NormalRecord(offset, record_type, raw[3:], raw))
        offset = record_end

    return records


def payload_analysis_json(data: bytes) -> str:
    report = []
    for record in parse_payload_stream(data):
        item = asdict(record)
        item["kind"] = type(record).__name__
        for key, value in tuple(item.items()):
            if isinstance(value, bytes):
                item[key] = value.hex()
        report.append(item)
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def write_payload_analysis(payload: str | Path, output: str | Path) -> None:
    payload_path = Path(payload).resolve()
    output_path = Path(output).resolve()
    if payload_path == output_path:
        raise ValueError("payload input and report output resolve to the same file")

    rendered = payload_analysis_json(payload_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=output_path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp.write(rendered)
            temp_name = temp.name
        Path(temp_name).replace(output_path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
