#!/usr/bin/env python3
"""Fit smooth interval-anchored permeability multiplier fields from pulse tests."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/smoke_test/bulk_w_projections.vtu"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/smooth_permeability_fit"),
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
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument(
        "--length-scales-m",
        nargs="*",
        help="Gaussian smoothing lengths in metres. Defaults to 0.05, 0.10, 0.20, 0.40, 0.80.",
    )
    parser.add_argument(
        "--shift-scales",
        nargs="*",
        help=(
            "Optional damping factors for target-derived log10 shifts. "
            "Defaults to 1.0, which reproduces the original full-shift diagnostic."
        ),
    )
    parser.add_argument("--cutoff-factor", type=float, default=3.0)
    parser.add_argument("--max-abs-log10-shift", type=float, default=8.0)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def first_cell_block(mesh: meshio.Mesh) -> tuple[str, np.ndarray]:
    if not mesh.cells:
        raise ValueError("mesh contains no cells")
    block = mesh.cells[0]
    return block.type, np.asarray(block.data)


def cell_centroids(mesh: meshio.Mesh) -> np.ndarray:
    _, cells = first_cell_block(mesh)
    return np.asarray(mesh.points[cells].mean(axis=1), dtype=float)[:, :2]


def read_cell_field(mesh: meshio.Mesh, field_name: str) -> np.ndarray:
    cell_type, _ = first_cell_block(mesh)
    try:
        field = np.asarray(mesh.cell_data_dict[field_name][cell_type], dtype=float)
    except KeyError as exc:
        available = sorted(mesh.cell_data_dict.keys())
        raise KeyError(f"field {field_name!r} not found; available: {available}") from exc
    if field.ndim == 1:
        field = field.reshape((-1, 1))
    if field.shape[1] not in {1, 4}:
        raise ValueError(f"field {field_name!r} must be scalar or 2D tensor; got shape {field.shape}")
    return field


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def directional_permeability(field: np.ndarray, cell_id: int, tangent_x: float, tangent_y: float) -> float:
    values = field[cell_id]
    if values.size == 1:
        return float(values[0])
    tangent = np.array([tangent_x, tangent_y], dtype=float)
    norm = float(np.linalg.norm(tangent))
    if norm == 0.0 or not np.isfinite(norm):
        return math.nan
    tangent = tangent / norm
    tensor = np.array([[values[0], values[1]], [values[2], values[3]]], dtype=float)
    return float(tangent @ tensor @ tangent)


def duplicate_weights(fit_rows: pd.DataFrame) -> pd.Series:
    keys = (
        fit_rows["campaign_year"].astype(str)
        + "|"
        + fit_rows["normalized_segment_label"].astype(str)
        + "|"
        + fit_rows["borehole_depth_m"].astype(float).round(6).astype(str)
        + "|"
        + fit_rows["observed_log10_permeability_m2"].astype(float).round(8).astype(str)
    )
    counts = keys.value_counts()
    return 1.0 / keys.map(counts).astype(float)


def eigenvalue_limited_scale(values: np.ndarray, requested_scale: float, min_k: float, max_k: float) -> float:
    if values.size == 1:
        base = float(values[0])
        if base <= 0.0 or not np.isfinite(base):
            return 1.0
        return float(np.clip(requested_scale, min_k / base, max_k / base))
    tensor = np.array([[values[0], values[1]], [values[2], values[3]]], dtype=float)
    eigvals = np.linalg.eigvalsh(tensor)
    min_eig = float(eigvals.min())
    max_eig = float(eigvals.max())
    if min_eig <= 0.0 or max_eig <= 0.0 or not np.isfinite(min_eig) or not np.isfinite(max_eig):
        return 1.0
    return float(np.clip(requested_scale, min_k / min_eig, max_k / max_eig))


def make_cell_data(mesh: meshio.Mesh, field_name: str, adjusted_field: np.ndarray, extras: dict[str, np.ndarray]) -> dict[str, list[Any]]:
    cell_data: dict[str, list[Any]] = {
        name: [np.array(block_values) for block_values in values]
        for name, values in mesh.cell_data.items()
    }
    cell_data[field_name] = [adjusted_field]
    for name, values in extras.items():
        cell_data[name] = [values]
    return cell_data


def build_anchor_table(field: np.ndarray, targets_path: Path, target_cells_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    targets = pd.read_csv(targets_path)
    target_cells = pd.read_csv(target_cells_path)
    merged = target_cells.merge(
        targets,
        on=["observation_id", "normalized_segment_label", "borehole_depth_m", "permeability_m2", "log10_permeability_m2"],
        suffixes=("_cell", ""),
    )
    usable = merged["usable_for_current_ogs_fit_cell"].map(bool_value)
    finite_obs = np.isfinite(merged["log10_permeability_m2"].astype(float))
    fit_rows = merged[usable & finite_obs].copy()
    predictions = []
    for _, row in fit_rows.iterrows():
        predictions.append(
            directional_permeability(
                field,
                int(row["lookup_cell_id"]),
                float(row["segment_tangent_x"]),
                float(row["segment_tangent_y"]),
            )
        )
    fit_rows["prior_predicted_permeability_m2"] = predictions
    fit_rows["prior_predicted_log10_permeability_m2"] = np.log10(fit_rows["prior_predicted_permeability_m2"])
    fit_rows = fit_rows[np.isfinite(fit_rows["prior_predicted_log10_permeability_m2"])].copy()
    fit_rows["observed_log10_permeability_m2"] = fit_rows["log10_permeability_m2"].astype(float)
    fit_rows["requested_log10_shift"] = (
        fit_rows["observed_log10_permeability_m2"] - fit_rows["prior_predicted_log10_permeability_m2"]
    )
    fit_rows["objective_weight"] = duplicate_weights(fit_rows)

    anchor_rows: list[dict[str, Any]] = []
    for cell_id, group in fit_rows.groupby("lookup_cell_id"):
        weights = group["objective_weight"].to_numpy(dtype=float)
        shifts = group["requested_log10_shift"].to_numpy(dtype=float)
        anchor_rows.append(
            {
                "lookup_cell_id": int(cell_id),
                "anchor_log10_shift": float(np.sum(weights * shifts) / np.sum(weights)),
                "anchor_weight": float(np.sum(weights)),
                "anchor_target_rows": int(group.shape[0]),
                "observed_log10_min": float(group["observed_log10_permeability_m2"].min()),
                "observed_log10_max": float(group["observed_log10_permeability_m2"].max()),
                "prior_predicted_log10_min": float(group["prior_predicted_log10_permeability_m2"].min()),
                "prior_predicted_log10_max": float(group["prior_predicted_log10_permeability_m2"].max()),
            }
        )
    return fit_rows, pd.DataFrame(anchor_rows).sort_values("lookup_cell_id")


def smooth_log_shift(
    centroids: np.ndarray,
    anchor_cells: np.ndarray,
    anchor_shifts: np.ndarray,
    anchor_weights: np.ndarray,
    length_scale: float,
    cutoff_factor: float,
    max_abs_shift: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if length_scale <= 0.0:
        raise ValueError("length_scale must be positive")
    anchor_xy = centroids[anchor_cells]
    output = np.zeros(centroids.shape[0], dtype=float)
    kernel_sum = np.zeros(centroids.shape[0], dtype=float)
    nearest_distance = np.full(centroids.shape[0], math.nan, dtype=float)
    cutoff = cutoff_factor * length_scale

    for cell_index, xy in enumerate(centroids):
        distances = np.linalg.norm(anchor_xy - xy, axis=1)
        nearest_distance[cell_index] = float(distances.min()) if distances.size else math.nan
        active = distances <= cutoff
        if not np.any(active):
            continue
        kernels = np.exp(-0.5 * (distances[active] / length_scale) ** 2) * anchor_weights[active]
        denom = float(kernels.sum())
        if denom <= 0.0 or not np.isfinite(denom):
            continue
        output[cell_index] = float(np.sum(kernels * anchor_shifts[active]) / denom)
        kernel_sum[cell_index] = denom
    return np.clip(output, -max_abs_shift, max_abs_shift), kernel_sum, nearest_distance


def write_mesh(
    mesh: meshio.Mesh,
    field_name: str,
    field: np.ndarray,
    requested_log_shift: np.ndarray,
    kernel_sum: np.ndarray,
    nearest_distance: np.ndarray,
    args: argparse.Namespace,
    output_mesh: Path,
) -> tuple[np.ndarray, np.ndarray]:
    requested_scale = np.power(10.0, requested_log_shift)
    applied_scale = np.ones(field.shape[0], dtype=float)
    for cell_id in range(field.shape[0]):
        applied_scale[cell_id] = eigenvalue_limited_scale(
            field[cell_id],
            float(requested_scale[cell_id]),
            args.min_k_eigenvalue,
            args.max_k_eigenvalue,
        )
    applied_log_shift = np.log10(applied_scale)
    adjusted_field = field * applied_scale[:, None]
    extras = {
        "k_smooth_requested_log10_multiplier_rd": requested_log_shift.reshape((-1, 1)),
        "k_smooth_applied_log10_multiplier_rd": applied_log_shift.reshape((-1, 1)),
        "k_smooth_kernel_weight_sum_rd": kernel_sum.reshape((-1, 1)),
        "k_smooth_nearest_anchor_distance_m_rd": nearest_distance.reshape((-1, 1)),
    }
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        output_mesh,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=make_cell_data(mesh, field_name, adjusted_field, extras),
        field_data=mesh.field_data,
    )
    return adjusted_field, applied_log_shift


def run_candidate(
    mesh: meshio.Mesh,
    field: np.ndarray,
    centroids: np.ndarray,
    anchors: pd.DataFrame,
    length_scale: float,
    shift_scale: float,
    args: argparse.Namespace,
) -> dict[str, Any]:
    label = f"length_{length_scale:.3f}m".replace(".", "p")
    if not math.isclose(shift_scale, 1.0):
        label = f"{label}_shift_{shift_scale:.3f}".replace(".", "p")
    candidate_dir = args.output_dir / label
    output_mesh = candidate_dir / "bulk_w_projections.vtu"
    requested_log_shift, kernel_sum, nearest_distance = smooth_log_shift(
        centroids,
        anchors["lookup_cell_id"].to_numpy(dtype=int),
        anchors["anchor_log10_shift"].to_numpy(dtype=float),
        anchors["anchor_weight"].to_numpy(dtype=float),
        length_scale,
        args.cutoff_factor,
        args.max_abs_log10_shift,
    )
    requested_log_shift = np.clip(
        requested_log_shift * shift_scale,
        -args.max_abs_log10_shift,
        args.max_abs_log10_shift,
    )
    _, applied_log_shift = write_mesh(
        mesh,
        args.field_name,
        field,
        requested_log_shift,
        kernel_sum,
        nearest_distance,
        args,
        output_mesh,
    )
    evaluation, summary = evaluate_targets(
        mesh_path=output_mesh,
        field_name=args.field_name,
        targets_path=args.targets,
        target_cells_path=args.target_cells,
        log10_sigma=args.log10_sigma,
        include_non_usable=True,
    )
    evaluation_path = candidate_dir / "permeability_fit_evaluation.csv"
    summary_path = candidate_dir / "permeability_fit_summary.json"
    evaluation.to_csv(evaluation_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    affected = kernel_sum > 0.0
    affected_applied = applied_log_shift[affected]
    return {
        "rank_by_objective": 0,
        "candidate_id": label,
        "length_scale_m": length_scale,
        "shift_scale": shift_scale,
        "cutoff_factor": args.cutoff_factor,
        "affected_cells": int(np.count_nonzero(affected)),
        "requested_log10_shift_min": float(requested_log_shift[affected].min()) if np.any(affected) else 0.0,
        "requested_log10_shift_max": float(requested_log_shift[affected].max()) if np.any(affected) else 0.0,
        "applied_log10_shift_min": float(applied_log_shift[affected].min()) if np.any(affected) else 0.0,
        "applied_log10_shift_max": float(applied_log_shift[affected].max()) if np.any(affected) else 0.0,
        "mean_abs_applied_log10_shift_affected": (
            float(np.mean(np.abs(affected_applied))) if affected_applied.size else 0.0
        ),
        "rms_applied_log10_shift_affected": (
            float(np.sqrt(np.mean(affected_applied**2))) if affected_applied.size else 0.0
        ),
        "sum_squared_applied_log10_shift_all_cells": float(np.sum(applied_log_shift**2)),
        "objective_value": summary["objective_value"],
        "objective_value_after_global_shift": summary["objective_value_after_global_shift"],
        "weighted_rmse_log10": summary["weighted_rmse_log10"],
        "weighted_rmse_log10_after_global_shift": summary["weighted_rmse_log10_after_global_shift"],
        "weighted_mean_abs_log10_residual": summary["weighted_mean_abs_log10_residual"],
        "max_abs_log10_residual": summary["max_abs_log10_residual"],
        "optimal_global_permeability_multiplier": summary["optimal_global_permeability_multiplier"],
        "used_in_objective_rows": summary["used_in_objective_rows"],
        "effective_objective_weight": summary["effective_objective_weight"],
        "mesh": str(output_mesh),
        "evaluation_csv": str(evaluation_path),
        "summary_json": str(summary_path),
    }


def write_summary_markdown(path: Path, results: pd.DataFrame, summary: dict[str, Any]) -> None:
    best = summary["best_candidate"]
    lines = [
        "# Smooth Permeability Candidate Search",
        "",
        "This search builds Gaussian-smoothed permeability multiplier fields from the",
        "usable pulse-test interval targets. It evaluates only the direct",
        "permeability target layer; it does not execute OGS or activate state",
        "observation residuals.",
        "",
        "## Best Candidate",
        "",
        f"- Candidate: `{best['candidate_id']}`",
        f"- Length scale: {best['length_scale_m']:.3f} m",
        f"- Shift scale: {best['shift_scale']:.2f}",
        f"- Affected cells: {int(best['affected_cells'])}",
        f"- Direct objective: {best['objective_value']:.2f}",
        f"- Weighted RMSE: {best['weighted_rmse_log10']:.2f} log10(k)",
        f"- Applied log10 multiplier range: {best['applied_log10_shift_min']:.2f} to {best['applied_log10_shift_max']:.2f}",
        "",
        "## Ranked Candidates",
        "",
        "| Rank | Candidate | Length [m] | Shift scale | Affected cells | Objective | RMSE log10(k) | RMS shift |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_objective"])),
                    f"`{row['candidate_id']}`",
                    f"{float(row['length_scale_m']):.3f}",
                    f"{float(row['shift_scale']):.2f}",
                    str(int(row["affected_cells"])),
                    f"{float(row['objective_value']):.2f}",
                    f"{float(row['weighted_rmse_log10']):.2f}",
                    f"{float(row['rms_applied_log10_shift_affected']):.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Shorter length scales approach the direct cell-fit diagnostic while still",
            "  spreading corrections beyond the 30 anchor cells.",
            "- Shift scales below 1.0 intentionally under-fit the direct targets and are",
            "  retained as regularized proposal fields for later OGS/state-observation",
            "  comparison.",
            "- The best direct candidate should still be tested against NMR, ERT,",
            "  Taupe/TDR and HM validation targets after OGS outputs are available.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    if args.output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {args.output_dir}")
        import shutil

        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)

    mesh = meshio.read(args.input_mesh)
    field = read_cell_field(mesh, args.field_name)
    centroids = cell_centroids(mesh)
    fit_rows, anchors = build_anchor_table(field, args.targets, args.target_cells)
    if anchors.empty:
        raise SystemExit("no anchor cells available for smooth fit")

    anchor_path = args.output_dir / "smooth_fit_anchor_cells.csv"
    target_path = args.output_dir / "smooth_fit_target_rows.csv"
    anchors.to_csv(anchor_path, index=False)
    fit_rows.to_csv(target_path, index=False)

    length_scales = parse_float_list(args.length_scales_m, [0.05, 0.10, 0.20, 0.40, 0.80])
    shift_scales = parse_float_list(args.shift_scales, [1.0])
    rows = [
        run_candidate(mesh, field, centroids, anchors, length_scale, shift_scale, args)
        for length_scale in length_scales
        for shift_scale in shift_scales
    ]
    results = pd.DataFrame(rows).sort_values(["objective_value", "length_scale_m"]).reset_index(drop=True)
    results["rank_by_objective"] = range(1, len(results) + 1)
    results_path = args.output_dir / "smooth_fit_results.csv"
    results.to_csv(results_path, index=False)

    best = results.iloc[0].to_dict()
    summary = {
        "input_mesh": str(args.input_mesh),
        "output_dir": str(args.output_dir),
        "targets": str(args.targets),
        "target_cells": str(args.target_cells),
        "anchor_cells": int(anchors.shape[0]),
        "fit_target_rows": int(fit_rows.shape[0]),
        "length_scales_m": length_scales,
        "shift_scales": shift_scales,
        "results_csv": str(results_path),
        "anchor_cells_csv": str(anchor_path),
        "target_rows_csv": str(target_path),
        "best_candidate": best,
        "notes": [
            "This is a smooth direct target-field diagnostic, not a full OGS inversion.",
            "The field preserves tensor orientation/anisotropy by applying scalar log10 multipliers.",
            "Gaussian smoothing spreads target-derived shifts over nearby cells with a finite cutoff.",
            "Shift scales below 1.0 deliberately damp the direct target-derived correction for regularization/proposal testing.",
            "The fitted field should be treated as a candidate parameterization for later OGS evaluation.",
        ],
    }
    summary_path = args.output_dir / "SMOOTH_FIT_SUMMARY.json"
    summary_md_path = args.output_dir / "SMOOTH_FIT_SUMMARY.md"
    summary["summary_markdown"] = str(summary_md_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_summary_markdown(summary_md_path, results, summary)
    print(f"wrote {results_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {summary_md_path}")
    print(f"best candidate: {best['candidate_id']}")
    print(f"best objective: {best['objective_value']:.6g}")
    print(f"best weighted rmse log10: {best['weighted_rmse_log10']:.6g}")


if __name__ == "__main__":
    main()
