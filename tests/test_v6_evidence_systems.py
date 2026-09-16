import json
import tempfile
import unittest
from pathlib import Path

from chapter_server_v6 import EvidenceFullWorldV6
from hzw_protocol import SessionState


ROOT = Path(__file__).resolve().parents[1]


class EvidenceSystemsV6Tests(unittest.TestCase):
    def make_world(self, username="v6hero", area="wm_square"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        world = EvidenceFullWorldV6(Path(tmp.name))
        p = world.chapter.load_player(username)
        p.area = area
        p.x, p.y = map(int, world.chapter.area(area)["spawn"])
        world.chapter.save_player(p)
        state = SessionState(username=username, logged_in=True)
        world._spawn_area(p, state)
        return world, p, state

    def test_v860_direct_catalog_is_enabled_and_post_v860_is_not(self):
        world, _p, _state = self.make_world()
        catalog = world.systems.catalog
        self.assertTrue(catalog["deputies"]["hunter"]["enabled"])
        direct_mounts = {
            x["name"] for x in catalog["mounts"].values()
            if x.get("evidence") == "V860_DIRECT_CONFIRMED" and x.get("enabled")
        }
        self.assertEqual({"雷象", "剑齿兽"}, direct_mounts)
        self.assertTrue(catalog["features"]["artifact_fusion"]["enabled"])
        self.assertFalse(catalog["features"]["divine_forge"]["enabled"])
        self.assertFalse(catalog["features"]["mystery_shop_late"]["enabled"])

    def test_profession_selection_is_level_ten_and_persistent(self):
        world, p, _state = self.make_world()
        p.level = 9
        ok, _ = world.systems.choose_profession(p, "warrior")
        self.assertFalse(ok)
        p.level = 10
        ok, msg = world.systems.choose_profession(p, "warrior")
        self.assertTrue(ok)
        self.assertIn("战士", msg)
        self.assertEqual("warrior", world.systems.load(p.username)["profession"])

    def test_windmill_ship_progress_syncs_without_inventing_extra_rewards(self):
        world, p, _state = self.make_world()
        p.completed_quests.append("wm10")
        p.give_item("新手炮", 1)
        if "初级炮术" not in p.skills:
            p.skills.append("初级炮术")
        world.chapter.save_player(p)
        state = world.systems.sync_progress(p)
        self.assertTrue(state["ship"]["owned"])
        self.assertEqual("新手炮", state["ship"]["cannon"])
        self.assertEqual(1, state["ship"]["gunnery_level"])

    def test_marine_deputy_sidequest_unlocks_persistent_starter_deputy(self):
        world, p, _state = self.make_world(area="mb_registry")
        p.completed_quests.append("mbs04")
        p.give_item("初级副官", 1)
        world.chapter.save_player(p)
        state = world.systems.sync_progress(p)
        self.assertIn("初级副官", state["deputies"])
        self.assertEqual("初级副官", state["active_deputy"])

    def test_all_original_keypad_roots_return_live_responses(self):
        world, p, state = self.make_world()
        for key in ("1", "3", "5", "7", "9", "0"):
            out = world.handle_commands([key], state)
            self.assertTrue(out, key)
            text = "\n".join(x for x in out if isinstance(x, str))
            self.assertTrue(text, key)
        # Direction keys are client/world movement paths and should be accepted.
        for cmd in ("#7", "#10", "#13", "#16", "#1", "#2", "#3", "#4"):
            self.assertIsNotNone(world._move(p, state, cmd))

    def test_player_facing_system_text_uses_hzw_terminology(self):
        world, p, state = self.make_world()
        payloads = []
        payloads += world._personal_root()
        payloads += world._system_root()
        payloads += world._deputy(p)
        payloads += world._skills(p)
        payloads += world._handle_ui("ui v860systems", p, state)
        text = "\n".join(x for x in payloads if isinstance(x, str))
        self.assertIn("副官", text)
        self.assertIn("战斗技能", text)
        self.assertIn("公会", text)
        self.assertNotIn("宠物", text)
        self.assertNotIn("武功", text)
        self.assertNotIn("帮派", text)

    def test_map_discovery_persists_current_area(self):
        world, p, _state = self.make_world(area="wm_square")
        state = world.systems.sync_progress(p)
        self.assertIn("wm_square", state["discovered_areas"])
        p.area = "mb_center"
        world.systems.sync_progress(p)
        self.assertIn("mb_center", world.systems.load(p.username)["discovered_areas"])

    def test_v6_content_file_is_valid_json_and_has_evidence_policy(self):
        data = json.loads((ROOT / "content" / "systems" / "v860_systems.json").read_text("utf-8"))
        self.assertEqual("V860", data["meta"]["profile"])
        self.assertIn("POST_V860", data["meta"]["policy"])


if __name__ == "__main__":
    unittest.main()
