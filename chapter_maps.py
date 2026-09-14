from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MapStyle:
    tilesets: tuple[int, ...]
    mode: str = "road"


STYLES: dict[str, MapStyle] = {
    "wm_ship": MapStyle((7, 19), "ship"),
    "wm_road": MapStyle((10, 1, 28), "road"),
    "wm_westroad": MapStyle((10, 1, 28), "road"),
    "wm_square": MapStyle((10, 28, 1), "square"),
    "wm_bar": MapStyle((7, 29), "interior"),
    "wm_shop": MapStyle((7, 29), "interior"),
    "wm_luffyhouse": MapStyle((7, 29), "interior"),
    "wm_backhill": MapStyle((1, 15, 10), "forest"),
    "wm_cave": MapStyle((29, 21), "cave"),
    "wm_woods": MapStyle((1, 15, 10), "forest"),
    "wm_temple": MapStyle((25, 29), "temple"),
    "wm_cliff": MapStyle((28, 10, 19), "coast"),
    "wm_sea": MapStyle((19, 12, 14), "water"),
    "wm_eastport": MapStyle((28, 7, 19), "port"),
    "mb_entrance": MapStyle((28, 10, 1), "road"),
    "mb_center": MapStyle((10, 28, 11), "square"),
    "mb_bar": MapStyle((7, 29), "interior"),
    "mb_registry": MapStyle((7, 29), "interior"),
    "mb_trial": MapStyle((29, 7), "interior"),
    "mb_training": MapStyle((10, 28, 11), "square"),
    "mb_canteen": MapStyle((7, 29), "interior"),
    "mb_prison": MapStyle((29, 21), "cave"),
    "mb_hq": MapStyle((29, 28, 11), "square"),
    "mb_church": MapStyle((25, 29), "temple"),
    "mb_barracks": MapStyle((7, 29), "interior"),
    "mb_wasteland": MapStyle((10, 28, 15), "road"),
    "mb_lighthouse": MapStyle((28, 29, 19), "coast"),
    "mb_rangerbeach": MapStyle((10, 28, 19), "coast"),
    "mb_dawang": MapStyle((10, 28, 19), "coast"),
    "mb_forest": MapStyle((1, 15, 10), "forest"),
}


def _cell(slot: int, frame: int, walk: int = 0x3F) -> bytes:
    return bytes((slot & 0x0F, frame & 0xFF, 0xFF, walk & 0xFF))


def _choose(style: MapStyle, x: int, y: int, w: int, h: int) -> tuple[int, int]:
    mode = style.mode
    cx, cy = w // 2, h // 2
    if mode == "water":
        return (0 if (x + y) % 5 else min(1, len(style.tilesets)-1), (x * 3 + y * 5) & 15)
    if mode == "ship":
        if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
            return min(1, len(style.tilesets)-1), (x + y) & 15
        return 0, (x + y * 2) & 15
    if mode in {"interior", "cave", "temple"}:
        border = x <= 1 or y <= 1 or x >= w - 2 or y >= h - 2
        return (min(1, len(style.tilesets)-1) if border else 0, (x + y * 3) & 15)
    if mode == "forest":
        edge = x <= 2 or y <= 2 or x >= w - 3 or y >= h - 3
        if edge and len(style.tilesets) > 1:
            return 1, (x * 2 + y) & 15
        if (x + 2*y) % 11 == 0 and len(style.tilesets) > 2:
            return 2, (x + y) & 15
        return 0, (x + y * 3) & 15
    if mode == "coast":
        if x >= w - 5 and len(style.tilesets) > 2:
            return 2, (x + y * 2) & 15
        if x in {w - 6, w - 7} and len(style.tilesets) > 1:
            return 1, (x + y) & 15
        return 0, (x + 3*y) & 15
    if mode == "port":
        if x >= w - 5 and len(style.tilesets) > 2:
            return 2, (x + y) & 15
        if y in {cy - 1, cy, cy + 1} and len(style.tilesets) > 1:
            return 1, x & 15
        return 0, (x + y) & 15
    if mode == "square":
        if abs(x - cx) <= 2 or abs(y - cy) <= 2:
            return min(1, len(style.tilesets)-1), (x + y) & 15
        if (x + y) % 13 == 0 and len(style.tilesets) > 2:
            return 2, (x * 2 + y) & 15
        return 0, (x + y * 2) & 15
    # road/default: cross-shaped road plus original grass/edge accents.
    if abs(x - cx) <= 1 or abs(y - cy) <= 1:
        return min(2, len(style.tilesets)-1), (x + y) & 15
    if (x + 3*y) % 17 == 0 and len(style.tilesets) > 1:
        return 1, (x + y * 2) & 15
    return 0, (x * 3 + y) & 15


def make_chapter_map(area_id: str, width: int = 24, height: int = 24) -> bytes:
    """Build a reconstructed V860 area from original bundled d/*.tij resources.

    The map geometry is reconstructed; the tile artwork itself is the original V860
    client artwork. Normal cells stay walkable so the original client performs its
    own continuous walking animation.
    """
    style = STYLES.get(area_id, MapStyle((10,), "road"))
    header = bytearray(20)
    header[18] = width
    header[19] = height
    cells = bytearray()
    for y in range(height):
        for x in range(width):
            slot, frame = _choose(style, x, y, width, height)
            cells += _cell(slot, frame)
    descriptor_offset = 20 + len(cells)
    descriptors = bytearray()
    for tid in style.tilesets:
        descriptors += b"\x00\x00" + int(tid).to_bytes(2, "little")
    section_end = descriptor_offset + len(descriptors)
    header[2] = len(style.tilesets)
    header[4:6] = descriptor_offset.to_bytes(2, "little")
    header[6] = 0
    header[8:10] = section_end.to_bytes(2, "little")
    header[10] = 0
    header[12:14] = section_end.to_bytes(2, "little")
    header[14] = 0
    header[16:18] = section_end.to_bytes(2, "little")
    return bytes(header) + bytes(cells) + bytes(descriptors)
