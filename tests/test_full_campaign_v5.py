import tempfile
import unittest
from pathlib import Path

from campaign_engine import FullCampaignEngine
from chapter_server_v5 import FullCampaignWorldV5
from hzw_protocol import SessionState


ROOT = Path(__file__).resolve().parents[1]


class FullCampaignV5Tests(unittest.TestCase):
    def make_engine(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return FullCampaignEngine(ROOT / "content", Path(tmp.name))

    def make_world(self, username="v5hero", area="wm_square"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        world = FullCampaignWorldV5(Path(tmp.name))
        p = world.chapter.load_player(username)
        p.area = area
        p.x, p.y = map(int, world.chapter.area(area)["spawn"])
        world.chapter.save_player(p)
        state = SessionState(username=username, logged_in=True)
        world._spawn_area(p, state)
        return world, p, state

    def test_all_recovered_main_campaigns_loaded(self):
        engine = self.make_engine()
        for qid in (
            "wm01", "mb08", "or_main", "ju_main", "lo_main", "sr_mainq",
            "ca_bridge", "lg_main", "bt_main", "wi_main", "fo_main", "be_main",
            "sm_main",
        ):
            self.assertIn(qid, engine.quests, qid)

    def test_late_areas_and_branch_loaded(self):
        engine = self.make_engine()
        for area in ("or_village", "lo_town", "sr_main", "lg_resort", "bt_square", "wi_town", "fo_castle", "be_town", "sm_city"):
            self.assertIn(area, engine.areas, area)
        self.assertEqual(engine.quests["sm_main"]["kind"], "side")
        self.assertTrue(engine.quests["sm_main"].get("major_side_campaign"))

    def test_campaign_route_validation_has_no_isolated_area(self):
        # Construction itself executes reference + connectivity validation.
        engine = self.make_engine()
        self.assertGreater(len(engine.areas), 60)

    def test_later_data_driven_doors_exist(self):
        world, _p, _state = self.make_world(area="or_village")
        specs = world._door_specs("or_village")
        self.assertTrue(any(rec[1] == "or_petshop" for rec in specs))
        specs = world._door_specs("lg_resort")
        targets = {rec[1] for rec in specs}
        self.assertTrue({"lg_centerhut", "lg_ancestral", "lg_library", "lg_pool"}.issubset(targets))

    def test_bat_to_winter_has_reciprocal_route(self):
        engine = self.make_engine()
        self.assertEqual(engine.areas["bt_port"]["portals"]["east"][0], "wi_port")
        self.assertEqual(engine.areas["wi_port"]["portals"]["west"][0], "bt_port")

    def test_v4_collision_and_fast_key5_survive_in_v5(self):
        world, p, state = self.make_world(area="wm_square")
        _oid, obj = next(
            (oid, obj) for oid, obj in state.metadata["chapter_objects"].items()
            if obj["kind"] == "npc"
        )
        p.x = int(obj["x"]) - 2
        p.y = int(obj["y"])
        bump = world._move(p, state, "#16")
        self.assertTrue(bump)
        key5 = world.handle_commands(["5"], state)
        text = "\n".join(x for x in key5 if isinstance(x, str))
        self.assertIn("<pmg>", text)

    def test_world_map_lists_late_and_parallel_campaigns(self):
        world, p, _state = self.make_world()
        text = "\n".join(world._full_world_map(p))
        self.assertIn("巨兽岛", text)
        self.assertIn("星月岛", text)
        self.assertIn("小花园", text)

    def test_native_portals_generated_for_late_areas(self):
        world, _p, _state = self.make_world(area="fo_castle")
        routes = [r for r in world.trigger_routes.values() if r["source"] == "fo_castle"]
        self.assertGreaterEqual(len(routes), 3)
        data = world._area_map("fo_castle")
        self.assertGreater(data[14], 0)


if __name__ == "__main__":
    unittest.main()
