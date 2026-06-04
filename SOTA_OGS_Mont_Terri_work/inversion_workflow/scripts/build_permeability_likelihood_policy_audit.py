#!/usr/bin/env python3
"""Compare direct-permeability likelihood policies for the current field.

This audit does not change the active objective and does not run OGS.  It uses
the residual-conflict audit to separate field-fit limitations from likelihood
semantics: repeated pulse-test rows can map to the same model support cell while
carrying mutually inconsistent log10 permeability values.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-audit",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.csv"),
    )
    parser.add_argument(
        "--residual-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit_summary.json"),
    )
    parser.add_argument(
        "--support-cell-audit",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_support_cell_audit.csv"),
    )
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--huber-delta-normalized", type=float, default=2.0)
    parser.add_argument("--student-t-nu", type=float, default=4.0)
    parser.add_argument("--cap-abs-log10", type=float, default=1.0)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit.csv"),
    )
    parser.add_argument(
        "--row-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_row_audit.csv"),
    )
    parser.add_argument(
        "--group-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_group_summary.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit"),
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


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights) / float(np.sum(weights))
    return float(values[np.searchsorted(cumulative, 0.5, side="left")])


def finite_average(values: np.ndarray, weights: np.ndarray | None = None) -> float:
    values = np.asarray(values, dtype=float)
    if weights is None:
        mask = np.isfinite(values)
        return float(np.mean(values[mask])) if mask.any() else math.nan
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(np.average(values[mask], weights=weights[mask]))


def weighted_rmse(residuals: np.ndarray, weights: np.ndarray) -> float:
    residuals = np.asarray(residuals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(residuals) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(math.sqrt(np.average(residuals[mask] ** 2, weights=weights[mask])))


def weighted_mae(residuals: np.ndarray, weights: np.ndarray) -> float:
    residuals = np.asarray(residuals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(residuals) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(np.average(np.abs(residuals[mask]), weights=weights[mask]))


def gaussian_loss(z: np.ndarray) -> np.ndarray:
    return 0.5 * z**2


def capped_gaussian_loss(z: np.ndarray, cap_z: float) -> np.ndarray:
    return 0.5 * np.minimum(z**2, cap_z**2)


def huber_loss(z: np.ndarray, delta: float) -> np.ndarray:
    abs_z = np.abs(z)
    return np.where(abs_z <= delta, 0.5 * z**2, delta * (abs_z - 0.5 * delta))


def student_t_loss(z: np.ndarray, nu: float) -> np.ndarray:
    return 0.5 * (nu + 1.0) * np.log1p((z**2) / nu)


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].map(bool_value)


def build_row_audit(active: pd.DataFrame, sigma: float, cap_abs_log10: float, huber_delta: float, student_nu: float) -> pd.DataFrame:
    rows = active.copy()
    rows["primary_cell_id"] = rows["selected_cell_ids"].map(first_cell_id)
    residual = rows["log10_residual_pred_minus_obs"].astype(float).to_numpy()
    weights = rows["objective_weight"].astype(float).to_numpy()
    z = residual / sigma
    cap_z = cap_abs_log10 / sigma
    rows["gaussian_row_loss"] = weights * gaussian_loss(z)
    rows["capped_abs1_log10_row_loss"] = weights * capped_gaussian_loss(z, cap_z)
    rows["huber_delta_2sigma_row_loss"] = weights * huber_loss(z, huber_delta)
    rows["student_t_nu4_row_loss"] = weights * student_t_loss(z, student_nu)
    total_loss = float(np.sum(rows["gaussian_row_loss"]))
    rows["gaussian_row_loss_share"] = rows["gaussian_row_loss"] / total_loss if total_loss > 0 else math.nan
    rows["policy_class"] = rows.apply(row_policy_class, axis=1)
    keep = [
        "observation_id",
        "source_sheet",
        "campaign_year",
        "normalized_segment_label",
        "borehole_depth_m",
        "primary_cell_id",
        "observed_log10_permeability_m2",
        "predicted_log10_permeability_m2",
        "log10_residual_pred_minus_obs",
        "abs_log10_residual",
        "normalized_residual",
        "objective_weight",
        "duplicate_count",
        "configured_scalar_feasibility_status",
        "residual_sign",
        "recommended_next_action",
        "gaussian_row_loss",
        "gaussian_row_loss_share",
        "capped_abs1_log10_row_loss",
        "huber_delta_2sigma_row_loss",
        "student_t_nu4_row_loss",
        "policy_class",
    ]
    return rows[[column for column in keep if column in rows.columns]].sort_values(
        ["gaussian_row_loss", "observation_id"],
        ascending=[False, True],
    )


def row_policy_class(row: pd.Series) -> str:
    status = str(row.get("configured_scalar_feasibility_status", ""))
    abs_residual = float(row.get("abs_log10_residual", math.nan))
    if status != "observed_inside_configured_scalar_range":
        return "configured_scalar_range_decision_required"
    if np.isfinite(abs_residual) and abs_residual >= 2.0:
        return "large_residual_heavy_tail_or_support_review"
    if np.isfinite(abs_residual) and abs_residual >= 1.0:
        return "moderate_residual_uncertainty_review"
    return "ordinary_gaussian_row"


def build_group_summary(active: pd.DataFrame, sigma: float) -> pd.DataFrame:
    rows = active.copy()
    rows["primary_cell_id"] = rows["selected_cell_ids"].map(first_cell_id)
    group_rows: list[dict[str, Any]] = []
    for cell_id, group in rows.dropna(subset=["primary_cell_id"]).groupby("primary_cell_id"):
        observed = group["observed_log10_permeability_m2"].astype(float).to_numpy()
        predicted = group["predicted_log10_permeability_m2"].astype(float).to_numpy()
        weights = group["objective_weight"].astype(float).to_numpy()
        residual = group["log10_residual_pred_minus_obs"].astype(float).to_numpy()
        observed_mean = finite_average(observed, weights)
        predicted_mean = finite_average(predicted, weights)
        observed_median = weighted_median(observed, weights)
        mean_residual = predicted_mean - observed_mean
        median_residual = predicted_mean - observed_median
        current_loss = float(np.sum(weights * gaussian_loss(residual / sigma)))
        statuses = sorted(set(group["configured_scalar_feasibility_status"].astype(str)))
        signs = sorted(set(group["residual_sign"].astype(str)))
        observed_range = float(np.nanmax(observed) - np.nanmin(observed)) if observed.size else math.nan
        group_policy_class = "ordinary_support_group"
        if any(status != "observed_inside_configured_scalar_range" for status in statuses):
            group_policy_class = "configured_scalar_range_decision_required"
        elif np.isfinite(observed_range) and observed_range >= 1.0 and len(signs) > 1:
            group_policy_class = "within_support_conflict_group"
        elif np.isfinite(observed_range) and observed_range >= 1.0:
            group_policy_class = "within_support_high_range_group"
        group_rows.append(
            {
                "primary_cell_id": int(cell_id),
                "row_count": int(group.shape[0]),
                "effective_objective_weight": float(np.sum(weights)),
                "segments": ";".join(sorted(set(group["normalized_segment_label"].astype(str)))),
                "depth_min_m": float(group["borehole_depth_m"].min()),
                "depth_max_m": float(group["borehole_depth_m"].max()),
                "observed_log10_min": float(np.nanmin(observed)),
                "observed_log10_max": float(np.nanmax(observed)),
                "observed_log10_range": observed_range,
                "weighted_observed_mean_log10": observed_mean,
                "weighted_observed_median_log10": observed_median,
                "weighted_predicted_log10": predicted_mean,
                "support_mean_residual_log10": mean_residual,
                "support_median_residual_log10": median_residual,
                "current_row_gaussian_loss": current_loss,
                "support_mean_unit_gaussian_loss": 0.5 * (mean_residual / sigma) ** 2
                if np.isfinite(mean_residual)
                else math.nan,
                "support_median_unit_gaussian_loss": 0.5 * (median_residual / sigma) ** 2
                if np.isfinite(median_residual)
                else math.nan,
                "configured_scalar_feasibility_statuses": ";".join(statuses),
                "residual_signs": ";".join(signs),
                "group_policy_class": group_policy_class,
            }
        )
    if not group_rows:
        return pd.DataFrame()
    groups = pd.DataFrame(group_rows)
    total_loss = float(groups["current_row_gaussian_loss"].sum())
    groups["current_row_gaussian_loss_share"] = (
        groups["current_row_gaussian_loss"] / total_loss if total_loss > 0.0 else math.nan
    )
    return groups.sort_values(
        ["current_row_gaussian_loss", "observed_log10_range", "primary_cell_id"],
        ascending=[False, False, True],
    )


def loss_dominance(losses: np.ndarray) -> dict[str, float]:
    losses = np.asarray(losses, dtype=float)
    losses = losses[np.isfinite(losses) & (losses >= 0.0)]
    total = float(np.sum(losses))
    if total <= 0.0:
        return {"top_5_share": 0.0, "top_10_share": 0.0}
    ordered = np.sort(losses)
    return {
        "top_5_share": float(np.sum(ordered[-5:]) / total),
        "top_10_share": float(np.sum(ordered[-10:]) / total),
    }


def policy_row(
    *,
    policy_id: str,
    policy_type: str,
    row_count: int,
    effective_weight: float,
    objective_like_value: float,
    rmse_log10: float,
    mae_log10: float,
    max_abs_log10: float,
    rows_ge_1: int,
    rows_ge_2: int,
    outside_scalar_rows: int,
    interpretation: str,
) -> dict[str, Any]:
    return {
        "policy_id": policy_id,
        "policy_type": policy_type,
        "row_or_group_count": row_count,
        "effective_weight": effective_weight,
        "objective_like_value": objective_like_value,
        "weighted_rmse_log10": rmse_log10,
        "weighted_mae_log10": mae_log10,
        "max_abs_log10": max_abs_log10,
        "rows_or_groups_ge_1_log10": rows_ge_1,
        "rows_or_groups_ge_2_log10": rows_ge_2,
        "outside_configured_scalar_rows": outside_scalar_rows,
        "interpretation": interpretation,
    }


def build_policy_summary(
    active: pd.DataFrame,
    row_audit: pd.DataFrame,
    groups: pd.DataFrame,
    sigma: float,
    cap_abs_log10: float,
    huber_delta: float,
    student_nu: float,
) -> pd.DataFrame:
    residual = active["log10_residual_pred_minus_obs"].astype(float).to_numpy()
    weights = active["objective_weight"].astype(float).to_numpy()
    z = residual / sigma
    outside_scalar = ~active["configured_scalar_feasibility_status"].astype(str).eq("observed_inside_configured_scalar_range")
    rows: list[dict[str, Any]] = []
    rows.append(
        policy_row(
            policy_id="current_duplicate_weighted_gaussian",
            policy_type="active_current_policy",
            row_count=int(active.shape[0]),
            effective_weight=float(np.sum(weights)),
            objective_like_value=float(np.sum(weights * gaussian_loss(z))),
            rmse_log10=weighted_rmse(residual, weights),
            mae_log10=weighted_mae(residual, weights),
            max_abs_log10=float(np.max(np.abs(residual))),
            rows_ge_1=int((np.abs(residual) >= 1.0).sum()),
            rows_ge_2=int((np.abs(residual) >= 2.0).sum()),
            outside_scalar_rows=int(outside_scalar.sum()),
            interpretation="Retained active semantics: duplicate-weighted Gaussian rows with sigma=0.5 log10.",
        )
    )
    rows.append(
        policy_row(
            policy_id="capped_gaussian_abs1_log10",
            policy_type="robust_row_policy_diagnostic",
            row_count=int(active.shape[0]),
            effective_weight=float(np.sum(weights)),
            objective_like_value=float(np.sum(row_audit["capped_abs1_log10_row_loss"])),
            rmse_log10=weighted_rmse(np.clip(residual, -cap_abs_log10, cap_abs_log10), weights),
            mae_log10=weighted_mae(np.clip(residual, -cap_abs_log10, cap_abs_log10), weights),
            max_abs_log10=cap_abs_log10,
            rows_ge_1=int((np.abs(residual) >= 1.0).sum()),
            rows_ge_2=int((np.abs(residual) >= 2.0).sum()),
            outside_scalar_rows=int(outside_scalar.sum()),
            interpretation="Diagnostic only: caps each row at one log10 unit so large conflicts cannot dominate the objective.",
        )
    )
    rows.append(
        policy_row(
            policy_id="huber_delta_2sigma",
            policy_type="robust_row_policy_diagnostic",
            row_count=int(active.shape[0]),
            effective_weight=float(np.sum(weights)),
            objective_like_value=float(np.sum(row_audit["huber_delta_2sigma_row_loss"])),
            rmse_log10=weighted_rmse(residual, weights),
            mae_log10=weighted_mae(residual, weights),
            max_abs_log10=float(np.max(np.abs(residual))),
            rows_ge_1=int((np.abs(residual) >= 1.0).sum()),
            rows_ge_2=int((np.abs(residual) >= 2.0).sum()),
            outside_scalar_rows=int(outside_scalar.sum()),
            interpretation=f"Diagnostic only: Huber transition at {huber_delta:.1f} sigma, equal to one log10 unit here.",
        )
    )
    rows.append(
        policy_row(
            policy_id="student_t_nu4",
            policy_type="robust_row_policy_diagnostic",
            row_count=int(active.shape[0]),
            effective_weight=float(np.sum(weights)),
            objective_like_value=float(np.sum(row_audit["student_t_nu4_row_loss"])),
            rmse_log10=weighted_rmse(residual, weights),
            mae_log10=weighted_mae(residual, weights),
            max_abs_log10=float(np.max(np.abs(residual))),
            rows_ge_1=int((np.abs(residual) >= 1.0).sum()),
            rows_ge_2=int((np.abs(residual) >= 2.0).sum()),
            outside_scalar_rows=int(outside_scalar.sum()),
            interpretation=f"Diagnostic only: Student-t heavy-tail kernel with nu={student_nu:g}.",
        )
    )
    if not groups.empty:
        mean_residual = groups["support_mean_residual_log10"].astype(float).to_numpy()
        median_residual = groups["support_median_residual_log10"].astype(float).to_numpy()
        unit_weights = np.ones_like(mean_residual, dtype=float)
        rows.append(
            policy_row(
                policy_id="support_cell_weighted_mean_unit_gaussian",
                policy_type="support_aggregation_diagnostic",
                row_count=int(groups.shape[0]),
                effective_weight=float(groups.shape[0]),
                objective_like_value=float(np.nansum(groups["support_mean_unit_gaussian_loss"])),
                rmse_log10=weighted_rmse(mean_residual, unit_weights),
                mae_log10=weighted_mae(mean_residual, unit_weights),
                max_abs_log10=float(np.nanmax(np.abs(mean_residual))),
                rows_ge_1=int((np.abs(mean_residual) >= 1.0).sum()),
                rows_ge_2=int((np.abs(mean_residual) >= 2.0).sum()),
                outside_scalar_rows=int(
                    groups["configured_scalar_feasibility_statuses"]
                    .astype(str)
                    .str.contains("observed_above_configured_scalar_range|observed_below_configured_scalar_range", regex=True)
                    .sum()
                ),
                interpretation=(
                    "Diagnostic only: collapses rows sharing one model support cell to their objective-weighted mean. "
                    "A near-zero value means the current field fits support-cell averages while rowwise conflicts remain."
                ),
            )
        )
        rows.append(
            policy_row(
                policy_id="support_cell_weighted_median_unit_gaussian",
                policy_type="support_aggregation_diagnostic",
                row_count=int(groups.shape[0]),
                effective_weight=float(groups.shape[0]),
                objective_like_value=float(np.nansum(groups["support_median_unit_gaussian_loss"])),
                rmse_log10=weighted_rmse(median_residual, unit_weights),
                mae_log10=weighted_mae(median_residual, unit_weights),
                max_abs_log10=float(np.nanmax(np.abs(median_residual))),
                rows_ge_1=int((np.abs(median_residual) >= 1.0).sum()),
                rows_ge_2=int((np.abs(median_residual) >= 2.0).sum()),
                outside_scalar_rows=int(
                    groups["configured_scalar_feasibility_statuses"]
                    .astype(str)
                    .str.contains("observed_above_configured_scalar_range|observed_below_configured_scalar_range", regex=True)
                    .sum()
                ),
                interpretation="Diagnostic only: support-cell median aggregation is less forgiving when repeated rows favor one extreme.",
            )
        )
    inside = active[~outside_scalar].copy()
    if not inside.empty:
        inside_residual = inside["log10_residual_pred_minus_obs"].astype(float).to_numpy()
        inside_weights = inside["objective_weight"].astype(float).to_numpy()
        rows.append(
            policy_row(
                policy_id="configured_scalar_inside_only_gaussian",
                policy_type="bounds_gate_diagnostic",
                row_count=int(inside.shape[0]),
                effective_weight=float(np.sum(inside_weights)),
                objective_like_value=float(np.sum(inside_weights * gaussian_loss(inside_residual / sigma))),
                rmse_log10=weighted_rmse(inside_residual, inside_weights),
                mae_log10=weighted_mae(inside_residual, inside_weights),
                max_abs_log10=float(np.max(np.abs(inside_residual))),
                rows_ge_1=int((np.abs(inside_residual) >= 1.0).sum()),
                rows_ge_2=int((np.abs(inside_residual) >= 2.0).sum()),
                outside_scalar_rows=0,
                interpretation="Diagnostic only: removes rows outside the configured scalar tensor range instead of fitting them as ordinary Gaussian rows.",
            )
        )
    return pd.DataFrame(rows)


def recommendation(summary: dict[str, Any]) -> str:
    outside = int(summary.get("active_rows_outside_configured_scalar_range", 0) or 0)
    conflict_groups = int(summary.get("support_groups_with_observed_range_ge_1_log10", 0) or 0)
    current_objective = float(summary.get("current_gaussian_objective", math.nan))
    support_mean_objective = float(summary.get("support_mean_unit_objective", math.nan))
    if outside or conflict_groups:
        return (
            "Keep the current Gaussian row policy as the recorded active objective for reproducibility, "
            "but do not treat more spatial sampling as the next default step. First decide whether the direct "
            "permeability likelihood should use robust tails, support-cell aggregation, or explicit exclusion/"
            "reinterpretation of configured-scalar-range outliers. The support-cell weighted-mean diagnostic "
            f"changes the objective-like value from {current_objective:.6g} to {support_mean_objective:.6g}, "
            "which shows that the current field is fitting mapped support averages while row-level pulse-test "
            "conflicts dominate the active Gaussian loss."
        )
    return (
        "The active rowwise Gaussian policy is not dominated by support conflicts in this audit; keep it as "
        "the default direct permeability likelihood unless the modelling team wants a robust sensitivity case."
    )


def write_markdown(path: Path, summary: dict[str, Any], policies: pd.DataFrame, groups: pd.DataFrame, rows: pd.DataFrame) -> None:
    lines = [
        "# Permeability Likelihood Policy Audit",
        "",
        "This audit compares objective semantics for the existing direct pulse-test residuals.",
        "It does not change the active objective, alter any permeability field, or run OGS.",
        "",
        "## Current Active Policy",
        "",
        f"- Active direct rows: {summary['active_direct_rows']}",
        f"- Effective duplicate-weighted objective weight: {summary['effective_objective_weight']:.6g}",
        f"- Current Gaussian objective: {summary['current_gaussian_objective']:.6f}",
        f"- Weighted RMSE: {summary['current_weighted_rmse_log10']:.6f} log10(k)",
        f"- Rows with |residual| >= 1 log10: {summary['large_residual_active_rows_ge_1_log10']}",
        f"- Rows with |residual| >= 2 log10: {summary['very_large_residual_active_rows_ge_2_log10']}",
        f"- Rows outside configured scalar range: {summary['active_rows_outside_configured_scalar_range']}",
        f"- Top 5 row-loss share: {summary['row_loss_top_5_share']:.3f}",
        f"- Top 10 row-loss share: {summary['row_loss_top_10_share']:.3f}",
        "",
        "## Policy Comparison",
        "",
        "| Policy | Type | Count | Effective weight | Objective-like value | RMSE | Rows/groups >=1 | Interpretation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in policies.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['policy_id']}`",
                    str(row["policy_type"]),
                    str(int(row["row_or_group_count"])),
                    f"{float(row['effective_weight']):.3f}",
                    f"{float(row['objective_like_value']):.6g}",
                    f"{float(row['weighted_rmse_log10']):.3f}",
                    str(int(row["rows_or_groups_ge_1_log10"])),
                    str(row["interpretation"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Support-Cell Conflict Summary",
            "",
            f"- Support-cell groups: {summary['support_group_count']}",
            f"- Repeated-row support-cell groups: {summary['support_groups_with_repeated_rows']}",
            f"- Support-cell groups with observed range >= 1 log10: {summary['support_groups_with_observed_range_ge_1_log10']}",
            f"- Current row Gaussian loss in top two support cells: {summary['top_2_support_group_loss_share']:.3f}",
            "",
            "| Cell | Rows | Segment | Depth range [m] | Observed range | Row loss | Mean-residual loss | Median-residual loss | Class |",
            "| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for _, row in groups.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["primary_cell_id"])),
                    str(int(row["row_count"])),
                    f"`{row['segments']}`",
                    f"{float(row['depth_min_m']):.2f}-{float(row['depth_max_m']):.2f}",
                    f"{float(row['observed_log10_range']):.3f}",
                    f"{float(row['current_row_gaussian_loss']):.3f}",
                    f"{float(row['support_mean_unit_gaussian_loss']):.3g}",
                    f"{float(row['support_median_unit_gaussian_loss']):.3f}",
                    str(row["group_policy_class"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Dominant Rows",
            "",
            "| Observation | Segment | Depth [m] | Cell | Observed | Predicted | Residual | Weight | Row loss | Class |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for _, row in rows.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['observation_id']}`",
                    f"`{row['normalized_segment_label']}`",
                    f"{float(row['borehole_depth_m']):.2f}",
                    str(int(row["primary_cell_id"])) if np.isfinite(row["primary_cell_id"]) else "",
                    f"{float(row['observed_log10_permeability_m2']):.3f}",
                    f"{float(row['predicted_log10_permeability_m2']):.3f}",
                    f"{float(row['log10_residual_pred_minus_obs']):+.3f}",
                    f"{float(row['objective_weight']):.3f}",
                    f"{float(row['gaussian_row_loss']):.3f}",
                    str(row["policy_class"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            summary["recommendation"],
            "",
            "## Outputs",
            "",
            f"- Policy comparison: `{summary['output_csv']}`",
            f"- Row audit: `{summary['row_output_csv']}`",
            f"- Support-cell group summary: `{summary['group_output_csv']}`",
            f"- Machine-readable summary: `{summary['summary_output_json']}`",
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
    residual_audit_path = resolve(repo, args.residual_audit).resolve()
    residual_summary_path = resolve(repo, args.residual_summary).resolve()
    support_cell_path = resolve(repo, args.support_cell_audit).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    row_output = resolve(repo, args.row_output).resolve()
    group_output = resolve(repo, args.group_output).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    residual_audit = pd.read_csv(residual_audit_path)
    residual_summary = read_json(residual_summary_path)
    used = bool_series(residual_audit, "used_in_objective")
    active = residual_audit[used].copy()
    active["log10_residual_pred_minus_obs"] = pd.to_numeric(
        active["log10_residual_pred_minus_obs"],
        errors="coerce",
    )
    active = active[np.isfinite(active["log10_residual_pred_minus_obs"])].copy()
    active["objective_weight"] = pd.to_numeric(active["objective_weight"], errors="coerce").fillna(0.0)
    active["abs_log10_residual"] = active["log10_residual_pred_minus_obs"].abs()
    active["normalized_residual"] = active["log10_residual_pred_minus_obs"] / args.log10_sigma

    if active.empty:
        raise SystemExit("No active finite direct permeability rows found in residual audit.")

    row_audit = build_row_audit(
        active,
        sigma=args.log10_sigma,
        cap_abs_log10=args.cap_abs_log10,
        huber_delta=args.huber_delta_normalized,
        student_nu=args.student_t_nu,
    )
    group_summary = build_group_summary(active, sigma=args.log10_sigma)
    policy_summary = build_policy_summary(
        active,
        row_audit,
        group_summary,
        sigma=args.log10_sigma,
        cap_abs_log10=args.cap_abs_log10,
        huber_delta=args.huber_delta_normalized,
        student_nu=args.student_t_nu,
    )

    residual = active["log10_residual_pred_minus_obs"].astype(float).to_numpy()
    weights = active["objective_weight"].astype(float).to_numpy()
    gaussian_losses = row_audit["gaussian_row_loss"].astype(float).to_numpy()
    dominance = loss_dominance(gaussian_losses)
    group_loss_share = 0.0
    if not group_summary.empty:
        total_group_loss = float(group_summary["current_row_gaussian_loss"].sum())
        if total_group_loss > 0.0:
            group_loss_share = float(group_summary["current_row_gaussian_loss"].head(2).sum() / total_group_loss)

    current_policy = policy_summary[policy_summary["policy_id"].eq("current_duplicate_weighted_gaussian")].iloc[0]
    support_mean_policy = policy_summary[
        policy_summary["policy_id"].eq("support_cell_weighted_mean_unit_gaussian")
    ]
    summary = {
        "status": "permeability_likelihood_policy_audit_generated",
        "residual_audit_csv": str(residual_audit_path),
        "residual_summary_json": str(residual_summary_path),
        "support_cell_audit_csv": str(support_cell_path),
        "log10_sigma": args.log10_sigma,
        "huber_delta_normalized": args.huber_delta_normalized,
        "student_t_nu": args.student_t_nu,
        "cap_abs_log10": args.cap_abs_log10,
        "active_direct_rows": int(active.shape[0]),
        "effective_objective_weight": float(np.sum(weights)),
        "current_gaussian_objective": float(current_policy["objective_like_value"]),
        "current_weighted_rmse_log10": weighted_rmse(residual, weights),
        "current_weighted_mae_log10": weighted_mae(residual, weights),
        "current_max_abs_log10": float(np.max(np.abs(residual))),
        "large_residual_active_rows_ge_1_log10": int((np.abs(residual) >= 1.0).sum()),
        "very_large_residual_active_rows_ge_2_log10": int((np.abs(residual) >= 2.0).sum()),
        "active_rows_outside_configured_scalar_range": int(
            (~active["configured_scalar_feasibility_status"].astype(str).eq("observed_inside_configured_scalar_range")).sum()
        ),
        "support_group_count": int(group_summary.shape[0]),
        "support_groups_with_repeated_rows": int((group_summary["row_count"] > 1).sum()) if not group_summary.empty else 0,
        "support_groups_with_observed_range_ge_1_log10": int(
            (group_summary["observed_log10_range"] >= 1.0).sum()
        ) if not group_summary.empty else 0,
        "support_groups_with_observed_range_ge_2_log10": int(
            (group_summary["observed_log10_range"] >= 2.0).sum()
        ) if not group_summary.empty else 0,
        "row_loss_top_5_share": dominance["top_5_share"],
        "row_loss_top_10_share": dominance["top_10_share"],
        "top_2_support_group_loss_share": group_loss_share,
        "policy_comparison_rows": int(policy_summary.shape[0]),
        "support_mean_unit_objective": float(support_mean_policy.iloc[0]["objective_like_value"])
        if not support_mean_policy.empty
        else math.nan,
        "support_median_unit_objective": float(
            policy_summary[
                policy_summary["policy_id"].eq("support_cell_weighted_median_unit_gaussian")
            ].iloc[0]["objective_like_value"]
        )
        if policy_summary["policy_id"].eq("support_cell_weighted_median_unit_gaussian").any()
        else math.nan,
        "robust_huber_delta_2sigma_objective": float(
            policy_summary[policy_summary["policy_id"].eq("huber_delta_2sigma")].iloc[0]["objective_like_value"]
        ),
        "robust_student_t_nu4_objective": float(
            policy_summary[policy_summary["policy_id"].eq("student_t_nu4")].iloc[0]["objective_like_value"]
        ),
        "residual_conflict_interpretation": residual_summary.get("interpretation"),
        "notes": [
            "Objective-like values are comparable within a policy family but robust policies omit normalization constants.",
            "Support-cell aggregation is a diagnostic because it assumes rows sharing one model support cell should not be fitted independently.",
            "The active objective remains the duplicate-weighted Gaussian row policy unless the modelling team explicitly changes it.",
        ],
        "output_csv": str(output_csv),
        "row_output_csv": str(row_output),
        "group_output_csv": str(group_output),
        "summary_output_json": str(summary_output),
        "summary_markdown": str(markdown_output),
    }
    summary["recommendation"] = recommendation(summary)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    policy_summary.to_csv(output_csv, index=False)
    row_audit.to_csv(row_output, index=False)
    group_summary.to_csv(group_output, index=False)
    write_markdown(markdown_output, summary, policy_summary, group_summary, row_audit)
    summary["catalogue_copies"] = copy_catalogue_artifacts(
        catalogue_dir,
        [output_csv, row_output, group_output, markdown_output],
        repo,
    )
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, summary, policy_summary, group_summary, row_audit)
    copy_catalogue_artifacts(catalogue_dir, [summary_output, markdown_output], repo)

    print(f"wrote {output_csv}")
    print(f"wrote {row_output}")
    print(f"wrote {group_output}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")
    print(f"current Gaussian objective: {summary['current_gaussian_objective']:.6g}")
    print(f"support-cell weighted-mean objective: {summary['support_mean_unit_objective']:.6g}")
    print(f"top 10 row-loss share: {summary['row_loss_top_10_share']:.3f}")


if __name__ == "__main__":
    main()
