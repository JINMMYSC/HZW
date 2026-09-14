from __future__ import annotations

from typing import Iterable

ServerPart = str | bytes


def join_server_parts(parts: Iterable[ServerPart]) -> bytes:
    """Join V860 text commands with recovered binary world records."""
    out = bytearray()
    for part in parts:
        if isinstance(part, str):
            out.extend(part.encode("utf-8"))
            if not part.endswith("\n"):
                out.append(0x0A)
        else:
            out.extend(part)
    return bytes(out)


def encode_smallint(value: int) -> bytes:
    """Integer form consumed by O0OO0O0.OO00O0(byte[], int)."""
    if 0 <= value < 127:
        return bytes((value,))
    if 0 <= value <= 0xFFFF:
        return bytes((127, (value >> 8) & 0xFF, value & 0xFF))
    raise ValueError(f"V860 smallint out of range: {value}")


def encode_inline_string(text: str) -> bytes:
    """Inline UTF-8 string form consumed by O0OO0O0.O0O0O(byte[], int)."""
    raw = text.encode("utf-8")
    marker = 129 + len(raw)
    if marker > 255:
        raise ValueError("inline V860 string too long")
    return bytes((marker,)) + raw + b"\x00"


def make_normal_record(record_type: int, payload: bytes) -> bytes:
    if not 0 <= record_type <= 123:
        raise ValueError("normal V860 record type must be <= 123")
    body = bytes((record_type,)) + payload
    n = len(body)
    if n > 0x7FFF:
        raise ValueError("record too large")
    return bytes(((n >> 8) & 0xFF, n & 0xFF)) + body


def make_map_switch_record(map_token: str = "hzwlocal00") -> bytes:
    """Type 1 record. V860 replaces token's last two chars with 'sj'."""
    raw = map_token.encode("utf-8")
    if len(raw) > 127:
        raise ValueError("map token too long")
    return make_normal_record(1, bytes((128 + len(raw),)) + raw)


def make_entity_record(
    name: str,
    template_id: int,
    direction: int,
    object_id: int,
    x: int,
    y: int,
) -> bytes:
    """Type 4 record: label, c/<template_id>.chj id, direction, object id, x, y."""
    payload = bytearray(encode_inline_string(name))
    for value in (template_id, direction, object_id, x, y):
        payload += encode_smallint(value)
    return make_normal_record(4, bytes(payload))


def make_position_record(
    object_id: int,
    x: int,
    y: int,
    direction: int,
    aux_a: int = 0,
    aux_b: int = 0,
) -> bytes:
    """Type 7 entity position/direction update recovered from V860.

    O0OO0O0.O00O(byte[]) parses this record as:
      object_id, x, y, aux_a, aux_b, direction
    then applies O00OO00(entity, x, y) and stores the direction byte.
    Coordinates use the client's half-tile world units: flat movement changes
    one axis by 2 for each map cell.
    """
    payload = bytearray()
    for value in (object_id, x, y, aux_a, aux_b, direction):
        payload += encode_smallint(value)
    return make_normal_record(7, bytes(payload))


def make_map_download_block(cache_key: str, map_bytes: bytes) -> bytes:
    """Special stream marker 127 returned after '#map 60<cache_key>'."""
    key = cache_key.encode("utf-8")
    if b"\x00" in key:
        raise ValueError("cache key cannot contain NUL")
    if len(map_bytes) > 0xFFFF:
        raise ValueError("map too large")
    n = len(map_bytes)
    return b"\x00\x00\x7f" + key + b"\x00" + n.to_bytes(2, "little") + map_bytes


def _base_map_header(width: int, height: int) -> bytearray:
    if not (1 <= width <= 127 and 1 <= height <= 127):
        raise ValueError("width/height must fit positive Java byte")
    header = bytearray(20)
    header[18] = width
    header[19] = height
    return header


def make_blank_map(width: int = 24, height: int = 24) -> bytes:
    """Protocol-only blank field retained as a diagnostic fixture."""
    header = _base_map_header(width, height)
    end = 20 + width * height * 4
    header[2] = 0
    header[4:6] = end.to_bytes(2, "little")
    header[6] = 0
    header[8:10] = end.to_bytes(2, "little")
    header[10] = 0
    header[12:14] = end.to_bytes(2, "little")
    header[14] = 0
    header[16:18] = end.to_bytes(2, "little")
    cell = bytes((0x0F, 0xFF, 0xFF, 0x80))
    return bytes(header) + cell * (width * height)


def make_tiled_map(
    width: int = 24,
    height: int = 24,
    tileset_id: int = 10,
    tile_flags: int = 0x3F,
) -> bytes:
    """Visible bootstrap map using one JAR-bundled ``d/<id>.tij`` tileset.

    Recovered V860 cell layout:
      cell[0] low nibble -> tileset slot
      cell[1]            -> tile/frame attributes
      cell[2]            -> overlay selector (0xFF disables overlay)
      cell[3]            -> WALKABILITY BITS

    The Phase-5 server accidentally put 0x3F into cell[1]. The real movement
    routine O000O0O.O0OO0O(...) reads cell[3], which is why the real client
    could turn but never emitted #1/#2/#3/#4 step commands. Phase 6 writes
    walkability to the correct byte.
    """
    if not 0 <= tileset_id <= 0xFFFF:
        raise ValueError("tileset_id out of range")
    header = _base_map_header(width, height)
    cell = bytes((0x00, 0x00, 0xFF, tile_flags & 0xFF))
    cells = cell * (width * height)
    descriptor_offset = 20 + len(cells)
    descriptor = b"\x00\x00" + int(tileset_id).to_bytes(2, "little")
    section_end = descriptor_offset + len(descriptor)

    header[2] = 1
    header[4:6] = descriptor_offset.to_bytes(2, "little")
    header[6] = 0
    header[8:10] = section_end.to_bytes(2, "little")
    header[10] = 0
    header[12:14] = section_end.to_bytes(2, "little")
    header[14] = 0
    header[16:18] = section_end.to_bytes(2, "little")
    return bytes(header) + cells + descriptor
