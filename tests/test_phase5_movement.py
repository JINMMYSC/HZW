import tempfile
import unittest
from pathlib import Path

from hzw_protocol import SessionState
from phase3_server import Phase6World
from world_protocol import make_position_record


class Phase6MovementTests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Phase6World(Path(tmp.name))

    def test_bootstrap_map_uses_real_cell3_walkability_byte(self):
        world = self.make_world()
        self.assertEqual(world.local_map[23] & 0x3F, 0x3F)
        self.assertEqual(world.local_map[21], 0)

    def test_turn_then_repeated_turn_fallback_moves(self):
        world = self.make_world()
        state = SessionState()
        state.metadata.update({"player_x": 10, "player_y": 10, "direction_code": 6})

        first = world.handle_commands(["#16"], state)
        self.assertIn(make_position_record(1, 10, 10, 5), first)
        self.assertEqual((state.metadata["player_x"], state.metadata["player_y"]), (10, 10))

        second = world.handle_commands(["#16"], state)
        self.assertIn(make_position_record(1, 12, 10, 5), second)
        self.assertEqual((state.metadata["player_x"], state.metadata["player_y"]), (12, 10))

    def test_flat_step_command_updates_coordinates_and_returns_type7(self):
        world = self.make_world()
        state = SessionState(username="tester")
        state.metadata.update({"player_x": 10, "player_y": 10, "direction_code": 5})
        responses = world.handle_commands(["#4"], state)
        self.assertIn(make_position_record(1, 12, 10, 5), responses)
        self.assertEqual(world.saved_positions["tester"], (12, 10, 5))

    def test_key5_dialogue_near_guide(self):
        world = self.make_world()
        state = SessionState()
        state.metadata.update({"player_x": 12, "player_y": 10, "direction_code": 5})
        responses = world.handle_commands(["5"], state)
        self.assertTrue(any("测试向导：" in x for x in responses if isinstance(x, str)))

    def test_hzw_terminology_for_shared_engine_commands(self):
        world = self.make_world()
        state = SessionState()
        responses = world.handle_commands(["petcmd 1", "guild"], state)
        self.assertIn("<smg>副官系统协议恢复中", responses)
        self.assertIn("<smg>公会系统协议恢复中", responses)


if __name__ == "__main__":
    unittest.main()
