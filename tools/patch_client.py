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


def patch_jar(src: Path, dst: Path, group: int, tcp_host: str, tcp_port: int, http_host: str, http_port: int) -> None:
    with zipfile.ZipFile(src, "r") as zin:
        encoded = zin.read("csys/list.dat")
        plain = decode_dat_resource(encoded)
        text = plain.decode("utf-8")
        patched = patch_proxy_group(text, group, tcp_host, tcp_port, http_host, http_port).encode("utf-8")
        if len(patched) != len(plain):
            print(f"note: list.dat length changed {len(plain)} -> {len(patched)} bytes")
        reencoded = encode_dat_resource(patched)
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = reencoded if info.filename == "csys/list.dat" else zin.read(info.filename)
                zout.writestr(info, data)
    print(f"patched client written: {dst}")
    print(f"proxy group #{group}: socket={tcp_host}:{tcp_port}, http={http_host}:{http_port}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch V860 newproxy group to a compatibility server")
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
