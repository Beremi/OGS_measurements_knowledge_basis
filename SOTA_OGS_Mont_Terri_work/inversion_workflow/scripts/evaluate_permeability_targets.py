#!/usr/bin/env python3
"""Evaluate permeability pulse-test targets against a generated OGS mesh field."""

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
        "--mesh",
        type=Path,
        default=Path("inversion_workflow/runs/smoke_test/bulk_w_projections.vtu"),
        help="VTU mesh containing a cell-data permeability field.",
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
        "--log10-sigma",
        type=float,
        default=0.5,
        help="Default log10 standard deviation for pulse-test residuals.",
    )
    parser.add_argument(
        "--include-non-usable",
        action="store_true",
        help="Also report residuals for targets flagged unusable for the current OGS fit if cell rows exist.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="CSV output path. Defaults to <mesh-dir>/permeability_fit_evaluation.csv.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="JSON output path. Defaults to <mesh-dir>/permeability_fit_summary.json.",
    )
    return parser.parse_args()


def first_cell_type(mesh: meshio.Mesh) -> str:
    if not mesh.cells:
        raise ValueError("mesh contains no cell blocks")
    return mesh.cells[0].type


def read_cell_field(mesh_path: Path, field_name: str) -> np.ndarray:
    mesh = meshio.read(mesh_path)
    cell_type = first_cell_type(mesh)
    try:
        field = mesh.cell_data_dict[field_name][cell_type]
    except KeyError as exc:
        available = sorted(mesh.cell_data_dict.keys())
        raise KeyError(f"field {field_name!r} not found in {mesh_path}; available: {available}") from exc
    field = np.asarray(field, dtype=float)
    if field.ndim == 1:
        field = field.reshape((-1, 1))
    if field.shape[1] not in {1, 4}:
        raise ValueError(
            f"field {field_name!r} must be scalar or 2D tensor with 4 components; got shape {field.shape}"
        )
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


def weighted_prediction(
    field: np.ndarray,
    target: pd.Series,
    cells: pd.DataFrame,
) -> dict[str, Any]:
    tangent_x = float(target.get("segment_tangent_x", math.nan))
    tangent_y = float(target.get("segment_tangent_y", math.nan))
    weighted_values: list[tuple[float, float]] = []
    for _, cell in cells.iterrows():
        cell_id = int(cell["lookup_cell_id"])
        if cell_id < 0 or cell_id >= field.shape[0]:
            continue
        weight = float(cell["cell_weight"])
        k_eff = directional_permeability(field, cell_id, tangent_x, tangent_y)
        if np.isfinite(k_eff) and k_eff > 0.0 and np.isfinite(weight) and weight > 0.0:
            weighted_values.append((weight, k_eff))
    if not weighted_values:
        return {
            "predicted_permeability_m2": math.nan,
            "predicted_log10_permeability_m2": math.nan,
            "prediction_cell_count": 0,
        }
    total_weight = sum(weight for weight, _ in weighted_values)
    predicted = sum(weight * value for weight, value in weighted_values) / total_weight
    return {
        "predicted_permeability_m2": predicted,
        "predicted_log10_permeability_m2": math.log10(predicted),
        "prediction_cell_count": len(weighted_values),
    }


