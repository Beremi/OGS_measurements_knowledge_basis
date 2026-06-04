#!/usr/bin/env python3
"""Build a detailed semantics audit for Taupe/TDR EDZ-band observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/taupe_tdr"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


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
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    return value


def quantiles(series: pd.Series) -> dict[str, float | None]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {key: None for key in ["min", "p10", "p25", "p50", "p75", "p90", "max"]}
    return {
        "min": float(clean.min()),
        "p10": float(clean.quantile(0.10)),
        "p25": float(clean.quantile(0.25)),
        "p50": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p90": float(clean.quantile(0.90)),
        "max": float(clean.max()),
    }


def value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {
        str(key): int(value)
        for key, value in frame[column].fillna("missing").value_counts().sort_index().items()
    }


def bool_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def numeric_stat(series: pd.Series, stat: str) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    if stat == "min":
        return float(clean.min())
    if stat == "median":
        return float(clean.median())
    if stat == "max":
        return float(clean.max())
    raise ValueError(f"unsupported numeric stat: {stat}")


def taupe_targets(state_targets: pd.DataFrame) -> pd.DataFrame:
    if state_targets.empty or "observation_family" not in state_targets.columns:
        return pd.DataFrame()
    return state_targets[state_targets["observation_family"].astype(str).eq("Taupe/TDR")].copy()


def classify_gate(row: pd.Series) -> str:
    mapping = str(row.get("mapping_status", ""))
    operator = str(row.get("operator_status", ""))
    if mapping == "mapped_band_samples" or operator == "trend_operator_ready_absolute_calibration_pending":
        return "trend_diagnostic_ready_pending_ogs_outputs_absolute_calibration_blocked"
    if mapping == "band_samples_outside_mesh":
        return "excluded_current_mesh_outside_support"
    if mapping in {"missing_segment_mapping", "no_segment_samples_in_band"}:
        return "excluded_pending_taupe_geometry_mapping"
    return "excluded_pending_manual_review"


def build_row_audit(operator: pd.DataFrame) -> pd.DataFrame:
    if operator.empty:
        return pd.DataFrame()
    frame = operator.copy()
    frame["semantic_activation_gate"] = frame.apply(classify_gate, axis=1)
    frame["measured_physical_quantity"] = (
        "Taupe/TDR EDZ-band workbook value: ARDP/dielectric water-content proxy with unit not confirmed"
    )
    frame["primary_model_quantity"] = "band-average theta_model = porosity * liquid_saturation"
    frame["recommended_residual"] = (
        "same-series standardized theta_model anomaly - taupe_standardized_anomaly"
    )
    frame["absolute_residual_status"] = (
        "blocked until Taupe_WC unit and sensor-specific dielectric/water-content calibration are confirmed"
    )
    frame["not_a_direct_measurement_of"] = (
        "absolute saturation; calibrated volumetric water content unless confirmed; permeability; pressure"
    )
    frame["first_model_use_after_ogs_outputs"] = (
        "compare baseline-normalized band-average theta_model trends for the same sensor, EDZ band, and date"
    )
    keep = [
        "source_file",
        "source_sheet",
        "sensor",
        "series_id",
        "date_iso",
        "source_column",
        "edz_band_cm",
        "edz_min_cm",
        "edz_max_cm",
        "segment_label",
        "band_sample_rows",
        "band_inside_sample_rows",
        "band_unique_cell_count",
        "band_mean_porosity",
        "band_min_porosity",
        "band_max_porosity",
        "mapping_status",
        "operator_status",
        "semantic_activation_gate",
        "taupe_value",
        "baseline_taupe_value",
        "baseline_date_min",
        "baseline_date_max",
        "taupe_delta_from_baseline",
        "taupe_relative_change_percent",
        "taupe_robust_scale",
        "taupe_standardized_anomaly",
        "measured_physical_quantity",
        "primary_model_quantity",
        "recommended_residual",
        "absolute_residual_status",
        "not_a_direct_measurement_of",
        "first_model_use_after_ogs_outputs",
        "theta_fraction_if_taupe_value_is_vol_percent",
        "saturation_if_taupe_value_is_vol_percent",
        "wc_percent_candidate_physical_saturation_0_1",
        "theta_fraction_if_taupe_value_is_topp_epsilon",
        "saturation_if_taupe_value_is_topp_epsilon",
        "topp_candidate_physical_saturation_0_1",
        "theta_fraction_if_linear_mixing_epsilon_rock_6",
        "saturation_if_linear_mixing_epsilon_rock_6",
        "linear_mixing_eps6_candidate_physical_saturation_0_1",
        "absolute_calibration_note",
    ]
    return frame[[column for column in keep if column in frame.columns]]


def summarize_series(row_audit: pd.DataFrame) -> pd.DataFrame:
    if row_audit.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for series_id, group in row_audit.groupby("series_id", sort=True):
        mapped_rows = int(group["mapping_status"].astype(str).eq("mapped_band_samples").sum())
        outside_rows = int(group["mapping_status"].astype(str).eq("band_samples_outside_mesh").sum())
        if mapped_rows == group.shape[0]:
            gate = "trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked"
        elif outside_rows == group.shape[0]:
            gate = "excluded_current_mesh_outside_support"
        else:
            gate = "mixed_mapping_status_review_before_use"
        rows.append(
            {
                "series_id": series_id,
                "sensor": str(group["sensor"].iloc[0]),
                "edz_band_cm": str(group["edz_band_cm"].iloc[0]),
                "row_count_from_operator": int(group.shape[0]),
                "date_min_from_operator": str(pd.to_datetime(group["date_iso"], errors="coerce").min().date()),
                "date_max_from_operator": str(pd.to_datetime(group["date_iso"], errors="coerce").max().date()),
                "mapping_statuses": "; ".join(sorted(group["mapping_status"].dropna().astype(str).unique())),
                "operator_statuses": "; ".join(sorted(group["operator_status"].dropna().astype(str).unique())),
                "semantic_activation_gate": gate,
                "mapped_trend_rows": mapped_rows,
                "outside_current_mesh_rows": outside_rows,
                "segment_labels": "; ".join(sorted(group["segment_label"].dropna().astype(str).unique())),
                "band_mean_porosity_min": numeric_stat(group["band_mean_porosity"], "min"),
                "band_mean_porosity_median": numeric_stat(group["band_mean_porosity"], "median"),
                "band_mean_porosity_max": numeric_stat(group["band_mean_porosity"], "max"),
                "taupe_value_min": numeric_stat(group["taupe_value"], "min"),
                "taupe_value_median": numeric_stat(group["taupe_value"], "median"),
                "taupe_value_max": numeric_stat(group["taupe_value"], "max"),
                "standardized_anomaly_min": numeric_stat(group["taupe_standardized_anomaly"], "min"),
                "standardized_anomaly_median": numeric_stat(group["taupe_standardized_anomaly"], "median"),
                "standardized_anomaly_max": numeric_stat(group["taupe_standardized_anomaly"], "max"),
                "wc_percent_candidate_physical_rows": bool_count(
                    group, "wc_percent_candidate_physical_saturation_0_1"
                ),
                "topp_candidate_physical_rows": bool_count(group, "topp_candidate_physical_saturation_0_1"),
                "linear_eps6_candidate_physical_rows": bool_count(
                    group, "linear_mixing_eps6_candidate_physical_saturation_0_1"
                ),
                "recommended_use": (
                    "trend diagnostic against same-series band-average theta_model anomaly"
                    if mapped_rows
                    else "retain as source data; outside current mesh support"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_series_audit(series: pd.DataFrame, row_audit: pd.DataFrame) -> pd.DataFrame:
    if series.empty and row_audit.empty:
        return pd.DataFrame()
    summary = summarize_series(row_audit)
    if series.empty:
        return summary
    if summary.empty:
        return series.copy()
    return series.merge(summary, on=["series_id", "sensor", "edz_band_cm"], how="left")


def summarize_group(group: pd.DataFrame, group_columns: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in group_columns:
        value = group[column].iloc[0]
        result[column] = "missing" if pd.isna(value) else value
    numeric = pd.to_numeric(group["taupe_value"], errors="coerce")
    anomaly = pd.to_numeric(group["taupe_standardized_anomaly"], errors="coerce")
    phi = pd.to_numeric(group["band_mean_porosity"], errors="coerce")
    result.update(
        {
            "rows": int(group.shape[0]),
            "mapped_trend_rows": int(group["mapping_status"].astype(str).eq("mapped_band_samples").sum()),
            "outside_current_mesh_rows": int(group["mapping_status"].astype(str).eq("band_samples_outside_mesh").sum()),
            "trend_ready_gate_rows": int(
                group["semantic_activation_gate"]
                .astype(str)
                .eq("trend_diagnostic_ready_pending_ogs_outputs_absolute_calibration_blocked")
                .sum()
            ),
            "wc_percent_candidate_physical_rows": bool_count(
                group, "wc_percent_candidate_physical_saturation_0_1"
            ),
            "topp_candidate_physical_rows": bool_count(group, "topp_candidate_physical_saturation_0_1"),
            "linear_eps6_candidate_physical_rows": bool_count(
                group, "linear_mixing_eps6_candidate_physical_saturation_0_1"
            ),
            "taupe_value_min": float(numeric.min()) if numeric.notna().any() else np.nan,
            "taupe_value_median": float(numeric.median()) if numeric.notna().any() else np.nan,
            "taupe_value_max": float(numeric.max()) if numeric.notna().any() else np.nan,
            "standardized_anomaly_min": float(anomaly.min()) if anomaly.notna().any() else np.nan,
            "standardized_anomaly_median": float(anomaly.median()) if anomaly.notna().any() else np.nan,
            "standardized_anomaly_max": float(anomaly.max()) if anomaly.notna().any() else np.nan,
            "band_mean_porosity_min": float(phi.min()) if phi.notna().any() else np.nan,
            "band_mean_porosity_median": float(phi.median()) if phi.notna().any() else np.nan,
            "band_mean_porosity_max": float(phi.max()) if phi.notna().any() else np.nan,
        }
    )
    return result


def build_group_summary(row_audit: pd.DataFrame) -> pd.DataFrame:
    if row_audit.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    group_specs = [
        ("semantic_activation_gate", ["semantic_activation_gate"]),
        ("mapping_status", ["mapping_status"]),
        ("operator_status", ["operator_status"]),
        ("sensor", ["sensor"]),
        ("edz_band", ["edz_band_cm"]),
        ("sensor_edz_band", ["sensor", "edz_band_cm"]),
        ("sensor_mapping", ["sensor", "mapping_status"]),
    ]
    for group_type, columns in group_specs:
        for _, group in row_audit.groupby(columns, dropna=False):
            summary = summarize_group(group, columns)
            summary["group_type"] = group_type
            summary["group_key"] = " | ".join(str(summary[column]) for column in columns)
            rows.append(summary)
    return pd.DataFrame(rows)


def build_summary(
    *,
    bands: pd.DataFrame,
    row_audit: pd.DataFrame,
    series_audit: pd.DataFrame,
    group_summary: pd.DataFrame,
    state_taupe: pd.DataFrame,
    operator_summary: dict[str, Any],
    outputs: dict[str, str],
    catalogue_dir: Path,
) -> dict[str, Any]:
    mapped = int(row_audit["mapping_status"].astype(str).eq("mapped_band_samples").sum()) if not row_audit.empty else 0
    outside = (
        int(row_audit["mapping_status"].astype(str).eq("band_samples_outside_mesh").sum())
        if not row_audit.empty
        else 0
    )
    sensors = sorted(row_audit["sensor"].dropna().astype(str).unique()) if not row_audit.empty else []
    edz_bands = sorted(row_audit["edz_band_cm"].dropna().astype(str).unique()) if not row_audit.empty else []
    trend_ready_series = (
        int(
            series_audit["semantic_activation_gate"]
            .astype(str)
            .eq("trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked")
            .sum()
        )
        if "semantic_activation_gate" in series_audit.columns
        else 0
    )
    outside_series = (
        int(series_audit["semantic_activation_gate"].astype(str).eq("excluded_current_mesh_outside_support").sum())
        if "semantic_activation_gate" in series_audit.columns
        else 0
    )
    source_workbook = (catalogue_dir / "source_files" / "Taupe_WC.xlsx").resolve()
    coordinate_workbook = (catalogue_dir / "source_files" / "Coordinates_NMR_Taupe_characborehole.xlsx").resolve()
    summary = {
        "status": "trend_semantics_ready_absolute_calibration_blocked",
        "workbook_rows": int(bands.shape[0]),
        "operator_rows": int(row_audit.shape[0]),
        "series_rows": int(series_audit.shape[0]),
        "trend_ready_series": trend_ready_series,
        "outside_current_mesh_series": outside_series,
        "date_min": operator_summary.get("date_min"),
        "date_max": operator_summary.get("date_max"),
        "sensors": sensors,
        "edz_bands_cm": edz_bands,
        "mapped_trend_rows": mapped,
        "outside_current_mesh_rows": outside,
        "semantic_activation_gate_counts": value_counts(row_audit, "semantic_activation_gate"),
        "mapping_status_counts": value_counts(row_audit, "mapping_status"),
        "operator_status_counts": value_counts(row_audit, "operator_status"),
        "state_target_rows": int(state_taupe.shape[0]),
        "state_target_status_counts": value_counts(state_taupe, "target_status"),
        "state_target_usable_rows": bool_count(state_taupe, "usable_for_current_state_fit"),
        "candidate_absolute_interpretation_physical_rows": {
            "taupe_value_as_vol_percent": bool_count(row_audit, "wc_percent_candidate_physical_saturation_0_1"),
            "taupe_value_as_topp_epsilon": bool_count(row_audit, "topp_candidate_physical_saturation_0_1"),
            "linear_mixing_epsilon_rock_6": bool_count(
                row_audit, "linear_mixing_eps6_candidate_physical_saturation_0_1"
            ),
        },
        "taupe_value_quantiles": quantiles(row_audit["taupe_value"]) if not row_audit.empty else {},
        "standardized_anomaly_quantiles": quantiles(row_audit["taupe_standardized_anomaly"]) if not row_audit.empty else {},
        "band_mean_porosity_quantiles": quantiles(row_audit["band_mean_porosity"]) if not row_audit.empty else {},
        "group_summary_rows": int(group_summary.shape[0]),
        "source_files": {
            "taupe_workbook": str(source_workbook),
            "coordinate_workbook": str(coordinate_workbook),
            "measurement_catalogue": str(catalogue_dir.resolve()),
        },
        "remaining_blocker": (
            "Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, "
            "apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute "
            "saturation or water-content residual weights."
        ),
        "outputs": outputs,
        "activation_rules": [
            "Taupe/TDR currently measures a Taupe workbook proxy or ARDP/dielectric response, not model saturation directly.",
            "The robust current use is a same-series temporal trend residual for each sensor and EDZ band.",
            "The model-side quantity is band-average theta_model = porosity * liquid_saturation over the mapped Taupe support.",
            "A3 and A4 provide the current mapped support; A7 and A8 are retained as source data but outside the current local OGS mesh.",
            "Do not activate absolute saturation or water-content residuals until the workbook unit and sensor calibration are documented.",
        ],
    }
    return summary


def link(path: Path, label: str | None = None) -> str:
    rendered = path.resolve()
    return f"[{label or rendered.name}]({rendered})"


def write_markdown_text(
    summary: dict[str, Any],
    series_audit: pd.DataFrame,
    group_summary: pd.DataFrame,
    catalogue_dir: Path,
) -> str:
    source_dir = catalogue_dir / "source_files"
    phys = summary["candidate_absolute_interpretation_physical_rows"]
    lines = [
        "# Taupe/TDR Measurement Semantics Audit",
        "",
        "This audit is the model-facing interpretation layer for the Taupe/TDR EDZ-band workbook.",
        "It separates a defensible trend diagnostic from unsupported absolute saturation or water-content use.",
        "",
        "## Source Files",
        "",
        f"- Raw Taupe workbook: {link(source_dir / 'Taupe_WC.xlsx')}",
        f"- Coordinate workbook: {link(source_dir / 'Coordinates_NMR_Taupe_characborehole.xlsx')}",
        f"- Location figures: {link(source_dir / 'NMR_Taupe_Char_brg_1.png')}, {link(source_dir / 'NMR_Taupe_Char_brg_2.png')}, {link(source_dir / 'NMR_Taupe_Char_brg_3.png')}",
        f"- ISU Taupe/TDR discussion slides: {link(source_dir / '2604_TD_CD-A_ISU.pdf')}",
        f"- TD modelling slides: {link(source_dir / 'CD-A_Slides_TD_260427x.pdf')}",
        "",
        "## Current Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Workbook rows: {summary['workbook_rows']}",
        f"- Operator/audit rows: {summary['operator_rows']}",
        f"- Sensor/EDZ-band series: {summary['series_rows']}",
        f"- Date range: {summary['date_min']} to {summary['date_max']}",
        f"- Mapped trend-ready rows: {summary['mapped_trend_rows']}",
        f"- Outside current local OGS mesh support: {summary['outside_current_mesh_rows']}",
        f"- State-target rows in the combined state table: {summary['state_target_rows']} "
        f"({summary['state_target_usable_rows']} active in the current state fit).",
        "",
        "The current defensible use is a same-series temporal trend diagnostic.  For each sensor and EDZ band, the Taupe operator compares the observed baseline-normalized Taupe anomaly with a matching baseline-normalized trend in band-averaged `theta_model = porosity * liquid_saturation`.  It is not yet an absolute saturation likelihood.",
        "",
        "## Semantics",
        "",
        "| Item | Interpretation |",
        "| --- | --- |",
        "| Measured/workbook quantity | Taupe/TDR EDZ-band value, treated as an ARDP/dielectric water-content proxy until the unit is confirmed. |",
        "| Model quantity | Band-average `theta_model = porosity * liquid_saturation`. |",
        "| Recommended residual | Same-series standardized model-theta anomaly minus Taupe standardized anomaly. |",
        "| Not a direct measurement of | Absolute saturation, calibrated volumetric water content unless confirmed, permeability, or pressure. |",
        "| Absolute residual gate | Blocked until `Taupe_WC.xlsx` unit and sensor-specific calibration are documented. |",
        "",
        "## Row Activation Counts",
        "",
        "| Gate | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["semantic_activation_gate_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "A3 and A4 account for the 2,544 mapped rows.  A7 and A8 are preserved in the archive and in the operator table, but they are outside the current local OGS mesh support and therefore are not active model targets in this setup.",
            "",
            "## Absolute Conversion Sanity Checks",
            "",
            "| Candidate interpretation | Physical rows within saturation [0, 1] | Role |",
            "| --- | ---: | --- |",
            f"| Taupe value as volumetric water-content percent | {phys['taupe_value_as_vol_percent']} | Plausibility check only. |",
            f"| Taupe value as Topp dielectric permittivity | {phys['taupe_value_as_topp_epsilon']} | Rejected as a default absolute conversion for this dataset. |",
            f"| Local linear dielectric mixing, `epsilon_rock = 6` | {phys['linear_mixing_epsilon_rock_6']} | Sensitivity check only. |",
            "",
            "These counts do not establish a calibration.  They only show which interpretations stay in a physical saturation range with the current porosity support.",
            "",
            "## Series-Level Audit",
            "",
            "| Series | Gate | Rows | Mapped | Outside mesh | Baseline | Scale | Taupe min | Taupe max | Net std change | WC% physical | Topp physical | Linear eps6 physical |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not series_audit.empty:
        for _, row in series_audit.sort_values("series_id").iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["series_id"]),
                        f"`{row.get('semantic_activation_gate', 'n/a')}`",
                        str(int(row["row_count"])),
                        str(int(row.get("mapped_trend_rows", 0))),
                        str(int(row.get("outside_current_mesh_rows", 0))),
                        f"{float(row['baseline_taupe_value']):.6g}",
                        f"{float(row['robust_scale_taupe_value']):.6g}",
                        f"{float(row['min_taupe_value']):.6g}",
                        f"{float(row['max_taupe_value']):.6g}",
                        f"{float(row['net_change_standardized']):.3f}",
                        str(int(row.get("wc_percent_candidate_physical_rows", 0))),
                        str(int(row.get("topp_candidate_physical_rows", 0))),
                        str(int(row.get("linear_eps6_candidate_physical_rows", 0))),
                    ]
                )
                + " |"
            )
    top_groups = group_summary[group_summary["group_type"].eq("sensor")] if not group_summary.empty else pd.DataFrame()
    lines.extend(
        [
            "",
            "## Sensor Summary",
            "",
            "| Sensor | Rows | Mapped | Outside mesh | Taupe min | Taupe median | Taupe max | Anomaly min | Anomaly max |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not top_groups.empty:
        for _, row in top_groups.sort_values("sensor").iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["sensor"]),
                        str(int(row["rows"])),
                        str(int(row["mapped_trend_rows"])),
                        str(int(row["outside_current_mesh_rows"])),
                        f"{float(row['taupe_value_min']):.6g}",
                        f"{float(row['taupe_value_median']):.6g}",
                        f"{float(row['taupe_value_max']):.6g}",
                        f"{float(row['standardized_anomaly_min']):.3f}",
                        f"{float(row['standardized_anomaly_max']):.3f}",
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## First Model Use",
            "",
            "After OGS state outputs exist, sample `theta_model = porosity * liquid_saturation` over the same Taupe EDZ-band support, normalize each model series against the same baseline dates, and compare trend anomalies by sensor, EDZ band, and time.  Use grouped weights by sensor/EDZ/time rather than treating every band row as independent if strong temporal or spatial correlation is retained.",
            "",
            "## Remaining Blocker",
            "",
            str(summary["remaining_blocker"]),
            "",
            "## Generated Audit Files",
            "",
        ]
    )
    for name, path in summary["outputs"].items():
        lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    bands = read_csv(args.processed_dir / "taupe_tdr_bands.csv")
    operator = read_csv(args.processed_dir / "taupe_tdr_trend_operator.csv")
    series = read_csv(args.processed_dir / "taupe_tdr_series_summary.csv")
    state_targets = read_csv(args.processed_dir / "state_observation_targets.csv")
    operator_summary = read_json(args.processed_dir / "taupe_tdr_observation_operator_summary.json")
    state_taupe = taupe_targets(state_targets)

    row_audit = build_row_audit(operator)
    series_audit = build_series_audit(series, row_audit)
    group_summary = build_group_summary(row_audit)

    outputs = {
        "row_audit": str(output_dir / "taupe_tdr_semantics_row_audit.csv"),
        "series_audit": str(output_dir / "taupe_tdr_semantics_series_audit.csv"),
        "group_summary": str(output_dir / "taupe_tdr_semantics_group_summary.csv"),
        "summary": str(output_dir / "taupe_tdr_semantics_summary.json"),
        "markdown": str(output_dir / "taupe_tdr_semantics.md"),
    }
    summary = build_summary(
        bands=bands,
        row_audit=row_audit,
        series_audit=series_audit,
        group_summary=group_summary,
        state_taupe=state_taupe,
        operator_summary=operator_summary,
        outputs=outputs,
        catalogue_dir=args.catalogue_dir,
    )
    markdown = write_markdown_text(summary, series_audit, group_summary, args.catalogue_dir)

    row_audit.to_csv(outputs["row_audit"], index=False)
    series_audit.to_csv(outputs["series_audit"], index=False)
    group_summary.to_csv(outputs["group_summary"], index=False)
    Path(outputs["summary"]).write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    Path(outputs["markdown"]).write_text(markdown, encoding="utf-8")
    for path in outputs.values():
        print(f"wrote {path}")
    print(f"operator rows: {summary['operator_rows']}")


if __name__ == "__main__":
    main()
