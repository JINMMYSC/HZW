import tempfile
import unittest
from pathlib import Path

from chapter_server_v3 import WindmillMarineWorldV3
from hzw_protocol import SessionState


class WorldInteractionV3Tests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return WindmillMarineWorldV3(Path(tmp.name))

    def make_player(self, world, username="v3hero", area="wm_square"):
        p = world.chapter.load_player(username)
        p.area = area
        p.x, p.y = map(int, world.chapter.area(area)["spawn"])
        world.chapter.save_player(p)
        state = SessionState(username=username, logged_in=True)
        world._spawn_area(p, state)
        return p, state

    def test_all_interactable_world_objects_use_native_collision_ids(self):
        world = self.make_world()
        p, state = self.make_player(world)
        self.assertTrue(state.metadata["chapter_objects"])
        self.assertTrue(all(
            oid >= 1000 for oid in state.metadata["chapter_objects"]
        ))

    def test_bumping_npc_auto_interacts_and_does_not_walk_through(self):
        world = self.make_world()
        p, state = self.make_player(world)
        npc_oid, npc = next(
            (oid, obj) for oid, obj in state.metadata["chapter_objects"].items()
            if obj["kind"] == "npc"
        )
        p.x = int(npc["x"]) - 2
        p.y = int(npc["y"])
        old = (p.x, p.y)
        reply = world._move(p, state, "#4")
        self.assertEqual((p.x, p.y), old)
        self.assertTrue(reply)
        self.assertTrue(any("<pmg>" in x or "<menu" in x for x in reply if isinstance(x, str)))
        self.assertGreaterEqual(npc_oid, 1000)

    def test_native_portal_trigger_is_embedded_in_map(self):
        world = self.make_world()
        data = world._area_map("wm_road")
        count = data[14]
        offset = int.from_bytes(data[16:18], "little")
        self.assertGreater(count, 0)
        self.assertLess(offset + 3, len(data))
        first_id = int.from_bytes(data[offset + 2:offset + 4], "little")
        self.assertGreaterEqual(first_id, 1001)
        self.assertLess(first_id, 4000)

    def test_reaching_edge_does_not_server_warp_early(self):
        world = self.make_world()
        p, state = self.make_player(world, "edgehero", "wm_road")
        p.x = world.MAP_WIDTH // 2 * 2
        p.y = 2
        world._move(p, state, "#1")
        self.assertEqual(p.area, "wm_road")
        self.assertEqual(p.y, 0)

    def test_tl_native_trigger_changes_area(self):
        world = self.make_world()
        p, state = self.make_player(world, "portalhero", "wm_road")
        trigger_id, route = next(
            (tid, route) for tid, route in world.trigger_routes.items()
            if route["source"] == "wm_road" and route["cardinal"] == "north"
        )
        world.handle_commands([f"t l{trigger_id}"], state)
        self.assertEqual(p.area, route["target"])
        self.assertEqual((p.x, p.y), (route["x"], route["y"]))

    def test_all_reconstructed_interiors_have_return_door(self):
        world = self.make_world()
        for area in (
            "wm_bar", "wm_shop", "wm_luffyhouse", "mb_bar", "mb_registry",
            "mb_trial", "mb_canteen", "mb_prison", "mb_church", "mb_barracks",
        ):
            specs = world._door_specs(area)
            self.assertTrue(specs, area)
            self.assertTrue(any("返回" in spec[0] for spec in specs), area)

    def test_key_1_personal_menu_uses_hzw_terms(self):
        world = self.make_world()
        _p, state = self.make_player(world, "personal")
        reply = world.handle_commands(["1"], state)
        text = "\n".join(x for x in reply if isinstance(x, str))
        self.assertIn("个人菜单", text)
        self.assertIn("副官指令", text)
        self.assertIn("战斗技能", text)
        self.assertNotIn("宠物", text)
        self.assertNotIn("武功", text)

    def test_key_0_system_menu_uses_guild_term(self):
        world = self.make_world()
        _p, state = self.make_player(world, "system")
        reply = world.handle_commands(["0"], state)
        text = "\n".join(x for x in reply if isinstance(x, str))
        self.assertIn("系统菜单", text)
        self.assertIn("公会指令", text)
        self.assertNotIn("帮派", text)

    def test_key_5_immediately_returns_nearby_menu(self):
        world = self.make_world()
        p, state = self.make_player(world, "nearby", "wm_square")
        first = next(iter(state.metadata["chapter_objects"].values()))
        p.x, p.y = int(first["x"]), max(0, int(first["y"]) - 2)
        reply = world.handle_commands(["5"], state)
        text = "\n".join(x for x in reply if isinstance(x, str))
        self.assertIn("附近目标", text)
        self.assertIn("npc1", text)

    def test_key_9_shows_task_outside_battle_and_toggles_auto_in_battle(self):
        world = self.make_world()
        _p, state = self.make_player(world, "taskkey")
        reply = world.handle_commands(["9"], state)
        self.assertTrue(any("<pmg>" in x for x in reply if isinstance(x, str)))
        state.metadata["battle"] = {"monster": "axe_gang", "hp": 10, "round": 1}
        reply = world.handle_commands(["9"], state)
        self.assertTrue(state.metadata["battle"]["auto"])
        self.assertTrue(any("自动战斗已开启" in x for x in reply if isinstance(x, str)))

    def test_gate_resets_to_safe_spawn(self):
        world = self.make_world()
        p, state = self.make_player(world, "stuck", "wm_square")
        p.x, p.y = 46, 46
        world.handle_commands(["gate"], state)
        self.assertEqual((p.x, p.y), tuple(world.chapter.area("wm_square")["spawn"]))


if __name__ == "__main__":
    unittest.main()
