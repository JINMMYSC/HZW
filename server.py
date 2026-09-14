from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
from urllib.parse import urlsplit, parse_qs

from hzw_protocol import (
    SessionState,
    decode_http_client_body,
    decode_socket_client_frame,
    encode_http_server_payload,
    encode_socket_server_payload,
    join_server_lines,
    split_commands,
)

LOG = logging.getLogger("hzw860")


@dataclass
class Account:
    username: str
    password: str
    created_at: float = field(default_factory=time.time)


class CompatWorld:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.accounts_file = self.data_dir / "accounts.json"
        self.accounts: Dict[str, Account] = {}
        self.sessions_by_cid: Dict[str, SessionState] = {}
        self.load_accounts()

    def load_accounts(self) -> None:
        if not self.accounts_file.exists():
            return
        try:
            raw = json.loads(self.accounts_file.read_text("utf-8"))
            for name, rec in raw.items():
                self.accounts[name] = Account(name, rec["password"], rec.get("created_at", time.time()))
        except Exception:
            LOG.exception("Could not load accounts.json")

    def save_accounts(self) -> None:
        raw = {k: {"password": v.password, "created_at": v.created_at} for k, v in self.accounts.items()}
        self.accounts_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), "utf-8")

    def make_cid(self) -> str:
        return "HZ" + secrets.token_hex(4).upper()

    def ensure_cid(self, state: SessionState) -> str:
        if not state.cid:
            state.cid = self.make_cid()
            self.sessions_by_cid[state.cid] = state
        return state.cid

    def create_guest(self) -> Account:
        while True:
            name = "guest" + str(secrets.randbelow(900000) + 100000)
            if name not in self.accounts:
                break
        password = secrets.token_hex(3)
        acct = Account(name, password)
        self.accounts[name] = acct
        self.save_accounts()
        return acct

    def handle_commands(self, commands: list[str], state: SessionState) -> list[str]:
        responses: list[str] = []
        if not state.cid:
            responses.append("<cid" + self.ensure_cid(state))

        for cmd in commands:
            LOG.info("CMD cid=%s sn=%s %r", state.cid, state.sn, cmd)
            if cmd == "new":
                acct = self.create_guest()
                state.username = acct.username
                responses.append(f"<newacc>{acct.username}:{acct.password}")
                responses.append("<pmg>兼容服务器已创建测试帐号")
                continue

            if "\x1f" in cmd and "\x1e" in cmd:
                user, rest = cmd.split("\x1f", 1)
                pwd = rest.split("\x1e", 1)[0]
                acct = self.accounts.get(user)
                if acct is None:
                    self.accounts[user] = Account(user, pwd)
                    self.save_accounts()
                    acct = self.accounts[user]
                if acct.password != pwd:
                    responses.append("<pmg>密码不正确")
                else:
                    state.username = user
                    state.logged_in = True
                    responses.extend(self.login_success_payload())
                continue

            if ".860" in cmd or "860." in cmd or "NON5800" in cmd:
                state.metadata["client_info"] = cmd
                continue

            if cmd.startswith("quit"):
                responses.append("<quitgame>")
                continue

            if cmd in {"0", "menu", "sys"}:
                responses.append("<menu>|[compat status]兼容服务器状态|[enter world]进入风车镇(协议恢复)|[quit]退出游戏")
                continue
            if cmd == "compat status":
                responses.append("<pmg>V860兼容服务器：网络层、CID/Session、登录与菜单协议已连接；地图协议恢复中。")
                continue

            if cmd == "enter world":
                responses.extend([
                    "<title>风车镇（兼容测试入口）",
                    "<pmg>V860 已经进入兼容服务器业务层。下一步接入原版人物状态、地图与 NPC 数据。",
                    "<menu>|[compat status]查看协议状态|[quit]退出游戏",
                ])
                continue

            if cmd and not cmd.startswith("#"):
                responses.append("<smg>兼容服已收到命令：" + self.escape_for_text(cmd[:80]))

        if len(responses) == 1 and responses[0].startswith("<cid"):
            responses.append("<smg>V860兼容服务器已连接")
        return responses

    @staticmethod
    def escape_for_text(s: str) -> str:
        return s.replace("\n", " ").replace("\r", " ")

    @staticmethod
    def login_success_payload() -> list[str]:
        return [
            "<log_suc>",
            "<title>V860兼容服务器",
            "<smg>V860兼容服务器登录成功",
            "<pmg>登录握手已通过。请选择兼容测试入口；原版地图与战斗协议正在逐项恢复。",
            "<menu>|[compat status]查看协议状态|[enter world]进入风车镇(协议恢复)|[quit]退出游戏",
        ]


