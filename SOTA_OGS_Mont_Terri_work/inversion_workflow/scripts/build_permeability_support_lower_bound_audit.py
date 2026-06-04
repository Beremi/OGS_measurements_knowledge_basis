#!/usr/bin/env python3
"""Audit the irreducible direct-permeability loss under the current support map.

This script is a no-OGS diagnostic.  It asks whether the remaining rowwise
pulse-test mismatch can still be reduced by another field that assigns one
effective permeability prediction to each current model support cell.  If the
current prediction equals the duplicate-weighted observed mean for each support
cell, the row-Gaussian loss is already at its single-support-value lower bound
and further same-support field sampling cannot improve that part of the
objective.
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
        "--likelihood-policy-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"),
    )
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--lower-bound-tolerance", type=float, default=1.0e-9)
    parser.add_argument(
        "--group-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_lower_bound_audit.csv"),
    )
    parser.add_argument(
        "--row-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_lower_bound_row_audit.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_lower_bound_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_support_lower_bound_audit"),
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


def finite_weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    values_array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    weights_array = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(values_array) & np.isfinite(weights_array) & (weights_array > 0.0)
    if not mask.any():
        return math.nan
    return float(np.average(values_array[mask], weights=weights_array[mask]))


def gaussian_loss(residual_log10: np.ndarray, weights: np.ndarray, sigma: float) -> np.ndarray:
    return 0.5 * weights * (residual_log10 / sigma) ** 2


def group_class(row: dict[str, Any], tolerance: float) -> str:
    if row["current_minus_lower_bound_loss"] > tolerance:
        return "same_support_field_still_reducible"
    if row["observed_log10_range"] >= 2.0:
        return "irreducible_large_same_support_conflict"
    if row["observed_log10_range"] >= 1.0:
        return "irreducible_moderate_same_support_conflict"
    return "single_support_value_lower_bound_met"


def build_lower_bound_tables(
    residual_audit: pd.DataFrame,
    *,
    sigma: float,
    tolerance: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    active = residual_audit[residual_audit["used_in_objective"].map(bool_value)].copy()
    numeric_columns = [
        "observed_log10_permeability_m2",
        "predicted_log10_permeability_m2",
        "log10_residual_pred_minus_obs",
        "objective_weight",
        "borehole_depth_m",
    ]
    for column in numeric_columns:
        active[column] = pd.to_numeric(active[column], errors="coerce")
    active = active[
        np.isfinite(active["observed_log10_permeability_m2"])
        & np.isfinite(active["predicted_log10_permeability_m2"])
        & np.isfinite(active["objective_weight"])
        & (active["objective_weight"] > 0.0)
    ].copy()
    if active.empty:
        raise SystemExit("No active finite direct permeability rows found.")

    support_source = active["support_cell_ids"] if "support_cell_ids" in active.columns else active["selected_cell_ids"]
    active["primary_support_cell_id"] = support_source.map(first_cell_id)
    active = active[active["primary_support_cell_id"].notna()].copy()
    active["primary_support_cell_id"] = active["primary_support_cell_id"].astype(int)
    if active.empty:
        raise SystemExit("No active permeability rows have support-cell ids.")

    row_records: list[dict[str, Any]] = []
    group_records: list[dict[str, Any]] = []
    for cell_id, group in active.groupby("primary_support_cell_id", sort=True):
        observed = group["observed_log10_permeability_m2"].to_numpy(dtype=float)
        predicted = group["predicted_log10_permeability_m2"].to_numpy(dtype=float)
        weights = group["objective_weight"].to_numpy(dtype=float)
        best_prediction = finite_weighted_mean(group["observed_log10_permeability_m2"], group["objective_weight"])
        current_prediction = finite_weighted_mean(group["predicted_log10_permeability_m2"], group["objective_weight"])
        current_losses = gaussian_loss(predicted - observed, weights, sigma)
        lower_losses = gaussian_loss(best_prediction - observed, weights, sigma)
        current_loss = float(np.sum(current_losses))
        lower_bound_loss = float(np.sum(lower_losses))
        current_minus_lower = current_loss - lower_bound_loss
        group_row = {
            "primary_support_cell_id": int(cell_id),
            "row_count": int(group.shape[0]),
            "effective_objective_weight": float(np.sum(weights)),
            "segments": ";".join(sorted(set(group["normalized_segment_label"].astype(str)))),
            "source_sheets": ";".join(sorted(set(group["source_sheet"].astype(str)))),
            "campaign_years": ";".join(sorted(set(group["campaign_year"].astype(str)))),
            "depth_min_m": float(np.nanmin(group["borehole_depth_m"])),
            "depth_max_m": float(np.nanmax(group["borehole_depth_m"])),
            "observed_log10_min": float(np.nanmin(observed)),
            "observed_log10_max": float(np.nanmax(observed)),
            "observed_log10_range": float(np.nanmax(observed) - np.nanmin(observed)),
            "best_single_support_prediction_log10": best_prediction,
            "current_weighted_prediction_log10": current_prediction,
            "prediction_minus_best_log10": current_prediction - best_prediction,
            "current_row_gaussian_loss": current_loss,
            "single_support_lower_bound_loss": lower_bound_loss,
            "current_minus_lower_bound_loss": current_minus_lower,
            "current_at_lower_bound": bool(abs(current_minus_lower) <= tolerance),
            "configured_scalar_feasibility_statuses": ";".join(
                sorted(set(group["configured_scalar_feasibility_status"].astype(str)))
            ),
            "residual_signs": ";".join(sorted(set(group["residual_sign"].astype(str)))),
        }
        group_row["support_lower_bound_class"] = group_class(group_row, tolerance)
        group_records.append(group_row)
        for (index, row), current_row_loss, lower_row_loss in zip(group.iterrows(), current_losses, lower_losses):
            row_records.append(
                {
                    "observation_id": row["observation_id"],
                    "primary_support_cell_id": int(cell_id),
                    "source_sheet": row.get("source_sheet", ""),
                    "campaign_year": row.get("campaign_year", ""),
                    "normalized_segment_label": row.get("normalized_segment_label", ""),
                    "borehole_depth_m": row.get("borehole_depth_m", math.nan),
                    "observed_log10_permeability_m2": row["observed_log10_permeability_m2"],
                    "current_predicted_log10_permeability_m2": row["predicted_log10_permeability_m2"],
                    "best_single_support_prediction_log10": best_prediction,
                    "current_log10_residual_pred_minus_obs": row["predicted_log10_permeability_m2"]
                    - row["observed_log10_permeability_m2"],
                    "lower_bound_log10_residual_pred_minus_obs": best_prediction
                    - row["observed_log10_permeability_m2"],
                    "objective_weight": row["objective_weight"],
                    "current_row_gaussian_loss": float(current_row_loss),
                    "single_support_lower_bound_row_loss": float(lower_row_loss),
                    "configured_scalar_feasibility_status": row.get("configured_scalar_feasibility_status", ""),
                    "residual_sign": row.get("residual_sign", ""),
                    "recommended_next_action": row.get("recommended_next_action", ""),
                }
            )

    group_table = pd.DataFrame(group_records).sort_values(
        ["current_row_gaussian_loss", "observed_log10_range", "primary_support_cell_id"],
        ascending=[False, False, True],
    )
    row_table = pd.DataFrame(row_records).sort_values(
        ["current_row_gaussian_loss", "observation_id"],
        ascending=[False, True],
    )
    total_current = float(group_table["current_row_gaussian_loss"].sum())
    total_lower = float(group_table["single_support_lower_bound_loss"].sum())
    total_gap = total_current - total_lower
    if total_current > 0.0:
        group_table["current_row_gaussian_loss_share"] = group_table["current_row_gaussian_loss"] / total_current
    else:
        group_table["current_row_gaussian_loss_share"] = math.nan

    class_counts = group_table["support_lower_bound_class"].value_counts().sort_index().to_dict()
    summary = {
        "active_direct_rows": int(active.shape[0]),
        "support_group_count": int(group_table.shape[0]),
        "repeated_support_group_count": int((group_table["row_count"] > 1).sum()),
        "support_groups_with_observed_range_ge_1_log10": int((group_table["observed_log10_range"] >= 1.0).sum()),
        "support_groups_with_observed_range_ge_2_log10": int((group_table["observed_log10_range"] >= 2.0).sum()),
        "current_row_gaussian_objective": total_current,
        "single_support_lower_bound_objective": total_lower,
        "same_support_reducible_objective_gap": total_gap,
        "same_support_reducible_objective_fraction": float(total_gap / total_current) if total_current > 0.0 else math.nan,
        "current_at_single_support_lower_bound": bool(abs(total_gap) <= tolerance),
        "support_groups_current_at_lower_bound": int(group_table["current_at_lower_bound"].sum()),
        "support_groups_reducible_above_tolerance": int((~group_table["current_at_lower_bound"]).sum()),
        "top_2_support_group_loss_share": float(group_table["current_row_gaussian_loss_share"].head(2).sum())
        if total_current > 0.0
        else math.nan,
        "top_5_support_group_loss_share": float(group_table["current_row_gaussian_loss_share"].head(5).sum())
        if total_current > 0.0
        else math.nan,
        "support_lower_bound_class_counts": class_counts,
    }
    return group_table, row_table, summary


def write_markdown(
    path: Path,
    summary: dict[str, Any],
    groups: pd.DataFrame,
    rows: pd.DataFrame,
) -> None:
    lines = [
        "# Permeability Support Lower-Bound Audit",
        "",
        "This audit quantifies the part of the active direct pulse-test objective that cannot be reduced by",
        "another permeability field as long as rows sharing the same current OGS support cell are fitted by",
        "one effective support value. It does not change the active objective and does not run OGS.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Active direct rows: {summary['active_direct_rows']}",
        f"- Support groups: {summary['support_group_count']}",
        f"- Repeated support groups: {summary['repeated_support_group_count']}",
        f"- Support groups with observed range >= 1 log10: {summary['support_groups_with_observed_range_ge_1_log10']}",
        f"- Support groups with observed range >= 2 log10: {summary['support_groups_with_observed_range_ge_2_log10']}",
        f"- Current row-Gaussian objective: {summary['current_row_gaussian_objective']:.6f}",
        f"- Single-support lower-bound objective: {summary['single_support_lower_bound_objective']:.6f}",
        f"- Same-support reducible objective gap: {summary['same_support_reducible_objective_gap']:.6g}",
        f"- Same-support reducible fraction: {summary['same_support_reducible_objective_fraction']:.6g}",
        f"- Current field at lower bound: {summary['current_at_single_support_lower_bound']}",
        f"- Top two support-group loss share: {summary['top_2_support_group_loss_share']:.3f}",
        f"- Top five support-group loss share: {summary['top_5_support_group_loss_share']:.3f}",
        "",
        "## Dominant Support Groups",
        "",
        "| Cell | Rows | Segment | Depth range [m] | Observed range | Current loss | Lower-bound loss | Reducible gap | Class |",
        "| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in groups.head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["primary_support_cell_id"])),
                    str(int(row["row_count"])),
                    f"`{row['segments']}`",
                    f"{float(row['depth_min_m']):.2f}-{float(row['depth_max_m']):.2f}",
                    f"{float(row['observed_log10_range']):.3f}",
                    f"{float(row['current_row_gaussian_loss']):.3f}",
                    f"{float(row['single_support_lower_bound_loss']):.3f}",
                    f"{float(row['current_minus_lower_bound_loss']):.3g}",
                    str(row["support_lower_bound_class"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Dominant Rows",
            "",
            "| Observation | Cell | Segment | Depth [m] | Observed | Current pred. | Lower-bound pred. | Current loss | Lower-bound loss |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in rows.head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['observation_id']}`",
                    str(int(row["primary_support_cell_id"])),
                    f"`{row['normalized_segment_label']}`",
                    f"{float(row['borehole_depth_m']):.2f}",
                    f"{float(row['observed_log10_permeability_m2']):.3f}",
                    f"{float(row['current_predicted_log10_permeability_m2']):.3f}",
                    f"{float(row['best_single_support_prediction_log10']):.3f}",
                    f"{float(row['current_row_gaussian_loss']):.3f}",
                    f"{float(row['single_support_lower_bound_row_loss']):.3f}",
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
            f"- Group audit: `{summary['group_output_csv']}`",
            f"- Row audit: `{summary['row_output_csv']}`",
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
    likelihood_summary_path = resolve(repo, args.likelihood_policy_summary).resolve()
    group_output = resolve(repo, args.group_output).resolve()
    row_output = resolve(repo, args.row_output).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    residual_audit = pd.read_csv(residual_audit_path)
    likelihood_summary = read_json(likelihood_summary_path)
    groups, rows, summary_numbers = build_lower_bound_tables(
        residual_audit,
        sigma=args.log10_sigma,
        tolerance=args.lower_bound_tolerance,
    )

    summary: dict[str, Any] = {
        "status": "permeability_support_lower_bound_audit_generated",
        "residual_audit_csv": str(residual_audit_path),
        "likelihood_policy_summary_json": str(likelihood_summary_path),
        "log10_sigma": args.log10_sigma,
        "lower_bound_tolerance": args.lower_bound_tolerance,
        **summary_numbers,
        "likelihood_policy_current_gaussian_objective": likelihood_summary.get("current_gaussian_objective"),
        "likelihood_policy_support_mean_unit_objective": likelihood_summary.get("support_mean_unit_objective"),
        "notes": [
            "The lower bound assumes the current observation-to-support-cell mapping and one scalar log10 prediction per support cell.",
            "A zero reducible gap does not prove the gas-pulse interpretation is correct; it proves same-support field sampling cannot reduce the rowwise Gaussian loss.",
            "Reducing this loss requires changing support mapping, likelihood semantics, measurement interpretation, or parameter bounds/tensor shape, not more same-family OGS sampling.",
        ],
        "group_output_csv": str(group_output),
        "row_output_csv": str(row_output),
        "summary_output_json": str(summary_output),
        "summary_markdown": str(markdown_output),
    }
    if summary["current_at_single_support_lower_bound"]:
        summary["interpretation"] = (
            "The current accepted permeability field is already at the duplicate-weighted row-Gaussian lower bound "
            "for the current one-value-per-support-cell mapping. The direct permeability mismatch is therefore "
            "irreducible by additional same-support spatial sampling: the dominant loss comes from mutually "
            "inconsistent pulse-test values assigned to the same model support cells, plus the separate configured "
            "scalar-range cases. The next defensible move is a support/likelihood/measurement-interpretation or "
            "bounds/tensor-shape decision, not another routine OGS batch in the same parameter family."
        )
    else:
        summary["interpretation"] = (
            "Some direct permeability loss remains reducible under the current one-value-per-support-cell mapping. "
            "Before treating the residual as a likelihood/support issue, inspect the reducible support groups and "
            "decide whether another field family can target them without changing measurement semantics."
        )

    group_output.parent.mkdir(parents=True, exist_ok=True)
    groups.to_csv(group_output, index=False)
    rows.to_csv(row_output, index=False)
    write_markdown(markdown_output, summary, groups, rows)
    summary["catalogue_copies"] = copy_catalogue_artifacts(
        catalogue_dir,
        [group_output, row_output, markdown_output],
        repo,
    )
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, summary, groups, rows)
    copy_catalogue_artifacts(catalogue_dir, [summary_output, markdown_output], repo)

    print(f"wrote {group_output}")
    print(f"wrote {row_output}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")
    print(f"current objective: {summary['current_row_gaussian_objective']:.6g}")
    print(f"single-support lower bound: {summary['single_support_lower_bound_objective']:.6g}")
    print(f"reducible same-support gap: {summary['same_support_reducible_objective_gap']:.6g}")


if __name__ == "__main__":
    main()
