from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PlayerState:
    username: str
    area: str = "wm_ship"
    x: int = 10
    y: int = 18
    direction: int = 6
    level: int = 1
    exp: int = 0
    silver: int = 0
    reputation: int = 0
    hp: int = 100
    max_hp: int = 100
    inventory: dict[str, int] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    active_quests: dict[str, int] = field(default_factory=dict)
    completed_quests: list[str] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)

    def give_item(self, name: str, count: int = 1) -> None:
        self.inventory[name] = int(self.inventory.get(name, 0)) + int(count)

    def has_item(self, name: str, count: int = 1) -> bool:
        return int(self.inventory.get(name, 0)) >= int(count)

    def add_flag(self, flag: str) -> None:
        if flag not in self.flags:
            self.flags.append(flag)


class ChapterEngine:
    def __init__(self, content_file: Path, data_dir: Path):
        self.content_file = Path(content_file)
        self.data_dir = Path(data_dir)
        self.players_dir = self.data_dir / "players"
        self.players_dir.mkdir(parents=True, exist_ok=True)
        self.content = json.loads(self.content_file.read_text("utf-8"))
        self.areas = self.content["areas"]
        self.npcs = self.content["npcs"]
        self.monsters = self.content["monsters"]
        self.quests = {q["id"]: q for q in self.content["quests"]}
        self._players: dict[str, PlayerState] = {}

    @staticmethod
    def _safe_name(username: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", username or "guest")[:80]

    def player_file(self, username: str) -> Path:
        return self.players_dir / f"{self._safe_name(username)}.json"

    def load_player(self, username: str) -> PlayerState:
        if username in self._players:
            return self._players[username]
        path = self.player_file(username)
        if path.exists():
            try:
                raw = json.loads(path.read_text("utf-8"))
                allowed = set(PlayerState.__dataclass_fields__)
                raw = {k: v for k, v in raw.items() if k in allowed}
                state = PlayerState(**raw)
            except Exception:
                state = PlayerState(username=username)
        else:
            state = PlayerState(username=username)
        self._players[username] = state
        self.ensure_main_quest(state)
        self.save_player(state)
        return state

    def save_player(self, state: PlayerState) -> None:
        self._players[state.username] = state
        self.player_file(state.username).write_text(
            json.dumps(asdict(state), ensure_ascii=False, indent=2), "utf-8"
        )

    def area(self, area_id: str) -> dict[str, Any]:
        return self.areas[area_id]

    def npcs_in_area(self, area_id: str) -> list[tuple[str, dict[str, Any]]]:
        return [(nid, n) for nid, n in self.npcs.items() if n["area"] == area_id]

    def monsters_in_area(self, area_id: str) -> list[tuple[str, dict[str, Any]]]:
        return [(mid, m) for mid, m in self.monsters.items() if m["area"] == area_id]

    def quest_available(self, state: PlayerState, qid: str) -> bool:
        if qid in state.completed_quests or qid in state.active_quests:
            return False
        q = self.quests[qid]
        prereq = q.get("prereq") or []
        if isinstance(prereq, str):
            prereq = [prereq]
        return all(p in state.completed_quests for p in prereq)

    def ensure_main_quest(self, state: PlayerState) -> None:
        if any(
            self.quests[qid]["kind"] == "main"
            for qid in state.active_quests
            if qid in self.quests
        ):
            return
        for q in self.content["quests"]:
            if q["kind"] == "main" and self.quest_available(state, q["id"]):
                state.active_quests[q["id"]] = 0
                return

    def current_main(self, state: PlayerState) -> dict[str, Any] | None:
        for qid, step in state.active_quests.items():
            q = self.quests.get(qid)
            if q and q["kind"] == "main":
                return {"quest": q, "step_index": int(step)}
        return None

    def nearest_npc(self, state: PlayerState, max_distance: int = 6) -> str | None:
        best: tuple[int, str] | None = None
        for npc_id, npc in self.npcs_in_area(state.area):
            nx, ny = npc["pos"]
            d = abs(state.x - int(nx)) + abs(state.y - int(ny))
            if d <= max_distance and (best is None or d < best[0]):
                best = (d, npc_id)
        return None if best is None else best[1]

    def start_side_quests_for_npc(self, state: PlayerState, npc_id: str) -> list[str]:
        started = []
        for q in self.content["quests"]:
            if (
                q["kind"] == "side"
                and q["start_npc"] == npc_id
                and self.quest_available(state, q["id"])
            ):
                state.active_quests[q["id"]] = 0
                started.append(q["id"])
        return started

    def _event_matches(self, step: dict[str, Any], event: dict[str, Any]) -> bool:
        t = step.get("type")
        if t != event.get("type"):
            return False
        if t == "talk":
            return step.get("npc") == event.get("npc")
        if t in {"visit", "enter"}:
            return step.get("area") == event.get("area")
        if t in {"collect", "equip"}:
            return step.get("item") == event.get("item")
        if t == "learn":
            return step.get("skill") == event.get("skill")
        if t == "kill":
            return step.get("monster") == event.get("monster")
        if t == "rescue":
            return step.get("target") == event.get("target")
        if t == "defeat_sequence":
            return step.get("target") == event.get("target")
        if t == "talk_cycle":
            return event.get("npc") in (step.get("npcs") or [])
        return False

    @staticmethod
    def _counter_key(qid: str, step_index: int) -> str:
        return f"{qid}:{step_index}"

    @staticmethod
    def _step_target_count(step: dict[str, Any]) -> int:
        if step["type"] == "talk_cycle":
            return int(step.get("rounds", 1)) * len(step.get("npcs") or [])
        return int(step.get("count", 1))

    def _consume_event(self, state: PlayerState, qid: str, event: dict[str, Any]) -> bool:
        q = self.quests[qid]
        step_index = int(state.active_quests[qid])
        if step_index >= len(q["steps"]):
            return False
        step = q["steps"][step_index]
        if not self._event_matches(step, event):
            return False
        key = self._counter_key(qid, step_index)
        amount = int(event.get("count", 1))
        state.counters[key] = int(state.counters.get(key, 0)) + amount
        if state.counters[key] < self._step_target_count(step):
            return True
        state.active_quests[qid] = step_index + 1
        if state.active_quests[qid] >= len(q["steps"]):
            self._complete_quest(state, qid)
        return True

    def _complete_quest(self, state: PlayerState, qid: str) -> None:
        q = self.quests[qid]
        rewards = q.get("rewards") or {}
        state.exp += int(rewards.get("exp", 0))
        state.silver += int(rewards.get("silver", 0))
        state.reputation += int(rewards.get("reputation", 0))
        for item, count in (rewards.get("items") or {}).items():
            state.give_item(item, int(count))
        for flag in rewards.get("flags") or []:
            state.add_flag(flag)
        state.active_quests.pop(qid, None)
        if not q.get("repeatable") and qid not in state.completed_quests:
            state.completed_quests.append(qid)
        self._recalculate_level(state)
        self.ensure_main_quest(state)

    @staticmethod
    def _recalculate_level(state: PlayerState) -> None:
        thresholds = [0, 50, 130, 260, 450, 700, 1000, 1400, 1900, 2500, 3200]
        level = 1
        for i, xp in enumerate(thresholds[1:], start=2):
            if state.exp >= xp:
                level = i
        state.level = max(state.level, level)
        state.max_hp = 100 + (state.level - 1) * 18
        state.hp = min(state.hp, state.max_hp)

    def record_event(self, state: PlayerState, event: dict[str, Any]) -> list[str]:
        messages: list[str] = []
        if event.get("type") in {"enter", "visit"} and event.get("area") in self.areas:
            state.area = event["area"]
        if event.get("type") == "collect":
            state.give_item(str(event["item"]), int(event.get("count", 1)))
        if event.get("type") == "learn":
            skill = str(event["skill"])
            if skill not in state.skills:
                state.skills.append(skill)
        if event.get("type") == "talk" and event.get("npc"):
            self.start_side_quests_for_npc(state, str(event["npc"]))
        before_completed = set(state.completed_quests)
        for qid in list(state.active_quests):
            if qid in self.quests:
                self._consume_event(state, qid, event)
        for qid in state.completed_quests:
            if qid not in before_completed:
                messages.append(f"任务完成：{self.quests[qid]['title']}")
        self.ensure_main_quest(state)
        self.save_player(state)
        return messages

    def talk(self, state: PlayerState, npc_id: str) -> list[str]:
        npc = self.npcs[npc_id]
        messages = [f"{npc['name']}："]
        main = self.current_main(state)
        if main:
            q = main["quest"]
            idx = main["step_index"]
            if idx < len(q["steps"]) and q["steps"][idx].get("type") == "talk" and q["steps"][idx].get("npc") == npc_id:
                messages.append(f"主线《{q['title']}》推进。")
        messages.extend(self.record_event(state, {"type": "talk", "npc": npc_id}))
        main_after = self.current_main(state)
        if main_after:
            q = main_after["quest"]
            idx = main_after["step_index"]
            if idx < len(q["steps"]):
                messages.append(f"下一目标：{self.describe_step(q['steps'][idx])}")
        else:
            messages.append("风车镇与海军基地主线已完成。")
        return messages

    def describe_step(self, step: dict[str, Any]) -> str:
        t = step["type"]
        if t == "talk":
            return f"与{self.npcs[step['npc']]['name']}交谈"
        if t in {"visit", "enter"}:
            return f"前往{self.areas[step['area']]['name']}"
        if t == "kill":
            return f"击败{self.monsters[step['monster']]['name']} ×{step.get('count',1)}"
        if t == "collect":
            return f"取得{step['item']} ×{step.get('count',1)}"
        if t == "equip":
            return f"装备{step['item']}"
        if t == "learn":
            return f"学习{step['skill']}"
        if t == "rescue":
            return f"救出{step['target']}"
        if t == "defeat_sequence":
            return f"战胜{step['target']} ×{step.get('count',1)}"
        if t == "talk_cycle":
            return "在指定NPC之间往返"
        return t

    def status_lines(self, state: PlayerState) -> list[str]:
        area = self.areas[state.area]["name"]
        main = self.current_main(state)
        lines = [
            f"区域：{area}",
            f"等级：{state.level}  实战经验：{state.exp}",
            f"银币：{state.silver}  声望：{state.reputation}",
        ]
        if main:
            q = main["quest"]
            idx = main["step_index"]
            lines.append(f"主线：{q['title']}")
            if idx < len(q["steps"]):
                lines.append("目标：" + self.describe_step(q["steps"][idx]))
        else:
            lines.append("主线：风车镇与海军基地已完成")
        return lines
