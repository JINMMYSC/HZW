from __future__ import annotations

import re

import server as legacy
from chapter_server_v3 import WindmillMarineServerV3, WindmillMarineWorldV3
from hzw_protocol import SessionState


class WindmillMarineWorldV4(WindmillMarineWorldV3):
    """Original-keypad/menu compatibility pass for V860.

    This layer keeps the V3 native map triggers/collision objects, then adds the
    exact legacy submenu commands decoded from csys/list.dat so every keypad
    route has a live destination on the compatibility server.
    """

    def _move(self, p, state: SessionState, cmd: str):
        # Some J2ME emulators report only the turn command when the next cell is
        # occupied.  Mirror original bump-to-interact even in that case.
        if cmd in self.TURN:
            _name, code, dx, dy = self.TURN[cmd]
            p.direction = code
            collision = self._collision_target(state, p.x + dx, p.y + dy)
            self.chapter.save_player(p)
            if collision:
                oid, obj = collision
                return self._npc_command(p, state, oid, obj.get("action", "b"))
            return []
        return super()._move(p, state, cmd)

    def _nearby_menu(self, p, state: SessionState):
        nearby = self._sorted_nearby(state, p, 18)
        state.metadata["nearest_cache"] = nearby
        if not nearby:
            return ["<smg>附近没有可以互动的目标。"]
        # Original feel: when there is an obvious adjacent target, 5 acts as an
        # immediate confirm instead of forcing another slow target-selection step.
        if nearby[0][0] <= 6:
            _d, oid, obj = nearby[0]
            return self._npc_command(p, state, oid, obj.get("action", "b"))
        return super()._nearby_menu(p, state)

    def _legacy_ui_alias(self, cmd: str) -> str | None:
        normalized = re.sub(r"\s+", " ", cmd.strip())
        aliases = {
            # Personal menu decoded from list.dat.
            "11": "ui status",
            "1 1 1": "ui equipment",
            "1 1 2": "ui attributes",
            "1 1 3": "ui quest",
            "12": "ui bag",
            "1 2 1": "ui bag equipment",
            "1 2 2": "ui bag assist",
            "1 2 3": "ui bag quest",
            "1 2 4": "ui bag stall",
            "pet": "ui deputy",
            "1 4": "ui team",
            "1 5": "ui skills",
            "1 6": "ui shop",
            "17": "ui coins",
            "1 7 1": "ui coins",
            "1 7 2": "ui coins",
            # System menu decoded from list.dat.
            "0r": "ui account",
            "0 r": "ui account",
            "0s": "ui settings",
            "0h": "ui help",
            "0hs": "ui help",
            "0q": "ui exit",
        }
        return aliases.get(normalized) or super()._legacy_ui_alias(cmd)

    def _bag_category(self, p, category: str):
        def is_equipment(name: str) -> bool:
            return any(token in name for token in ("炮", "剑", "刀", "枪", "服", "甲", "披肩", "帽", "鞋", "戒", "项链"))

        quest_words = ("信", "名单", "钥匙", "帽子", "宝藏", "日记", "印章", "尾巴", "斧头", "船帆", "墨水")
        rows = []
        for name, count in sorted(p.inventory.items()):
            if int(count) <= 0:
                continue
            if category == "equipment" and not is_equipment(name):
                continue
            if category == "quest" and not any(w in name for w in quest_words):
                continue
            if category == "assist" and (is_equipment(name) or any(w in name for w in quest_words)):
                continue
            rows.append(f"{name}×{count}")
        if category == "stall":
            return ["<pmg>摆摊出售：本地单人复原服不需要玩家摆摊，物品不会丢失。"]
        return ["<pmg>" + ("\x1a".join(rows) if rows else "该分类暂无物品。")]

    def _handle_ui(self, cmd: str, p, state: SessionState):
        normalized = re.sub(r"\s+", " ", cmd.strip())
        alias = self._legacy_ui_alias(normalized)
        if alias:
            normalized = alias

        if normalized.startswith("ui bag "):
            return self._bag_category(p, normalized.split(" ", 2)[2])

        # Task/map submenu from the original key 9 entry.
        if normalized == "9 1":
            return self._quest_status(p)
        if normalized == "9 2":
            return [f"<pmg>区域地图：{self.chapter.area(p.area)['name']}\x1a当前位置：{p.x},{p.y}"]
        if normalized == "9 3":
            return ["<pmg>世界地图：风车镇 → 海军基地。当前双章主线已接入；后续岛屿按章节继续恢复。"]
        if normalized == "9 4":
            return ["<input(@)(x:mapsearch )>请输入地图名称："]

        # Account/settings/help commands emitted by the original system menus.
        if normalized in {"regist", "0 a5", "0 a2"}:
            return [f"<pmg>本地帐号：{p.username}\x1a原运营帐号/短信服务已关闭；角色数据保存在 data/players。"]
        if normalized == "0 s":
            return ["<input(@)(x:setsaying )>请输入常用短语："]
        if normalized == "0 g":
            key = "setting_refuse_guild"
            if key in p.flags:
                p.flags.remove(key)
                enabled = False
            else:
                p.add_flag(key)
                enabled = True
            self.chapter.save_player(p)
            return ["<smg>拒入公会已" + ("开启" if enabled else "关闭") + "。"]
        if normalized == "0 3":
            key = "setting_broadcast_off"
            if key in p.flags:
                p.flags.remove(key)
                off = False
            else:
                p.add_flag(key)
                off = True
            self.chapter.save_player(p)
            return ["<smg>广播已" + ("关闭" if off else "开启") + "。"]
        if normalized == "0 a3":
            return ["<smg>黑名单已清空。"]
        if normalized == "0 a6":
            return ["<pmg>《海贼王：秘宝传说》V860 本地复原服\x1a当前恢复：风车镇 + 海军基地。"]
        if normalized == "tw":
            return ["<pmg>原在线客服已停服。本地复原调试请查看服务器窗口日志。"]

        # Exact legacy chat commands from list.dat.
        if normalized == "7 2":
            return ["<pmg>最新联系：当前没有其他在线玩家。"]
        if normalized == "7 3":
            return ["<input(@)(x:whisper )>请输入玩家和悄悄话内容："]
        if normalized == "7 5":
            return ["<pmg>信箱：当前没有新邮件。"]
        if normalized == "7 7":
            return ["<pmg>系统消息：风车镇与海军基地复原服务运行中。"]
        if normalized in {"761", "762", "763", "764"}:
            label = {"761": "公会", "762": "队伍", "763": "买卖", "764": "聊天"}[normalized]
            return [f"<input(@)(x:7 {normalized[-2:]})>{label}频道：你想说什么?"]
        if normalized.startswith("7 11 ") or normalized.startswith("7 14 ") or re.match(r"^7 6[1-4] ", normalized):
            return ["<smg>消息已发送。"]

        if normalized.startswith("petcmd"):
            # Internal protocol name is retained for compatibility; player-facing
            # terminology is 副官 throughout the restored game.
            return self._deputy(p)

        return super()._handle_ui(normalized, p, state)


class WindmillMarineServerV4(WindmillMarineServerV3):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = WindmillMarineWorldV4(data_dir)


legacy.HZWCompatServer = WindmillMarineServerV4

if __name__ == "__main__":
    legacy.main()
