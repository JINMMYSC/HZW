import tempfile
import unittest
from pathlib import Path

from hzw_protocol import SessionState
from chapter_server import WindmillMarineWorld


class ChapterServerTests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return WindmillMarineWorld(Path(tmp.name))

    def test_normal_step_is_smooth_no_type7_echo(self):
        world = self.make_world()
        p = world.chapter.load_player("smooth")
        state = SessionState(username="smooth", logged_in=True)
        p.area = "wm_road"; p.x = 10; p.y = 10
        response = world._move(p, state, "#4")
        self.assertEqual(response, [])
        self.assertEqual((p.x, p.y, p.direction), (12, 10, 5))

    def test_turn_is_local_no_teleport(self):
        world = self.make_world()
        p = world.chapter.load_player("turner")
        state = SessionState(username="turner", logged_in=True)
        old = (p.x, p.y)
        response = world._move(p, state, "#16")
        self.assertEqual(response, [])
        self.assertEqual((p.x, p.y), old)
        self.assertEqual(p.direction, 5)

    def test_spawn_exposes_real_npc_talk_actions(self):
        world = self.make_world()
        p = world.chapter.load_player("npcuser")
        state = SessionState(username="npcuser", logged_in=True)
        payload = world._spawn_area(p, state)
        self.assertTrue(any(isinstance(x, str) and x.startswith("<r>npc") and x.endswith(":b") for x in payload))

    def test_area_map_uses_v860_walkability_byte(self):
        world = self.make_world()
        m = world._area_map("wm_road")
        self.assertEqual(m[23] & 0x3F, 0x3F)

    def test_windmill_to_marine_transition_requires_completion_flag(self):
        world = self.make_world()
        p = world.chapter.load_player("sailor")
        state = SessionState(username="sailor", logged_in=True)
        p.area = "wm_eastport"; p.flags.append("风车镇完成")
        response = world._talk(p, state, "wm_mate")
        self.assertEqual(p.area, "mb_entrance")
        self.assertTrue(any(isinstance(x, str) and "海军基地" in x for x in response))


if __name__ == "__main__":
    unittest.main()
