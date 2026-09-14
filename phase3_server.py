from __future__ import annotations

import logging
import re
from pathlib import Path

import server as legacy
from hzw_protocol import SessionState
from world_protocol import (
    join_server_parts,
    make_entity_record,
    make_map_download_block,
    make_map_switch_record,
    make_position_record,
    make_tiled_map,
)

LOG = logging.getLogger("hzw860.phase6")
legacy.join_server_lines = join_server_parts


class Phase6World(legacy.CompatWorld):
    PLAYER_TEMPLATE_ID = 53
    GUIDE_TEMPLATE_ID = 54
    GROUND_TILESET_ID = 10
    MAP_WIDTH = 24
    MAP_HEIGHT = 24
    PLAYER_ID = 1
    GUIDE_ID = 2
    GUIDE_X = 16
    GUIDE_Y = 10

    # Recovered logical directions used by O000O0O.O0OO0O(...):
    # 1=up, 6=down, 2=left, 5=right.
    TURN_COMMANDS = {
        "#7": ("UP", 1, 0, -2),
        "#10": ("DOWN", 6, 0, 2),
        "#13": ("LEFT", 2, -2, 0),
        "#16": ("RIGHT", 5, 2, 0),
    }
    STEP_COMMANDS = {
        "#1": ("UP", 1, 0, -2),
        "#2": ("DOWN", 6, 0, 2),
        "#3": ("LEFT", 2, -2, 0),
        "#4": ("RIGHT", 5, 2, 0),
    }
    SPECIAL_STEP_COMMANDS = {
        "#5": ("UP", 1, -2, -2),
        "#6": ("UP", 1, 2, -2),
        "#8": ("DOWN", 6, -2, 2),
        "#9": ("DOWN", 6, 2, 2),
        "#11": ("LEFT", 2, -2, -2),
        "#12": ("LEFT", 2, -2, 2),
        "#14": ("RIGHT", 5, 2, -2),
        "#15": ("RIGHT", 5, 2, 2),
    }

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.local_map_key = "hzwlocalsj"
        # IMPORTANT: make_tiled_map now writes 0x3F into cell[3], the byte the
        # real V860 movement routine actually tests.
        self.local_map = make_tiled_map(
            self.MAP_WIDTH,
            self.MAP_HEIGHT,
            tileset_id=self.GROUND_TILESET_ID,
            tile_flags=0x3F,
        )
        # Preserve position across reconnects while this server process is alive.
        self.saved_positions: dict[str, tuple[int, int, int]] = {}

    @staticmethod
    def login_success_payload() -> list[str | bytes]:
        # legacy.CompatWorld calls this during credential validation. World records
        # are appended afterwards when the SessionState (and username) is known.
        return ["<log_suc>"]

    @staticmethod
    def _base_passthrough(cmd: str) -> bool:
        return (
            cmd == "new"
            or ("\x1f" in cmd and "\x1e" in cmd)
            or ".860" in cmd
            or "860." in cmd
            or "NON5800" in cmd
            or cmd.startswith("quit")
            or cmd in {"0", "menu", "sys", "compat status", "enter world"}
        )

    def _spawn_payload(self, state: SessionState) -> list[str | bytes]:
        x, y, direction = self.saved_positions.get(state.username, (10, 10, 6))
        state.metadata["player_x"] = x
        state.metadata["player_y"] = y
        state.metadata["direction_code"] = direction
        state.metadata["world_initialized"] = True
        LOG.info(
            "WORLD spawn user=%s pos=(%d,%d) dir=%d",
            state.username, x, y, direction,
        )
        return [
            "<title>HZW V860 本地兼容世界",
            "<smg>移动与NPC交互测试已开启；靠近测试向导按5交谈。",
            make_map_switch_record("hzwlocal00"),
            make_entity_record(
                "航海者", template_id=self.PLAYER_TEMPLATE_ID,
                direction=direction, object_id=self.PLAYER_ID, x=x, y=y,
            ),
            make_entity_record(
                "测试向导", template_id=self.GUIDE_TEMPLATE_ID,
                direction=2, object_id=self.GUIDE_ID,
                x=self.GUIDE_X, y=self.GUIDE_Y,
            ),
            "<r>walk 1",
        ]

    def _current_pos(self, state: SessionState) -> tuple[int, int, int]:
        return (
            int(state.metadata.get("player_x", 10)),
            int(state.metadata.get("player_y", 10)),
            int(state.metadata.get("direction_code", 6)),
        )

    def _sync_position(
        self,
        state: SessionState,
        direction_name: str,
        direction_code: int,
        dx: int,
        dy: int,
        source_cmd: str,
    ) -> bytes:
        x, y, _old_dir = self._current_pos(state)
        min_x = 2
        min_y = 2
        max_x = (self.MAP_WIDTH - 2) * 2
        max_y = (self.MAP_HEIGHT - 2) * 2
        new_x = max(min_x, min(max_x, x + dx))
        new_y = max(min_y, min(max_y, y + dy))

        state.metadata["player_x"] = new_x
        state.metadata["player_y"] = new_y
        state.metadata["direction_code"] = direction_code
        state.metadata["last_direction"] = direction_name
        state.metadata["position_updates"] = int(
            state.metadata.get("position_updates", 0)
        ) + 1
        if state.username:
            self.saved_positions[state.username] = (new_x, new_y, direction_code)

        LOG.info(
            "MOVE apply cmd=%s direction=%s pos=(%d,%d)->(%d,%d) updates=%s",
            source_cmd, direction_name, x, y, new_x, new_y,
            state.metadata["position_updates"],
        )
        return make_position_record(
            self.PLAYER_ID, new_x, new_y, direction_code
        )

    def _handle_move_command(
        self, cmd: str, state: SessionState
    ) -> list[str | bytes] | None:
        if cmd in self.TURN_COMMANDS:
            name, code, dx, dy = self.TURN_COMMANDS[cmd]
            _x, _y, old_code = self._current_pos(state)
            state.metadata["turn_events"] = int(state.metadata.get("turn_events", 0)) + 1
            if old_code == code:
                # Compatibility fallback: if an emulator keeps emitting only the
                # turn command, a repeated command in the same direction becomes
                # one server-authoritative step. With the corrected map byte the
                # real client should normally emit #1/#2/#3/#4 instead.
                LOG.info("MOVE repeated-turn fallback direction=%s cmd=%s", name, cmd)
                return [self._sync_position(state, name, code, dx, dy, cmd)]

            state.metadata["direction_code"] = code
            state.metadata["last_direction"] = name
            LOG.info("MOVE turn direction=%s cmd=%s", name, cmd)
            x, y, _ = self._current_pos(state)
            return [make_position_record(self.PLAYER_ID, x, y, code)]

        if cmd in self.STEP_COMMANDS:
            name, code, dx, dy = self.STEP_COMMANDS[cmd]
            state.metadata["step_events"] = int(state.metadata.get("step_events", 0)) + 1
            return [self._sync_position(state, name, code, dx, dy, cmd)]

        if cmd in self.SPECIAL_STEP_COMMANDS:
            name, code, dx, dy = self.SPECIAL_STEP_COMMANDS[cmd]
            state.metadata["special_step_events"] = int(
                state.metadata.get("special_step_events", 0)
            ) + 1
            return [self._sync_position(state, name, code, dx, dy, cmd)]

        return None

    def _npc_interaction(self, state: SessionState) -> list[str | bytes]:
        x, y, _direction = self._current_pos(state)
        distance = abs(x - self.GUIDE_X) + abs(y - self.GUIDE_Y)
        LOG.info("NPC interact key=5 player=(%d,%d) distance=%d", x, y, distance)
        if distance <= 4:
            return [
                "<pmg>测试向导：航海者，你已经真正进入V860世界。移动协议与坐标同步已恢复；下一阶段接入风车镇NPC与任务。"
            ]
        return ["<smg>请走近测试向导后按5交谈。"]

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str | bytes]:
        base_commands: list[str] = []
        responses: list[str | bytes] = []

        for cmd in commands:
            if cmd.startswith("#map 60"):
                requested = cmd[len("#map 60"):].strip()
                if requested == self.local_map_key:
                    LOG.info(
                        "Serving corrected walkable map key=%s bytes=%d tileset=d/%d.tij cell3=0x3F",
                        requested, len(self.local_map), self.GROUND_TILESET_ID,
                    )
                    responses.append(make_map_download_block(requested, self.local_map))
                else:
                    LOG.info("Unknown map request %r", requested)
                continue

            move_response = self._handle_move_command(cmd, state)
            if move_response is not None:
                responses.extend(move_response)
                continue

            if cmd == "5":
                responses.extend(self._npc_interaction(state))
                continue

            if cmd.startswith("petcmd"):
                LOG.info("Legacy deputy command: %r", cmd)
                responses.append("<smg>副官系统协议恢复中")
                continue

            if cmd == "guild" or cmd.startswith("guild "):
                LOG.info("Guild command: %r", cmd)
                responses.append("<smg>公会系统协议恢复中")
                continue

            if (
                cmd.startswith("loginzhuowang")
                or re.match(r"^\d+\s+\d+$", cmd)
                or cmd == "?"
                or cmd.startswith("#maps")
                or cmd.startswith("#chs")
            ):
                LOG.info("Ignoring recovered internal command: %r", cmd)
                continue

            if self._base_passthrough(cmd):
                base_commands.append(cmd)
            else:
                LOG.info("Unimplemented gameplay command (logged only): %r", cmd)

        if base_commands:
            base_responses = super().handle_commands(base_commands, state)
            responses[:0] = base_responses
            if (
                state.logged_in
                and not state.metadata.get("world_initialized")
                and any(part == "<log_suc>" for part in base_responses if isinstance(part, str))
            ):
                responses.extend(self._spawn_payload(state))

        return responses


class Phase6CompatServer(legacy.HZWCompatServer):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = Phase6World(data_dir)


legacy.HZWCompatServer = Phase6CompatServer

if __name__ == "__main__":
    legacy.main()
