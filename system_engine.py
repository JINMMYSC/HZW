from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class SystemEngine:
    """Persistent non-story systems recovered from HZW research.

    The catalog deliberately separates V860_DIRECT from contemporary and
    post-V860 evidence.  Unknown acquisition formulas are never invented.
    """

    def __init__(self, catalog_file: Path, data_dir: Path):
        self.catalog_file = Path(catalog_file)
        self.catalog = json.loads(self.catalog_file.read_text("utf-8"))
        self.players_dir = Path(data_dir) / "systems"
        self.players_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _safe(username: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", username or "guest")[:80]

    def _path(self, username: str) -> Path:
        return self.players_dir / f"{self._safe(username)}.json"

    @staticmethod
    def _default(username: str) -> dict[str, Any]:
        return {
            "username": username,
            "profession": "",
            "deputies": [],
            "active_deputy": "",
            "mounts": [],
            "active_mount": "",
            "ship": {"owned": False, "cannon": "", "gunnery_level": 0},
            "sea_exp": 0,
            "discovered_areas": [],
            "flight_unlocked": [],
            "system_flags": [],
        }

    def load(self, username: str) -> dict[str, Any]:
        if username in self._cache:
            return self._cache[username]
        state = self._default(username)
        path = self._path(username)
        if path.exists():
            try:
                raw = json.loads(path.read_text("utf-8"))
                if isinstance(raw, dict):
                    state.update(raw)
            except Exception:
                pass
        self._cache[username] = state
        self.save(state)
        return state

    def save(self, state: dict[str, Any]) -> None:
        username = str(state.get("username") or "guest")
        self._cache[username] = state
        self._path(username).write_text(
            json.dumps(state, ensure_ascii=False, indent=2), "utf-8"
        )

    def sync_progress(self, player) -> dict[str, Any]:
        state = self.load(player.username)
        changed = False

        if player.area not in state["discovered_areas"]:
            state["discovered_areas"].append(player.area)
            changed = True

        # Windmill walkthrough: Hait gives the first ship, starter cannon and
        # level-1 gunnery.  wm10 is the restored quest representing that event.
        if (
            "wm10" in player.completed_quests
            or player.inventory.get("新手炮", 0) > 0
            or "初级炮术" in player.skills
        ):
            ship = state["ship"]
            if not ship.get("owned"):
                ship["owned"] = True
                changed = True
            if player.inventory.get("新手炮", 0) > 0 and ship.get("cannon") != "新手炮":
                ship["cannon"] = "新手炮"
                changed = True
            if "初级炮术" in player.skills and int(ship.get("gunnery_level", 0)) < 1:
                ship["gunnery_level"] = 1
                changed = True

        # Marine side quest reward is explicitly named 初级副官 in recovered data.
        if "mbs04" in player.completed_quests or player.inventory.get("初级副官", 0) > 0:
            if "初级副官" not in state["deputies"]:
                state["deputies"].append("初级副官")
                changed = True
            if not state.get("active_deputy"):
                state["active_deputy"] = "初级副官"
                changed = True

        if changed:
            self.save(state)
        return state

    def profession_spec(self, key: str) -> dict[str, Any] | None:
        return (self.catalog.get("professions") or {}).get(key)

    def choose_profession(self, player, key: str) -> tuple[bool, str]:
        state = self.sync_progress(player)
        spec = self.profession_spec(key)
        if not spec or not spec.get("enabled"):
            return False, "没有这个可选职业。"
        if state.get("profession"):
            current = self.profession_spec(str(state["profession"])) or {}
            return False, f"已经选择职业：{current.get('name', state['profession'])}。"
        required = int(spec.get("min_level", 10))
        if int(player.level) < required:
            return False, f"职业选择需要达到{required}级。"
        state["profession"] = key
        self.save(state)
        return True, f"职业已选择：{spec['name']}。"

    def profession_lines(self, player) -> list[str]:
        state = self.sync_progress(player)
        if state.get("profession"):
            spec = self.profession_spec(str(state["profession"])) or {}
            return [
                f"当前职业：{spec.get('name', state['profession'])}",
                f"定位：{spec.get('role', '资料待补')}",
                f"证据：{spec.get('evidence', 'UNKNOWN')}",
            ]
        rows = ["当前职业：未选择", "原服资料确认10级开放职业选择。"]
        for key, spec in (self.catalog.get("professions") or {}).items():
            if spec.get("enabled"):
                rows.append(f"{key}={spec['name']}（{spec.get('role','')}）")
        return rows

    def deputy_lines(self, player) -> list[str]:
        state = self.sync_progress(player)
        owned = state.get("deputies") or []
        rows = ["副官系统"]
        rows.append("已拥有：" + ("、".join(owned) if owned else "暂无"))
        rows.append("当前任命：" + (state.get("active_deputy") or "无"))
        rows.append("2008常人旅馆已证实：桃子、萌萌、兰迪、初级男女海盗；价格资料未恢复，不编造。")
        rows.append("V860直接确认新增副官：追猎者；获取方式/属性尚未恢复。")
        return rows

    def mount_lines(self, player) -> list[str]:
        state = self.sync_progress(player)
        owned = state.get("mounts") or []
        rows = ["坐骑系统", "已拥有：" + ("、".join(owned) if owned else "暂无")]
        rows.append("当前骑乘：" + (state.get("active_mount") or "无"))
        direct = [
            spec["name"] for spec in (self.catalog.get("mounts") or {}).values()
            if spec.get("evidence") == "V860_DIRECT_CONFIRMED"
        ]
        rows.append("V860直接确认：" + "、".join(direct))
        rows.append("获取方式/数值/速度尚无V860直接资料，因此不会免费发放或伪造属性。")
        return rows

    def ship_lines(self, player) -> list[str]:
        state = self.sync_progress(player)
        ship = state["ship"]
        return [
            "航海/船只",
            "船只：" + ("已获得" if ship.get("owned") else "尚未获得"),
            "舰炮：" + (ship.get("cannon") or "未装备"),
            f"炮术等级：{int(ship.get('gunnery_level', 0))}",
            f"海战经验：{int(state.get('sea_exp', 0))}",
            "风车镇→海军基地同期攻略明确存在实际军舰航行阶段；海域逐格几何仍待原图/录像。",
        ]

    def v860_feature_lines(self) -> list[str]:
        rows = ["V860直接确认系统"]
        for spec in (self.catalog.get("features") or {}).values():
            if spec.get("evidence") == "V860_DIRECT_CONFIRMED":
                unknown = "；待恢复：" + "、".join(spec.get("unknown") or []) if spec.get("unknown") else ""
                rows.append(spec["name"] + unknown)
        return rows

    def post_v860_lines(self) -> list[str]:
        rows = ["原服后续系统（默认不回填V860）"]
        for group in ("features", "deputies", "mounts"):
            for spec in (self.catalog.get(group) or {}).values():
                ev = str(spec.get("evidence") or "")
                if ev.startswith("POST_V860"):
                    rows.append(f"{spec['name']} [{ev}]")
        return rows

    def discovery_lines(self, player, area_names: dict[str, str]) -> list[str]:
        state = self.sync_progress(player)
        discovered = state.get("discovered_areas") or []
        rows = [f"已探索区域：{len(discovered)}"]
        rows.extend(area_names.get(aid, aid) for aid in discovered[-20:])
        return rows
