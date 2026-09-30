from __future__ import annotations

import json
import re
import tempfile
import zipfile
from pathlib import Path

from jar_diff import inventory_jar

V860_MIDLET_VERSION = "8.60.0"
V860_INTERNAL_VERSION = "860.1HZ0000.NON5800.CT"

_INTERNAL_VERSION = re.compile(rb"(?<![A-Za-z0-9])\d{3}\.\d+HZ[A-Z0-9.]+")
_NETWORK_ENDPOINT = re.compile(
    rb"(?:https?|socket)://[A-Za-z0-9._~:/?#\[\]@!$&'*+,;=%-]+"
)


def _scan_binary_strings(path: Path, entry_names: list[str]) -> tuple[list[str], list[str]]:
    versions: set[str] = set()
    endpoints: set[str] = set()
    with zipfile.ZipFile(path) as jar:
        for entry_name in entry_names:
            payload = jar.read(entry_name)
            versions.update(
                match.decode("ascii") for match in _INTERNAL_VERSION.findall(payload)
            )
            endpoints.update(
                match.rstrip(b".,;:").decode("ascii")
                for match in _NETWORK_ENDPOINT.findall(payload)
            )
    return sorted(versions), sorted(endpoints)


def _classify(manifest_version: str | None, internal_versions: list[str]) -> str:
    has_v860_internal = V860_INTERNAL_VERSION in internal_versions
    if manifest_version == V860_MIDLET_VERSION and has_v860_internal:
        return "V860_DIRECT_BINARY_MATCH"
    if manifest_version and manifest_version != V860_MIDLET_VERSION:
        return "VERSION_DRIFT"
    if internal_versions and not has_v860_internal:
        return "VERSION_DRIFT"
    if manifest_version == V860_MIDLET_VERSION:
        return "JAR_CANDIDATE_NEEDS_INTERNAL_VERSION"
    if has_v860_internal:
        return "JAR_CANDIDATE_NEEDS_MANIFEST_VERSION"
    return "JAR_CANDIDATE_NEEDS_VERSION_EVIDENCE"


def scan_candidate(
    path: str | Path,
    *,
    source_url: str | None = None,
    claimed_device: str | None = None,
) -> dict[str, object]:
    jar_path = Path(path).resolve()
    inventory = inventory_jar(jar_path)
    entry_names = sorted(str(name) for name in inventory["entries"])
    internal_versions, endpoints = _scan_binary_strings(jar_path, entry_names)
    manifest = dict(inventory["manifest"])
    manifest_version = manifest.get("MIDlet-Version")

    provenance = {
        key: value
        for key, value in {
            "source_url": source_url,
            "claimed_device": claimed_device,
        }.items()
        if value is not None
    }
    return {
        "schema": "hzw-jar-intake-v1",
        "evidence_grade": _classify(manifest_version, internal_versions),
        "name": inventory["name"],
        "path": inventory["path"],
        "size": inventory["size"],
        "sha256": inventory["sha256"],
        "manifest": manifest,
        "matched_internal_versions": internal_versions,
        "network_endpoints": endpoints,
        "class_count": len(inventory["classes"]),
        "resource_count": len(inventory["resources"]),
        "provenance": provenance,
        "classification_rule": (
            "V860_DIRECT_BINARY_MATCH requires both MIDlet-Version 8.60.0 and "
            "the exact internal string 860.1HZ0000.NON5800.CT."
        ),
    }


def write_intake_report(
    path: str | Path,
    output: str | Path,
    *,
    source_url: str | None = None,
    claimed_device: str | None = None,
) -> None:
    jar_path = Path(path).resolve()
    output_path = Path(output).resolve()
    if jar_path == output_path:
        raise ValueError("JAR input and intake output resolve to the same file")

    report = scan_candidate(
        jar_path,
        source_url=source_url,
        claimed_device=claimed_device,
    )
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
