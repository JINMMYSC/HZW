from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MapStyle:
    tilesets: tuple[int, ...]
    mode: str = "road"


# Explicit opening maps that have already been exercised in the real V860 client.
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


# Later maps use only artwork already bundled in the V860 JAR.  The service-side
# original map binaries have not survived, so this table reconstructs scene
# categories rather than pretending to know the original per-tile geometry.
PREFIX_DEFAULTS: dict[str, MapStyle] = {
    "or_": MapStyle((10, 28, 1), "road"),
    "ju_": MapStyle((10, 1, 7), "road"),
    "lo_": MapStyle((10, 28, 29), "road"),
    "sr_": MapStyle((7, 29, 19), "interior"),
    "ca_": MapStyle((28, 10, 19), "coast"),
    "lg_": MapStyle((1, 10, 15), "forest"),
    "bt_": MapStyle((29, 1, 7), "cave"),
    "wi_": MapStyle((15, 19, 29), "forest"),
    "fo_": MapStyle((1, 29, 10), "forest"),
    "be_": MapStyle((10, 1, 15), "road"),
    "sm_": MapStyle((10, 25, 29), "square"),
}


def _style_for_area(area_id: str) -> MapStyle:
    explicit = STYLES.get(area_id)
    if explicit is not None:
        return explicit

    # Semantic refinements for the reconstructed later campaign.
    lower = area_id.lower()
    if any(token in lower for token in ("sea", "coast", "spring", "lake", "pool", "ghost")):
        return MapStyle((19, 28, 12), "water" if "sea" in lower or "lake" in lower else "coast")
    if any(token in lower for token in ("port", "beach")):
        return MapStyle((28, 10, 19), "port")
    if any(token in lower for token in ("cave", "cellar", "warehouse", "prison", "dungeon", "coldstore")):
        return MapStyle((29, 21, 7), "cave")
    if any(token in lower for token in ("bar", "clinic", "house", "mansion", "doctor", "shop", "palace", "alchemy", "lab", "kitchen", "bedroom", "upper", "captain")):
        return MapStyle((7, 29, 25), "interior")
    if any(token in lower for token in ("forest", "woods", "mountain", "highland", "volcano", "snow", "herb", "lavender", "maze", "fork")):
        return MapStyle((1, 15, 10), "forest")
    if any(token in lower for token in ("temple", "church", "miracle")):
        return MapStyle((25, 29, 10), "temple")
    if any(token in lower for token in ("square", "town", "village", "city", "resort", "training", "knight")):
        return MapStyle((10, 28, 1), "square")

    for prefix, style in PREFIX_DEFAULTS.items():
        if lower.startswith(prefix):
            return style
    return MapStyle((10, 1, 28), "road")


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
    if abs(x - cx) <= 1 or abs(y - cy) <= 1:
        return min(2, len(style.tilesets)-1), (x + y) & 15
    if (x + 3*y) % 17 == 0 and len(style.tilesets) > 1:
        return 1, (x + y * 2) & 15
    return 0, (x * 3 + y) & 15


def make_chapter_map(
    area_id: str,
    width: int = 24,
    height: int = 24,
    triggers: Iterable[tuple[int, int, int]] | None = None,
) -> bytes:
    """Build a reconstructed V860 area from original bundled ``d/*.tij`` art.

    ``triggers`` are original-format V860 map triggers ``(tile_x, tile_y, id)``.
    Area changes happen only when the client reaches that trigger tile and emits
    ``t l<ID>``; movement coordinates alone never cause an early map switch.

    The artwork is original-client material.  Later service-side map geometry is
    reconstructed because the historical server map binaries have not surfaced.
    """
    style = _style_for_area(area_id)
    trigger_list = list(triggers or [])
    if len(trigger_list) > 255:
        raise ValueError("too many V860 map triggers")

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
    descriptor_end = descriptor_offset + len(descriptors)

    trigger_bytes = bytearray()
    for x, y, trigger_id in trigger_list:
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"trigger outside map: {(x, y)}")
        if not (1001 <= int(trigger_id) <= 0xFFFF):
            raise ValueError(f"invalid V860 trigger id: {trigger_id}")
        trigger_bytes += bytes((x & 0xFF, y & 0xFF))
        trigger_bytes += int(trigger_id).to_bytes(2, "little")

    header[2] = len(style.tilesets)
    header[4:6] = descriptor_offset.to_bytes(2, "little")
    header[6] = 0
    header[8:10] = descriptor_end.to_bytes(2, "little")
    header[10] = 0
    header[12:14] = descriptor_end.to_bytes(2, "little")
    header[14] = len(trigger_list)
    header[16:18] = descriptor_end.to_bytes(2, "little")

    return bytes(header) + bytes(cells) + bytes(descriptors) + bytes(trigger_bytes)
