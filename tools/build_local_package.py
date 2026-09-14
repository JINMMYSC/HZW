from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.patch_client import patch_jar

ROOT = Path(__file__).resolve().parents[1]
SERVER_FILES = [
    "server.py", "hzw_protocol.py", "world_protocol.py", "chapter_engine.py",
    "chapter_server.py", "chapter_server_v2.py",
]


def copy_server(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in SERVER_FILES:
        shutil.copy2(ROOT / name, dst / name)
    (dst / "content").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "content" / "windmill_marine.json", dst / "content" / "windmill_marine.json")
    (dst / "data").mkdir(exist_ok=True)


def write_launchers(dst: Path, jar_name: str) -> None:
    (dst / "启动服务器.bat").write_text(
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        "cd /d \"%~dp0\"\r\n"
        "chcp 65001 >nul 2>nul\r\n"
        "set \"PY=\"\r\n"
        "python -c \"import sys\" >nul 2>nul && set \"PY=python\"\r\n"
        "if not defined PY py -3 -c \"import sys\" >nul 2>nul && set \"PY=py -3\"\r\n"
        "if not defined PY (echo [ERROR] Python 3 not found.& pause & exit /b 1)\r\n"
        "echo HZW V860 - Windmill Village + Marine Base server\r\n"
        "%PY% chapter_server_v2.py --debug\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    (dst / "README_先看我.txt").write_text(
        "HZW V860 风车镇 + 海军基地 本地复原包\n\n"
        "1. 双击 启动服务器.bat。\n"
        f"2. 保持服务器窗口开启，用手机顽童打开 {jar_name}。\n"
        "3. 虚拟屏幕使用 360x360。\n"
        "4. 角色/任务/物品存档位于 data\\players。\n"
        "5. 普通走路由原V860客户端本地动画完成，服务器维护权威坐标。\n\n"
        "说明：此包由你本地提供的原 V860 JAR 生成，不在仓库重新分发原游戏 JAR。\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a local HZW V860 Windmill+Marine test package")
    ap.add_argument("jar", type=Path, help="your original V860 JAR")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--out", type=Path, default=Path("dist/HZW-V860-Windmill-Marine"))
    args = ap.parse_args()
    src = args.jar.resolve()
    if not src.exists():
        raise SystemExit(f"JAR not found: {src}")
    out = args.out.resolve()
    if out.exists(): shutil.rmtree(out)
    copy_server(out)
    patched = out / "HZW-V860-风车镇-海军基地.jar"
    patch_jar(src, patched, 3, args.host, 5926, args.host, 8080)
    write_launchers(out, patched.name)
    archive = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
    print(f"package folder: {out}")
    print(f"package zip   : {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
