import tempfile
import unittest
from pathlib import Path

from chapter_server_v4 import WindmillMarineWorldV4
from hzw_protocol import SessionState


class V4OriginalControlsTests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return WindmillMarineWorldV4(Path(tmp.name))

    def spawn(self, world, username="v4hero", area="wm_square"):
        p = world.chapter.load_player(username)
        p.area = area
        p.x, p.y = map(int, world.chapter.area(area)["spawn"])
        world.chapter.save_player(p)
        state = SessionState(username=username, logged_in=True)
        world._spawn_area(p, state)
        return p, state

    def text(self, parts):
        return "\n".join(x for x in parts if isinstance(x, str))

    def test_turning_into_adjacent_npc_auto_interacts(self):
        world = self.make_world()
        p, state = self.spawn(world)
        oid, obj = next(
            (oid, obj) for oid, obj in state.metadata["chapter_objects"].items()
            if obj["kind"] == "npc"
        )
        p.x = int(obj["x"]) - 2
        p.y = int(obj["y"])
        reply = world._move(p, state, "#16")
        self.assertTrue(reply)
        self.assertEqual((p.x, p.y), (int(obj["x"]) - 2, int(obj["y"])))
        self.assertIn("<pmg>", self.text(reply))
        self.assertGreaterEqual(oid, 1000)

    def test_key5_adjacent_target_is_immediate_not_slow_selection(self):
        world = self.make_world()
        p, state = self.spawn(world, "key5fast")
        oid, obj = next(
            (oid, obj) for oid, obj in state.metadata["chapter_objects"].items()
            if obj["kind"] == "npc"
        )
        p.x = int(obj["x"]) - 2
        p.y = int(obj["y"])
        reply = world.handle_commands(["5"], state)
        text = self.text(reply)
        self.assertIn("<pmg>", text)
        self.assertNotIn("附近目标|", text)

    def test_no_coordinate_edge_warp_without_native_trigger(self):
        world = self.make_world()
        p, state = self.spawn(world, "noearlywarp", "wm_road")
        p.x = world.MAP_WIDTH // 2 * 2
        p.y = 2
        world._move(p, state, "#1")
        self.assertEqual(p.area, "wm_road")
        self.assertEqual(p.y, 0)

    def test_native_tl_trigger_is_only_world_transition_path(self):
        world = self.make_world()
        p, state = self.spawn(world, "nativeportal", "wm_road")
        tid, route = next(
            (tid, route) for tid, route in world.trigger_routes.items()
            if route["source"] == "wm_road" and route["cardinal"] == "north"
        )
        world.handle_commands([f"t l{tid}"], state)
        self.assertEqual(p.area, route["target"])
        self.assertEqual((p.x, p.y), (route["x"], route["y"]))

    def test_every_reconstructed_interior_has_return_path(self):
        world = self.make_world()
        interiors = (
            "wm_bar", "wm_shop", "wm_luffyhouse", "mb_bar", "mb_registry",
            "mb_trial", "mb_canteen", "mb_prison", "mb_church", "mb_barracks",
        )
        for area in interiors:
            specs = world._door_specs(area)
            self.assertTrue(any("返回" in rec[0] for rec in specs), area)

    def test_personal_root_uses_hzw_terms_and_all_entries_have_handlers(self):
        world = self.make_world()
        p, state = self.spawn(world, "personal")
        root = self.text(world.handle_commands(["1"], state))
        self.assertIn("个人状态", root)
        self.assertIn("物品行囊", root)
        self.assertIn("副官指令", root)
        self.assertIn("队伍指令", root)
        self.assertIn("战斗技能", root)
        self.assertNotIn("宠物指令", root)
        self.assertNotIn("武功技能", root)
        for cmd in ("11", "12", "pet", "1 4", "1 5", "1 6", "17"):
            self.assertTrue(world.handle_commands([cmd], state), cmd)

    def test_system_root_and_original_aliases_are_live(self):
        world = self.make_world()
        p, state = self.spawn(world, "system")
        root = self.text(world.handle_commands(["0"], state))
        self.assertIn("系统菜单", root)
        self.assertIn("公会指令", root)
        self.assertNotIn("帮派指令", root)
        for cmd in ("0r", "0s", "0h", "0q", "guild"):
            self.assertTrue(world.handle_commands([cmd], state), cmd)

    def test_core_numeric_keys_are_live(self):
        world = self.make_world()
        p, state = self.spawn(world, "keys")
        for cmd in ("1", "3", "5", "7", "9", "0"):
            reply = world.handle_commands([cmd], state)
            self.assertTrue(reply, cmd)
        # Movement keys are handled client-side and mirrored through # commands.
        for cmd in ("#7", "#10", "#13", "#16"):
            self.assertIsNotNone(world._move(p, state, cmd))


if __name__ == "__main__":
    unittest.main()
