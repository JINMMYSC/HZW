from __future__ import annotations

import argparse
import py_compile
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.patch_client import patch_jar

ROOT = Path(__file__).resolve().parents[1]
SERVER_FILES = [
    "server.py",
    "hzw_protocol.py",
    "world_protocol.py",
    "chapter_engine.py",
    "chapter_maps.py",
    "chapter_server.py",
    "chapter_server_v2.py",
    "chapter_server_v3.py",
]


def copy_server(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in SERVER_FILES:
        src = ROOT / name
        if not src.exists():
            raise RuntimeError(f"required server module missing from source tree: {src}")
        shutil.copy2(src, dst / name)
    (dst / "content").mkdir(exist_ok=True)
    content_src = ROOT / "content" / "windmill_marine.json"
    if not content_src.exists():
        raise RuntimeError(f"required content database missing: {content_src}")
    shutil.copy2(content_src, dst / "content" / "windmill_marine.json")
    (dst / "data").mkdir(exist_ok=True)


def validate_server_package(dst: Path) -> None:
    required = [dst / name for name in SERVER_FILES]
    required.append(dst / "content" / "windmill_marine.json")
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("package validation failed; missing files: " + ", ".join(missing))

    for name in SERVER_FILES:
        py_compile.compile(str(dst / name), doraise=True)

    old_path = list(sys.path)
    module_names = (
        "server", "hzw_protocol", "world_protocol", "chapter_engine",
        "chapter_maps", "chapter_server", "chapter_server_v2", "chapter_server_v3",
    )
    old_modules = {name: sys.modules.pop(name, None) for name in module_names}
    try:
        sys.path.insert(0, str(dst))
        __import__("chapter_server_v3")
    finally:
        sys.path[:] = old_path
        for name in module_names:
            sys.modules.pop(name, None)
        for name, module in old_modules.items():
            if module is not None:
                sys.modules[name] = module


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
        "echo HZW V860 - Windmill Village + Marine Base V3 server\r\n"
        "echo Native exits / NPC collision / keypad menus enabled\r\n"
        "%PY% chapter_server_v3.py --debug\r\n"
        "set \"EC=%ERRORLEVEL%\"\r\n"
        "echo.\r\n"
        "if not \"%EC%\"==\"0\" echo [ERROR] Server exited with code %EC%.\r\n"
        "pause\r\n"
        "exit /b %EC%\r\n",
        encoding="utf-8",
    )
    (dst / "README_先看我.txt").write_text(
        "HZW V860 风车镇 + 海军基地 本地复原包 V3\n\n"
        "1. 双击 启动服务器.bat。\n"
        f"2. 保持服务器窗口开启，用手机顽童打开 {jar_name}。\n"
        "3. 虚拟屏幕使用 360x360。\n"
        "4. 角色/任务/物品存档位于 data\\players。\n"
        "5. 地图出口采用原V860地图触发点；NPC使用原客户端碰撞交互对象。\n"
        "6. 1/3/5/7/9/0及个人/系统菜单已接入服务器。\n"
        "7. 普通走路由原V860客户端本地动画完成，服务器维护权威坐标。\n\n"
        "说明：此包由你本地提供的原 V860 JAR 生成，不在仓库重新分发原游戏 JAR。\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a local HZW V860 Windmill+Marine V3 package")
    ap.add_argument("jar", type=Path, help="your original V860 JAR")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--out", type=Path, default=Path("dist/HZW-V860-Windmill-Marine"))
    args = ap.parse_args()
    src = args.jar.resolve()
    if not src.exists():
        raise SystemExit(f"JAR not found: {src}")
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    copy_server(out)
    patched = out / "HZW-V860-风车镇-海军基地.jar"
    patch_jar(src, patched, 3, args.host, 5926, args.host, 8080)
    write_launchers(out, patched.name)
    validate_server_package(out)
    archive = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
    print("[OK] V3 package validation passed")
    print(f"package folder: {out}")
    print(f"package zip   : {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
