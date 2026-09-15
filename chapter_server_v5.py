from __future__ import annotations

import json
from pathlib import Path

import server as legacy
from campaign_engine import FullCampaignEngine
from chapter_server_v4 import WindmillMarineServerV4, WindmillMarineWorldV4
from hzw_protocol import SessionState

ROOT = Path(__file__).resolve().parent
CONTENT_ROOT = ROOT / "content"


class FullCampaignWorldV5(WindmillMarineWorldV4):
    """Full recovered-campaign world on top of V4 original interaction logic."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.chapter = FullCampaignEngine(CONTENT_ROOT, data_dir)
        self.trigger_routes = {}
        self.area_triggers = {}
        self._build_native_portals()
        self.map_cache.clear()
        self.cache_key_to_area.clear()
        manifest = CONTENT_ROOT / "full_campaign_manifest.json"
        self.campaign_manifest = json.loads(manifest.read_text("utf-8")) if manifest.exists() else {}

    def _door_specs(self, area_id: str):
        """Opening hard-coded doors + later chapter doors from content data."""
        specs = list(super()._door_specs(area_id))
        for door in self.chapter.area(area_id).get("doors") or []:
            specs.append((
                str(door.get("label") or "入口"),
                str(door["target"]),
                int(door.get("x", 12)),
                int(door.get("y", 8)),
                None if door.get("dest_x") is None else int(door["dest_x"]),
                None if door.get("dest_y") is None else int(door["dest_y"]),
            ))
        return specs

    def _auto_script(self, p, event_source: str):
        """Generic static-item restoration for later chapter packs.

        Surviving walkthroughs often say an item is taken from a room/object rather
        than dropped by a monster. Chapter data can mark that collect step with
        source_area/source_npc, keeping this reconstruction explicit and data-driven.
        """
        messages = list(super()._auto_script(p, event_source))
        while True:
            main = self.chapter.current_main(p)
            if not main:
                break
            q, idx = main["quest"], int(main["step_index"])
            if idx >= len(q["steps"]):
                break
            step = q["steps"][idx]
            if step.get("type") != "collect":
                break
            matches = False
            if event_source == "area" and step.get("source_area") == p.area:
                matches = True
            if event_source.startswith("talk:") and step.get("source_npc") == event_source.split(":", 1)[1]:
                matches = True
            if not matches:
                break
            item = str(step["item"])
            count = int(step.get("count", 1))
            messages += self.chapter.record_event(p, {"type": "collect", "item": item, "count": count})
            messages.append(f"取得：{item}×{count}")
        self.chapter.save_player(p)
        return messages

    def _native_portal(self, p, state: SessionState, trigger_id: int):
        route = self.trigger_routes.get(trigger_id)
        if not route:
            return ["<smg>未知地图出口。"]
        target = route["target"]
        target_area = self.chapter.areas.get(target, {})
        required = target_area.get("requires_quests") or []
        if isinstance(required, str):
            required = [required]
        missing = [qid for qid in required if qid not in p.completed_quests]
        if missing:
            return ["<smg>当前主线尚未推进到这个区域。"]
        # Level gates stay advisory until the original repeatable/grind economy is
        # recovered. We do not invent a fake exact 1-73 experience curve.
        return super()._native_portal(p, state, trigger_id)

    def _full_world_map(self, p):
        names = []
        for cid in self.campaign_manifest.get("main_route", []):
            chapter = next((c for c in self.campaign_manifest.get("chapters", []) if c.get("id") == cid), None)
            if chapter:
                names.append(chapter["name"])
        parallel = [
            c["name"] for c in self.campaign_manifest.get("chapters", [])
            if c.get("id") in {"star_moon", "food_god"}
        ]
        text = " → ".join(names)
        if parallel:
            text += "\x1a支线/挑战：" + "、".join(parallel)
        return ["<pmg>世界地图：" + text]

    def _handle_ui(self, cmd: str, p, state: SessionState):
        normalized = " ".join(cmd.strip().split())
        if normalized == "9 3":
            return self._full_world_map(p)
        if normalized == "ui campaign":
            return self._full_world_map(p)
        return super()._handle_ui(cmd, p, state)


class FullCampaignServerV5(WindmillMarineServerV4):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = FullCampaignWorldV5(data_dir)


legacy.HZWCompatServer = FullCampaignServerV5

if __name__ == "__main__":
    legacy.main()
