#!/usr/bin/env python3
"""Build a direct pulse-test sensitivity plan for permeability anisotropy."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_permeability_targets import evaluate_targets  # noqa: E402
from fit_smooth_permeability_field_from_targets import make_cell_data, read_cell_field  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_loop_001_001_length_0p003m_shift_1p006/bulk_w_projections.vtu"),
        help="Incumbent or baseline mesh containing a tensor cell-data field.",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_targets.csv"),
    )
    parser.add_argument(
        "--target-cells",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_cells.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/anisotropy_sensitivity_plan"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--theta-deg", type=float, nargs="*", default=[120, 130, 140, 144, 150, 160, 170])
    parser.add_argument("--anisotropy-ratio", type=float, nargs="*", default=[1.0, 1.5, 2.5, 4.0, 6.0])
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--execution-batch-size", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is None or value is pd.NA:
        return None
    return value


def candidate_label(theta_deg: float, ratio: float) -> str:
    return f"anis_theta_{theta_deg:.1f}_ratio_{ratio:.2f}".replace(".", "p").replace("-", "m")


def tensor_stats(field: np.ndarray) -> dict[str, Any]:
    mats = field.reshape((-1, 2, 2))
    mats = 0.5 * (mats + np.swapaxes(mats, 1, 2))
    eigvals, eigvecs = np.linalg.eigh(mats)
    ratios = eigvals[:, 1] / eigvals[:, 0]
    angles = np.degrees(np.arctan2(eigvecs[:, 1, 1], eigvecs[:, 0, 1]))
    angles = (angles + 180.0) % 180.0
    return {
        "cells": int(field.shape[0]),
        "min_eigenvalue": float(np.nanmin(eigvals)),
        "max_eigenvalue": float(np.nanmax(eigvals)),
        "anisotropy_ratio_min": float(np.nanmin(ratios)),
        "anisotropy_ratio_median": float(np.nanmedian(ratios)),
        "anisotropy_ratio_max": float(np.nanmax(ratios)),
        "orientation_deg_p05": float(np.nanpercentile(angles, 5)),
        "orientation_deg_p50": float(np.nanpercentile(angles, 50)),
        "orientation_deg_p95": float(np.nanpercentile(angles, 95)),
    }


def anisotropy_adjusted_field(
    field: np.ndarray,
    theta_deg: float,
    ratio: float,
    min_eigenvalue: float,
    max_eigenvalue: float,
) -> np.ndarray:
    if field.ndim != 2 or field.shape[1] != 4:
        raise ValueError(f"anisotropy adjustment requires a 2D tensor field; got {field.shape}")
    if ratio <= 0.0 or not np.isfinite(ratio):
        raise ValueError("anisotropy ratio must be positive")

    mats = field.reshape((-1, 2, 2))
    mats = 0.5 * (mats + np.swapaxes(mats, 1, 2))
    eigvals = np.linalg.eigvalsh(mats)
    eigvals = np.clip(eigvals, min_eigenvalue, max_eigenvalue)
    geometric_mean = np.sqrt(eigvals[:, 0] * eigvals[:, 1])

    ratio_sqrt = math.sqrt(ratio)
    k_minor = np.clip(geometric_mean / ratio_sqrt, min_eigenvalue, max_eigenvalue)
    k_major = np.clip(geometric_mean * ratio_sqrt, min_eigenvalue, max_eigenvalue)

    theta = math.radians(theta_deg)
    e_major = np.array([math.cos(theta), math.sin(theta)], dtype=float)
    e_minor = np.array([-math.sin(theta), math.cos(theta)], dtype=float)
    major_outer = np.outer(e_major, e_major)
    minor_outer = np.outer(e_minor, e_minor)

    adjusted = k_major[:, None, None] * major_outer[None, :, :] + k_minor[:, None, None] * minor_outer[None, :, :]
    return adjusted.reshape((-1, 4))


def write_candidate_mesh(
    mesh: meshio.Mesh,
    field_name: str,
    field: np.ndarray,
    theta_deg: float,
    ratio: float,
    output_mesh: Path,
) -> None:
    extras = {
        "k_anisotropy_theta_deg_rd": np.full((field.shape[0], 1), float(theta_deg)),
        "k_anisotropy_ratio_rd": np.full((field.shape[0], 1), float(ratio)),
    }
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        output_mesh,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=make_cell_data(mesh, field_name, field, extras),
        field_data=mesh.field_data,
    )


def write_markdown(path: Path, results: pd.DataFrame, summary: dict[str, Any]) -> None:
    best = summary["best_candidate"]
    lines = [
        "# Anisotropy Sensitivity Plan",
        "",
        "This plan tests whether the direct pulse-test objective prefers a different",
        "global tensor orientation or anisotropy ratio than the current incumbent",
        "field.  It does not change the GESA source model: each candidate is a",
        "run-local mesh override for `k_i_rd`.",
        "",
        "Each candidate preserves the cell-wise geometric-mean permeability of the",
        "input mesh and changes only the principal-direction angle and anisotropy",
        "ratio.  The score below is the direct pulse-test objective only; OGS state",
        "rows must be evaluated with `run_inversion_candidate_search.py` before any",
        "combined-objective decision.",
        "",
        "## Input Field",
        "",
        f"- Input mesh: `{summary['input_mesh']}`",
        f"- Baseline direct objective: {summary['baseline_direct_objective']:.6f}",
        f"- Baseline weighted RMSE log10: {summary['baseline_weighted_rmse_log10']:.6f}",
        f"- Baseline median anisotropy ratio: {summary['baseline_tensor_stats']['anisotropy_ratio_median']:.3f}",
        f"- Baseline median orientation: {summary['baseline_tensor_stats']['orientation_deg_p50']:.3f} deg",
        "",
        "## Best Direct Candidate",
        "",
        f"- Candidate: `{best['candidate_id']}`",
        f"- Orientation: {float(best['theta_deg']):.3f} deg",
        f"- Anisotropy ratio: {float(best['anisotropy_ratio']):.3f}",
        f"- Direct objective: {float(best['objective_value']):.6f}",
        f"- Direct objective delta vs baseline: {float(best['direct_objective_delta_vs_baseline']):+.6f}",
        f"- Weighted RMSE log10: {float(best['weighted_rmse_log10']):.6f}",
        "",
        "## Top Candidates",
        "",
        "| Rank | Candidate | Theta [deg] | Ratio | Direct objective | Delta | RMSE log10 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_direct_objective"])),
                    f"`{row['candidate_id']}`",
                    f"{float(row['theta_deg']):.1f}",
                    f"{float(row['anisotropy_ratio']):.2f}",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_baseline']):+.3f}",
                    f"{float(row['weighted_rmse_log10']):.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execution Handoff",
            "",
            f"The proposed OGS execution batch is `{summary['next_candidate_batch_csv']}`.",
            "Run it through the existing candidate-search harness when a combined",
            "state-plus-permeability check is wanted.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = (repo / args.output_dir if not args.output_dir.is_absolute() else args.output_dir).resolve()
    input_mesh = (repo / args.input_mesh if not args.input_mesh.is_absolute() else args.input_mesh).resolve()
    targets = (repo / args.targets if not args.targets.is_absolute() else args.targets).resolve()
    target_cells = (repo / args.target_cells if not args.target_cells.is_absolute() else args.target_cells).resolve()

    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {output_dir}")
        import shutil

        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    mesh = meshio.read(input_mesh)
    baseline_field = read_cell_field(mesh, args.field_name)
    if baseline_field.shape[1] != 4:
        raise SystemExit(f"field {args.field_name!r} must be a 2D tensor field; got {baseline_field.shape}")

    _, baseline_summary = evaluate_targets(
        mesh_path=input_mesh,
        field_name=args.field_name,
        targets_path=targets,
        target_cells_path=target_cells,
        log10_sigma=args.log10_sigma,
        include_non_usable=True,
    )
    baseline_objective = float(baseline_summary["objective_value"])

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for theta_deg in args.theta_deg:
        for ratio in args.anisotropy_ratio:
            label = candidate_label(float(theta_deg), float(ratio))
            if label in seen:
                continue
            seen.add(label)
            candidate_dir = output_dir / label
            candidate_mesh = candidate_dir / "bulk_w_projections.vtu"
            adjusted = anisotropy_adjusted_field(
                baseline_field,
                float(theta_deg),
                float(ratio),
                args.min_k_eigenvalue,
                args.max_k_eigenvalue,
            )
            write_candidate_mesh(mesh, args.field_name, adjusted, float(theta_deg), float(ratio), candidate_mesh)
            evaluation, summary = evaluate_targets(
                mesh_path=candidate_mesh,
                field_name=args.field_name,
                targets_path=targets,
                target_cells_path=target_cells,
                log10_sigma=args.log10_sigma,
                include_non_usable=True,
            )
            evaluation_path = candidate_dir / "permeability_fit_evaluation.csv"
            summary_path = candidate_dir / "permeability_fit_summary.json"
            evaluation.to_csv(evaluation_path, index=False)
            summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
            rows.append(
                {
                    "rank_by_direct_objective": 0,
                    "candidate_id": label,
                    "theta_deg": float(theta_deg),
                    "anisotropy_ratio": float(ratio),
                    "mesh": str(candidate_mesh),
                    "evaluation_csv": str(evaluation_path),
                    "summary_json": str(summary_path),
                    "objective_value": float(summary["objective_value"]),
                    "objective_value_after_global_shift": float(summary["objective_value_after_global_shift"]),
                    "weighted_rmse_log10": float(summary["weighted_rmse_log10"]),
                    "weighted_rmse_log10_after_global_shift": float(summary["weighted_rmse_log10_after_global_shift"]),
                    "weighted_mean_abs_log10_residual": float(summary["weighted_mean_abs_log10_residual"]),
                    "max_abs_log10_residual": float(summary["max_abs_log10_residual"]),
                    "optimal_global_permeability_multiplier": float(summary["optimal_global_permeability_multiplier"]),
                    "used_in_objective_rows": int(summary["used_in_objective_rows"]),
                    "effective_objective_weight": float(summary["effective_objective_weight"]),
                    "direct_objective_delta_vs_baseline": float(summary["objective_value"]) - baseline_objective,
                }
            )

    results = pd.DataFrame(rows).sort_values(["objective_value", "theta_deg", "anisotropy_ratio"]).reset_index(drop=True)
    results["rank_by_direct_objective"] = range(1, results.shape[0] + 1)
    batch = results.head(args.execution_batch_size).copy()

    results_path = output_dir / "anisotropy_sensitivity_results.csv"
    batch_path = output_dir / "next_anisotropy_candidate_batch.csv"
    summary_json_path = output_dir / "ANISOTROPY_SENSITIVITY_PLAN.json"
    summary_md_path = output_dir / "ANISOTROPY_SENSITIVITY_PLAN.md"
    results.to_csv(results_path, index=False)
    batch.to_csv(batch_path, index=False)

    summary = {
        "input_mesh": str(input_mesh),
        "output_dir": str(output_dir),
        "field_name": args.field_name,
        "targets": str(targets),
        "target_cells": str(target_cells),
        "theta_deg_values": [float(value) for value in args.theta_deg],
        "anisotropy_ratio_values": [float(value) for value in args.anisotropy_ratio],
        "candidate_count": int(results.shape[0]),
        "execution_batch_size": int(args.execution_batch_size),
        "results_csv": str(results_path),
        "next_candidate_batch_csv": str(batch_path),
        "summary_markdown": str(summary_md_path),
        "baseline_direct_objective": baseline_objective,
        "baseline_weighted_rmse_log10": float(baseline_summary["weighted_rmse_log10"]),
        "baseline_tensor_stats": tensor_stats(baseline_field),
        "best_candidate": json_ready(results.iloc[0].to_dict()),
        "top_candidates": [json_ready(row) for row in results.head(12).to_dict(orient="records")],
        "notes": [
            "Direct pulse-test anisotropy sensitivity only; OGS state outputs are not evaluated here.",
            "Cell-wise geometric-mean permeability is preserved from the input mesh.",
            "Use next_anisotropy_candidate_batch.csv with run_inversion_candidate_search.py for combined OGS-backed scoring.",
        ],
    }
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, results, summary)

    print(f"wrote {results_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"best candidate: {results.iloc[0]['candidate_id']}")
    print(f"best direct objective: {float(results.iloc[0]['objective_value']):.6g}")


if __name__ == "__main__":
    main()
