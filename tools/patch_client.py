from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hzw_protocol import decode_dat_resource, encode_dat_resource


def patch_proxy_group(text: str, group: int, tcp_host: str, tcp_port: int, http_host: str, http_port: int) -> str:
    marker = "<newproxy>"
    start = text.find(marker)
    if start < 0:
        raise RuntimeError("newproxy config not found in csys/list.dat")
    line_end = text.find("\n", start)
    if line_end < 0:
        line_end = len(text)
    line = text[start:line_end]

    groups = line[len(marker):].split("#")
    out = []
    found = False
    for part in groups:
        if not part:
            continue
        if part.startswith(str(group) + "_"):
            part = f"{group}_s{tcp_host}:{tcp_port}|h{http_host}:{http_port}"
            found = True
        out.append(part)
    if not found:
        raise RuntimeError(f"proxy group #{group} not found")
    newline = marker + "#" + "#".join(out)
    return text[:start] + newline + text[line_end:]


def patch_hzw_ui(text: str) -> str:
    """Keep V860's original local menu mechanism but fix HZW-facing terms/routes.

    The shipped list.dat contains generic-engine leftovers (宠物/武功/帮派).
    Those internal command names are still accepted by the server, but the player
    facing menus are routed to the restored HZW concepts: 副官/战斗技能/公会.
    """
    replacements = {
        "<menu>|[\x1c11]个人状态|[\x1c12]物品行囊|[\x1cpet]宠物指令|[1 4]队伍指令|[1 5]武功技能|[1 6]神秘商店|[\x1c17]换取金币":
            "<menu>|[ui status]个人状态|[ui bag]物品行囊|[ui deputy]副官指令|[ui team]队伍指令|[ui skills]战斗技能|[ui shop]神秘商店|[ui coins]金币",
        "<menu(g:a)(x:1 1)>个人状态|[1]当前装备|[2]个人属性|[3]当前任务":
            "<menu(g:a)>个人状态|[ui equipment]当前装备|[ui attributes]个人属性|[ui quest]当前任务",
        "<menu(g:a)(x:1 2)>|[1]武器装备|[2]辅助物品|[3]任务道具|[4]摆摊出售":
            "<menu(g:a)>物品行囊|[ui bag equipment]武器装备|[ui bag assist]辅助物品|[ui bag quest]任务道具|[ui bag stall]摆摊出售",
        "<menu(g:a)(x:9 )>|[1]查看任务|[2]区域地图|[3]世界地图|[4]搜索地图":
            "<menu(g:a)>任务与地图|[9 1]查看任务|[9 2]区域地图|[9 3]世界地图|[9 4]搜索地图",
        "<menu>|[3]好友列表|[\x1c7]聊天指令|[guild]帮派指令|[\x1c0r]注册帐号|[\x1c0s]常用设置|[\x1c0h]游戏帮助|[\x1c0q]退出游戏":
            "<menu>|[ui friends]好友列表|[ui chat]聊天指令|[ui guild]公会指令|[ui account]帐号信息|[ui settings]常用设置|[ui help]游戏帮助|[ui exit]退出游戏",
        "<menu(g:a)>常用设置|[0 s]编写短语|[0 g]拒入帮会|[0 3]广播开关|[0 a3]清空黑名单":
            "<menu(g:a)>常用设置|[0 s]编写短语|[0 g]拒入公会|[0 3]广播开关|[0 a3]清空黑名单",
        "<menu>频道广播|[\x1c761]帮派|[\x1c762]队伍|[\x1c763]买卖|[\x1c764]吵架":
            "<menu>频道广播|[\x1c761]公会|[\x1c762]队伍|[\x1c763]买卖|[\x1c764]聊天",
        "<input(@)(x:7 61)>帮派频道：你想说什么?":
            "<input(@)(x:7 61)>公会频道：你想说什么?",
        "<menu(x:petcmd )>|[1]叫出宠物|[2]收回宠物|[3]宠物喂食|[4]宠物取名|[5]察看宠物":
            "<menu(x:petcmd )>副官指令|[1]副官出战|[2]副官休息|[3]副官培养|[4]副官设置|[5]查看副官",
        "切磋武功": "切磋",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def patch_jar(src: Path, dst: Path, group: int, tcp_host: str, tcp_port: int, http_host: str, http_port: int) -> None:
    with zipfile.ZipFile(src, "r") as zin:
        encoded = zin.read("csys/list.dat")
        plain = decode_dat_resource(encoded)
        text = plain.decode("utf-8")
        text = patch_proxy_group(text, group, tcp_host, tcp_port, http_host, http_port)
        text = patch_hzw_ui(text)
        patched = text.encode("utf-8")
        if len(patched) != len(plain):
            print(f"note: list.dat length changed {len(plain)} -> {len(patched)} bytes")
        reencoded = encode_dat_resource(patched)
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = reencoded if info.filename == "csys/list.dat" else zin.read(info.filename)
                zout.writestr(info, data)
    print(f"patched client written: {dst}")
    print(f"proxy group #{group}: socket={tcp_host}:{tcp_port}, http={http_host}:{http_port}")
    print("HZW UI terminology/routes patched: deputy / battle skills / guild")


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch V860 to the local HZW compatibility server")
    ap.add_argument("jar", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--group", type=int, default=3, help="V860 menu entries in this client use #3")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--tcp-port", type=int, default=5926)
    ap.add_argument("--http-port", type=int, default=8080)
    args = ap.parse_args()
    patch_jar(args.jar, args.out, args.group, args.host, args.tcp_port, args.host, args.http_port)


if __name__ == "__main__":
    main()
