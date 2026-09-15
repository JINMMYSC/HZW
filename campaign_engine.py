from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from chapter_engine import ChapterEngine


class FullCampaignEngine(ChapterEngine):
    """Load the opening restoration plus every chapter pack under content/chapters.

    The historical service kept story/map state server-side. Recovered chapters
    therefore live in separate evidence-backed packs; adding an island must not
    require editing the V860 network/parser implementation.
    """

    def __init__(self, content_root: Path, data_dir: Path):
        root = Path(content_root)
        base = root / "windmill_marine.json"
        if not base.exists():
            raise RuntimeError(f"missing base campaign content: {base}")

        docs = [json.loads(base.read_text("utf-8"))]
        chapter_dir = root / "chapters"
        if chapter_dir.exists():
            for path in sorted(chapter_dir.glob("*.json")):
                docs.append(json.loads(path.read_text("utf-8")))

        merged = {
            "meta": {
                "id": "hzw_v860_full_campaign",
                "title": "HZW V860 全章节复原",
                "evidence_policy": "verified facts are separated from reconstructed service-side gaps",
            },
            "areas": {}, "npcs": {}, "monsters": {}, "quests": [],
            "reconstruction": {"packs": []},
        }

        quest_order: list[str] = []
        quest_by_id: dict[str, dict] = {}
        for doc in docs:
            pack_id = str((doc.get("meta") or {}).get("id") or "unnamed")
            merged["reconstruction"]["packs"].append(pack_id)
            for collection in ("areas", "npcs", "monsters"):
                for key, value in (doc.get(collection) or {}).items():
                    if key in merged[collection] and isinstance(value, dict):
                        current = merged[collection][key]
                        if isinstance(current, dict):
                            self._deep_update(current, value)
                            continue
                    merged[collection][key] = value
            for quest in doc.get("quests") or []:
                qid = str(quest["id"])
                if qid not in quest_by_id:
                    quest_order.append(qid)
                quest_by_id[qid] = quest

        merged["quests"] = [quest_by_id[qid] for qid in quest_order]

        # 星月岛/新月岛 is a large parallel campaign reached from the Little Garden
        # era. It must not hijack the linear Winter -> Forgotten -> Beast route.
        for quest in merged["quests"]:
            if quest.get("id") == "sm_main":
                quest["kind"] = "side"
                quest["major_side_campaign"] = True

        self.content_file = root
        self.data_dir = Path(data_dir)
        self.players_dir = self.data_dir / "players"
        self.players_dir.mkdir(parents=True, exist_ok=True)
        self.content = merged
        self.areas = merged["areas"]
        self.npcs = merged["npcs"]
        self.monsters = merged["monsters"]
        self.quests = {q["id"]: q for q in merged["quests"]}
        self._players = {}
        self.validate_campaign()

    @classmethod
    def _deep_update(cls, dst: dict, patch: dict) -> None:
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                cls._deep_update(dst[key], value)
            else:
                dst[key] = value

    def validate_campaign(self) -> None:
        """Fail startup for broken routes/references instead of trapping a player."""
        for area_id, area in self.areas.items():
            for _direction, portal in (area.get("portals") or {}).items():
                if not portal:
                    continue
                target = str(portal[0])
                if target not in self.areas:
                    raise RuntimeError(f"area {area_id} portal targets missing area {target}")
            for door in area.get("doors") or []:
                target = str(door.get("target", ""))
                if target not in self.areas:
                    raise RuntimeError(f"area {area_id} door targets missing area {target}")

        for npc_id, npc in self.npcs.items():
            if npc.get("area") not in self.areas:
                raise RuntimeError(f"NPC {npc_id} references missing area {npc.get('area')}")
        for monster_id, monster in self.monsters.items():
            if monster.get("area") not in self.areas:
                raise RuntimeError(f"monster {monster_id} references missing area {monster.get('area')}")

        for qid, quest in self.quests.items():
            for prereq in quest.get("prereq") or []:
                if prereq not in self.quests:
                    raise RuntimeError(f"quest {qid} has missing prerequisite {prereq}")
            start_npc = quest.get("start_npc")
            if start_npc and start_npc not in self.npcs:
                raise RuntimeError(f"quest {qid} starts at missing NPC {start_npc}")
            for step in quest.get("steps") or []:
                if step.get("type") in {"visit", "enter"} and step.get("area") not in self.areas:
                    raise RuntimeError(f"quest {qid} references missing area {step.get('area')}")
                if step.get("type") == "talk" and step.get("npc") not in self.npcs:
                    raise RuntimeError(f"quest {qid} references missing NPC {step.get('npc')}")
                if step.get("type") == "kill" and step.get("monster") not in self.monsters:
                    raise RuntimeError(f"quest {qid} references missing monster {step.get('monster')}")

        # Connectivity check ignores quest gates: it asks whether every authored
        # area has a physical way in/out once unlocked. This catches the exact
        # "entered a map and cannot leave" failure reported by the real client.
        graph: dict[str, set[str]] = {aid: set() for aid in self.areas}
        for aid, area in self.areas.items():
            for portal in (area.get("portals") or {}).values():
                if portal and str(portal[0]) in graph:
                    graph[aid].add(str(portal[0]))
                    graph[str(portal[0])].add(aid)
            for door in area.get("doors") or []:
                target = str(door.get("target", ""))
                if target in graph:
                    graph[aid].add(target)
                    graph[target].add(aid)

        start = "wm_ship"
        if start in graph:
            seen = {start}
            todo = deque([start])
            while todo:
                cur = todo.popleft()
                for nxt in graph[cur] - seen:
                    seen.add(nxt)
                    todo.append(nxt)
            isolated = sorted(set(graph) - seen)
            if isolated:
                raise RuntimeError("campaign has unreachable areas: " + ", ".join(isolated))
