#!/usr/bin/env python3
"""Generate and rank heterogeneous anisotropic permeability priors by pulse-test fit."""

from __future__ import annotations

import argparse
import itertools
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_SEEDS = [20260528, 20260529]
DEFAULT_THETA_DEG = [16.236187, 109.430186, 144.0]
DEFAULT_ANISOTROPY = [1.0, 2.5]
DEFAULT_MEAN_K = [6.32e-20, 1.0e-18]
DEFAULT_LOG_SIGMA = [1.0]


def parse_float_list(values: list[str] | None, default: list[float]) -> list[float]:
    if values is None:
        return default
    output: list[float] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                output.append(float(item))
    if not output:
        raise ValueError("empty float list")
    return output


def parse_int_list(values: list[str] | None, default: list[int]) -> list[int]:
    if values is None:
        return default
    output: list[int] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                output.append(int(item))
    if not output:
        raise ValueError("empty integer list")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05/bulk.vtu"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_prior_sweep"),
    )
    parser.add_argument("--seeds", nargs="*", help="Comma-separated or space-separated integer seeds.")
    parser.add_argument("--theta-deg", nargs="*", help="Candidate tensor angles in model coordinates.")
    parser.add_argument("--anisotropy-ratio", nargs="*", help="Candidate k_parallel/k_perp ratios.")
    parser.add_argument("--mean-k-ref", nargs="*", help="Candidate geometric-mean permeability values.")
    parser.add_argument("--log-sigma", nargs="*", help="Candidate lognormal standard deviations.")
    parser.add_argument("--corr-length", type=float, default=0.6)
    parser.add_argument("--n-features", type=int, default=96)
    parser.add_argument("--min-k", type=float, default=1.0e-22)
    parser.add_argument("--max-k", type=float, default=1.0e-13)
    parser.add_argument("--porosity", type=float, default=0.105)
    parser.add_argument("--max-candidates", type=int, help="Optional cap after deterministic grid ordering.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output directory.")
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    finished = time.time()
    record = {
        "command": command,
        "returncode": result.returncode,
        "duration_s": finished - started,
        "stdout_tail": result.stdout.splitlines()[-40:],
        "stderr_tail": result.stderr.splitlines()[-40:],
    }
    if result.returncode != 0:
        raise RuntimeError(json.dumps(record, indent=2))
    return record


