#!/usr/bin/env python3
"""Audit residual structure in the active direct permeability target layer.

This audit is deliberately narrower than a new inversion run.  It asks why the
current accepted field still has a large direct pulse-test RMSE after smooth,
local-basis, local-anisotropy, cross-stream hybrid, and structural/EDZ screens:

* which observations dominate the residuals,
* whether those observations are inside the configured scalar multiplier bounds,
* whether residuals cluster by segment, campaign, depth, or support cell, and
* which next action is supported before spending more OGS time.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_permeability_targets import directional_permeability, evaluate_targets  # noqa: E402
from fit_smooth_permeability_field_from_targets import read_cell_field  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu"),
        help="Current accepted run-local permeability mesh.",
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
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.md"),
    )
    parser.add_argument(
        "--support-cell-output",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_support_cell_audit.csv"),
    )
    parser.add_argument(
        "--segment-output",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_segment_summary.csv"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_residual_conflict_audit"),
    )
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def first_cell_id(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    first = text.split(";")[0].split(",")[0].strip()
    try:
        number = int(float(first))
    except ValueError:
        return None
    return number if number >= 0 else None


def tensor_eigenvalues(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 1:
        base = float(values[0])
        return base, base
    tensor = np.array([[values[0], values[1]], [values[2], values[3]]], dtype=float)
    eigvals = np.linalg.eigvalsh(0.5 * (tensor + tensor.T))
    return float(eigvals[0]), float(eigvals[1])


def scalar_multiplier_range(values: np.ndarray, min_k: float, max_k: float) -> tuple[float, float]:
    min_eig, max_eig = tensor_eigenvalues(values)
    if min_eig <= 0.0 or max_eig <= 0.0 or not np.isfinite(min_eig) or not np.isfinite(max_eig):
        return 1.0, 1.0
    return float(min_k / min_eig), float(max_k / max_eig)


def weighted_feasible_prediction(
    field: np.ndarray,
    target: pd.Series,
    cells: pd.DataFrame,
    min_k: float,
    max_k: float,
) -> dict[str, Any]:
    tangent_x = float(target.get("segment_tangent_x", math.nan))
    tangent_y = float(target.get("segment_tangent_y", math.nan))
    weighted_current: list[tuple[float, float]] = []
    weighted_min: list[tuple[float, float]] = []
    weighted_max: list[tuple[float, float]] = []
    cell_ids: list[int] = []
    material_ids: list[int] = []
    min_scales: list[float] = []
    max_scales: list[float] = []
    for _, cell in cells.iterrows():
        cell_id = int(cell["lookup_cell_id"])
        if cell_id < 0 or cell_id >= field.shape[0]:
            continue
        weight = float(cell["cell_weight"])
        if not np.isfinite(weight) or weight <= 0.0:
            continue
        current = directional_permeability(field, cell_id, tangent_x, tangent_y)
        if not np.isfinite(current) or current <= 0.0:
            continue
        min_scale, max_scale = scalar_multiplier_range(field[cell_id], min_k, max_k)
        current_min = current * min_scale
        current_max = current * max_scale
        if current_min > current_max:
            current_min, current_max = current_max, current_min
        weighted_current.append((weight, current))
        weighted_min.append((weight, current_min))
        weighted_max.append((weight, current_max))
        cell_ids.append(cell_id)
        material_ids.append(int(cell.get("lookup_material_id", -1)))
        min_scales.append(min_scale)
        max_scales.append(max_scale)

    if not weighted_current:
        return {
            "support_cell_count": 0,
            "support_cell_ids": "",
            "support_material_ids": "",
            "current_log10_prediction_from_cells": math.nan,
            "configured_scalar_feasible_log10_min": math.nan,
            "configured_scalar_feasible_log10_max": math.nan,
            "configured_scalar_min_multiplier_min": math.nan,
            "configured_scalar_max_multiplier_min": math.nan,
            "configured_scalar_max_multiplier_max": math.nan,
        }

    def weighted_average(rows: list[tuple[float, float]]) -> float:
        denominator = sum(weight for weight, _ in rows)
        return sum(weight * value for weight, value in rows) / denominator

    current_value = weighted_average(weighted_current)
    min_value = weighted_average(weighted_min)
    max_value = weighted_average(weighted_max)
    return {
        "support_cell_count": len(cell_ids),
        "support_cell_ids": ";".join(str(cell_id) for cell_id in cell_ids),
        "support_material_ids": ";".join(str(material_id) for material_id in material_ids),
        "current_log10_prediction_from_cells": math.log10(current_value),
        "configured_scalar_feasible_log10_min": math.log10(min_value),
        "configured_scalar_feasible_log10_max": math.log10(max_value),
        "configured_scalar_min_multiplier_min": float(np.min(min_scales)) if min_scales else math.nan,
        "configured_scalar_max_multiplier_min": float(np.min(max_scales)) if max_scales else math.nan,
        "configured_scalar_max_multiplier_max": float(np.max(max_scales)) if max_scales else math.nan,
    }


def residual_band(abs_residual: float) -> str:
    if not np.isfinite(abs_residual):
        return "not_finite"
    if abs_residual >= 3.0:
        return "abs_ge_3_log10"
    if abs_residual >= 2.0:
        return "abs_2_to_3_log10"
    if abs_residual >= 1.0:
        return "abs_1_to_2_log10"
    if abs_residual >= 0.5:
        return "abs_0p5_to_1_log10"
    return "abs_lt_0p5_log10"


def feasibility_status(observed: float, low: float, high: float) -> str:
    if not (np.isfinite(observed) and np.isfinite(low) and np.isfinite(high)):
        return "not_evaluated"
    eps = 1.0e-9
    if observed < low - eps:
        return "observed_below_configured_scalar_range"
    if observed > high + eps:
        return "observed_above_configured_scalar_range"
    return "observed_inside_configured_scalar_range"


def next_action(row: pd.Series) -> str:
    status = str(row.get("configured_scalar_feasibility_status", ""))
    abs_residual = float(row.get("abs_log10_residual", math.nan))
    if status != "observed_inside_configured_scalar_range":
        return "review_sampler_bounds_tensor_shape_or_measurement_interpretation_before_more_spatial_sampling"
    if np.isfinite(abs_residual) and abs_residual >= 1.0:
        return "review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs"
    if np.isfinite(abs_residual) and abs_residual >= 0.5:
        return "keep_as_noisy_direct_constraint_with_explicit_sigma"
    return "locally_consistent_under_current_log10_sigma"


def build_rows(
    mesh_path: Path,
    field_name: str,
    targets_path: Path,
    target_cells_path: Path,
    log10_sigma: float,
    min_k: float,
    max_k: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    mesh = meshio.read(mesh_path)
    field = read_cell_field(mesh, field_name)
    targets = pd.read_csv(targets_path)
    target_cells = pd.read_csv(target_cells_path)
    cells_by_observation = {str(key): group.copy() for key, group in target_cells.groupby("observation_id")}
    targets_by_observation = {str(row["observation_id"]): row for _, row in targets.iterrows()}

    evaluation, direct_summary = evaluate_targets(
        mesh_path=mesh_path,
        field_name=field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=log10_sigma,
        include_non_usable=True,
    )

    rows: list[dict[str, Any]] = []
    for _, row in evaluation.iterrows():
        observation_id = str(row["observation_id"])
        target = targets_by_observation.get(observation_id)
        cells = cells_by_observation.get(observation_id, pd.DataFrame())
        feasible = (
            weighted_feasible_prediction(field, target, cells, min_k, max_k)
            if target is not None and not cells.empty
            else {}
        )
        observed = float(row.get("observed_log10_permeability_m2", math.nan))
        predicted = float(row.get("predicted_log10_permeability_m2", math.nan))
        residual = float(row.get("log10_residual_pred_minus_obs", math.nan))
        low = float(feasible.get("configured_scalar_feasible_log10_min", math.nan))
        high = float(feasible.get("configured_scalar_feasible_log10_max", math.nan))
        status = feasibility_status(observed, low, high)
        output = {
            "observation_id": observation_id,
            "source_sheet": row.get("source_sheet", ""),
            "campaign_year": row.get("campaign_year", ""),
            "block_label": row.get("block_label", ""),
            "normalized_segment_label": row.get("normalized_segment_label", ""),
            "borehole_depth_m": row.get("borehole_depth_m", math.nan),
            "target_status": row.get("target_status", ""),
            "usable_for_current_ogs_fit": bool_value(row.get("usable_for_current_ogs_fit", False)),
            "used_in_objective": bool_value(row.get("used_in_objective", False)),
            "observed_log10_permeability_m2": observed,
            "predicted_log10_permeability_m2": predicted,
            "log10_residual_pred_minus_obs": residual,
            "abs_log10_residual": abs(residual) if np.isfinite(residual) else math.nan,
            "normalized_residual": residual / log10_sigma if np.isfinite(residual) else math.nan,
            "objective_weight": row.get("objective_weight", math.nan),
            "duplicate_count": row.get("duplicate_count", 0),
            "prediction_cell_count": row.get("prediction_cell_count", 0),
            "selected_cell_ids": row.get("selected_cell_ids", ""),
            "selected_material_ids": row.get("selected_material_ids", ""),
            **feasible,
            "configured_scalar_feasibility_status": status,
            "headroom_up_log10_from_current": high - predicted if np.isfinite(high) and np.isfinite(predicted) else math.nan,
            "headroom_down_log10_from_current": predicted - low if np.isfinite(low) and np.isfinite(predicted) else math.nan,
            "residual_band": residual_band(abs(residual) if np.isfinite(residual) else math.nan),
            "residual_sign": (
                "underpredicts_observation" if np.isfinite(residual) and residual < 0.0
                else "overpredicts_observation" if np.isfinite(residual) and residual > 0.0
                else "zero_residual" if np.isfinite(residual)
                else "not_finite"
            ),
        }
        output["recommended_next_action"] = next_action(pd.Series(output))
        rows.append(output)

    audit = pd.DataFrame(rows)
    active = audit[audit["used_in_objective"] & np.isfinite(audit["log10_residual_pred_minus_obs"])].copy()

    if active.empty:
        segment_summary = pd.DataFrame()
    else:
        segment_summary = (
            active.groupby("normalized_segment_label", as_index=False)
            .agg(
                active_rows=("observation_id", "size"),
                mean_residual=("log10_residual_pred_minus_obs", "mean"),
                mean_abs_residual=("abs_log10_residual", "mean"),
                max_abs_residual=("abs_log10_residual", "max"),
                weighted_mean_abs_residual=("abs_log10_residual", lambda x: float(np.average(x, weights=active.loc[x.index, "objective_weight"]))),
                min_depth_m=("borehole_depth_m", "min"),
                max_depth_m=("borehole_depth_m", "max"),
                observed_log10_min=("observed_log10_permeability_m2", "min"),
                observed_log10_max=("observed_log10_permeability_m2", "max"),
                predicted_log10_min=("predicted_log10_permeability_m2", "min"),
                predicted_log10_max=("predicted_log10_permeability_m2", "max"),
            )
            .sort_values("normalized_segment_label")
        )

    cell_rows = []
    active_cells = active.copy()
    active_cells["primary_cell_id"] = active_cells["selected_cell_ids"].map(first_cell_id)
    for cell_id, group in active_cells.dropna(subset=["primary_cell_id"]).groupby("primary_cell_id"):
        observed = group["observed_log10_permeability_m2"].to_numpy(dtype=float)
        residuals = group["log10_residual_pred_minus_obs"].to_numpy(dtype=float)
        cell_rows.append(
            {
                "primary_cell_id": int(cell_id),
                "row_count": int(group.shape[0]),
                "segments": ";".join(sorted(set(group["normalized_segment_label"].astype(str)))),
                "depth_min_m": float(group["borehole_depth_m"].min()),
                "depth_max_m": float(group["borehole_depth_m"].max()),
                "observed_log10_min": float(np.min(observed)),
                "observed_log10_max": float(np.max(observed)),
                "observed_log10_range": float(np.max(observed) - np.min(observed)),
                "mean_abs_residual": float(np.mean(np.abs(residuals))),
                "max_abs_residual": float(np.max(np.abs(residuals))),
                "feasibility_statuses": ";".join(sorted(set(group["configured_scalar_feasibility_status"].astype(str)))),
                "residual_signs": ";".join(sorted(set(group["residual_sign"].astype(str)))),
            }
        )
    support_cell_audit = pd.DataFrame(cell_rows).sort_values(
        ["max_abs_residual", "observed_log10_range", "primary_cell_id"],
        ascending=[False, False, True],
    ) if cell_rows else pd.DataFrame()

    summary = {
        "status": "permeability_residual_conflict_audit_generated",
        "mesh": str(mesh_path),
        "field_name": field_name,
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "configured_min_k_eigenvalue": min_k,
        "configured_max_k_eigenvalue": max_k,
        "log10_sigma": log10_sigma,
        "target_rows": int(targets.shape[0]),
        "evaluation_rows": int(audit.shape[0]),
        "active_direct_rows": int(active.shape[0]),
        "direct_summary": json_ready(direct_summary),
        "target_status_counts": {
            str(key): int(value) for key, value in targets["target_status"].value_counts().to_dict().items()
        },
        "residual_band_counts_active": {
            str(key): int(value) for key, value in active["residual_band"].value_counts().to_dict().items()
        } if not active.empty else {},
        "residual_sign_counts_active": {
            str(key): int(value) for key, value in active["residual_sign"].value_counts().to_dict().items()
        } if not active.empty else {},
        "configured_scalar_feasibility_counts_active": {
            str(key): int(value)
            for key, value in active["configured_scalar_feasibility_status"].value_counts().to_dict().items()
        } if not active.empty else {},
        "recommended_next_action_counts_active": {
            str(key): int(value) for key, value in active["recommended_next_action"].value_counts().to_dict().items()
        } if not active.empty else {},
        "large_residual_active_rows_ge_1_log10": int((active["abs_log10_residual"] >= 1.0).sum()) if not active.empty else 0,
        "very_large_residual_active_rows_ge_2_log10": int((active["abs_log10_residual"] >= 2.0).sum()) if not active.empty else 0,
        "extreme_residual_active_rows_ge_3_log10": int((active["abs_log10_residual"] >= 3.0).sum()) if not active.empty else 0,
        "active_rows_outside_configured_scalar_range": int(
            (~active["configured_scalar_feasibility_status"].eq("observed_inside_configured_scalar_range")).sum()
        ) if not active.empty else 0,
        "support_cell_rows": int(support_cell_audit.shape[0]),
        "support_cells_with_repeated_active_rows": int((support_cell_audit.get("row_count", pd.Series(dtype=int)) > 1).sum())
        if not support_cell_audit.empty
        else 0,
        "support_cells_with_observed_range_ge_1_log10": int(
            (support_cell_audit.get("observed_log10_range", pd.Series(dtype=float)) >= 1.0).sum()
        ) if not support_cell_audit.empty else 0,
        "top_abs_residual_rows": json_ready(
            active.sort_values("abs_log10_residual", ascending=False)
            .head(10)
            [
                [
                    "observation_id",
                    "normalized_segment_label",
                    "borehole_depth_m",
                    "observed_log10_permeability_m2",
                    "predicted_log10_permeability_m2",
                    "log10_residual_pred_minus_obs",
                    "configured_scalar_feasibility_status",
                    "recommended_next_action",
                ]
            ]
            .to_dict(orient="records")
        ) if not active.empty else [],
        "segment_summary": json_ready(segment_summary.to_dict(orient="records")),
        "interpretation": "",
        "notes": [
            "Residuals are predicted log10(k) minus observed log10(k).",
            "The configured scalar range assumes each cell tensor keeps its orientation/anisotropy ratio and can only scale until the configured eigenvalue bounds are hit.",
            "This is a direct pulse-test audit only; it does not run OGS or change likelihood activation gates.",
        ],
    }
    outside = summary["active_rows_outside_configured_scalar_range"]
    large = summary["large_residual_active_rows_ge_1_log10"]
    if outside:
        summary["interpretation"] = (
            f"{outside} active rows are outside the configured scalar multiplier range; more spatial "
            "sampling within the same scalar-bounded family cannot close those rows without revisiting "
            "bounds, tensor-shape release, or measurement interpretation."
        )
    elif large:
        summary["interpretation"] = (
            f"All active rows are inside the configured scalar multiplier range, but {large} rows have "
            "absolute residuals of at least 1 log10 unit. The remaining mismatch is therefore not a simple "
            "eigenvalue-bound issue; it points to support geometry, gas-to-water interpretation, uncertainty, "
            "or a more expressive spatial parameterization."
        )
    else:
        summary["interpretation"] = (
            "The active direct permeability residuals are mostly within one log10 unit and inside the "
            "configured scalar range; the remaining direct layer is not the dominant blocker."
        )
    return audit, segment_summary, support_cell_audit, summary


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    direct = summary.get("direct_summary", {})
    lines = [
        "# Permeability Residual Conflict Audit",
        "",
        "This audit explains the remaining direct pulse-test residuals for the current accepted field.",
        "It is not a new OGS run and it does not promote additional measurement streams into the likelihood.",
        "",
        "## Current Direct Fit",
        "",
        f"- Mesh: `{summary['mesh']}`",
        f"- Active direct rows: {summary['active_direct_rows']}",
        f"- Direct objective: {float(direct.get('objective_value', math.nan)):.6f}",
        f"- Weighted RMSE: {float(direct.get('weighted_rmse_log10', math.nan)):.6f} log10(k)",
        f"- Weighted mean absolute residual: {float(direct.get('weighted_mean_abs_log10_residual', math.nan)):.6f} log10(k)",
        f"- Max absolute residual: {float(direct.get('max_abs_log10_residual', math.nan)):.6f} log10(k)",
        "",
        "## Residual Counts",
        "",
        f"- Residual bands: `{summary['residual_band_counts_active']}`",
        f"- Residual signs: `{summary['residual_sign_counts_active']}`",
        f"- Configured scalar feasibility: `{summary['configured_scalar_feasibility_counts_active']}`",
        f"- Recommended next actions: `{summary['recommended_next_action_counts_active']}`",
        f"- Active rows with |residual| >= 1 log10: {summary['large_residual_active_rows_ge_1_log10']}",
        f"- Active rows with |residual| >= 2 log10: {summary['very_large_residual_active_rows_ge_2_log10']}",
        f"- Active rows outside configured scalar range: {summary['active_rows_outside_configured_scalar_range']}",
        "",
        "## Segment Summary",
        "",
        "| Segment | Rows | Mean residual | Mean abs | Max abs | Depth range [m] | Observed log10 range |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in summary.get("segment_summary", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['normalized_segment_label']}`",
                    str(int(row["active_rows"])),
                    f"{float(row['mean_residual']):+.3f}",
                    f"{float(row['mean_abs_residual']):.3f}",
                    f"{float(row['max_abs_residual']):.3f}",
                    f"{float(row['min_depth_m']):.2f}-{float(row['max_depth_m']):.2f}",
                    f"{float(row['observed_log10_min']):.2f} to {float(row['observed_log10_max']):.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Largest Active Residuals",
            "",
            "| Observation | Segment | Depth [m] | Observed | Predicted | Residual | Feasibility | Next action |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in summary.get("top_abs_residual_rows", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['observation_id']}`",
                    f"`{row['normalized_segment_label']}`",
                    f"{float(row['borehole_depth_m']):.2f}",
                    f"{float(row['observed_log10_permeability_m2']):.3f}",
                    f"{float(row['predicted_log10_permeability_m2']):.3f}",
                    f"{float(row['log10_residual_pred_minus_obs']):+.3f}",
                    str(row["configured_scalar_feasibility_status"]),
                    str(row["recommended_next_action"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "## Outputs",
            "",
            f"- Row audit: `{summary['output_csv']}`",
            f"- Segment summary: `{summary['segment_output_csv']}`",
            f"- Support-cell audit: `{summary['support_cell_output_csv']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_catalogue_artifacts(catalogue_dir: Path, artifacts: list[Path], repo: Path) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for path in artifacts:
        if not path.exists():
            continue
        target = derived / path.name
        shutil.copy2(path, target)
        copies.append(
            {
                "source": os.path.relpath(path.resolve(), repo),
                "catalogue_copy": os.path.relpath(target.resolve(), repo),
            }
        )
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    mesh_path = resolve(repo, args.input_mesh).resolve()
    targets_path = resolve(repo, args.targets).resolve()
    target_cells_path = resolve(repo, args.target_cells).resolve()
    current_summary_path = resolve(repo, args.current_field_summary).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    support_output = resolve(repo, args.support_cell_output).resolve()
    segment_output = resolve(repo, args.segment_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    audit, segment_summary, support_cell_audit, summary = build_rows(
        mesh_path=mesh_path,
        field_name=args.field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=args.log10_sigma,
        min_k=args.min_k_eigenvalue,
        max_k=args.max_k_eigenvalue,
    )
    current_summary = read_json(current_summary_path)
    summary.update(
        {
            "current_field_summary": str(current_summary_path),
            "current_field_run_id": current_summary.get("run_id"),
            "output_csv": str(output_csv),
            "segment_output_csv": str(segment_output),
            "support_cell_output_csv": str(support_output),
            "summary_markdown": str(markdown_output),
        }
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output_csv, index=False)
    segment_summary.to_csv(segment_output, index=False)
    support_cell_audit.to_csv(support_output, index=False)
    write_markdown(markdown_output, summary)
    summary["catalogue_copies"] = copy_catalogue_artifacts(
        catalogue_dir,
        [output_csv, segment_output, support_output, markdown_output],
        repo,
    )
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, summary)
    copy_catalogue_artifacts(catalogue_dir, [summary_output, markdown_output], repo)

    print(f"wrote {output_csv}")
    print(f"wrote {segment_output}")
    print(f"wrote {support_output}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")
    print(f"active direct rows: {summary['active_direct_rows']}")
    print(f"weighted rmse log10: {summary['direct_summary']['weighted_rmse_log10']:.6g}")
    print(f"large residual rows >=1 log10: {summary['large_residual_active_rows_ge_1_log10']}")
    print(f"outside scalar range rows: {summary['active_rows_outside_configured_scalar_range']}")


if __name__ == "__main__":
    main()
