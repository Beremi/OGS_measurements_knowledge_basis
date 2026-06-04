#!/usr/bin/env python3
"""Build a local disposition for direct-permeability configured-scalar outliers."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.csv"),
    )
    parser.add_argument(
        "--support-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_support_cell_audit.csv"),
    )
    parser.add_argument(
        "--semantics-csv",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_measurement_semantics_audit.csv"),
    )
    parser.add_argument(
        "--likelihood-row-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_row_audit.csv"),
    )
    parser.add_argument(
        "--policy-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_configured_scalar_outlier_disposition.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/permeability_configured_scalar_outlier_disposition.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit/derived_files"),
    )
    return parser.parse_args()


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


def fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    if abs(number) < 1.0e-5 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.{digits}g}"


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def first_cell_id(value: Any) -> str:
    text = str(value)
    if not text or text.lower() == "nan":
        return ""
    return text.split(";")[0].split(",")[0].split()[0].replace(".0", "")


def classification(row: pd.Series) -> str:
    excess = abs(float(row.get("range_excess_log10", 0.0) or 0.0))
    support_range = float(row.get("support_observed_range_log10", 0.0) or 0.0)
    duplicate_total = int(row.get("same_physical_value_row_count", 1) or 1)
    if excess <= 0.25 and support_range >= 2.0 and duplicate_total > 1:
        return "minor_upper_envelope_duplicate_inside_major_same_support_conflict"
    if excess <= 0.25 and support_range >= 2.0:
        return "minor_upper_envelope_row_inside_major_same_support_conflict"
    if excess <= 0.25:
        return "minor_configured_scalar_envelope_excess"
    if support_range >= 2.0:
        return "large_support_conflict_with_scalar_envelope_excess"
    return "configured_scalar_envelope_excess_requires_policy_decision"


def build_disposition(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    residual = pd.read_csv(args.residual_csv)
    support = pd.read_csv(args.support_csv)
    semantics = pd.read_csv(args.semantics_csv)
    likelihood_rows = pd.read_csv(args.likelihood_row_csv)
    policy_summary = read_json(args.policy_summary)

    residual = residual.copy()
    residual["used_in_objective_bool"] = as_bool(residual["used_in_objective"])
    residual["primary_support_cell_id"] = residual["support_cell_ids"].map(first_cell_id)
    active = residual[
        residual["used_in_objective_bool"]
        & residual["configured_scalar_feasibility_status"].astype(str).str.contains(
            "observed_above|observed_below", regex=True, na=False
        )
    ].copy()

    support = support.rename(
        columns={
            "primary_cell_id": "primary_support_cell_id",
            "observed_log10_range": "support_observed_range_log10",
            "row_count": "same_support_row_count",
        }
    )
    support["primary_support_cell_id"] = support["primary_support_cell_id"].astype(str)

    semantics = semantics[
        [
            "observation_id",
            "source_file",
            "source_sheet",
            "source_row_1based",
            "measured_physical_quantity",
            "model_comparison_quantity",
            "not_a_direct_measurement_of",
            "key_caveats",
        ]
    ].copy()

    likelihood_rows = likelihood_rows[
        [
            "observation_id",
            "gaussian_row_loss",
            "gaussian_row_loss_share",
            "capped_abs1_log10_row_loss",
            "student_t_nu4_row_loss",
            "policy_class",
        ]
    ].rename(
        columns={
            "gaussian_row_loss": "current_row_gaussian_loss",
            "gaussian_row_loss_share": "current_loss_share",
            "capped_abs1_log10_row_loss": "capped_gaussian_loss",
            "student_t_nu4_row_loss": "student_t_loss",
            "policy_class": "policy_row_class",
        }
    )

    rows = active.merge(
        support[
            [
                "primary_support_cell_id",
                "same_support_row_count",
                "depth_min_m",
                "depth_max_m",
                "observed_log10_min",
                "observed_log10_max",
                "support_observed_range_log10",
                "feasibility_statuses",
                "residual_signs",
            ]
        ],
        on="primary_support_cell_id",
        how="left",
    )
    rows = rows.merge(semantics, on="observation_id", how="left", suffixes=("", "_semantics"))
    rows = rows.merge(likelihood_rows, on="observation_id", how="left")

    rows["physical_value_key"] = (
        rows["normalized_segment_label"].astype(str)
        + "|"
        + rows["borehole_depth_m"].round(3).astype(str)
        + "|"
        + rows["observed_log10_permeability_m2"].round(12).astype(str)
        + "|"
        + rows["primary_support_cell_id"].astype(str)
    )
    duplicate_counts = rows.groupby("physical_value_key")["observation_id"].transform("count")
    rows["same_physical_value_row_count"] = duplicate_counts.astype(int)

    rows["range_excess_direction"] = np.where(
        rows["configured_scalar_feasibility_status"].eq("observed_above_configured_scalar_range"),
        "above_configured_upper_log10",
        "below_configured_lower_log10",
    )
    rows["range_excess_log10"] = np.where(
        rows["range_excess_direction"].eq("above_configured_upper_log10"),
        rows["observed_log10_permeability_m2"] - rows["configured_scalar_feasible_log10_max"],
        rows["configured_scalar_feasible_log10_min"] - rows["observed_log10_permeability_m2"],
    )
    rows["range_excess_factor"] = np.power(10.0, rows["range_excess_log10"])
    rows["same_support_range_factor"] = np.power(10.0, rows["support_observed_range_log10"])
    rows["local_classification"] = rows.apply(classification, axis=1)
    rows["recommended_local_disposition"] = (
        "Keep the row visible and included under the current rowwise Gaussian default, "
        "but mark it as a minor configured-upper-envelope exceedance embedded in a major same-support conflict; "
        "do not release tensor bounds or tensor shape from this duplicate row alone."
    )
    rows["policy_reopen_condition"] = (
        "A modelling-team decision must either accept this local disposition, choose a capped/robust row policy, "
        "aggregate by support cell, or explicitly release bounds/tensor shape before using the row to justify new OGS spending."
    )
    rows["same_support_context"] = (
        "The same OGS support cell contains high and low active pulse-test values with opposite residual signs; "
        "same-support spatial sampling cannot resolve that contradiction."
    )
    unique_groups = rows["physical_value_key"].nunique()

    selected_columns = [
        "observation_id",
        "source_file",
        "source_sheet",
        "source_row_1based",
        "normalized_segment_label",
        "borehole_depth_m",
        "primary_support_cell_id",
        "observed_log10_permeability_m2",
        "predicted_log10_permeability_m2",
        "log10_residual_pred_minus_obs",
        "abs_log10_residual",
        "configured_scalar_feasible_log10_min",
        "configured_scalar_feasible_log10_max",
        "range_excess_direction",
        "range_excess_log10",
        "range_excess_factor",
        "same_support_row_count",
        "support_observed_range_log10",
        "same_support_range_factor",
        "same_physical_value_row_count",
        "current_row_gaussian_loss",
        "current_loss_share",
        "capped_gaussian_loss",
        "student_t_loss",
        "policy_row_class",
        "measured_physical_quantity",
        "model_comparison_quantity",
        "not_a_direct_measurement_of",
        "key_caveats",
        "local_classification",
        "recommended_local_disposition",
        "policy_reopen_condition",
        "same_support_context",
    ]
    rows = rows[selected_columns].sort_values(["primary_support_cell_id", "borehole_depth_m", "observation_id"])

    row_loss_sum = float(pd.to_numeric(rows["current_row_gaussian_loss"], errors="coerce").sum())
    current_objective = float(policy_summary.get("current_gaussian_objective", np.nan))
    row_loss_share = row_loss_sum / current_objective if np.isfinite(current_objective) and current_objective else None
    class_counts = rows["local_classification"].value_counts().sort_index().to_dict()
    max_excess = float(pd.to_numeric(rows["range_excess_log10"], errors="coerce").max()) if not rows.empty else 0.0
    max_support_range = (
        float(pd.to_numeric(rows["support_observed_range_log10"], errors="coerce").max()) if not rows.empty else 0.0
    )
    summary = {
        "status": "permeability_configured_scalar_outlier_disposition_generated",
        "outlier_row_count": int(rows.shape[0]),
        "unique_physical_outlier_group_count": int(unique_groups),
        "classification_counts": class_counts,
        "max_range_excess_log10": max_excess,
        "max_range_excess_factor": float(10.0**max_excess),
        "max_same_support_observed_range_log10": max_support_range,
        "max_same_support_observed_range_factor": float(10.0**max_support_range),
        "current_row_gaussian_loss_from_outlier_rows": row_loss_sum,
        "current_row_gaussian_loss_share_from_outlier_rows": row_loss_share,
        "bounds_release_recommended_now": False,
        "tensor_shape_release_recommended_now": False,
        "same_support_active_objective_batch_reopened_by_this_disposition": False,
        "recommended_disposition": (
            "Record the two active scalar-envelope outlier rows as one duplicated high-permeability BCD-A32 "
            "support-cell value that is only slightly above the configured upper envelope, but embedded in a much "
            "larger same-support conflict with a low-permeability row. Keep the active rowwise Gaussian objective "
            "unchanged for reproducibility; do not widen bounds or release tensor shape on this evidence alone."
        ),
        "remaining_policy_decision": (
            "Before new OGS spending or final promotion, the modelling team still has to accept this local disposition "
            "or choose a robust/capped/support-aggregation/outlier policy explicitly."
        ),
        "source_artifacts": [
            str(args.residual_csv),
            str(args.support_csv),
            str(args.semantics_csv),
            str(args.likelihood_row_csv),
            str(args.policy_summary),
        ],
    }
    return rows, summary


def write_outputs(rows: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Permeability Configured-Scalar Outlier Disposition",
        "",
        "This artifact classifies the active direct-permeability rows that fall outside",
        "the configured scalar tensor envelope. It is a local disposition record only:",
        "it does not change the active objective, run OGS, or modify the frozen GESA model.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Active outlier rows: {summary['outlier_row_count']}",
        f"- Unique physical outlier groups: {summary['unique_physical_outlier_group_count']}",
        f"- Max envelope excess: {fmt(summary['max_range_excess_log10'], 3)} log10 "
        f"(factor {fmt(summary['max_range_excess_factor'], 3)})",
        f"- Max same-support observed range: {fmt(summary['max_same_support_observed_range_log10'], 3)} log10 "
        f"(factor {fmt(summary['max_same_support_observed_range_factor'], 3)})",
        f"- Bounds release recommended now: {summary['bounds_release_recommended_now']}",
        f"- Tensor-shape release recommended now: {summary['tensor_shape_release_recommended_now']}",
        "",
        "## Disposition",
        "",
        summary["recommended_disposition"],
        "",
        summary["remaining_policy_decision"],
        "",
        "## Row Table",
        "",
        "| Observation | Source | Segment | Depth m | Cell | Observed log10 | Feasible max log10 | Excess log10 | Residual log10 | Support range log10 | Classification |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows.to_dict(orient="records"):
        source = f"{Path(str(row['source_file'])).name}:{row['source_sheet']}:{row['source_row_1based']}"
        lines.append(
            f"| `{row['observation_id']}` | `{source}` | `{row['normalized_segment_label']}` | "
            f"{fmt(row['borehole_depth_m'], 3)} | `{row['primary_support_cell_id']}` | "
            f"{fmt(row['observed_log10_permeability_m2'], 4)} | "
            f"{fmt(row['configured_scalar_feasible_log10_max'], 4)} | "
            f"{fmt(row['range_excess_log10'], 4)} | {fmt(row['log10_residual_pred_minus_obs'], 4)} | "
            f"{fmt(row['support_observed_range_log10'], 4)} | `{row['local_classification']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The two rows are the same BCD-A32 0.87 m high-permeability value recorded in two source workbooks.",
            "- The value is only about 0.107 log10 above the configured scalar upper envelope, but it shares model support cell 4648 with an active low-permeability row near 0.85 m.",
            "- The same-support spread is about 6.949 log10, so the dominant problem is not this small envelope exceedance; it is incompatible row-level pulse-test values mapped to one OGS support cell.",
            "- The local recommendation is therefore no immediate eigenvalue-bound widening or tensor-shape release from these rows alone. Treat them through an explicit likelihood/support decision before any new OGS spending.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.catalogue_dir:
        args.catalogue_dir.mkdir(parents=True, exist_ok=True)
        generated = [args.output_csv, args.output_json, args.output_md]
        copies = []
        for path in generated:
            target = args.catalogue_dir / path.name
            shutil.copy2(path, target)
            copies.append({"source": str(path), "catalogue_copy": str(target)})
        summary["catalogue_copies"] = copies
        args.output_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


def main() -> None:
    args = parse_args()
    rows, summary = build_disposition(args)
    write_outputs(rows, summary, args)


if __name__ == "__main__":
    main()
