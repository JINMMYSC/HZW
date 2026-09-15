import json
import tempfile
import unittest
from pathlib import Path

from chapter_engine import ChapterEngine

ROOT = Path(__file__).resolve().parents[1]


class ChapterContentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = ChapterEngine(ROOT / "content" / "windmill_marine.json", Path(self.tmp.name))

    def test_all_references_resolve(self):
        e = self.engine
        for nid, npc in e.npcs.items():
            self.assertIn(npc["area"], e.areas, nid)
        for mid, monster in e.monsters.items():
            self.assertIn(monster["area"], e.areas, mid)
        for qid, q in e.quests.items():
            self.assertIn(q["start_npc"], e.npcs, qid)
            prereq = q.get("prereq") or []
            if isinstance(prereq, str): prereq = [prereq]
            for pre in prereq: self.assertIn(pre, e.quests, (qid, pre))
            for step in q["steps"]:
                if step["type"] == "talk": self.assertIn(step["npc"], e.npcs, qid)
                if step["type"] in {"visit", "enter"}: self.assertIn(step["area"], e.areas, qid)
                if step["type"] == "kill": self.assertIn(step["monster"], e.monsters, qid)
                if step["type"] == "talk_cycle":
                    for n in step["npcs"]: self.assertIn(n, e.npcs, qid)

    def test_two_chapter_main_chain_order(self):
        main = [q["id"] for q in self.engine.content["quests"] if q["kind"] == "main"]
        self.assertEqual(main[:12], [f"wm{i:02d}" for i in range(1, 13)])
        self.assertEqual(main[12:], [f"mb{i:02d}" for i in range(1, 9)])

    def test_marine_side_quests_all_present(self):
        sides = [q for q in self.engine.content["quests"] if q["chapter"] == "marine" and q["kind"] == "side"]
        self.assertEqual(len(sides), 11)
        titles = {q["title"] for q in sides}
        self.assertIn("永生的美人鱼", titles)
        self.assertIn("人民公敌", titles)
        self.assertIn("航海的副官", titles)

    def test_persistence_roundtrip(self):
        p = self.engine.load_player("tester")
        p.area = "wm_square"; p.exp = 123; p.give_item("木头", 2)
        self.engine.save_player(p)
        e2 = ChapterEngine(ROOT / "content" / "windmill_marine.json", Path(self.tmp.name))
        p2 = e2.load_player("tester")
        self.assertEqual(p2.area, "wm_square")
        self.assertEqual(p2.exp, 123)
        self.assertEqual(p2.inventory["木头"], 2)

    def test_first_quest_progresses_into_second(self):
        p = self.engine.load_player("hero")
        self.assertIn("wm01", p.active_quests)
        messages = self.engine.record_event(p, {"type": "talk", "npc": "wm_sailor"})
        self.assertIn("wm01", p.completed_quests)
        self.assertIn("wm02", p.active_quests)
        self.assertTrue(any("初次航行课" in m for m in messages))

    def test_content_records_known_restore_gaps(self):
        raw = json.loads((ROOT / "content" / "windmill_marine.json").read_text("utf-8"))
        gaps = " ".join(raw["reconstruction"]["known_gaps"])
        self.assertIn("对白", gaps)
        self.assertIn("地图二进制", gaps)


if __name__ == "__main__":
    unittest.main()