class HZWCompatServer:
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir: Path):
        self.host = host
        self.tcp_port = tcp_port
        self.http_port = http_port
        self.world = CompatWorld(data_dir)
        self.http_states: Dict[str, SessionState] = {}

    async def serve(self) -> None:
        tcp = await asyncio.start_server(self.handle_tcp, self.host, self.tcp_port)
        http = await asyncio.start_server(self.handle_http, self.host, self.http_port)
        for s in tcp.sockets or []:
            LOG.info("V860 socket listening on %s", s.getsockname())
        for s in http.sockets or []:
            LOG.info("V860 HTTP listening on %s", s.getsockname())
        async with tcp, http:
            await asyncio.gather(tcp.serve_forever(), http.serve_forever())

    async def handle_tcp(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        state = SessionState()
        LOG.info("TCP connect %s", peer)
        try:
            connect_line = await asyncio.wait_for(reader.readline(), timeout=10)
            LOG.info("TCP CONNECT line %s: %r", peer, connect_line)
            if not connect_line.startswith(b"CONNECT "):
                LOG.warning("Unexpected first line from %s", peer)
                return

            bootstrap = await asyncio.wait_for(reader.readexactly(10), timeout=5)
            if not (bootstrap[:2] == b"\x80\x5e" and bootstrap[4:10] == b"\x80kawa\n"):
                LOG.warning("Unexpected bootstrap from %s: %s", peer, bootstrap.hex())
            else:
                LOG.info("V860 bootstrap accepted from %s", peer)

            while True:
                header = await reader.readexactly(6)
                ack0 = header[0]
                old_seed = state.lcg_seed
                rot = state.next_lcg_rot(ack0)
                rotated_len = header[4] | (header[5] << 8)
                from hzw_protocol import rol16
                n = rol16(rotated_len, rot)
                state.lcg_seed = old_seed
                if n > 65535:
                    raise ValueError(f"unreasonable frame length {n}")
                payload = await reader.readexactly(n) if n else b""
                plain = decode_socket_client_frame(header, payload, state)
                if not plain:
                    LOG.debug("heartbeat/ack frame from %s", peer)
                    continue
                commands = split_commands(plain)
                LOG.info("TCP RX %s: %r", peer, commands)
                responses = self.world.handle_commands(commands, state)
                if responses:
                    packet = encode_socket_server_payload(join_server_lines(responses), state)
                    writer.write(packet)
                    await writer.drain()
                    LOG.info("TCP TX %s: %r", peer, responses)
        except asyncio.IncompleteReadError:
            LOG.info("TCP closed %s", peer)
        except (ConnectionResetError, BrokenPipeError):
            LOG.info("TCP reset %s", peer)
        except Exception:
            LOG.exception("TCP session error %s", peer)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def handle_http(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=10)
            if not request_line:
                return
            parts = request_line.decode("latin1").strip().split()
            if len(parts) != 3:
                return
            _method, target, _version = parts
            headers: Dict[str, str] = {}
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                k, _, v = line.decode("latin1").partition(":")
                headers[k.strip().lower()] = v.strip()
            n = int(headers.get("content-length", "0") or "0")
            body = await reader.readexactly(n) if n else b""

            u = urlsplit(target)
            cid_match = re.search(r"/([^/]+)\.jsp$", u.path)
            cid = cid_match.group(1) if cid_match else ""
            qs = parse_qs(u.query)
            sn = int(qs.get("sn", ["1"])[0] or "1")
            key = cid or f"bootstrap:{peer[0] if peer else 'unknown'}"
            state = self.http_states.get(key)
            if state is None:
                state = SessionState(cid=cid, sn=sn)
                self.http_states[key] = state
                if cid:
                    self.world.sessions_by_cid[cid] = state
            else:
                if cid and not state.cid:
                    state.cid = cid
                state.sn = sn

            commands: list[str] = []
            if body:
                try:
                    plain = decode_http_client_body(body, state)
                    commands = split_commands(plain)
                    LOG.info("HTTP RX %s %s: %r", peer, target, commands)
                except ValueError:
                    LOG.exception("Could not decode HTTP POST from %s target=%s", peer, target)

            responses = self.world.handle_commands(commands, state) if commands else ["<smg>V860兼容服务器HTTP通道在线"]
            response_body = encode_http_server_payload(join_server_lines(responses), state)
            head = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "Pragma: no-cache\r\n\r\n"
            ).encode("ascii")
            writer.write(head + response_body)
            await writer.drain()
            LOG.info("HTTP TX %s: %r", peer, responses)
        except Exception:
            LOG.exception("HTTP error %s", peer)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Experimental compatibility server for Suishou/Troodon HZW V8.60.0")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--tcp-port", type=int, default=5926)
    ap.add_argument("--http-port", type=int, default=8080)
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    server = HZWCompatServer(args.host, args.tcp_port, args.http_port, args.data_dir)
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
