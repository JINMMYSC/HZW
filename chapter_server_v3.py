from __future__ import annotations

import logging
import re
from pathlib import Path

import server as legacy
from chapter_maps import make_chapter_map
from chapter_server_v2 import WindmillMarineServerV2, WindmillMarineWorldV2
from hzw_protocol import SessionState
from world_protocol import make_entity_record

LOG = logging.getLogger("hzw860.chapters.v3")


class WindmillMarineWorldV3(WindmillMarineWorldV2):
    """V860-native interaction pass for the two restored opening regions.

    Phase V3 deliberately moves world interaction back to mechanisms recovered
    from the original client instead of approximating them in the server:

    * world entities start at id 1000 so the client treats them as collision /
      interaction objects;
    * map exits are encoded as native map triggers.  V860 sends ``t l<ID>``
      when the player reaches an exit tile;
    * normal movement never changes area merely because a server-side x/y
      threshold was reached;
    * keypad, personal menu and system menu commands are all live.
    """

    OBJECT_ID_START = 1000
    TRIGGER_ID_START = 2001
    MAX_X = (WindmillMarineWorldV2.MAP_WIDTH - 1) * 2
    MAX_Y = (WindmillMarineWorldV2.MAP_HEIGHT - 1) * 2

    # Explicit reciprocal indoor exits.  Tuples are:
    # label, target_area, object_x, object_y, destination_x, destination_y.
    RETURN_DOORS = {
        "wm_bar": [("返回风车广场", "wm_square", 12, 40, 6, 10)],
        "wm_shop": [("返回风车广场", "wm_square", 12, 40, 10, 10)],
        "wm_luffyhouse": [("返回风车广场", "wm_square", 12, 40, 14, 10)],
        "mb_bar": [("返回基地中心区", "mb_center", 12, 40, 8, 10)],
        "mb_registry": [("返回基地中心区", "mb_center", 12, 40, 16, 10)],
        "mb_trial": [("返回副官登记处", "mb_registry", 12, 40, 12, 12)],
        "mb_canteen": [("返回海军操练场", "mb_training", 12, 40, 8, 10)],
        "mb_prison": [("返回海军操练场", "mb_training", 12, 40, 16, 10)],
        "mb_church": [("返回海军总部", "mb_hq", 12, 40, 8, 10)],
        "mb_barracks": [("返回海军总部", "mb_hq", 12, 40, 16, 10)],
    }

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.trigger_routes: dict[int, dict] = {}
        self.area_triggers: dict[str, list[tuple[int, int, int]]] = {}
        self._build_native_portals()
        # V2 may have constructed a diagnostic map before V3 portal tables exist.
        # Always rebuild from the V3 map format.
        self.map_cache.clear()
        self.cache_key_to_area.clear()

    def _build_native_portals(self) -> None:
        tid = self.TRIGGER_ID_START
        edge = {
            "north": (self.MAP_WIDTH // 2, 0),
            "south": (self.MAP_WIDTH // 2, self.MAP_HEIGHT - 1),
            "west": (0, self.MAP_HEIGHT // 2),
            "east": (self.MAP_WIDTH - 1, self.MAP_HEIGHT // 2),
        }
        for area_id in sorted(self.chapter.areas):
            portals = self.chapter.area(area_id).get("portals", {}) or {}
            for cardinal in ("north", "east", "south", "west"):
                portal = portals.get(cardinal)
                if not portal:
                    continue
                target, x, y = portal
                tx, ty = edge[cardinal]
                self.area_triggers.setdefault(area_id, []).append((tx, ty, tid))
                self.trigger_routes[tid] = {
                    "source": area_id,
                    "cardinal": cardinal,
                    "target": str(target),
                    "x": int(x),
                    "y": int(y),
                }
                tid += 1

    def _area_map(self, area_id: str) -> bytes:
        if area_id not in self.map_cache:
            self.map_cache[area_id] = make_chapter_map(
                area_id,
                self.MAP_WIDTH,
                self.MAP_HEIGHT,
                triggers=self.area_triggers.get(area_id, ()),
            )
            self.cache_key_to_area[self._map_cache_key(area_id)] = area_id
        return self.map_cache[area_id]

    def _door_specs(self, area_id: str):
        # Base forward doors are 4-tuples.  V3 return doors carry destination
        # coordinates as well so entering/exiting never strands the player.
        specs = []
        for rec in self.DOORS.get(area_id, []):
            label, target, x, y = rec[:4]
            specs.append((label, target, int(x), int(y), None, None))
        specs.extend(self.RETURN_DOORS.get(area_id, []))
        return specs

    def _alloc_objects(self, p, state: SessionState) -> list[str | bytes]:
        parts: list[str | bytes] = []
        objects: dict[int, dict] = {}
        oid = self.OBJECT_ID_START

        for npc_id, npc in self.chapter.npcs_in_area(p.area):
            nx, ny = map(int, npc["pos"])
            parts.append(make_entity_record(
                npc["name"], int(npc["template"]), 6, oid, nx, ny
            ))
            # 'b' is the recovered V860 action code for 交谈.
            parts.append(f"<r>npc{oid}:b")
            objects[oid] = {
                "kind": "npc", "id": npc_id, "name": npc["name"],
                "x": nx, "y": ny, "action": "b",
            }
            oid += 1

        for label, target, x, y, dest_x, dest_y in self._door_specs(p.area):
            parts.append(make_entity_record(label, self.DOOR_TEMPLATE, 6, oid, x, y))
            parts.append(f"<r>npc{oid}:;[enter]进入")
            objects[oid] = {
                "kind": "door", "target": target, "name": label,
                "x": x, "y": y, "action": "enter",
                "dest_x": dest_x, "dest_y": dest_y,
            }
            oid += 1

        for monster_id, monster in self.chapter.monsters_in_area(p.area):
            mx, my = 6 + ((oid * 3) % 24), 12 + ((oid * 5) % 18)
            mx = min(mx, self.MAX_X - 4)
            my = min(my, self.MAX_Y - 4)
            parts.append(make_entity_record(
                monster["name"], int(monster["template"]), 2, oid, mx, my
            ))
            # 'h' is the recovered V860 action code for 击杀.
            parts.append(f"<r>npc{oid}:h")
            objects[oid] = {
                "kind": "monster", "id": monster_id, "name": monster["name"],
                "x": mx, "y": my, "action": "h",
            }
            oid += 1

        state.metadata["chapter_objects"] = objects
        state.metadata["nearest_cache"] = self._sorted_nearby(state, p, 24)
        return parts

    def _sorted_nearby(self, state: SessionState, p, radius: int = 18):
        nearby = []
        for oid, obj in self._obj_map(state).items():
            d = self._distance(p, obj)
            if d <= radius:
                nearby.append((d, int(oid), obj))
        nearby.sort(key=lambda row: (row[0], row[1]))
        return nearby

    def _nearby_menu(self, p, state: SessionState) -> list[str | bytes]:
        nearby = self._sorted_nearby(state, p, 18)
        state.metadata["nearest_cache"] = nearby
        if not nearby:
            return ["<smg>附近没有可以互动的目标。"]
        entries = []
        for _d, oid, obj in nearby[:9]:
            if obj["kind"] == "npc":
                label, action = obj.get("name", "人物"), "b"
            elif obj["kind"] == "monster":
                label, action = "攻击 " + obj.get("name", "目标"), "h"
            else:
                label, action = obj.get("name", "入口"), "enter"
            entries.append(f"[npc{oid} {action}]{label}")
        return ["<menu(g:a)>附近目标|" + "|".join(entries)]

    def _enter_object_door(self, p, state: SessionState, obj: dict):
        target = obj["target"]
        if target not in self.chapter.areas:
            return ["<smg>该入口尚未恢复。"]
        p.area = target
        if obj.get("dest_x") is not None and obj.get("dest_y") is not None:
            p.x, p.y = int(obj["dest_x"]), int(obj["dest_y"])
        else:
            p.x, p.y = map(int, self.chapter.area(target)["spawn"])
        self.chapter.record_event(p, {"type": "visit", "area": target})
        self.chapter.record_event(p, {"type": "enter", "area": target})
        auto = self._auto_script(p, "area")
        self.chapter.save_player(p)
        return self._spawn_area(p, state, "；".join(auto) if auto else None)

    def _npc_command(self, p, state: SessionState, oid: int, action: str):
        obj = self._obj_map(state).get(oid)
        if not obj:
            return ["<smg>目标已经离开。"]
        # Collision-triggered actions arrive at zero/one-cell distance.  Manual
        # key-5 selection is allowed over the visible nearby radius.
        if self._distance(p, obj) > 18:
            return ["<smg>距离太远。"]
        if obj["kind"] == "npc":
            return self._talk(p, state, obj["id"])
        if obj["kind"] == "door":
            return self._enter_object_door(p, state, obj)
        if obj["kind"] == "monster":
            return self._battle_menu(p, state, obj["id"])
        return []

    def _native_portal(self, p, state: SessionState, trigger_id: int):
        route = self.trigger_routes.get(trigger_id)
        if not route:
            return ["<smg>未知地图出口。"]
        if route["source"] != p.area:
            LOG.info("Ignoring stale map trigger id=%s source=%s current=%s",
                     trigger_id, route["source"], p.area)
            return []
        target = route["target"]
        p.area = target
        p.x, p.y = route["x"], route["y"]
        self.chapter.record_event(p, {"type": "visit", "area": target})
        self.chapter.record_event(p, {"type": "enter", "area": target})
        auto = self._auto_script(p, "area")
        self.chapter.save_player(p)
        LOG.info("PORTAL native trigger=%d %s -> %s", trigger_id,
                 route["source"], target)
        return self._spawn_area(p, state, "；".join(auto) if auto else None)

    def _collision_target(self, state: SessionState, x: int, y: int):
        for oid, obj in self._obj_map(state).items():
            if int(obj.get("x", -999)) == x and int(obj.get("y", -999)) == y:
                return int(oid), obj
        return None

    def _move(self, p, state: SessionState, cmd: str):
        if cmd in self.TURN:
            _name, code, _dx, _dy = self.TURN[cmd]
            p.direction = code
            self.chapter.save_player(p)
            return []

        spec = self.STEP.get(cmd) or self.SPECIAL_STEP.get(cmd)
        if spec is None:
            return None
        _cardinal, code, dx, dy = spec
        target_x = max(0, min(self.MAX_X, p.x + dx))
        target_y = max(0, min(self.MAX_Y, p.y + dy))

        # The original client normally catches this locally for entity ids >=1000.
        # This server-side mirror keeps the same behaviour in emulators whose
        # collision callback differs: bumping an NPC/door/monster interacts rather
        # than walking through it.
        collision = self._collision_target(state, target_x, target_y)
        if collision:
            oid, obj = collision
            LOG.info("COLLISION auto-interact oid=%d kind=%s", oid, obj["kind"])
            return self._npc_command(p, state, oid, obj.get("action", "b"))

        p.direction = code
        p.x, p.y = target_x, target_y
        self.chapter.save_player(p)
        state.metadata["nearest_cache"] = self._sorted_nearby(state, p, 24)
        LOG.debug("MOVE native user=%s area=%s cmd=%s pos=(%d,%d)",
                  p.username, p.area, cmd, p.x, p.y)
        # Crucially: no area switch here.  The map trigger causes V860 itself to
        # send `t l<ID>` exactly when it reaches an exit tile.
        return []

    @staticmethod
    def _menu(title: str, entries: list[tuple[str, str]]) -> str:
        return "<menu(g:a)>" + title + "|" + "|".join(
            f"[{cmd}]{label}" for cmd, label in entries
        )

    def _personal_root(self):
        return [self._menu("个人菜单", [
            ("ui status", "个人状态"), ("ui bag", "物品行囊"),
            ("ui deputy", "副官指令"), ("ui team", "队伍指令"),
            ("ui skills", "战斗技能"), ("ui shop", "神秘商店"),
            ("ui coins", "金币"),
        ])]

    def _status_menu(self, p):
        return [self._menu("个人状态", [
            ("ui equipment", "当前装备"), ("ui attributes", "个人属性"),
            ("ui quest", "当前任务"),
        ])]

    def _attributes(self, p):
        area = self.chapter.area(p.area)["name"]
        return [
            f"<pmg>等级：{p.level}\x1a生命：{p.hp}/{p.max_hp}\x1a经验：{p.exp}"
            f"\x1a银币：{p.silver}\x1a声望：{p.reputation}\x1a所在地：{area}"
        ]

    def _equipment(self, p):
        owned = []
        for name in ("新手炮", "海军服", "高级披肩", "海军炮", "海军巨炮", "毁灭者"):
            if p.inventory.get(name, 0):
                owned.append(name)
        return ["<pmg>当前装备：" + ("、".join(owned) if owned else "新手基础装备")]

    def _bag(self, p):
        items = [f"{k}×{v}" for k, v in sorted(p.inventory.items()) if int(v) > 0]
        return ["<pmg>物品行囊：\x1a" + ("\x1a".join(items) if items else "行囊为空")]

    def _deputy(self, p):
        unlocked = any(
            self.chapter.quests.get(qid, {}).get("title") == "航海的副官"
            for qid in p.completed_quests
        )
        text = "初级副官已经加入你的航海队伍。" if unlocked else (
            "尚未获得副官。完成海军基地支线《航海的副官》后可获得初级副官。"
        )
        return ["<pmg>副官指令\x1a" + text]

    def _team(self, p):
        return ["<pmg>队伍指令：当前为本地复原服单人队伍。组队协议接口已保留。"]

    def _skills(self, p):
        skills = "、".join(p.skills) if p.skills else "尚未学习战斗技能"
        return ["<pmg>战斗技能：" + skills]

    def _shop(self, p):
        return [self._menu("神秘商店", [
            ("shop potion", "中瓶回复剂 50银币"),
            ("shop leave", "离开商店"),
        ])]

    def _buy_potion(self, p):
        if p.silver < 50:
            return ["<smg>银币不足，需要50银币。"]
        p.silver -= 50
        p.give_item("中瓶回复剂", 1)
        self.chapter.save_player(p)
        return ["<pmg>购买成功：中瓶回复剂×1"]

    def _system_root(self):
        return [self._menu("系统菜单", [
            ("ui friends", "好友列表"), ("ui chat", "聊天指令"),
            ("ui guild", "公会指令"), ("ui account", "帐号信息"),
            ("ui settings", "常用设置"), ("ui help", "游戏帮助"),
            ("gate", "卡死修复"), ("ui exit", "退出游戏"),
        ])]

    def _friends(self):
        return ["<pmg>好友列表：当前本地复原服没有其他在线玩家。"]

    def _chat(self):
        return [self._menu("聊天指令", [
            ("chat nearby", "附近频道"), ("chat private", "悄悄话"),
            ("chat world", "世界频道"), ("chat guild", "公会频道"),
            ("chat team", "队伍频道"), ("chat trade", "买卖频道"),
            ("chat faction", "阵营频道"), ("chat system", "系统消息"),
        ])]

    def _guild(self):
        return ["<pmg>公会指令：公会属于原版系统；当前两章不强制加入公会。"]

    def _settings(self, p):
        return [self._menu("常用设置", [
            ("setting broadcast", "广播开关"),
            ("setting refuseguild", "拒入公会开关"),
            ("setting blacklist", "清空黑名单"),
        ])]

    def _help(self):
        return [
            "<pmg>基本操作：\x1a2/4/6/8 控制方向"
            "\x1a5 查看附近NPC并确认菜单"
            "\x1a1 个人菜单；3 好友/社交；7 聊天"
            "\x1a9 非战斗查看任务，战斗中开启自动战斗"
            "\x1a0 系统菜单；* 开关人名；# 开关聊天记录"
        ]

    def _quest_status(self, p):
        return ["<pmg>" + "\x1a".join(self.chapter.status_lines(p))]

    def _legacy_ui_alias(self, cmd: str) -> str | None:
        normalized = re.sub(r"\s+", " ", cmd.strip())
        aliases = {
            "11": "ui status", "1 1": "ui equipment", "1 2": "ui attributes",
            "1 3": "ui quest", "12": "ui bag", "pet": "ui deputy",
            "1 4": "ui team", "1 5": "ui skills", "1 6": "ui shop",
            "17": "ui coins", "0r": "ui account", "0 r": "ui account",
            "0s": "ui settings", "0 s": "ui settings", "0h": "ui help",
            "0 h": "ui help", "0hs": "ui help", "0 hs": "ui help",
            "0q": "ui exit", "0 q": "ui exit",
        }
        return aliases.get(normalized)

    def _handle_ui(self, cmd: str, p, state: SessionState):
        alias = self._legacy_ui_alias(cmd)
        if alias:
            cmd = alias

        if cmd == "1": return self._personal_root()
        if cmd == "0": return self._system_root()
        if cmd == "3": return self._friends()
        if cmd == "5": return self._nearby_menu(p, state)
        if cmd == "7": return self._chat()
        if cmd == "9":
            if state.metadata.get("battle"):
                state.metadata["battle"]["auto"] = not bool(
                    state.metadata["battle"].get("auto", False)
                )
                enabled = state.metadata["battle"]["auto"]
                return ["<smg>自动战斗已" + ("开启" if enabled else "关闭") + "。"]
            return self._quest_status(p)

        if cmd == "ui status": return self._status_menu(p)
        if cmd == "ui equipment": return self._equipment(p)
        if cmd == "ui attributes": return self._attributes(p)
        if cmd == "ui quest": return self._quest_status(p)
        if cmd == "ui bag": return self._bag(p)
        if cmd == "ui deputy": return self._deputy(p)
        if cmd == "ui team": return self._team(p)
        if cmd == "ui skills": return self._skills(p)
        if cmd == "ui shop": return self._shop(p)
        if cmd == "ui coins":
            return ["<pmg>金币：本地复原服不接入原运营短信/付费通道。剧情与两章玩法不需要充值。"]
        if cmd == "ui friends": return self._friends()
        if cmd == "ui chat": return self._chat()
        if cmd == "ui guild" or cmd == "guild": return self._guild()
        if cmd == "ui account":
            return [f"<pmg>帐号：{p.username}\x1a本地复原服帐号数据保存在 data/players。"]
        if cmd == "ui settings": return self._settings(p)
        if cmd == "ui help": return self._help()
        if cmd == "ui exit":
            return [self._menu("退出游戏", [("quit log", "退至选单"), ("quit", "退出游戏")])]
        if cmd == "shop potion": return self._buy_potion(p)
        if cmd == "shop leave": return self._personal_root()
        if cmd.startswith("chat "):
            channel = cmd.split(" ", 1)[1]
            labels = {
                "nearby": "附近", "private": "悄悄话", "world": "世界",
                "guild": "公会", "team": "队伍", "trade": "买卖",
                "faction": "阵营", "system": "系统消息",
            }
            return [f"<smg>已选择{labels.get(channel, channel)}频道。"]
        if cmd == "setting broadcast":
            key = "setting_broadcast_off"
            if key in p.flags: p.flags.remove(key)
            else: p.add_flag(key)
            self.chapter.save_player(p)
            return ["<smg>广播已" + ("关闭" if key in p.flags else "开启") + "。"]
        if cmd == "setting refuseguild":
            key = "setting_refuse_guild"
            if key in p.flags: p.flags.remove(key)
            else: p.add_flag(key)
            self.chapter.save_player(p)
            return ["<smg>拒入公会已" + ("开启" if key in p.flags else "关闭") + "。"]
        if cmd == "setting blacklist":
            return ["<smg>黑名单已清空。"]
        if cmd in {"*", "#"}:
            # These are normally consumed entirely by the original client.  Keep
            # a harmless acknowledgement for emulator/keymap variants that send
            # them to the server instead.
            return ["<smg>该显示开关由V860客户端本地处理。"]
        return None

    def _repair_position(self, p, state: SessionState):
        p.x, p.y = map(int, self.chapter.area(p.area)["spawn"])
        self.chapter.save_player(p)
        return self._spawn_area(p, state, "位置已修复到当前区域安全点。")

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str | bytes]:
        # We need to intercept the native map trigger and keypad/UI commands
        # before the V2/base handlers classify them as unknown generic traffic.
        remaining: list[str] = []
        responses: list[str | bytes] = []
        p = self.chapter.load_player(state.username) if state.username else None

        for cmd in commands:
            if p is not None:
                m = re.match(r"^t\s+l(\d+)$", cmd.strip())
                if m:
                    responses.extend(self._native_portal(p, state, int(m.group(1))))
                    continue
                if cmd == "gate":
                    responses.extend(self._repair_position(p, state))
                    continue
                ui = self._handle_ui(cmd, p, state)
                if ui is not None:
                    responses.extend(ui)
                    continue
            remaining.append(cmd)

        if remaining:
            responses.extend(super().handle_commands(remaining, state))
        return responses


class WindmillMarineServerV3(WindmillMarineServerV2):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = WindmillMarineWorldV3(data_dir)


legacy.HZWCompatServer = WindmillMarineServerV3

if __name__ == "__main__":
    legacy.main()
