#!/usr/bin/env python3
"""Prepare an OGS run directory with a generated anisotropic permeability field."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


MODEL_FILE_SUFFIXES = {".xml", ".prj", ".vtu", ".txt"}
KEEP_EXTRA_FILES = {"README.txt"}
REQUIRED_RUN_FILES = [
    "cd_a_open_niche_quad.prj",
    "01_processes_TRM.xml",
    "02_process_variables_TRM.xml",
    "03_parameters_TRM.xml",
    "04_media_TRM.xml",
    "04_1_media_aqu_liq.xml",
    "04_2_media_twophase.xml",
    "05_time_loop_TRM.xml",
    "05_1_fixed_timestepping.xml",
    "06_nonlinear_solver_T.xml",
    "07_linear_solver_T.xml",
    "08_curves.xml",
    "bulk.vtu",
    "bulk_all.vtu",
    "bulk_w_projections.vtu",
    "cd-a_niche4.vtu",
    "cd-a_left.vtu",
    "cd-a_right.vtu",
    "cd-a_top.vtu",
    "cd-a_bottom.vtu",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("inversion_workflow/run_config.example.json"),
        help="Run-preparation JSON config.",
    )
    parser.add_argument("--run-id", help="Override run_id from config.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing run directory.")
    parser.add_argument(
        "--mesh-override",
        type=Path,
        help=(
            "Use an existing bulk_w_projections.vtu instead of generating a new "
            "permeability field. This is useful for fitted diagnostic fields."
        ),
    )
    parser.add_argument(
        "--output-variables",
        nargs="*",
        help=(
            "Optional active output variable list to write into 05_time_loop_TRM.xml "
            "in the run copy. This changes only output configuration, not equations."
        ),
    )
    return parser.parse_args()


def read_config(path: Path, run_id_override: str | None) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if run_id_override:
        config["run_id"] = run_id_override
    return config


def copy_model_files(source_dir: Path, run_dir: Path) -> list[str]:
    copied: list[str] = []
    for source in sorted(source_dir.iterdir()):
        if not source.is_file():
            continue
        if source.suffix.lower() not in MODEL_FILE_SUFFIXES and source.name not in KEEP_EXTRA_FILES:
            continue
        target = run_dir / source.name
        shutil.copy2(source, target)
        copied.append(source.name)
    return copied


def generate_field(config: dict[str, Any], run_dir: Path, script_path: Path) -> dict[str, Any]:
    field = config["permeability_field"]
    output_mesh = run_dir / "bulk_w_projections.vtu"
    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(run_dir / "bulk.vtu"),
        "--output",
        str(output_mesh),
        "--field-name",
        str(field.get("field_name", "k_i_rd")),
        "--seed",
        str(field["seed"]),
        "--theta-deg",
        str(field["theta_deg"]),
        "--anisotropy-ratio",
        str(field["anisotropy_ratio"]),
        "--mean-k-ref",
        str(field["mean_k_ref"]),
        "--log-sigma",
        str(field["log_sigma"]),
        "--corr-length",
        str(field["corr_length"]),
        "--n-features",
        str(field["n_features"]),
        "--min-k",
        str(field["min_k"]),
        "--max-k",
        str(field["max_k"]),
    ]
    if "porosity" in field:
        cmd.extend(["--porosity", str(field["porosity"])])
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return {
        "command": cmd,
        "stdout": result.stdout.strip().splitlines(),
        "output_mesh": str(output_mesh),
    }


def use_mesh_override(mesh_override: Path, run_dir: Path) -> dict[str, Any]:
    if not mesh_override.is_file():
        raise FileNotFoundError(f"mesh override not found: {mesh_override}")
    output_mesh = run_dir / "bulk_w_projections.vtu"
    shutil.copy2(mesh_override, output_mesh)
    return {
        "command": [],
        "stdout": [f"copied mesh override {mesh_override} to {output_mesh}"],
        "output_mesh": str(output_mesh),
        "mesh_override": str(mesh_override.resolve()),
    }


def patch_output_variables(time_loop_file: Path, variables: list[str] | None) -> dict[str, Any]:
    if variables is None:
        return {"updated": False, "variables": None}
    if not variables:
        raise ValueError("--output-variables was provided but no variable names were given")

    text = time_loop_file.read_text(encoding="utf-8")
    rendered = "\n".join(f"        <variable>{variable}</variable>" for variable in variables)
    replacement = f"<variables>\n{rendered}\n    </variables>"
    updated, count = re.subn(
        r"<variables>.*?</variables>",
        replacement,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError(f"could not find exactly one <variables> block in {time_loop_file}")
    time_loop_file.write_text(updated, encoding="utf-8")
    return {"updated": True, "variables": variables, "file": str(time_loop_file)}


def write_manifest(
    config: dict[str, Any],
    run_dir: Path,
    copied_files: list[str],
    generation: dict[str, Any],
    output_configuration: dict[str, Any],
) -> Path:
    missing = [name for name in REQUIRED_RUN_FILES if not (run_dir / name).exists()]
    manifest = {
        "run_id": config["run_id"],
        "run_dir": str(run_dir),
        "project_file": config.get("project_file", "cd_a_open_niche_quad.prj"),
        "source_projection_model_dir": str(Path(config["projection_model_dir"]).resolve()),
        "copied_files": copied_files,
        "missing_required_files": missing,
        "permeability_field": config["permeability_field"],
        "field_generation": generation,
        "output_configuration": output_configuration,
        "notes": [
            "The governing OGS process/XML semantics are not changed here.",
            "bulk_w_projections.vtu is regenerated with k_i_rd and n_rd mesh-cell data.",
            "Optional output-variable edits affect only what the run writes for observation comparison.",
            "Before a production OGS run, verify or regenerate submeshes with identifySubdomains as noted in the recovered projection README.",
        ],
    }
    path = run_dir / "RUN_MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if missing:
        raise RuntimeError(f"run directory missing required files: {missing}")
    return path


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = read_config(config_path, args.run_id)
    source_dir = Path(config["projection_model_dir"]).resolve()
    run_root = Path(config["run_root"]).resolve()
    run_dir = run_root / config["run_id"]

    if not source_dir.is_dir():
        raise SystemExit(f"projection model directory not found: {source_dir}")
    if run_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"run directory exists, pass --overwrite to replace: {run_dir}")
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    copied = copy_model_files(source_dir, run_dir)
    if args.mesh_override:
        generation = use_mesh_override(args.mesh_override.resolve(), run_dir)
    else:
        script_path = Path(__file__).with_name("generate_anisotropic_permeability_field.py").resolve()
        generation = generate_field(config, run_dir, script_path)
    output_configuration = patch_output_variables(run_dir / "05_time_loop_TRM.xml", args.output_variables)
    manifest_path = write_manifest(config, run_dir, copied, generation, output_configuration)

    print(f"prepared run directory: {run_dir}")
    print(f"project file: {run_dir / config.get('project_file', 'cd_a_open_niche_quad.prj')}")
    print(f"manifest: {manifest_path}")
    for line in generation["stdout"]:
        print(line)


if __name__ == "__main__":
    main()
