from __future__ import annotations

import json
from pathlib import Path

from chapter_engine import ChapterEngine


class FullCampaignEngine(ChapterEngine):
    """Load the opening restoration plus every chapter pack under content/chapters.

    The original service kept story/map state server-side.  Keeping recovered
    chapters in separate data files lets us add/replace evidence without touching
    the recovered V860 protocol implementation.
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
            "areas": {},
            "npcs": {},
            "monsters": {},
            "quests": [],
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
                        # Area patches may add a portal without replacing the
                        # original map definition.
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

        # ChapterEngine expects a path.  Initialize its storage fields directly
        # with the merged in-memory document instead of emitting a generated DB.
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

    @classmethod
    def _deep_update(cls, dst: dict, patch: dict) -> None:
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                cls._deep_update(dst[key], value)
            else:
                dst[key] = value
