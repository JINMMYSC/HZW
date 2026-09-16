import tempfile
import unittest
from pathlib import Path

from hzw_protocol import SessionState
from chapter_server_v2 import WindmillMarineWorldV2


class ChapterFlowV2Tests(unittest.TestCase):
    def make_world(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return WindmillMarineWorldV2(Path(tmp.name))

    def test_deputy_trial_room_is_reachable_from_registry(self):
        world = self.make_world()
        targets = {target for _label, target, _x, _y in world.DOORS["mb_registry"]}
        self.assertIn("mb_trial", targets)
        self.assertIn("novice_examiner", world.chapter.monsters)
        self.assertEqual(world.chapter.monsters["novice_examiner"]["area"], "mb_trial")

    def test_cave_collects_both_consecutive_quest_items(self):
        world = self.make_world()
        p = world.chapter.load_player("cavehero")
        p.active_quests = {"wm07": 2}
        p.completed_quests = [f"wm{i:02d}" for i in range(1, 7)]
        p.area = "wm_cave"
        world._auto_script(p, "area")
        self.assertEqual(p.active_quests["wm07"], 4)
        self.assertGreaterEqual(p.inventory.get("航海日记", 0), 1)
        self.assertGreaterEqual(p.inventory.get("银币袋", 0), 1)

    def test_kill_then_critical_drop_advances_following_collect_step(self):
        world = self.make_world()
        p = world.chapter.load_player("fighter")
        p.active_quests = {"wm11": 0}
        p.completed_quests = [f"wm{i:02d}" for i in range(1, 11)]
        state = SessionState(username="fighter", logged_in=True)
        state.metadata["battle"] = {"monster": "crocodile", "hp": 1, "round": 1}
        world._battle_action(p, state, "attack")
        self.assertEqual(p.active_quests["wm11"], 2)
        self.assertGreaterEqual(p.inventory.get("鳄鱼尾巴", 0), 1)

    def test_prison_rescue_is_an_interactable_swordsman(self):
        world = self.make_world()
        p = world.chapter.load_player("rescue")
        p.area = "mb_prison"
        state = SessionState(username="rescue", logged_in=True)
        world._spawn_area(p, state)
        ids = {obj.get("id") for obj in state.metadata["chapter_objects"].values()}
        self.assertIn("mb_swordsman", ids)


if __name__ == "__main__":
    unittest.main()
