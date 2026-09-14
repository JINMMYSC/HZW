from __future__ import annotations

import argparse
import re
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hzw_protocol import (
    SOCKET_RESPONSE_LEN_XOR,
    SessionState,
    chain_decode,
    encode_socket_client_frame_for_test,
)
from world_protocol import make_entity_record, make_map_switch_record

BOOTSTRAP = b"\x80\x5e\x78\x78\x80kawa\n"


def recv_server_frame(sock: socket.socket) -> tuple[bytes, bytes]:
    h = sock.recv(6)
    if len(h) != 6:
        raise RuntimeError(f"short server header: {len(h)}")
    n = (h[4] | (h[5] << 8)) ^ SOCKET_RESPONSE_LEN_XOR
    body = bytearray()
    while len(body) < n:
        chunk = sock.recv(n - len(body))
        if not chunk:
            raise RuntimeError("server closed while receiving payload")
        body.extend(chunk)
    return h[:4], chain_decode(bytes(body), h[4])


def send_client_frame(sock: socket.socket, state: SessionState, ack4: bytes, text: str) -> None:
    sock.sendall(encode_socket_client_frame_for_test(text.encode("utf-8"), state, ack4))


def main() -> int:
    ap = argparse.ArgumentParser(description="V860 Phase-5 movement world smoke client")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5926)
    ap.add_argument("--timeout", type=float, default=5.0)
    args = ap.parse_args()

    state = SessionState()
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as s:
        s.settimeout(args.timeout)
        s.sendall(b"CONNECT 1hzg0\n")
        s.sendall(BOOTSTRAP)
        send_client_frame(s, state, b"\x00\x00\x00\x00", "new\n860.1HZ0000.NON5800.CT\n")
        ack1, first = recv_server_frame(s)
        first_text = first.decode("utf-8", errors="replace")
        m = re.search(r"<newacc>([^:\r\n]+):([^\r\n]+)", first_text)
        if not m:
            raise RuntimeError("server did not return <newacc>")

        username, password = m.group(1), m.group(2)
        send_client_frame(s, state, ack1, f"{username}\x1f{password}\x1eds\n")
        ack2, second = recv_server_frame(s)
        second_text = second.decode("utf-8", errors="replace")
        if "<log_suc>" not in second_text:
            raise RuntimeError("world bootstrap missing <log_suc>")
        if make_map_switch_record("hzwlocal00") not in second:
            raise RuntimeError("world bootstrap missing type-1 map switch")
        if make_entity_record("航海者", 53, 0, 1, 10, 10) not in second:
            raise RuntimeError("world bootstrap missing visible player sprite template")
        if make_entity_record("测试向导", 54, 0, 2, 14, 10) not in second:
            raise RuntimeError("world bootstrap missing reference NPC sprite")
        if b"<r>walk 1\n" not in second:
            raise RuntimeError("world bootstrap missing parser-compatible player selector")
        print("LOGIN_MOVEMENT_WORLD_BOOTSTRAP_OK")

        send_client_frame(s, state, ack2, "#map 60hzwlocalsj\n")
        ack3, third = recv_server_frame(s)
        if not third.startswith(b"\x00\x00\x7f"):
            raise RuntimeError("map response missing marker 127")
        zero = third.find(b"\x00", 3)
        key = third[3:zero].decode("utf-8")
        map_len = third[zero + 1] | (third[zero + 2] << 8)
        map_bytes = third[zero + 3:zero + 3 + map_len]
        if key != "hzwlocalsj" or len(map_bytes) != map_len:
            raise RuntimeError("invalid map download payload")
        if map_bytes[18:20] != bytes((24, 24)):
            raise RuntimeError("wrong bootstrap map dimensions")
        if map_bytes[2] != 1:
            raise RuntimeError("visible map missing bundled tileset descriptor")
        descriptor_offset = int.from_bytes(map_bytes[4:6], "little")
        if map_bytes[descriptor_offset:descriptor_offset + 4] != bytes((0, 0, 10, 0)):
            raise RuntimeError("visible map is not wired to d/10.tij")
        if map_bytes[21] & 0x3F != 0x3F:
            raise RuntimeError("movement exit bits are not enabled on bootstrap map")
        print(
            f"WALKABLE_MAP_DOWNLOAD_OK key={key} bytes={map_len} "
            "size=24x24 tileset=d/10.tij flags=0x3F"
        )

        # Player-facing terminology check using a command observed from the real client.
        send_client_frame(s, state, ack3, "guild\n")
        _ack4, fourth = recv_server_frame(s)
        if "公会系统协议恢复中".encode("utf-8") not in fourth:
            raise RuntimeError("guild command did not use HZW player-facing terminology")
        print("GUILD_TERMINOLOGY_OK")
        print("SMOKE_MOVEMENT_WORLD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