def evaluate_targets(
    mesh_path: Path,
    field_name: str,
    targets_path: Path,
    target_cells_path: Path,
    log10_sigma: float,
    include_non_usable: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    field = read_cell_field(mesh_path, field_name)
    targets = pd.read_csv(targets_path)
    target_cells = pd.read_csv(target_cells_path)
    cells_by_observation = {
        observation_id: group.copy()
        for observation_id, group in target_cells.groupby("observation_id")
    }

    rows: list[dict[str, Any]] = []
    for _, target in targets.iterrows():
        observation_id = target["observation_id"]
        usable = bool_value(target.get("usable_for_current_ogs_fit", False))
        cells = cells_by_observation.get(observation_id)
        has_cells = cells is not None and not cells.empty
        should_fit = bool(usable and has_cells)
        should_report = bool((include_non_usable and has_cells) or should_fit)

        output: dict[str, Any] = {
            "observation_id": observation_id,
            "source_sheet": target.get("source_sheet", ""),
            "campaign_year": target.get("campaign_year", ""),
            "block_label": target.get("block_label", ""),
            "normalized_segment_label": target.get("normalized_segment_label", ""),
            "borehole_depth_m": target.get("borehole_depth_m", math.nan),
            "target_status": target.get("target_status", ""),
            "usable_for_current_ogs_fit": usable,
            "used_in_objective": should_fit,
            "observed_permeability_m2": target.get("permeability_m2", math.nan),
            "observed_log10_permeability_m2": target.get("log10_permeability_m2", math.nan),
            "log10_sigma": log10_sigma,
            "segment_tangent_x": target.get("segment_tangent_x", math.nan),
            "segment_tangent_y": target.get("segment_tangent_y", math.nan),
            "selected_cell_ids": target.get("selected_cell_ids", ""),
            "prediction_note": "no cell mapping available" if not has_cells else "",
        }
        if should_report:
            prediction = weighted_prediction(field, target, cells)
            output.update(prediction)
            observed_log = float(output["observed_log10_permeability_m2"])
            predicted_log = float(prediction["predicted_log10_permeability_m2"])
            if np.isfinite(observed_log) and np.isfinite(predicted_log):
                residual = predicted_log - observed_log
                output["log10_residual_pred_minus_obs"] = residual
                output["normalized_residual"] = residual / log10_sigma
                output["unweighted_objective_contribution"] = 0.5 * (residual / log10_sigma) ** 2 if should_fit else math.nan
            else:
                output["log10_residual_pred_minus_obs"] = math.nan
                output["normalized_residual"] = math.nan
                output["unweighted_objective_contribution"] = math.nan
        else:
            output.update(
                {
                    "predicted_permeability_m2": math.nan,
                    "predicted_log10_permeability_m2": math.nan,
                    "prediction_cell_count": 0,
                    "log10_residual_pred_minus_obs": math.nan,
                    "normalized_residual": math.nan,
                    "unweighted_objective_contribution": math.nan,
                }
            )
        rows.append(output)

    evaluation = pd.DataFrame(rows)
    evaluation["duplicate_group_key"] = ""
    evaluation["duplicate_count"] = 0
    evaluation["objective_weight"] = 0.0
    evaluation["objective_contribution"] = math.nan

    fit_mask = evaluation["used_in_objective"] & np.isfinite(evaluation["log10_residual_pred_minus_obs"])
    if fit_mask.any():
        keys = (
            evaluation.loc[fit_mask, "campaign_year"].astype(str)
            + "|"
            + evaluation.loc[fit_mask, "normalized_segment_label"].astype(str)
            + "|"
            + evaluation.loc[fit_mask, "borehole_depth_m"].astype(float).round(6).astype(str)
            + "|"
            + evaluation.loc[fit_mask, "observed_log10_permeability_m2"].astype(float).round(8).astype(str)
        )
        evaluation.loc[fit_mask, "duplicate_group_key"] = keys
        duplicate_counts = keys.value_counts()
        evaluation.loc[fit_mask, "duplicate_count"] = keys.map(duplicate_counts).astype(int).to_numpy()
        evaluation.loc[fit_mask, "objective_weight"] = 1.0 / evaluation.loc[fit_mask, "duplicate_count"].astype(float)
        evaluation.loc[fit_mask, "objective_contribution"] = (
            evaluation.loc[fit_mask, "unweighted_objective_contribution"]
            * evaluation.loc[fit_mask, "objective_weight"]
        )

    fit_rows = evaluation[evaluation["used_in_objective"]].copy()
    finite = fit_rows[np.isfinite(fit_rows["log10_residual_pred_minus_obs"])]
    weights = finite["objective_weight"].to_numpy(dtype=float) if not finite.empty else np.array([], dtype=float)
    residuals = finite["log10_residual_pred_minus_obs"].to_numpy(dtype=float) if not finite.empty else np.array([], dtype=float)
    effective_weight = float(weights.sum()) if weights.size else math.nan
    optimal_shift = float(-np.sum(weights * residuals) / np.sum(weights)) if weights.size else math.nan
    shifted_residuals = residuals + optimal_shift if weights.size else np.array([], dtype=float)
    summary: dict[str, Any] = {
        "mesh": str(mesh_path),
        "field_name": field_name,
        "field_shape": list(field.shape),
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "log10_sigma": log10_sigma,
        "target_rows": int(evaluation.shape[0]),
        "reported_prediction_rows": int(evaluation["predicted_permeability_m2"].notna().sum()),
        "used_in_objective_rows": int(fit_rows.shape[0]),
        "finite_objective_rows": int(finite.shape[0]),
        "effective_objective_weight": effective_weight,
        "duplicate_groups": int(evaluation.loc[fit_mask, "duplicate_group_key"].nunique()) if fit_mask.any() else 0,
        "objective_value": float(finite["objective_contribution"].sum()) if not finite.empty else math.nan,
        "weighted_rmse_log10": float(np.sqrt(np.sum(weights * residuals**2) / np.sum(weights))) if weights.size else math.nan,
        "weighted_mean_abs_log10_residual": float(np.sum(weights * np.abs(residuals)) / np.sum(weights)) if weights.size else math.nan,
        "max_abs_log10_residual": float(np.max(np.abs(residuals))) if residuals.size else math.nan,
        "optimal_global_log10_shift_to_prediction": optimal_shift,
        "optimal_global_permeability_multiplier": float(10**optimal_shift) if np.isfinite(optimal_shift) else math.nan,
        "objective_value_after_global_shift": float(
            np.sum(0.5 * weights * (shifted_residuals / log10_sigma) ** 2)
        ) if weights.size else math.nan,
        "weighted_rmse_log10_after_global_shift": float(
            np.sqrt(np.sum(weights * shifted_residuals**2) / np.sum(weights))
        ) if weights.size else math.nan,
        "residual_by_segment": {},
        "notes": [
            "Prediction uses weighted arithmetic averaging of e^T K e over selected target cells.",
            "Residuals are predicted log10(k) minus observed log10(k).",
            "Objective weights divide duplicate rows with the same campaign, segment, depth and observed log10(k).",
            "This evaluates only the direct permeability target layer; it does not run OGS or compare state observations.",
        ],
    }
    if not finite.empty:
        grouped = finite.groupby("normalized_segment_label")
        summary["residual_by_segment"] = {
            str(segment): {
                "count": int(group.shape[0]),
                "effective_weight": float(group["objective_weight"].sum()),
                "weighted_rmse_log10": float(
                    np.sqrt(
                        np.sum(group["objective_weight"] * group["log10_residual_pred_minus_obs"] ** 2)
                        / np.sum(group["objective_weight"])
                    )
                ),
                "weighted_mean_abs_log10_residual": float(
                    np.sum(group["objective_weight"] * np.abs(group["log10_residual_pred_minus_obs"]))
                    / np.sum(group["objective_weight"])
                ),
            }
            for segment, group in grouped
        }
    return evaluation, summary


def main() -> None:
    args = parse_args()
    mesh_path = args.mesh.resolve()
    output = args.output.resolve() if args.output else mesh_path.parent / "permeability_fit_evaluation.csv"
    summary_output = (
        args.summary_output.resolve()
        if args.summary_output
        else mesh_path.parent / "permeability_fit_summary.json"
    )
    evaluation, summary = evaluate_targets(
        mesh_path=mesh_path,
        field_name=args.field_name,
        targets_path=args.targets.resolve(),
        target_cells_path=args.target_cells.resolve(),
        log10_sigma=args.log10_sigma,
        include_non_usable=args.include_non_usable,
    )
    evaluation.to_csv(output, index=False)
    summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {output}")
    print(f"wrote {summary_output}")
    print(f"used objective rows: {summary['used_in_objective_rows']}")
    print(f"effective objective weight: {summary['effective_objective_weight']:.6g}")
    print(f"objective value: {summary['objective_value']:.6g}")
    print(f"weighted rmse log10: {summary['weighted_rmse_log10']:.6g}")


if __name__ == "__main__":
    main()
