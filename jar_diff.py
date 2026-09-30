from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

MAX_JAR_ENTRIES = 10_000
MAX_ENTRY_SIZE = 32 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_SIZE = 128 * 1024 * 1024


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(payload: bytes) -> dict[str, str]:
    text = payload.decode("utf-8", errors="replace").replace("\r\n", "\n")
    unfolded: list[str] = []
    for line in text.split("\n"):
        if line.startswith(" ") and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    result: dict[str, str] = {}
    for line in unfolded:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.lstrip()
    return result


def inventory_jar(path: str | Path) -> dict[str, object]:
    jar_path = Path(path).resolve()
    entry_hashes: dict[str, str] = {}
    manifest: dict[str, str] = {}

    with zipfile.ZipFile(jar_path) as jar:
        infos = [info for info in jar.infolist() if not info.is_dir()]
        if len(infos) > MAX_JAR_ENTRIES:
            raise ValueError(f"JAR has too many entries: {len(infos)}")
        total_size = sum(info.file_size for info in infos)
        if total_size > MAX_TOTAL_UNCOMPRESSED_SIZE:
            raise ValueError(f"JAR uncompressed size exceeds limit: {total_size}")

        seen: set[str] = set()
        for info in sorted(infos, key=lambda item: item.filename):
            if info.is_dir():
                continue
            if info.filename in seen:
                raise ValueError(f"duplicate JAR entry: {info.filename}")
            seen.add(info.filename)
            if info.file_size > MAX_ENTRY_SIZE:
                raise ValueError(
                    f"JAR entry exceeds size limit: {info.filename} ({info.file_size})"
                )

            digest = hashlib.sha256()
            manifest_payload = bytearray()
            is_manifest = info.filename.upper() == "META-INF/MANIFEST.MF"
            with jar.open(info) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
                    if is_manifest:
                        manifest_payload.extend(chunk)
            entry_hashes[info.filename] = digest.hexdigest()
            if info.filename.upper() == "META-INF/MANIFEST.MF":
                manifest = parse_manifest(bytes(manifest_payload))

    paths = sorted(entry_hashes)
    return {
        "name": jar_path.name,
        "path": str(jar_path),
        "size": jar_path.stat().st_size,
        "sha256": _sha256_file(jar_path),
        "manifest": manifest,
        "classes": [path for path in paths if path.endswith(".class")],
        "resources": [path for path in paths if not path.endswith(".class")],
        "entries": entry_hashes,
    }


def compare_jars(paths: Iterable[str | Path]) -> dict[str, object]:
    resolved_paths = [Path(path).resolve() for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("duplicate JAR input path")

    inventories = [inventory_jar(path) for path in resolved_paths]
    if len(inventories) < 2:
        raise ValueError("compare_jars requires at least two JAR files")

    name_counts = Counter(str(inventory["name"]) for inventory in inventories)
    for inventory in inventories:
        name = str(inventory["name"])
        inventory["id"] = name if name_counts[name] == 1 else str(inventory["path"])

    entry_sets = [set(inventory["entries"]) for inventory in inventories]
    shared_paths = set.intersection(*entry_sets)
    identical_in_all: list[str] = []
    changed_shared_paths: list[str] = []
    for path in sorted(shared_paths):
        hashes = {inventory["entries"][path] for inventory in inventories}
        if len(hashes) == 1:
            identical_in_all.append(path)
        else:
            changed_shared_paths.append(path)

    partially_shared_paths: dict[str, dict[str, object]] = {}
    all_paths = set().union(*entry_sets)
    for path in sorted(all_paths - shared_paths):
        present = [
            inventory
            for inventory in inventories
            if path in inventory["entries"]
        ]
        if len(present) < 2:
            continue
        hashes = {inventory["entries"][path] for inventory in present}
        partially_shared_paths[path] = {
            "present_in": [str(inventory["id"]) for inventory in present],
            "content_identical": len(hashes) == 1,
        }

    unique_paths: dict[str, list[str]] = {}
    for index, inventory in enumerate(inventories):
        other_paths = set().union(
            *(entry_sets[other] for other in range(len(entry_sets)) if other != index)
        )
        unique_paths[str(inventory["id"])] = sorted(entry_sets[index] - other_paths)

    return {
        "schema": "hzw-jar-diff-v1",
        "jar_count": len(inventories),
        "jars": inventories,
        "identical_in_all": identical_in_all,
        "changed_shared_paths": changed_shared_paths,
        "partially_shared_paths": partially_shared_paths,
        "unique_paths": unique_paths,
    }


def write_report(paths: Iterable[str | Path], output: str | Path) -> None:
    input_paths = [Path(path).resolve() for path in paths]
    output_path = Path(output).resolve()
    if output_path in input_paths:
        raise ValueError("JAR input and report output resolve to the same file")

    report = compare_jars(input_paths)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=output_path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp.write(rendered)
            temp_name = temp.name
        Path(temp_name).replace(output_path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
