#!/usr/bin/env python3
"""Create a first direct permeability-field fit from mapped pulse-test targets.

This script only modifies mesh-cell data.  It does not run OGS and does not change
the governing process XML.  The fitted field is a diagnostic starting point for a
future inversion: each mapped pulse-test target contributes a log10 multiplier to
the selected mesh cell, duplicate workbook rows are down-weighted, and the tensor
orientation/anisotropy already present in ``k_i_rd`` is preserved.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/smoke_test/bulk_w_projections.vtu"),
        help="VTU mesh containing the prior/proposal permeability tensor field.",
    )
    parser.add_argument(
        "--output-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_fit/bulk_w_projections.vtu"),
        help="Output VTU mesh with fitted permeability tensor field.",
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
        "--max-abs-log10-shift",
        type=float,
        default=8.0,
        help="Clip any requested per-cell multiplier to this absolute log10 value.",
    )
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_fit/permeability_direct_fit_targets.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_fit/permeability_direct_fit_summary.json"),
    )
    return parser.parse_args()


def first_cell_type(mesh: meshio.Mesh) -> str:
    if not mesh.cells:
        raise ValueError("mesh contains no cell blocks")
    return mesh.cells[0].type


def read_cell_field(mesh: meshio.Mesh, field_name: str) -> np.ndarray:
    cell_type = first_cell_type(mesh)
    try:
        field = mesh.cell_data_dict[field_name][cell_type]
    except KeyError as exc:
        available = sorted(mesh.cell_data_dict.keys())
        raise KeyError(f"field {field_name!r} not found; available: {available}") from exc
    field = np.asarray(field, dtype=float)
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
        lower = min_k / base
        upper = max_k / base
        return float(np.clip(requested_scale, lower, upper))

    tensor = np.array([[values[0], values[1]], [values[2], values[3]]], dtype=float)
    eigvals = np.linalg.eigvalsh(tensor)
    min_eig = float(eigvals.min())
    max_eig = float(eigvals.max())
    if min_eig <= 0.0 or max_eig <= 0.0 or not np.isfinite(min_eig) or not np.isfinite(max_eig):
        return 1.0
    lower = min_k / min_eig
    upper = max_k / max_eig
    return float(np.clip(requested_scale, lower, upper))


def make_cell_data(mesh: meshio.Mesh, field_name: str, adjusted_field: np.ndarray, extras: dict[str, np.ndarray]) -> dict[str, list[Any]]:
    cell_data: dict[str, list[Any]] = {
        name: [np.array(block_values) for block_values in values]
        for name, values in mesh.cell_data.items()
    }
    cell_data[field_name] = [adjusted_field]
    for name, values in extras.items():
        cell_data[name] = [values]
    return cell_data


def main() -> None:
    args = parse_args()
    mesh = meshio.read(args.input_mesh)
    field = read_cell_field(mesh, args.field_name)
    targets = pd.read_csv(args.targets)
    target_cells = pd.read_csv(args.target_cells)
    merged = target_cells.merge(
        targets,
        on=["observation_id", "normalized_segment_label", "borehole_depth_m", "permeability_m2", "log10_permeability_m2"],
        suffixes=("_cell", ""),
    )

    usable = merged["usable_for_current_ogs_fit_cell"].map(bool_value)
    finite_obs = np.isfinite(merged["log10_permeability_m2"].astype(float))
    fit_rows = merged[usable & finite_obs].copy()
    if fit_rows.empty:
        raise SystemExit("no usable finite permeability targets found")

    predictions = []
    for _, row in fit_rows.iterrows():
        cell_id = int(row["lookup_cell_id"])
        predicted = directional_permeability(
            field,
            cell_id,
            float(row["segment_tangent_x"]),
            float(row["segment_tangent_y"]),
        )
        predictions.append(predicted)
    fit_rows["prior_predicted_permeability_m2"] = predictions
    fit_rows["prior_predicted_log10_permeability_m2"] = np.log10(fit_rows["prior_predicted_permeability_m2"])
    finite_pred = np.isfinite(fit_rows["prior_predicted_log10_permeability_m2"])
    fit_rows = fit_rows[finite_pred].copy()

    fit_rows["observed_log10_permeability_m2"] = fit_rows["log10_permeability_m2"].astype(float)
    fit_rows["requested_log10_shift"] = (
        fit_rows["observed_log10_permeability_m2"] - fit_rows["prior_predicted_log10_permeability_m2"]
    )
    fit_rows["objective_weight"] = duplicate_weights(fit_rows)

    grouped_rows = []
    requested_log_shift = np.zeros(field.shape[0], dtype=float)
    anchor_weight = np.zeros(field.shape[0], dtype=float)
    anchor_count = np.zeros(field.shape[0], dtype=float)

    for cell_id, group in fit_rows.groupby("lookup_cell_id"):
        weights = group["objective_weight"].to_numpy(dtype=float)
        shifts = group["requested_log10_shift"].to_numpy(dtype=float)
        weighted_shift = float(np.sum(weights * shifts) / np.sum(weights))
        clipped_shift = float(np.clip(weighted_shift, -args.max_abs_log10_shift, args.max_abs_log10_shift))
        cell_id_int = int(cell_id)
        requested_log_shift[cell_id_int] = clipped_shift
        anchor_weight[cell_id_int] = float(np.sum(weights))
        anchor_count[cell_id_int] = float(group.shape[0])
        grouped_rows.append(
            {
                "lookup_cell_id": cell_id_int,
                "target_rows": int(group.shape[0]),
                "objective_weight": float(np.sum(weights)),
                "requested_log10_shift_mean": weighted_shift,
                "requested_log10_shift_clipped": clipped_shift,
                "observed_log10_min": float(group["observed_log10_permeability_m2"].min()),
                "observed_log10_max": float(group["observed_log10_permeability_m2"].max()),
                "prior_predicted_log10_min": float(group["prior_predicted_log10_permeability_m2"].min()),
                "prior_predicted_log10_max": float(group["prior_predicted_log10_permeability_m2"].max()),
            }
        )

    requested_scale = np.power(10.0, requested_log_shift)
    applied_scale = np.ones(field.shape[0], dtype=float)
    for cell_id in np.flatnonzero(anchor_count > 0.0):
        applied_scale[cell_id] = eigenvalue_limited_scale(
            field[cell_id],
            float(requested_scale[cell_id]),
            args.min_k_eigenvalue,
            args.max_k_eigenvalue,
        )

    adjusted_field = field.copy()
    adjusted_field *= applied_scale[:, None]
    applied_log_shift = np.log10(applied_scale)

    fit_rows["cell_requested_log10_shift"] = fit_rows["lookup_cell_id"].map(
        {row["lookup_cell_id"]: row["requested_log10_shift_clipped"] for row in grouped_rows}
    )
    fit_rows["cell_applied_log10_shift"] = fit_rows["lookup_cell_id"].map(
        {int(cell_id): float(applied_log_shift[int(cell_id)]) for cell_id in np.flatnonzero(anchor_count > 0.0)}
    )
    fit_rows["fitted_predicted_permeability_m2"] = [
        directional_permeability(
            adjusted_field,
            int(row["lookup_cell_id"]),
            float(row["segment_tangent_x"]),
            float(row["segment_tangent_y"]),
        )
        for _, row in fit_rows.iterrows()
    ]
    fit_rows["fitted_predicted_log10_permeability_m2"] = np.log10(fit_rows["fitted_predicted_permeability_m2"])
    fit_rows["fitted_log10_residual_pred_minus_obs"] = (
        fit_rows["fitted_predicted_log10_permeability_m2"] - fit_rows["observed_log10_permeability_m2"]
    )

    extras = {
        "k_fit_requested_log10_multiplier_rd": requested_log_shift.reshape((-1, 1)),
        "k_fit_applied_log10_multiplier_rd": applied_log_shift.reshape((-1, 1)),
        "k_fit_anchor_weight_rd": anchor_weight.reshape((-1, 1)),
        "k_fit_anchor_count_rd": anchor_count.reshape((-1, 1)),
    }
    args.output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        args.output_mesh,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=make_cell_data(mesh, args.field_name, adjusted_field, extras),
        field_data=mesh.field_data,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    fit_rows.to_csv(args.report, index=False)
    grouped = pd.DataFrame(grouped_rows).sort_values("lookup_cell_id")
    grouped_path = args.summary.with_name("permeability_direct_fit_cells.csv")
    grouped.to_csv(grouped_path, index=False)

    weights = fit_rows["objective_weight"].to_numpy(dtype=float)
    residuals = fit_rows["fitted_log10_residual_pred_minus_obs"].to_numpy(dtype=float)
    prior_residuals = (
        fit_rows["prior_predicted_log10_permeability_m2"] - fit_rows["observed_log10_permeability_m2"]
    ).to_numpy(dtype=float)
    summary = {
        "input_mesh": str(args.input_mesh),
        "output_mesh": str(args.output_mesh),
        "targets": str(args.targets),
        "target_cells": str(args.target_cells),
        "field_name": args.field_name,
        "fit_rows": int(fit_rows.shape[0]),
        "adjusted_cells": int(np.count_nonzero(anchor_count > 0.0)),
        "effective_objective_weight": float(weights.sum()),
        "prior_weighted_rmse_log10": float(np.sqrt(np.sum(weights * prior_residuals**2) / np.sum(weights))),
        "fitted_weighted_rmse_log10": float(np.sqrt(np.sum(weights * residuals**2) / np.sum(weights))),
        "prior_weighted_mean_abs_log10_residual": float(np.sum(weights * np.abs(prior_residuals)) / np.sum(weights)),
        "fitted_weighted_mean_abs_log10_residual": float(np.sum(weights * np.abs(residuals)) / np.sum(weights)),
        "requested_log10_shift_range": [
            float(requested_log_shift[anchor_count > 0.0].min()),
            float(requested_log_shift[anchor_count > 0.0].max()),
        ],
        "applied_log10_shift_range": [
            float(applied_log_shift[anchor_count > 0.0].min()),
            float(applied_log_shift[anchor_count > 0.0].max()),
        ],
        "min_k_eigenvalue": args.min_k_eigenvalue,
        "max_k_eigenvalue": args.max_k_eigenvalue,
        "report": str(args.report),
        "cell_report": str(grouped_path),
        "notes": [
            "This is a direct target-field diagnostic, not a full OGS inversion.",
            "Only cells selected by mapped usable pulse-test rows are modified.",
            "Duplicate workbook rows are down-weighted before per-cell shifts are averaged.",
            "The existing tensor shape/orientation is preserved by scalar multiplication.",
        ],
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {args.output_mesh}")
    print(f"wrote {args.report}")
    print(f"wrote {grouped_path}")
    print(f"wrote {args.summary}")
    print(f"adjusted cells: {summary['adjusted_cells']}")
    print(f"weighted RMSE log10 prior -> fitted: {summary['prior_weighted_rmse_log10']:.6g} -> {summary['fitted_weighted_rmse_log10']:.6g}")


if __name__ == "__main__":
    main()
