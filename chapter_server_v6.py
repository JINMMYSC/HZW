from __future__ import annotations

from pathlib import Path

import server as legacy
from chapter_server_v5 import FullCampaignServerV5, FullCampaignWorldV5
from hzw_protocol import SessionState
from system_engine import SystemEngine

ROOT = Path(__file__).resolve().parent
SYSTEM_CATALOG = ROOT / "content" / "systems" / "v860_systems.json"


class EvidenceFullWorldV6(FullCampaignWorldV5):
    """Evidence-backed gameplay systems layered on the recovered full campaign.

    This layer never promotes POST_V860 material into the V860 profile and never
    invents missing acquisition prices/formulas.  It turns confirmed systems into
    persistent state while keeping the original V860 keypad/menu routes alive.
    """

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.systems = SystemEngine(SYSTEM_CATALOG, data_dir)

    def _sync_systems(self, p):
        return self.systems.sync_progress(p)

    def _spawn_area(self, p, state: SessionState, notice: str | None = None):
        self._sync_systems(p)
        return super()._spawn_area(p, state, notice)

    def _status_menu(self, p):
        # Keep the recovered original three routes first; additional restored
        # state pages are appended so old keypad aliases remain compatible.
        return [self._menu("个人状态", [
            ("ui equipment", "当前装备"),
            ("ui attributes", "个人属性"),
            ("ui quest", "当前任务"),
            ("ui profession", "职业信息"),
            ("ui ship", "航海/船只"),
            ("ui exploration", "探索记录"),
        ])]

    def _deputy(self, p):
        return ["<pmg>" + "\x1a".join(self.systems.deputy_lines(p))]

    def _skills(self, p):
        profession = self.systems.profession_lines(p)
        learned = "、".join(p.skills) if p.skills else "尚未记录战斗技能"
        return ["<pmg>" + "\x1a".join(profession + ["已学技能：" + learned])]

    def _shop(self, p):
        # The 2012-11 Mystery Shop is original-service evidence but later than the
        # 2012-08 V860 update. Do not silently enable it as a V860-direct feature.
        return [self._menu("商店/商城", [
            ("ui shop map", "地图商店说明"),
            ("ui postv860", "原服后续系统资料"),
            ("shop leave", "返回个人菜单"),
        ])]

    def _system_root(self):
        base = super()._system_root()
        # Replace one menu payload so every inherited original command stays live,
        # while adding a restoration-status page rather than overloading gameplay.
        return [self._menu("系统菜单", [
            ("ui friends", "好友列表"),
            ("ui chat", "聊天指令"),
            ("ui guild", "公会指令"),
            ("ui account", "帐号信息"),
            ("ui settings", "常用设置"),
            ("ui help", "游戏帮助"),
            ("ui v860systems", "V860系统状态"),
            ("gate", "卡死修复"),
            ("ui exit", "退出游戏"),
        ])]

    def _attributes(self, p):
        state = self._sync_systems(p)
        profession = state.get("profession") or "未选择"
        if profession != "未选择":
            spec = self.systems.profession_spec(str(profession)) or {}
            profession = spec.get("name", profession)
        area = self.chapter.area(p.area)["name"]
        return [
            f"<pmg>等级：{p.level}\x1a生命：{p.hp}/{p.max_hp}\x1a实战经验：{p.exp}"
            f"\x1a银币：{p.silver}\x1a声望：{p.reputation}\x1a职业：{profession}"
            f"\x1a所在地：{area}"
        ]

    def _handle_ui(self, cmd: str, p, state: SessionState):
        normalized = " ".join(cmd.strip().split())

        if normalized == "ui profession":
            rows = self.systems.profession_lines(p)
            sys_state = self.systems.sync_progress(p)
            if not sys_state.get("profession") and int(p.level) >= 10:
                return [
                    "<pmg>" + "\x1a".join(rows),
                    self._menu("选择职业", [
                        ("profession choose warrior", "战士"),
                        ("profession choose fighter", "格斗家"),
                        ("profession choose doctor", "医师"),
                    ]),
                ]
            return ["<pmg>" + "\x1a".join(rows)]

        if normalized.startswith("profession choose "):
            key = normalized.rsplit(" ", 1)[-1]
            ok, message = self.systems.choose_profession(p, key)
            return [("<pmg>" if ok else "<smg>") + message]

        if normalized == "ui ship":
            return ["<pmg>" + "\x1a".join(self.systems.ship_lines(p))]

        if normalized == "ui mount":
            return ["<pmg>" + "\x1a".join(self.systems.mount_lines(p))]

        if normalized == "ui artifact":
            return ["<pmg>" + "\x1a".join(self.systems.v860_feature_lines())]

        if normalized == "ui exploration":
            names = {aid: spec.get("name", aid) for aid, spec in self.chapter.areas.items()}
            return ["<pmg>" + "\x1a".join(self.systems.discovery_lines(p, names))]

        if normalized == "ui v860systems":
            direct = self.systems.v860_feature_lines()
            mounts = self.systems.mount_lines(p)
            return [
                self._menu("V860系统", [
                    ("ui profession", "职业"),
                    ("ui deputy", "副官"),
                    ("ui mount", "坐骑"),
                    ("ui ship", "航海/船只"),
                    ("ui artifact", "法宝融合"),
                    ("ui exploration", "地图探索"),
                    ("ui postv860", "原服后续资料"),
                ]),
                "<pmg>" + "\x1a".join(direct + mounts[:1]),
            ]

        if normalized == "ui postv860":
            return ["<pmg>" + "\x1a".join(self.systems.post_v860_lines())]

        if normalized == "ui shop map":
            return [
                "<pmg>风车镇/各岛商店按地图NPC与任务物件恢复。"
                "\x1a2012-11神秘商店属于原服后续资料，不在V860模式默认开启。"
            ]

        result = super()._handle_ui(normalized, p, state)
        return result

    def handle_commands(self, commands: list[str], state: SessionState):
        responses = super().handle_commands(commands, state)
        if state.username:
            p = self.chapter.load_player(state.username)
            self._sync_systems(p)
        return responses


class EvidenceFullServerV6(FullCampaignServerV5):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = EvidenceFullWorldV6(data_dir)


legacy.HZWCompatServer = EvidenceFullServerV6

if __name__ == "__main__":
    legacy.main()
