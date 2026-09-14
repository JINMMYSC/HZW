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
    make_tiled_map,
)

LOG = logging.getLogger("hzw860.phase4")
legacy.join_server_lines = join_server_parts


class Phase4World(legacy.CompatWorld):
    PLAYER_TEMPLATE_ID = 53  # bundled multi-frame character strip: c/53.chj
    GROUND_TILESET_ID = 10   # bundled sand/ground tile strip: d/10.tij

    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.local_map_key = "hzwlocalsj"
        self.local_map = make_tiled_map(24, 24, tileset_id=self.GROUND_TILESET_ID)

    @classmethod
    def login_success_payload(cls) -> list[str | bytes]:
        return [
            "<log_suc>",
            "<title>HZW V860 本地兼容世界",
            "<smg>登录成功，正在载入原版资源测试场…",
            make_map_switch_record("hzwlocal00"),
            make_entity_record(
                "航海者", template_id=cls.PLAYER_TEMPLATE_ID,
                direction=0, object_id=1, x=10, y=10,
            ),
            "<r>walk 1",
        ]

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

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str | bytes]:
        base_commands: list[str] = []
        responses: list[str | bytes] = []

        for cmd in commands:
            if cmd.startswith("#map 60"):
                requested = cmd[len("#map 60"):].strip()
                if requested == self.local_map_key:
                    LOG.info(
                        "Serving visible bootstrap map key=%s bytes=%d tileset=d/%d.tij",
                        requested, len(self.local_map), self.GROUND_TILESET_ID,
                    )
                    responses.append(make_map_download_block(requested, self.local_map))
                else:
                    LOG.info("Unknown map request %r", requested)
                continue

            # The common engine still uses the historical internal token 'petcmd'.
            # In HZW the player-facing system is 副官, so never expose the old token.
            if cmd.startswith("petcmd"):
                LOG.info("Legacy deputy command: %r", cmd)
                responses.append("<smg>副官系统协议恢复中")
                continue

            # Keep engine/system probes in logs only. Do not echo raw protocol names
            # into the game UI as if they were HZW features.
            if (
                cmd.startswith("loginzhuowang")
                or re.match(r"^\d+\s+\d+$", cmd)
                or cmd in {"?", "#7"}
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
            responses[:0] = super().handle_commands(base_commands, state)
        return responses


class Phase4CompatServer(legacy.HZWCompatServer):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = Phase4World(data_dir)


legacy.HZWCompatServer = Phase4CompatServer

if __name__ == "__main__":
    legacy.main()