def candidate_grid(args: argparse.Namespace) -> list[dict[str, Any]]:
    seeds = parse_int_list(args.seeds, DEFAULT_SEEDS)
    theta_deg = parse_float_list(args.theta_deg, DEFAULT_THETA_DEG)
    anisotropy = parse_float_list(args.anisotropy_ratio, DEFAULT_ANISOTROPY)
    mean_k = parse_float_list(args.mean_k_ref, DEFAULT_MEAN_K)
    log_sigma = parse_float_list(args.log_sigma, DEFAULT_LOG_SIGMA)
    grid = [
        {
            "seed": seed,
            "theta_deg": theta,
            "anisotropy_ratio": ratio,
            "mean_k_ref": mean,
            "log_sigma": sigma,
        }
        for seed, theta, ratio, mean, sigma in itertools.product(seeds, theta_deg, anisotropy, mean_k, log_sigma)
    ]
    if args.max_candidates is not None:
        grid = grid[: args.max_candidates]
    return grid


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    output_dir = args.output_dir.resolve()
    input_mesh = args.input_mesh.resolve()
    scripts = repo / "inversion_workflow" / "scripts"

    if not input_mesh.is_file():
        raise SystemExit(f"input mesh not found: {input_mesh}")
    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    grid = candidate_grid(args)
    rows: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []

    for index, parameters in enumerate(grid):
        candidate_id = f"candidate_{index:04d}"
        candidate_dir = output_dir / candidate_id
        candidate_dir.mkdir()
        mesh_path = candidate_dir / "bulk_w_projections.vtu"
        evaluation_path = candidate_dir / "permeability_fit_evaluation.csv"
        summary_path = candidate_dir / "permeability_fit_summary.json"

        generate_cmd = [
            sys.executable,
            str(scripts / "generate_anisotropic_permeability_field.py"),
            "--input",
            str(input_mesh),
            "--output",
            str(mesh_path),
            "--seed",
            str(parameters["seed"]),
            "--theta-deg",
            str(parameters["theta_deg"]),
            "--anisotropy-ratio",
            str(parameters["anisotropy_ratio"]),
            "--mean-k-ref",
            str(parameters["mean_k_ref"]),
            "--log-sigma",
            str(parameters["log_sigma"]),
            "--corr-length",
            str(args.corr_length),
            "--n-features",
            str(args.n_features),
            "--min-k",
            str(args.min_k),
            "--max-k",
            str(args.max_k),
            "--porosity",
            str(args.porosity),
        ]
        commands.append({"candidate_id": candidate_id, "step": "generate", **run_command(generate_cmd, repo)})

        evaluate_cmd = [
            sys.executable,
            str(scripts / "evaluate_permeability_targets.py"),
            "--mesh",
            str(mesh_path),
            "--include-non-usable",
            "--output",
            str(evaluation_path),
            "--summary-output",
            str(summary_path),
        ]
        commands.append({"candidate_id": candidate_id, "step": "evaluate", **run_command(evaluate_cmd, repo)})

        summary = read_json(summary_path)
        rows.append(
            {
                "rank_by_objective": 0,
                "candidate_id": candidate_id,
                **parameters,
                "corr_length": args.corr_length,
                "n_features": args.n_features,
                "objective_value": summary["objective_value"],
                "objective_value_after_global_shift": summary["objective_value_after_global_shift"],
                "weighted_rmse_log10": summary["weighted_rmse_log10"],
                "weighted_rmse_log10_after_global_shift": summary["weighted_rmse_log10_after_global_shift"],
                "weighted_mean_abs_log10_residual": summary["weighted_mean_abs_log10_residual"],
                "max_abs_log10_residual": summary["max_abs_log10_residual"],
                "optimal_global_log10_shift_to_prediction": summary["optimal_global_log10_shift_to_prediction"],
                "optimal_global_permeability_multiplier": summary["optimal_global_permeability_multiplier"],
                "used_in_objective_rows": summary["used_in_objective_rows"],
                "effective_objective_weight": summary["effective_objective_weight"],
                "mesh": str(mesh_path),
                "evaluation_csv": str(evaluation_path),
                "summary_json": str(summary_path),
            }
        )

    results = pd.DataFrame(rows).sort_values(["objective_value", "objective_value_after_global_shift"]).reset_index(drop=True)
    results["rank_by_objective"] = range(1, len(results) + 1)
    results_path = output_dir / "sweep_results.csv"
    results.to_csv(results_path, index=False)

    command_log_path = output_dir / "command_log.json"
    command_log_path.write_text(json.dumps(commands, indent=2, sort_keys=True), encoding="utf-8")

    best = results.iloc[0].to_dict() if not results.empty else {}
    sweep_summary = {
        "input_mesh": str(input_mesh),
        "output_dir": str(output_dir),
        "candidate_count": int(len(results)),
        "results_csv": str(results_path),
        "command_log": str(command_log_path),
        "best_candidate": best,
        "default_parameter_note": (
            "Default theta candidates include the two usable pulse-test segment "
            "orientations (about 16.24 and 109.43 deg) plus the bedding-angle prior "
            "(144 deg)."
        ),
        "notes": [
            "This sweep evaluates direct pulse-test permeability only; it does not execute OGS.",
            "objective_value_after_global_shift is diagnostic and reports remaining spatial mismatch after an optimal uniform scaling.",
            "The ranked fields are proposal/prior candidates; the direct cell-fit diagnostic remains a separate local fit.",
        ],
    }
    summary_path = output_dir / "SWEEP_SUMMARY.json"
    summary_path.write_text(json.dumps(sweep_summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {results_path}")
    print(f"wrote {summary_path}")
    if best:
        print(f"best candidate: {best['candidate_id']}")
        print(f"best objective: {best['objective_value']:.6g}")
        print(f"best weighted rmse log10: {best['weighted_rmse_log10']:.6g}")


if __name__ == "__main__":
    main()
