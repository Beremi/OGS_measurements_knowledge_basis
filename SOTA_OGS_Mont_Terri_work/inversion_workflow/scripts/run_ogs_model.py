#!/usr/bin/env python3
"""Run or dry-run an OGS project directory and record execution status."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run"),
        help="Prepared OGS run directory.",
    )
    parser.add_argument("--project-file", default="cd_a_open_niche_quad.prj")
    parser.add_argument("--ogs", type=Path, help="Path to the OGS executable. Defaults to PATH lookup.")
    parser.add_argument(
        "--sif",
        type=Path,
        help="Apptainer/Singularity SIF image containing OGS. Mutually exclusive with --ogs.",
    )
    parser.add_argument(
        "--container-runtime",
        help="Container runtime for --sif. Defaults to apptainer, singularity, then run-singularity on PATH.",
    )
    parser.add_argument(
        "--docker-apptainer-image",
        help=(
            "Docker image providing an apptainer executable for running --sif, "
            "for example ghcr.io/apptainer/apptainer:latest."
        ),
    )
    parser.add_argument(
        "--docker-workspace-root",
        type=Path,
        help=(
            "Host directory mounted at /work for --docker-apptainer-image. "
            "Defaults to the common parent of the run directory, SIF, and output directory."
        ),
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        help="Optional wall-clock timeout in seconds for the OGS command.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="OGS output directory. Defaults to <run-dir>/ogs_output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the exact command/status without executing OGS.",
    )
    parser.add_argument(
        "--status-file",
        type=Path,
        help="Status JSON path. Defaults to <run-dir>/OGS_EXECUTION_STATUS.json.",
    )
    return parser.parse_args()


def resolve_ogs(path: Path | None) -> str | None:
    if path is not None:
        return str(path.resolve()) if path.is_file() else None
    return shutil.which("ogs")


def resolve_container_runtime(name: str | None) -> str | None:
    if name:
        candidate = Path(name)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        return shutil.which(name)
    for candidate in ["apptainer", "singularity", "run-singularity"]:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def common_workspace_root(paths: list[Path]) -> Path:
    existing = [path if path.is_dir() else path.parent for path in paths]
    root = Path(os.path.commonpath([str(path.resolve()) for path in existing]))
    return root if root.is_dir() else root.parent


def docker_path(path: Path, workspace_root: Path) -> Path:
    resolved = path.resolve()
    if not is_relative_to(resolved, workspace_root):
        raise ValueError(f"{resolved} is not below Docker workspace root {workspace_root}")
    return Path("/work") / resolved.relative_to(workspace_root)


def container_command(
    runtime: str,
    sif: Path,
    run_dir: Path,
    project_file: Path,
    output_dir: Path,
) -> list[str]:
    runtime_name = Path(runtime).name
    if is_relative_to(output_dir, run_dir):
        container_output_dir = Path("/work") / output_dir.relative_to(run_dir)
        bind_args = [f"{run_dir}:/work"]
    else:
        container_output_dir = Path("/output")
        bind_args = [f"{run_dir}:/work", f"{output_dir}:/output"]
    if runtime_name in {"apptainer", "singularity"}:
        command = [runtime, "exec", "--pwd", "/work"]
        for bind_arg in bind_args:
            command.extend(["--bind", bind_arg])
        command.extend([str(sif), "ogs", "-o", str(container_output_dir), project_file.name])
        return command
    if runtime_name == "run-singularity":
        return [str(sif), "ogs", "-o", str(output_dir), project_file.name]
    return [runtime, "exec", "--pwd", "/work", "--bind", bind_args[0], str(sif), "ogs", "-o", str(container_output_dir), project_file.name]


def docker_apptainer_command(
    docker_image: str,
    sif: Path,
    run_dir: Path,
    project_file: Path,
    output_dir: Path,
    workspace_root: Path,
) -> list[str]:
    container_run_dir = docker_path(run_dir, workspace_root)
    container_sif = docker_path(sif, workspace_root)
    if is_relative_to(output_dir, run_dir):
        container_output_dir = output_dir.relative_to(run_dir)
    else:
        container_output_dir = docker_path(output_dir, workspace_root)
    return [
        "docker",
        "run",
        "--rm",
        "--privileged",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-v",
        "/etc/passwd:/etc/passwd:ro",
        "-v",
        "/etc/group:/etc/group:ro",
        "-v",
        f"{workspace_root}:/work",
        docker_image,
        "apptainer",
        "exec",
        "--bind",
        "/work:/work",
        "--pwd",
        str(container_run_dir),
        str(container_sif),
        "ogs",
        "-o",
        str(container_output_dir),
        project_file.name,
    ]


def with_timeout(command: list[str], timeout_s: int | None) -> list[str]:
    if timeout_s is None:
        return command
    if timeout_s <= 0:
        raise ValueError("--timeout-s must be positive")
    timeout_exe = shutil.which("timeout")
    if not timeout_exe:
        raise RuntimeError("timeout command not found; omit --timeout-s or install coreutils timeout")
    return [timeout_exe, str(timeout_s), *command]


def write_status(path: Path, status: dict[str, Any]) -> None:
    path.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.ogs and args.sif:
        raise SystemExit("--ogs and --sif are mutually exclusive")
    if args.docker_apptainer_image and not args.sif:
        raise SystemExit("--docker-apptainer-image requires --sif")
    run_dir = args.run_dir.resolve()
    project_file = run_dir / args.project_file
    output_dir = (args.output_dir or (run_dir / "ogs_output")).resolve()
    status_file = (args.status_file or (run_dir / "OGS_EXECUTION_STATUS.json")).resolve()

    if not run_dir.is_dir():
        raise SystemExit(f"run directory not found: {run_dir}")
    if not project_file.is_file():
        raise SystemExit(f"project file not found: {project_file}")

    ogs_executable = resolve_ogs(args.ogs) if not args.sif else None
    sif_image = args.sif.resolve() if args.sif else None
    docker_workspace_root = None
    if sif_image and args.docker_apptainer_image:
        docker_workspace_root = (
            args.docker_workspace_root.resolve()
            if args.docker_workspace_root
            else common_workspace_root([run_dir, sif_image, output_dir])
        )
        command = docker_apptainer_command(
            args.docker_apptainer_image,
            sif_image,
            run_dir,
            project_file,
            output_dir,
            docker_workspace_root,
        )
        execution_backend = "docker_apptainer_sif"
        container_runtime = "docker"
    elif sif_image:
        container_runtime = resolve_container_runtime(args.container_runtime) if sif_image else None
        if container_runtime:
            command = container_command(container_runtime, sif_image, run_dir, project_file, output_dir)
            execution_backend = "host_sif_runtime"
        else:
            command = [
                args.container_runtime or "apptainer|singularity|run-singularity",
                "exec",
                str(sif_image),
                "ogs",
                "-o",
                str(output_dir),
                str(project_file.name),
            ]
            execution_backend = "missing_sif_runtime"
    else:
        container_runtime = None
        command = [ogs_executable or "ogs", "-o", str(output_dir), str(project_file.name)]
        execution_backend = "host_ogs" if ogs_executable else "missing_host_ogs"
    try:
        recorded_command = with_timeout(command, args.timeout_s)
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    status: dict[str, Any] = {
        "run_dir": str(run_dir),
        "project_file": str(project_file),
        "output_dir": str(output_dir),
        "ogs_executable": ogs_executable,
        "sif_image": str(sif_image) if sif_image else None,
        "container_runtime": container_runtime,
        "docker_apptainer_image": args.docker_apptainer_image,
        "docker_workspace_root": str(docker_workspace_root) if docker_workspace_root else None,
        "execution_backend": execution_backend,
        "timeout_s": args.timeout_s,
        "command": recorded_command,
        "dry_run": args.dry_run,
        "started_at_unix": None,
        "finished_at_unix": None,
        "returncode": None,
        "timed_out": False,
        "stdout_tail": [],
        "stderr_tail": [],
        "notes": [],
    }

    if sif_image and not sif_image.is_file():
        status["notes"].append(f"SIF image not found: {sif_image}")
        status["notes"].append("The command is recorded but was not executed.")
        write_status(status_file, status)
        print(f"SIF image not found; wrote {status_file}")
        print("command:", " ".join(command))
        return

    if args.docker_apptainer_image and shutil.which("docker") is None:
        status["notes"].append("Docker was requested as the SIF runner, but docker was not found on PATH.")
        status["notes"].append("Install Docker or omit --docker-apptainer-image and provide a host SIF runtime.")
        status["notes"].append("The command is recorded but was not executed.")
        write_status(status_file, status)
        print(f"Docker not found; wrote {status_file}")
        print("command:", " ".join(recorded_command))
        return

    if sif_image and container_runtime is None:
        status["notes"].append(
            "SIF image was provided, but no Apptainer/Singularity/run-singularity runtime was found."
        )
        if shutil.which("docker"):
            status["notes"].append(
                "Docker is present; pass --docker-apptainer-image ghcr.io/apptainer/apptainer:latest to run the SIF via Dockerized Apptainer."
            )
        status["notes"].append("Install a SIF runtime or pass --container-runtime /path/to/runtime.")
        status["notes"].append("The command is recorded but was not executed.")
        write_status(status_file, status)
        print(f"SIF runtime not found; wrote {status_file}")
        print("command:", " ".join(command))
        return

    if not sif_image and ogs_executable is None:
        status["notes"].append("No OGS executable found. Install OGS or pass --ogs /path/to/ogs.")
        status["notes"].append(
            "Alternatively pass --sif /path/to/apptainer_ogs6.5.4.sif after installing Apptainer/Singularity."
        )
        status["notes"].append("The command is recorded but was not executed.")
        write_status(status_file, status)
        print(f"OGS executable not found; wrote {status_file}")
        print("command:", " ".join(command))
        return

    if args.dry_run:
        status["notes"].append("Dry run requested; OGS was not executed.")
        write_status(status_file, status)
        print(f"dry run; wrote {status_file}")
        print("command:", " ".join(recorded_command))
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    status["started_at_unix"] = time.time()
    result = subprocess.run(recorded_command, cwd=run_dir, text=True, capture_output=True)
    status["finished_at_unix"] = time.time()
    status["returncode"] = result.returncode
    status["timed_out"] = args.timeout_s is not None and result.returncode == 124
    status["stdout_tail"] = result.stdout.splitlines()[-200:]
    status["stderr_tail"] = result.stderr.splitlines()[-200:]
    write_status(status_file, status)
    print(f"wrote {status_file}")
    print(f"returncode: {result.returncode}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
