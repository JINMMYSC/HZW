from __future__ import annotations

import logging
import re
from pathlib import Path

import server as legacy
from chapter_engine import ChapterEngine, PlayerState
from hzw_protocol import SessionState
from world_protocol import (
    join_server_parts,
    make_entity_record,
    make_map_download_block,
    make_map_switch_record,
    make_tiled_map,
)

LOG = logging.getLogger("hzw860.chapters")
legacy.join_server_lines = join_server_parts

ROOT = Path(__file__).resolve().parent
CONTENT_FILE = ROOT / "content" / "windmill_marine.json"


class WindmillMarineWorld(legacy.CompatWorld):
    PLAYER_TEMPLATE = 53
    DOOR_TEMPLATE = 303
    MAP_WIDTH = 24
    MAP_HEIGHT = 24
    PLAYER_ID = 1

    TURN = {
        "#7": ("north", 1, 0, -2), "#10": ("south", 6, 0, 2),
        "#13": ("west", 2, -2, 0), "#16": ("east", 5, 2, 0),
    }
    STEP = {
        "#1": ("north", 1, 0, -2), "#2": ("south", 6, 0, 2),
        "#3": ("west", 2, -2, 0), "#4": ("east", 5, 2, 0),
    }
    SPECIAL_STEP = {
        "#5": ("north", 1, -2, -2), "#6": ("north", 1, 2, -2),
        "#8": ("south", 6, -2, 2), "#9": ("south", 6, 2, 2),
        "#11": ("west", 2, -2, -2), "#12": ("west", 2, -2, 2),
        "#14": ("east", 5, 2, -2), "#15": ("east", 5, 2, 2),
    }

    # Reconstructed interior entries from surviving walkthrough topology.
    DOORS = {
        "wm_square": [("风车酒吧", "wm_bar", 6, 8), ("杂货/木材商店", "wm_shop", 10, 8), ("路飞家", "wm_luffyhouse", 14, 8)],
        "mb_center": [("海军基地酒吧", "mb_bar", 8, 8), ("副官登记处", "mb_registry", 16, 8)],
        "mb_training": [("餐馆/食堂", "mb_canteen", 8, 8), ("监狱", "mb_prison", 16, 8)],
        "mb_hq": [("教堂", "mb_church", 8, 8), ("海军宿舍", "mb_barracks", 16, 8)],
    }
    AUTO_AREA_ITEMS = {"wm_shop": ["墨水"], "wm_cave": ["航海日记", "银币袋"], "mb_hq": ["摩根的信"]}

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.chapter = ChapterEngine(CONTENT_FILE, data_dir)
        self.map_cache: dict[str, bytes] = {}
        self.cache_key_to_area: dict[str, str] = {}

    @staticmethod
    def login_success_payload() -> list[str | bytes]:
        return ["<log_suc>"]

    @staticmethod
    def _base_passthrough(cmd: str) -> bool:
        return (
            cmd == "new" or ("\x1f" in cmd and "\x1e" in cmd)
            or ".860" in cmd or "860." in cmd or "NON5800" in cmd
            or cmd.startswith("quit") or cmd in {"0", "menu", "sys", "compat status", "enter world"}
        )

    @staticmethod
    def _map_token(area_id: str) -> str:
        return ("hz" + re.sub(r"[^a-z0-9]", "", area_id.lower()))[:22] + "00"

    @classmethod
    def _map_cache_key(cls, area_id: str) -> str:
        token = cls._map_token(area_id)
        return token[:-2] + "sj"

    def _area_map(self, area_id: str) -> bytes:
        if area_id not in self.map_cache:
            area = self.chapter.area(area_id)
            self.map_cache[area_id] = make_tiled_map(
                self.MAP_WIDTH, self.MAP_HEIGHT, tileset_id=int(area["tileset"]), tile_flags=0x3F
            )
            self.cache_key_to_area[self._map_cache_key(area_id)] = area_id
        return self.map_cache[area_id]

    @staticmethod
    def _obj_map(state: SessionState) -> dict[int, dict]:
        return state.metadata.setdefault("chapter_objects", {})

    def _alloc_objects(self, p: PlayerState, state: SessionState) -> list[str | bytes]:
        parts: list[str | bytes] = []
        objects: dict[int, dict] = {}
        oid = 100
        for npc_id, npc in self.chapter.npcs_in_area(p.area):
            nx, ny = map(int, npc["pos"])
            parts.append(make_entity_record(npc["name"], int(npc["template"]), 6, oid, nx, ny))
            parts.append(f"<r>npc{oid}:b")  # recovered action b = 交谈
            objects[oid] = {"kind": "npc", "id": npc_id, "x": nx, "y": ny}
            oid += 1
        for label, target, x, y in self.DOORS.get(p.area, []):
            parts.append(make_entity_record(label, self.DOOR_TEMPLATE, 6, oid, x, y))
            parts.append(f"<r>npc{oid}:;[enter]进入")
            objects[oid] = {"kind": "door", "target": target, "x": x, "y": y}
            oid += 1
        for monster_id, monster in self.chapter.monsters_in_area(p.area):
            mx, my = 6 + ((oid * 3) % 12), 12 + ((oid * 5) % 8)
            parts.append(make_entity_record(monster["name"], int(monster["template"]), 2, oid, mx, my))
            parts.append(f"<r>npc{oid}:h")  # recovered action h = 击杀
            objects[oid] = {"kind": "monster", "id": monster_id, "x": mx, "y": my}
            oid += 1
        state.metadata["chapter_objects"] = objects
        return parts

    def _spawn_area(self, p: PlayerState, state: SessionState, notice: str | None = None) -> list[str | bytes]:
        area = self.chapter.area(p.area)
        token = self._map_token(p.area)
        self._area_map(p.area)
        state.metadata["world_initialized"] = True
        parts: list[str | bytes] = [f"<title>{area['name']}"]
        if notice:
            parts.append(f"<smg>{notice}")
        parts.extend([
            make_map_switch_record(token),
            make_entity_record(p.username or "航海者", self.PLAYER_TEMPLATE, p.direction, self.PLAYER_ID, p.x, p.y),
        ])
        parts.extend(self._alloc_objects(p, state))
        parts.append("<r>walk 1")
        LOG.info("AREA spawn user=%s area=%s pos=(%d,%d)", p.username, p.area, p.x, p.y)
        return parts

    @staticmethod
    def _distance(p: PlayerState, obj: dict) -> int:
        return abs(p.x - int(obj.get("x", 0))) + abs(p.y - int(obj.get("y", 0)))

    def _nearest(self, state: SessionState, p: PlayerState, max_distance: int = 7):
        best = None
        for oid, obj in self._obj_map(state).items():
            d = self._distance(p, obj)
            if d <= max_distance and (best is None or d < best[0]):
                best = (d, int(oid), obj)
        return best

    def _auto_script(self, p: PlayerState, source: str) -> list[str]:
        messages: list[str] = []
        main = self.chapter.current_main(p)
        if not main:
            return messages
        q, idx = main["quest"], main["step_index"]
        if idx >= len(q["steps"]):
            return messages
        step = q["steps"][idx]
        if source == "area":
            for item in self.AUTO_AREA_ITEMS.get(p.area, []):
                if step.get("type") == "collect" and step.get("item") == item:
                    messages += self.chapter.record_event(p, {"type": "collect", "item": item, "count": 1})
                    messages.append(f"取得：{item}")
                    break
        if source.startswith("talk:"):
            npc_id = source.split(":", 1)[1]
            if npc_id == "wm_shenfan" and step.get("type") == "collect" and step.get("item") == "船帆":
                messages += self.chapter.record_event(p, {"type": "collect", "item": "船帆", "count": 1})
                messages.append("取得：船帆")
            if npc_id == "wm_hait":
                main2 = self.chapter.current_main(p)
                if main2 and main2["quest"]["id"] == "wm10":
                    p.give_item("新手炮", 1)
                    self.chapter.record_event(p, {"type": "equip", "item": "新手炮"})
                    self.chapter.record_event(p, {"type": "learn", "skill": "初级炮术"})
                    messages.append("获得并装备：新手炮；学会：初级炮术")
            if npc_id == "mb_landlady" and step.get("type") == "collect" and step.get("item") == "老板娘的帽子":
                messages += self.chapter.record_event(p, {"type": "collect", "item": "老板娘的帽子", "count": 1})
                messages.append("取得：老板娘的帽子")
        self.chapter.save_player(p)
        return messages

    def _talk(self, p: PlayerState, state: SessionState, npc_id: str) -> list[str | bytes]:
        lines = self.chapter.talk(p, npc_id)
        lines += self._auto_script(p, f"talk:{npc_id}")
        if npc_id == "wm_mate" and "风车镇完成" in p.flags:
            p.area = "mb_entrance"
            p.x, p.y = map(int, self.chapter.area(p.area)["spawn"])
            self.chapter.record_event(p, {"type": "enter", "area": p.area})
            return ["<pmg>大副：准备出海，下一站海军基地。"] + self._spawn_area(p, state, "已抵达海军基地。")
        return ["<pmg>" + "\x1a".join(lines)]

    def _enter_area(self, p: PlayerState, state: SessionState, target: str) -> list[str | bytes]:
        if target not in self.chapter.areas:
            return ["<smg>该入口尚未恢复。"]
        p.area = target
        p.x, p.y = map(int, self.chapter.area(target)["spawn"])
        self.chapter.record_event(p, {"type": "visit", "area": target})
        self.chapter.record_event(p, {"type": "enter", "area": target})
        auto = self._auto_script(p, "area")
        self.chapter.save_player(p)
        return self._spawn_area(p, state, "；".join(auto) if auto else None)

    def _portal(self, p: PlayerState, state: SessionState, cardinal: str) -> list[str | bytes] | None:
        portal = self.chapter.area(p.area).get("portals", {}).get(cardinal)
        if not portal:
            return None
        target, x, y = portal
        p.area, p.x, p.y = target, int(x), int(y)
        self.chapter.record_event(p, {"type": "visit", "area": target})
        self.chapter.record_event(p, {"type": "enter", "area": target})
        auto = self._auto_script(p, "area")
        self.chapter.save_player(p)
        return self._spawn_area(p, state, "；".join(auto) if auto else None)

    def _move(self, p: PlayerState, state: SessionState, cmd: str) -> list[str | bytes] | None:
        if cmd in self.TURN:
            _, code, _, _ = self.TURN[cmd]
            p.direction = code
            self.chapter.save_player(p)
            return []  # smooth: never type-7 teleport normal turns
        spec = self.STEP.get(cmd) or self.SPECIAL_STEP.get(cmd)
        if spec is None:
            return None
        cardinal, code, dx, dy = spec
        p.direction, p.x, p.y = code, p.x + dx, p.y + dy
        if cardinal == "west" and p.x <= 2:
            switched = self._portal(p, state, "west")
            if switched: return switched
        if cardinal == "east" and p.x >= (self.MAP_WIDTH - 2) * 2:
            switched = self._portal(p, state, "east")
            if switched: return switched
        if cardinal == "north" and p.y <= 2:
            switched = self._portal(p, state, "north")
            if switched: return switched
        if cardinal == "south" and p.y >= (self.MAP_HEIGHT - 2) * 2:
            switched = self._portal(p, state, "south")
            if switched: return switched
        p.x = max(2, min((self.MAP_WIDTH - 2) * 2, p.x))
        p.y = max(2, min((self.MAP_HEIGHT - 2) * 2, p.y))
        self.chapter.save_player(p)
        LOG.debug("MOVE smooth user=%s area=%s cmd=%s pos=(%d,%d)", p.username, p.area, cmd, p.x, p.y)
        return []

    def _battle_menu(self, p: PlayerState, state: SessionState, monster_id: str) -> list[str | bytes]:
        monster = self.chapter.monsters[monster_id]
        state.metadata["battle"] = {"monster": monster_id, "hp": int(monster["hp"]), "round": 1}
        return [
            f"<title>战斗：{monster['name']}", f"<pmg>{monster['name']}出现了！",
            "<menu(g:a)>战斗指令|[battle attack]普通攻击|[battle skill]战斗技能|[battle item]使用物品|[battle flee]逃跑",
        ]

    def _item_needed(self, p: PlayerState, item: str) -> bool:
        for qid, idx in p.active_quests.items():
            q = self.chapter.quests.get(qid)
            if q and idx < len(q["steps"]):
                step = q["steps"][idx]
                if step.get("type") == "collect" and step.get("item") == item:
                    return True
        return False

    def _battle_action(self, p: PlayerState, state: SessionState, action: str) -> list[str | bytes]:
        battle = state.metadata.get("battle")
        if not battle: return ["<smg>当前没有战斗。"]
        monster_id = battle["monster"]
        monster = self.chapter.monsters[monster_id]
        if action == "flee":
            state.metadata.pop("battle", None); return ["<smg>你离开了战斗。"]
        if action == "item":
            if p.inventory.get("中瓶回复剂", 0) > 0:
                p.inventory["中瓶回复剂"] -= 1; p.hp = min(p.max_hp, p.hp + 50); self.chapter.save_player(p)
                return [f"<pmg>使用中瓶回复剂，生命恢复到 {p.hp}/{p.max_hp}。"]
            return ["<smg>没有可用的回复剂。"]
        damage = 14 + p.level * 4 + (8 if action == "skill" and p.skills else 0)
        battle["hp"] = max(0, int(battle["hp"]) - damage)
        if battle["hp"] <= 0:
            state.metadata.pop("battle", None)
            lines = [f"击败了{monster['name']}。"]
            p.exp += int(monster.get("exp", 0))
            for item, chance in (monster.get("drops") or {}).items():
                if float(chance) >= 1.0 or self._item_needed(p, item):
                    p.give_item(item, 1); lines.append(f"获得：{item}")
                    lines += self.chapter.record_event(p, {"type": "collect", "item": item, "count": 1})
            lines += self.chapter.record_event(p, {"type": "kill", "monster": monster_id, "count": 1})
            self.chapter._recalculate_level(p); self.chapter.save_player(p)
            return ["<pmg>" + "\x1a".join(lines)]
        retaliation = max(1, int(monster["atk"]) - p.level)
        p.hp = max(1, p.hp - retaliation); self.chapter.save_player(p)
        return [
            f"<pmg>你造成 {damage} 点伤害。\x1a{monster['name']}剩余 {battle['hp']} 生命。\x1a你受到 {retaliation} 点伤害。",
            "<menu(g:a)>战斗指令|[battle attack]普通攻击|[battle skill]战斗技能|[battle item]使用物品|[battle flee]逃跑",
        ]

    def _npc_command(self, p: PlayerState, state: SessionState, oid: int, action: str) -> list[str | bytes]:
        obj = self._obj_map(state).get(oid)
        if not obj: return ["<smg>目标已经离开。"]
        if self._distance(p, obj) > 10: return ["<smg>距离太远。"]
        if obj["kind"] == "npc": return self._talk(p, state, obj["id"])
        if obj["kind"] == "door": return self._enter_area(p, state, obj["target"])
        if obj["kind"] == "monster": return self._battle_menu(p, state, obj["id"])
        return []

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str | bytes]:
        base_commands: list[str] = []
        responses: list[str | bytes] = []
        p = self.chapter.load_player(state.username) if state.username else None
        for cmd in commands:
            if cmd.startswith("#map 60"):
                requested = cmd[len("#map 60"):].strip()
                area_id = self.cache_key_to_area.get(requested)
                if area_id is None:
                    area_id = next((aid for aid in self.chapter.areas if requested == self._map_cache_key(aid)), None)
                if area_id:
                    m = self._area_map(area_id); responses.append(make_map_download_block(requested, m))
                continue
            if p is not None:
                moved = self._move(p, state, cmd)
                if moved is not None: responses.extend(moved); continue
                match = re.match(r"^npc(\d+)\s+(.+)$", cmd)
                if match:
                    responses.extend(self._npc_command(p, state, int(match.group(1)), match.group(2).strip())); continue
                if cmd == "5":
                    near = self._nearest(state, p)
                    if near: responses.extend(self._npc_command(p, state, near[1], "b"))
                    else: responses.append("<smg>附近没有可以互动的目标。")
                    continue
                if cmd == "9" or cmd in {"task", "quest"}:
                    responses.append("<pmg>" + "\x1a".join(self.chapter.status_lines(p))); continue
                if cmd.startswith("battle "):
                    responses.extend(self._battle_action(p, state, cmd.split(" ", 1)[1].strip())); continue
                if cmd.startswith("petcmd"):
                    responses.append("<smg>副官系统：基础副官由海军基地支线《航海的副官》获得。"); continue
                if cmd == "guild" or cmd.startswith("guild "):
                    responses.append("<smg>公会功能不属于当前两章强制主线。"); continue
            if cmd.startswith("loginzhuowang") or re.match(r"^\d+\s+\d+$", cmd) or cmd == "?" or cmd.startswith("#maps") or cmd.startswith("#chs"):
                continue
            if self._base_passthrough(cmd): base_commands.append(cmd)
            else: LOG.info("Unimplemented chapter command: %r", cmd)
        if base_commands:
            base_responses = super().handle_commands(base_commands, state); responses[:0] = base_responses
            if state.logged_in and not state.metadata.get("world_initialized") and any(part == "<log_suc>" for part in base_responses if isinstance(part, str)):
                p = self.chapter.load_player(state.username)
                responses.extend(self._spawn_area(p, state, "风车镇与海军基地复原章节已载入。"))
        return responses


class WindmillMarineServer(legacy.HZWCompatServer):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = WindmillMarineWorld(data_dir)


legacy.HZWCompatServer = WindmillMarineServer

if __name__ == "__main__":
    legacy.main()
