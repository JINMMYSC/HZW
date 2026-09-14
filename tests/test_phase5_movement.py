import tempfile
import unittest
from pathlib import Path

from hzw_protocol import SessionState
from phase3_server import Phase5World


class Phase5MovementTests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Phase5World(Path(tmp.name))

    def test_bootstrap_map_is_walkable(self):
        world = self.make_world()
        self.assertEqual(world.local_map[21] & 0x3F, 0x3F)

    def test_exact_direction_commands_recovered_from_client(self):
        world = self.make_world()
        state = SessionState()
        responses = world.handle_commands(["#7", "#10", "#13", "#16"], state)
        self.assertEqual(responses, [])
        self.assertEqual(state.metadata["turn_events"], 4)
        self.assertEqual(state.metadata["last_direction"], "RIGHT")

    def test_flat_step_commands_are_tracked_without_echo(self):
        world = self.make_world()
        state = SessionState()
        responses = world.handle_commands(["#1", "#2", "#3", "#4"], state)
        self.assertEqual(responses, [])
        self.assertEqual(state.metadata["step_events"], 4)
        self.assertEqual(state.metadata["last_direction"], "RIGHT")

    def test_hzw_terminology_for_shared_engine_commands(self):
        world = self.make_world()
        state = SessionState()
        responses = world.handle_commands(["petcmd 1", "guild"], state)
        self.assertIn("<smg>副官系统协议恢复中", responses)
        self.assertIn("<smg>公会系统协议恢复中", responses)


if __name__ == "__main__":
    unittest.main()
