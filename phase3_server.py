from __future__ import annotations

import logging
from pathlib import Path

import server as legacy
from hzw_protocol import SessionState
from world_protocol import (
    join_server_parts,
    make_blank_map,
    make_entity_record,
    make_map_download_block,
    make_map_switch_record,
)

LOG = logging.getLogger("hzw860.phase3")

# Keep the Phase-2 transport that the real V860 client already verified, and
# replace only the text-only payload joiner so it can carry binary world data.
legacy.join_server_lines = join_server_parts


class Phase3World(legacy.CompatWorld):
    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.local_map_key = "hzwlocalsj"
        self.local_map = make_blank_map(24, 24)

    @staticmethod
    def login_success_payload() -> list[str | bytes]:
        # Type-1 map switch makes V860 request '#map 60hzwlocalsj'. The entity
        # and walk records stay queued until the map is installed by the client.
        return [
            "<log_suc>",
            "<title>HZW V860 本地兼容世界",
            "<smg>登录成功，正在载入本地测试世界…",
            make_map_switch_record("hzwlocal00"),
            make_entity_record(
                "player", template_id=14, direction=0, object_id=1, x=10, y=10
            ),
            "<r>walk1",
        ]

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str | bytes]:
        regular: list[str] = []
        binary_responses: list[str | bytes] = []
        for cmd in commands:
            if cmd.startswith("#map 60"):
                requested = cmd[len("#map 60"):].strip()
                if requested == self.local_map_key:
                    LOG.info(
                        "Serving bootstrap map key=%s bytes=%d",
                        requested,
                        len(self.local_map),
                    )
                    binary_responses.append(
                        make_map_download_block(requested, self.local_map)
                    )
                else:
                    binary_responses.append(
                        "<smg>兼容服尚未恢复地图：" + self.escape_for_text(requested[:48])
                    )
            else:
                regular.append(cmd)

        responses: list[str | bytes] = []
        if regular:
            responses.extend(super().handle_commands(regular, state))
        responses.extend(binary_responses)
        return responses


class Phase3CompatServer(legacy.HZWCompatServer):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = Phase3World(data_dir)


legacy.HZWCompatServer = Phase3CompatServer

if __name__ == "__main__":
    legacy.main()
