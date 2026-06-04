#!/usr/bin/env python3
"""Discover local OGS executables and record readiness for model execution."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_SEARCH_DIRS = [
    Path("/usr/bin"),
    Path("/usr/local/bin"),
    Path("/opt"),
    Path("/home/ber0061"),
]

DEFAULT_CONTAINER_SEARCH_DIRS = [
    Path("/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected"),
    Path("/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements"),
]

CONTAINER_RUNTIMES = ["apptainer", "singularity", "run-singularity"]
DEFAULT_DOCKER_APPTAINER_IMAGE = "ghcr.io/apptainer/apptainer:latest"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="append",
        type=Path,
        default=[],
        help="Explicit OGS executable candidate path. Can be repeated.",
    )
    parser.add_argument(
        "--search-dir",
        action="append",
        type=Path,
        default=[],
        help="Directory to search recursively for executable files named ogs.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum recursive search depth below each search directory.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/OGS_ENVIRONMENT_AUDIT.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/OGS_ENVIRONMENT_AUDIT.md"),
    )
    parser.add_argument(
        "--container-candidate",
        action="append",
        type=Path,
        default=[],
        help="Explicit Apptainer/Singularity SIF candidate path. Can be repeated.",
    )
    parser.add_argument(
        "--container-search-dir",
        action="append",
        type=Path,
        default=[],
        help="Directory to search recursively for .sif container images.",
    )
    parser.add_argument(
        "--container-max-depth",
        type=int,
        default=7,
        help="Maximum recursive search depth below each container search directory.",
    )
    parser.add_argument(
        "--docker-apptainer-image",
        default=DEFAULT_DOCKER_APPTAINER_IMAGE,
        help=(
            "Docker image that provides an apptainer executable for running SIF "
            "images when no native Apptainer/Singularity runtime is installed."
        ),
    )
    return parser.parse_args()


def is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def relative_depth(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 999999


def recursive_find_ogs(root: Path, max_depth: int) -> list[Path]:
    if not root.exists():
        return []
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        if relative_depth(root, current) > max_depth:
            continue
        try:
            entries = list(current.iterdir())
        except (OSError, PermissionError):
            continue
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                stack.append(entry)
            elif entry.name == "ogs" and is_executable_file(entry):
                found.append(entry.resolve())
    return sorted(set(found))


def recursive_find_sif(root: Path, max_depth: int) -> list[Path]:
    if not root.exists():
        return []
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        if relative_depth(root, current) > max_depth:
            continue
        try:
            entries = list(current.iterdir())
        except (OSError, PermissionError):
            continue
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                stack.append(entry)
            elif entry.suffix.lower() == ".sif" and entry.is_file():
                found.append(entry.resolve())
    return sorted(set(found))


def read_sif_header(path: Path, limit_bytes: int = 4 * 1024 * 1024) -> str:
    try:
        data = path.read_bytes()[:limit_bytes]
    except OSError:
        return ""
    return data.decode("utf-8", errors="ignore")


def regex_first(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def inspect_sif(path: Path) -> dict[str, Any]:
    header = read_sif_header(path)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "has_runsingularity_shebang": header.startswith("#!/usr/bin/env run-singularity"),
        "has_sif_magic": "SIF_MAGIC" in header,
        "source_image": regex_first(header, r'"from":\s*"([^"]+)"')
        or regex_first(header, r"from:\s*([^\n]+)"),
        "version_label": regex_first(header, r'"version":\s*"([^"]+)"'),
        "cmake_args": regex_first(header, r'"cmake_args":\s*"([^"]+)"'),
        "container_path_mentions_ogs": "/usr/local/ogs/build/bin" in header,
    }


def collect_container_candidates(explicit: list[Path], search_dirs: list[Path], max_depth: int) -> list[Path]:
    candidates: list[Path] = []
    for path in explicit:
        if path.is_file() and path.suffix.lower() == ".sif":
            candidates.append(path.resolve())
    for root in search_dirs:
        candidates.extend(recursive_find_sif(root.resolve(), max_depth))
    return sorted(set(candidates))


def runtime_status(docker_apptainer_image: str) -> dict[str, Any]:
    available = {name: shutil.which(name) for name in CONTAINER_RUNTIMES}
    available = {name: path for name, path in available.items() if path}
    docker_path = shutil.which("docker")
    native_runtime = next(iter(available.values()), None)
    if native_runtime:
        preferred_backend = "native_sif_runtime"
        preferred_runtime = native_runtime
    elif docker_path:
        preferred_backend = "docker_apptainer_sif"
        preferred_runtime = docker_path
    else:
        preferred_backend = None
        preferred_runtime = None
    return {
        "available_container_runtimes": available,
        "native_sif_runtime_available": bool(native_runtime),
        "docker_path": docker_path,
        "docker_apptainer_image": docker_apptainer_image,
        "docker_apptainer_backend_available": bool(docker_path),
        "preferred_container_backend": preferred_backend,
        "preferred_container_runtime": preferred_runtime,
        "notes": [
            "Apptainer/Singularity/run-singularity can execute SIF images.",
            "If no native SIF runtime is installed, the workflow can execute the collected SIF through Dockerized Apptainer.",
            "This audit records command availability; run_ogs_model.py records the actual OGS execution command and return code.",
        ],
    }


def run_version(path: Path) -> dict[str, Any]:
    commands = [[str(path), "--version"], [str(path), "-v"]]
    for command in commands:
        started = time.time()
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "command": command,
                "returncode": None,
                "stdout": "",
                "stderr": str(exc),
                "duration_s": time.time() - started,
                "version_probe_status": "failed_to_run",
            }
        if result.returncode == 0 or result.stdout.strip() or result.stderr.strip():
            return {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "duration_s": time.time() - started,
                "version_probe_status": "completed",
            }
    return {
        "command": commands[-1],
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "duration_s": 0.0,
        "version_probe_status": "no_output",
    }


def collect_candidates(explicit: list[Path], search_dirs: list[Path], max_depth: int) -> list[Path]:
    candidates: list[Path] = []
    path_match = shutil.which("ogs")
    if path_match:
        candidates.append(Path(path_match).resolve())
    for path in explicit:
        if is_executable_file(path):
            candidates.append(path.resolve())
    for root in search_dirs:
        candidates.extend(recursive_find_ogs(root.resolve(), max_depth))
    return sorted(set(candidates))


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# OGS Environment Audit",
        "",
        "This file records whether the local environment can execute the recovered",
        "CD-A OGS model. It is an execution-readiness artifact; it does not modify",
        "the GESA model or run OGS.",
        "",
        f"- Audit status: `{audit['status']}`",
        f"- `PATH` lookup: `{audit['path_lookup'] or 'not found'}`",
        f"- Executable candidates: {len(audit['candidates'])}",
        f"- Selected executable: `{audit['selected_executable'] or 'none'}`",
        "",
    ]
    if audit["candidates"]:
        lines.extend(["## Candidates", ""])
        lines.append("| Path | Version probe status | Version output |")
        lines.append("| --- | --- | --- |")
        for candidate in audit["candidates"]:
            version = candidate.get("version", {})
            output = version.get("stdout") or version.get("stderr") or ""
            output = output.splitlines()[0] if output else ""
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{candidate['path']}`",
                        str(version.get("version_probe_status", "")),
                        output.replace("|", "/"),
                    ]
                )
                + " |"
            )
    if audit.get("container_candidates"):
        lines.extend(["", "## Container Candidates", ""])
        lines.append("| Path | Version label | Runnable now | Runtime blocker |")
        lines.append("| --- | --- | --- | --- |")
        runtime_info = audit.get("runtime_status", {})
        runtime = runtime_info.get("preferred_container_runtime")
        backend = runtime_info.get("preferred_container_backend")
        for candidate in audit["container_candidates"]:
            runnable = bool(runtime)
            if runnable:
                blocker = ""
            else:
                blocker = "install Apptainer/Singularity, provide run-singularity, or enable Dockerized Apptainer"
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{candidate['path']}`",
                        str(candidate.get("version_label") or "").replace("|", "/"),
                        str(runnable),
                        blocker,
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "Container runtime status:",
                "",
                f"- Preferred container backend: `{backend or 'none'}`",
                f"- Preferred SIF runtime command: `{runtime or 'none'}`",
                f"- Available native SIF runtimes: `{runtime_info.get('available_container_runtimes', {})}`",
                f"- Docker path: `{runtime_info.get('docker_path') or 'not found'}`",
                f"- Dockerized Apptainer image: `{runtime_info.get('docker_apptainer_image') or 'none'}`",
            ]
        )
    if not audit["candidates"] and not audit.get("container_candidates"):
        lines.extend(
            [
                "## Required Action",
                "",
                "- Install or locate a compatible OGS executable.",
                "- If using the collected SIF container, install Apptainer/Singularity",
                "  or provide a `run-singularity` wrapper.",
                "- Re-run this audit with `--candidate /path/to/ogs` if OGS is outside",
                "  the standard search locations.",
                "- Then run `evaluate_inversion_candidate.py --ogs-mode execute --ogs",
                "  /path/to/ogs` or `run_inversion_candidate_search.py --ogs-mode",
                "  execute --ogs /path/to/ogs`.",
            ]
        )
    elif audit["status"] == "ogs_container_found_runtime_missing":
        lines.extend(
            [
                "",
                "## Required Action",
                "",
                "- Install Apptainer/Singularity or provide a `run-singularity` wrapper",
                "  so the collected SIF can be executed.",
                "- If Docker is available, the workflow can also run the collected SIF",
                "  through Dockerized Apptainer by passing",
                "  `--docker-apptainer-image ghcr.io/apptainer/apptainer:latest`",
                "  to `run_ogs_model.py` or the candidate-evaluation wrappers.",
                "- Then run `run_ogs_model.py --sif /path/to/apptainer_ogs6.5.4.sif`",
                "  on the prepared run directory, or pass the same `--sif` through",
                "  `evaluate_inversion_candidate.py --ogs-mode execute`.",
            ]
        )
    elif audit["status"] == "ogs_container_found_runtime_available":
        runtime_info = audit.get("runtime_status", {})
        backend = runtime_info.get("preferred_container_backend")
        lines.extend(
            [
                "",
                "## Execution Backend",
                "",
                f"- Preferred backend: `{backend}`",
                f"- Runtime command: `{runtime_info.get('preferred_container_runtime')}`",
            ]
        )
        if backend == "docker_apptainer_sif":
            lines.extend(
                [
                    f"- Dockerized Apptainer image: `{runtime_info.get('docker_apptainer_image')}`",
                    "- Run OGS through `run_ogs_model.py --sif ... --docker-apptainer-image ... --docker-workspace-root ...`.",
                ]
            )
    lines.extend(
        [
            "",
            "## Search Scope",
            "",
            f"- Search directories: {', '.join(audit['search_dirs'])}",
            f"- Maximum search depth: {audit['max_depth']}",
            f"- Container search directories: {', '.join(audit['container_search_dirs'])}",
            f"- Container maximum search depth: {audit['container_max_depth']}",
            "",
            "## Notes",
            "",
            "- State-observation residuals remain inactive until OGS produces output",
            "  VTU files that can be sampled at observation times and fields.",
            "- Direct permeability residuals can still be evaluated from candidate",
            "  mesh fields without executing OGS.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    search_dirs = args.search_dir or DEFAULT_SEARCH_DIRS
    container_search_dirs = args.container_search_dir or DEFAULT_CONTAINER_SEARCH_DIRS
    candidates = collect_candidates(args.candidate, search_dirs, args.max_depth)
    container_candidates = collect_container_candidates(
        args.container_candidate,
        container_search_dirs,
        args.container_max_depth,
    )
    candidate_records = [{"path": str(path), "version": run_version(path)} for path in candidates]
    container_records = [inspect_sif(path) for path in container_candidates]
    selected = str(candidates[0]) if candidates else None
    runtime = runtime_status(args.docker_apptainer_image)
    if selected:
        status = "ogs_executable_found"
    elif container_records and runtime["preferred_container_runtime"]:
        status = "ogs_container_found_runtime_available"
    elif container_records:
        status = "ogs_container_found_runtime_missing"
    else:
        status = "ogs_executable_missing"
    audit = {
        "status": status,
        "path_lookup": shutil.which("ogs"),
        "selected_executable": selected,
        "candidates": candidate_records,
        "selected_container": container_records[0]["path"] if container_records else None,
        "container_candidates": container_records,
        "runtime_status": runtime,
        "search_dirs": [str(path.resolve()) for path in search_dirs],
        "max_depth": args.max_depth,
        "container_search_dirs": [str(path.resolve()) for path in container_search_dirs],
        "container_max_depth": args.container_max_depth,
        "notes": [
            "This audit only checks local executable availability.",
            "A collected Apptainer/Singularity SIF can be a valid OGS candidate only if a SIF runtime is available.",
            "A successful candidate still needs a model run and output sampling before state residuals are active.",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.output_md, audit)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"status: {status}")


if __name__ == "__main__":
    main()
