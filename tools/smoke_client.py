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
    frame = encode_socket_client_frame_for_test(text.encode("utf-8"), state, ack4)
    sock.sendall(frame)


def main() -> int:
    ap = argparse.ArgumentParser(description="V860 protocol smoke client")
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
        ack, first = recv_server_frame(s)
        first_text = first.decode("utf-8", errors="replace")
        print("--- bootstrap response ---")
        print(first_text, end="")

        m = re.search(r"<newacc>([^:\r\n]+):([^\r\n]+)", first_text)
        if not m:
            raise RuntimeError("server did not return <newacc>")
        username, password = m.group(1), m.group(2)
        login_line = f"{username}\x1f{password}\x1eds\n"
        send_client_frame(s, state, ack, login_line)
        _ack2, second = recv_server_frame(s)
        second_text = second.decode("utf-8", errors="replace")
        print("--- login response ---")
        print(second_text, end="")
        required = ("<log_suc>", "<title>", "<menu>")
        missing = [x for x in required if x not in second_text]
        if missing:
            raise RuntimeError(f"login response missing {missing}")
        print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
