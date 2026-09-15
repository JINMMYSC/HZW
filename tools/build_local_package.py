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
    "chapter_server_v4.py",
]


def copy_server(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in SERVER_FILES:
        src = ROOT / name
        if not src.exists():
            raise RuntimeError(f"required server module missing from source tree: {src}")
        shutil.copy2(src, dst / name)
    (dst / "content").mkdir(exist_ok=True)
    for content_name in ("windmill_marine.json", "full_campaign_manifest.json"):
        src = ROOT / "content" / content_name
        if src.exists():
            shutil.copy2(src, dst / "content" / content_name)
    required_content = dst / "content" / "windmill_marine.json"
    if not required_content.exists():
        raise RuntimeError(f"required content database missing: {required_content}")
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
    module_names = tuple(Path(name).stem for name in SERVER_FILES)
    old_modules = {name: sys.modules.pop(name, None) for name in module_names}
    try:
        sys.path.insert(0, str(dst))
        __import__("chapter_server_v4")
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
        "echo HZW V860 - V4 native interaction server\r\n"
        "echo Native exits / reciprocal doors / NPC collision / original keypad menus enabled\r\n"
        "%PY% chapter_server_v4.py --debug\r\n"
        "set \"EC=%ERRORLEVEL%\"\r\n"
        "echo.\r\n"
        "if not \"%EC%\"==\"0\" echo [ERROR] Server exited with code %EC%.\r\n"
        "pause\r\n"
        "exit /b %EC%\r\n",
        encoding="utf-8",
    )
    (dst / "README_先看我.txt").write_text(
        "HZW V860 本地复原包 V4\n\n"
        "1. 双击 启动服务器.bat。\n"
        f"2. 保持服务器窗口开启，用手机顽童打开 {jar_name}。\n"
        "3. 虚拟屏幕使用 360x360。\n"
        "4. 角色/任务/物品存档位于 data\\players。\n"
        "5. 地图出口采用原V860地图触发点，不再按服务器坐标提前过图。\n"
        "6. 室内入口全部配对返回门；撞NPC会触发交互，5键会快速锁定附近目标。\n"
        "7. 1/3/5/7/9/0及个人/系统菜单按V860原客户端命令接入。\n"
        "8. 普通走路由原V860客户端本地动画完成，服务器仅同步状态。\n\n"
        "说明：此包由你本地提供的原 V860 JAR 生成，不在仓库重新分发原游戏 JAR。\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a local HZW V860 V4 package")
    ap.add_argument("jar", type=Path, help="your original V860 JAR")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--out", type=Path, default=Path("dist/HZW-V860-Full-Restore"))
    args = ap.parse_args()
    src = args.jar.resolve()
    if not src.exists():
        raise SystemExit(f"JAR not found: {src}")
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    copy_server(out)
    patched = out / "HZW-V860-本地复原.jar"
    patch_jar(src, patched, 3, args.host, 5926, args.host, 8080)
    write_launchers(out, patched.name)
    validate_server_package(out)
    archive = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
    print("[OK] V4 package validation passed")
    print(f"package folder: {out}")
    print(f"package zip   : {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
