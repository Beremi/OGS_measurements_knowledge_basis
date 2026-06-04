#!/usr/bin/env python3
"""Build a request package for RH-derived open-niche boundary-curve provenance."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MODEL_TIME_ORIGIN = datetime(2019, 9, 18)

REQUEST_SPECS = [
    {
        "request_id": "active_open_niche_curve_generation",
        "priority": "high",
        "request_category": "curve_generation",
        "scope": "08_08_open_niche_seasonal.xml / open_niche_seasonal_curve",
        "requested_files_or_answers": (
            "Original source time series, spreadsheet, script, or processing notebook used to generate "
            "the active open-niche pressure curve; include intermediate tables if the curve was smoothed, "
            "filtered, averaged, shifted, or manually edited."
        ),
        "requested_details": (
            "Sensor/source identifiers; date/time origin; interpolation grid; smoothing/filtering; "
            "outlier handling; formula; pressure sign convention; whether values are gauge or absolute; "
            "unit conversion; gas-pressure convention; temperature and density assumptions; and exact "
            "software/script version."
        ),
        "model_impact_if_resolved": (
            "Allows the active OGS open-niche pressure curve to be classified as a verified boundary "
            "forcing or replaced by a reproducible RH-derived forcing."
        ),
        "current_activation_status": "blocked_curve_generation_provenance_missing",
    },
    {
        "request_id": "time_range_and_curve_extension",
        "priority": "high",
        "request_category": "time_axis",
        "scope": "active curve coverage versus OT_RH5-8 measurements through 2025-09-04",
        "requested_files_or_answers": (
            "Decision on whether the active curve should stop at its current end time, be extended with "
            "later RH/temperature data, or be replaced by a new boundary series for 2022-2025 runs."
        ),
        "requested_details": (
            "Confirm the model-time zero date, timezone/local-time convention, timestep interpolation "
            "rule, extrapolation policy after the active curve end, and the intended curve for any "
            "post-2022 simulation period."
        ),
        "model_impact_if_resolved": (
            "Prevents silent extrapolation or stale forcing when comparing 2023-2025 RH/NMR/ERT/Taupe "
            "measurements to candidate OGS runs."
        ),
        "current_activation_status": "blocked_late_measurements_outside_active_curve_range",
    },
    {
        "request_id": "sensor_selection_and_quality_screening",
        "priority": "high",
        "request_category": "sensor_quality",
        "scope": "OT_RH5, OT_RH6, OT_RH7, OT_RH8 and any older/open-niche RH streams",
        "requested_files_or_answers": (
            "Quality-screening rule and sensor selection used for the active curve, including whether "
            "RH5/RH6, RH7/RH8, psychrometers, Geoscope auxiliary logs, or older sheets were used."
        ),
        "requested_details": (
            "Calibration certificates or quality flags; handling of RH7/RH8 low values near 13 percent; "
            "handling of open-twin thermo-hygrometer values above 95 percent RH; missing-data filling; "
            "sensor averaging/weighting; and periods rejected due to maintenance or door/opening events."
        ),
        "model_impact_if_resolved": (
            "Defines the measurement-error model and decides whether high-RH open-twin data are retained, "
            "downweighted, or excluded from any future forcing reconstruction."
        ),
        "current_activation_status": "blocked_sensor_selection_not_documented",
    },
    {
        "request_id": "kelvin_temperature_density_assumptions",
        "priority": "medium",
        "request_category": "physical_conversion",
        "scope": "Kelvin RH-to-liquid-pressure conversion and auxiliary temperature data",
        "requested_files_or_answers": (
            "Temperature series and constants used in the original conversion, or confirmation that a "
            "fixed temperature and fixed liquid density were used."
        ),
        "requested_details": (
            "Temperature source and unit; water density; molar mass; gas constant; vapour pressure/RH "
            "definition; whether RH is percent or fraction before conversion; whether atmospheric pressure "
            "is added; and whether suction/capillary pressure or liquid pressure is stored in XML."
        ),
        "model_impact_if_resolved": (
            "Makes the RH-to-pressure conversion reproducible and determines whether current 298.15 K / "
            "1095 kg/m3 assumptions are adequate for uncertainty propagation."
        ),
        "current_activation_status": "blocked_conversion_constants_unverified",
    },
    {
        "request_id": "open_closed_boundary_mapping",
        "priority": "medium",
        "request_category": "model_curve_mapping",
        "scope": "open and closed niche curve includes in 08_curves.xml",
        "requested_files_or_answers": (
            "Confirmation of which XML curve files are active, deprecated, or alternatives for open and "
            "closed niches, including the status of open_niche_seasonal_curve_shifted.xml."
        ),
        "requested_details": (
            "Open/closed niche source streams; whether the shifted open curve is an obsolete absolute-time "
            "variant or a candidate to use; whether closed_niche_seasonal_curve_shifted.xml is derived from "
            "separate closed-twin sensors; and boundary-surface assignment in the model."
        ),
        "model_impact_if_resolved": (
            "Avoids mixing active, shifted, open, and closed boundary curves when preparing candidate runs."
        ),
        "current_activation_status": "blocked_curve_mapping_needs_confirmation",
    },
    {
        "request_id": "retention_validation_and_parameter_release_gate",
        "priority": "medium",
        "request_category": "inversion_gate",
        "scope": "using RH/suction for retention validation or calibration",
        "requested_files_or_answers": (
            "Decision on whether the shared RH/suction data should be used only as boundary forcing, as "
            "retention validation, or as a future calibration target for van Genuchten parameters."
        ),
        "requested_details": (
            "Sensor support/locations for retention validation; accepted uncertainty model; whether the "
            "active p_b and exponent values are fixed; and which checks must pass before releasing "
            "retention parameters in the inverse problem."
        ),
        "model_impact_if_resolved": (
            "Keeps retention parameters frozen unless provenance, uncertainty, and OGS state outputs make "
            "a defensible RH/suction likelihood possible."
        ),
        "current_activation_status": "blocked_retention_use_policy_unconfirmed",
    },
]


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
        default=None,
        help="Optional suction/RH catalogue derived_files directory to copy outputs into.",
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


def fmt_number(value: Any, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    return f"{number:.{digits}f}"


def unique_join(values: list[Any] | pd.Series) -> str:
    seen: list[str] = []
    iterable = values.dropna().tolist() if isinstance(values, pd.Series) else values
    for value in iterable:
        text = str(value).strip()
        if text and text.lower() != "nan" and text not in seen:
            seen.append(text)
    return "; ".join(seen)


def work_root_from(processed_dir: Path) -> Path:
    return processed_dir.resolve().parents[1]


def catalogue_dir_from(processed_dir: Path) -> Path:
    return (
        processed_dir.resolve().parents[2]
        / "cda_knowledge_base"
        / "measurements"
        / "suction_relative_humidity"
        / "derived_files"
    )


def source_files(summary: dict[str, Any], processed_dir: Path) -> list[Path]:
    work_root = work_root_from(processed_dir)
    paths: list[Path] = [
        work_root / "ogs_settings" / "08_curves.xml",
        work_root / "ogs_settings" / "08_08_open_niche_seasonal.xml",
        work_root / "ogs_settings" / "open_niche_seasonal_curve_shifted.xml",
        work_root / "ogs_settings" / "closed_niche_seasonal_curve_shifted.xml",
        work_root / "GESA_model_original" / "projection_on_mesh_2025-09-05" / "08_curves.xml",
        work_root / "GESA_model_original" / "projection_on_mesh_2025-09-05" / "08_08_open_niche_seasonal.xml",
    ]
    for value in summary.get("source_files", {}).values():
        if isinstance(value, str):
            path = Path(value)
            if path.suffix:
                paths.append(path)
    return [path for path in paths if path.exists()]


def curve_date_range(curve: pd.DataFrame) -> tuple[str, str]:
    if curve.empty or "model_time_s" not in curve:
        return "n/a", "n/a"
    times = pd.to_numeric(curve["model_time_s"], errors="coerce").dropna()
    if times.empty:
        return "n/a", "n/a"
    start = MODEL_TIME_ORIGIN + timedelta(seconds=float(times.min()))
    end = MODEL_TIME_ORIGIN + timedelta(seconds=float(times.max()))
    return start.date().isoformat(), end.date().isoformat()


def include_mapping_evidence(processed_dir: Path) -> str:
    curves_xml = work_root_from(processed_dir) / "ogs_settings" / "08_curves.xml"
    if not curves_xml.exists():
        return "08_curves.xml was not found in ogs_settings."
    text = curves_xml.read_text(encoding="utf-8", errors="replace")
    active = "08_08_open_niche_seasonal.xml" in text
    shifted = "open_niche_seasonal_curve_shifted.xml" in text
    closed = "closed_niche_seasonal_curve_shifted.xml" in text
    return (
        f"ogs_settings/08_curves.xml references active open curve: {active}; "
        f"shifted open curve text present/commented: {shifted}; "
        f"closed shifted curve included: {closed}."
    )


def build_request_table(summary: dict[str, Any], curve: pd.DataFrame) -> pd.DataFrame:
    start_date, end_date = curve_date_range(curve)
    active = summary.get("active_curve", {})
    boundary = summary.get("boundary_audit", {})
    request_rows: list[dict[str, Any]] = []
    for spec in REQUEST_SPECS:
        row = {
            **spec,
            "current_evidence": (
                f"Active curve rows={active.get('rows', 'n/a')} with implied RH "
                f"{fmt_number(active.get('implied_rh_percent_quantiles', {}).get('min'), 2)}-"
                f"{fmt_number(active.get('implied_rh_percent_quantiles', {}).get('max'), 2)} percent; "
                f"{active.get('rows_below_clean_rh5_rh6_collected_rh_min', 'n/a')} of "
                f"{active.get('rows', 'n/a')} rows imply RH below the clean RH5/RH6 workbook minimum; "
                f"overlap residual median abs={fmt_number(boundary.get('overall_abs_residual_mpa', {}).get('median'), 2)} MPa; "
                f"curve date span from model time origin {MODEL_TIME_ORIGIN.date().isoformat()} is {start_date} to {end_date}."
            ),
            "hard_residual_gate": (
                "Do not use RH as a point residual or release retention/boundary parameters until "
                "the curve-generation provenance, time axis, sensor quality policy, and conversion "
                "constants are documented."
            ),
        }
        request_rows.append(row)
    return pd.DataFrame(request_rows)


def build_evidence_table(
    summary: dict[str, Any],
    sensor_summary: pd.DataFrame,
    curve: pd.DataFrame,
    processed_dir: Path,
) -> pd.DataFrame:
    active = summary.get("active_curve", {})
    pressure = active.get("pressure_mpa_quantiles", {})
    implied_rh = active.get("implied_rh_percent_quantiles", {})
    boundary = summary.get("boundary_audit", {})
    start_date, end_date = curve_date_range(curve)
    rows: list[dict[str, Any]] = [
        {
            "evidence_id": "active_curve_quantiles",
            "evidence_type": "generated_curve_semantics",
            "source_artifact": "rh_boundary_curve_semantics.csv; rh_measurement_semantics_summary.json",
            "measurement_scope": "active OGS open-niche pressure curve",
            "evidence_text": (
                f"Active curve has {active.get('rows', 'n/a')} rows, model-time date span "
                f"{start_date} to {end_date}, pressure quantiles min/p50/max "
                f"{fmt_number(pressure.get('min'), 3)}/{fmt_number(pressure.get('p50'), 3)}/"
                f"{fmt_number(pressure.get('max'), 3)} MPa, and implied RH min/p50/max "
                f"{fmt_number(implied_rh.get('min'), 2)}/{fmt_number(implied_rh.get('p50'), 2)}/"
                f"{fmt_number(implied_rh.get('max'), 2)} percent."
            ),
            "model_use": "existing boundary condition, not a verified reconstruction",
            "readiness_or_status": "provenance_unverified",
        },
        {
            "evidence_id": "curve_below_clean_sensor_range",
            "evidence_type": "range_mismatch",
            "source_artifact": "rh_boundary_curve_semantics.csv",
            "measurement_scope": "active curve inverted through Kelvin coefficient",
            "evidence_text": (
                f"{active.get('rows_below_clean_rh5_rh6_collected_rh_min', 'n/a')} of "
                f"{active.get('rows', 'n/a')} active curve rows imply RH below the clean RH5/RH6 "
                "workbook minimum; this is the strongest signal that the active curve is not a "
                "direct reconstruction of the copied OT_RH5/OT_RH6 sheets."
            ),
            "model_use": "provenance request trigger",
            "readiness_or_status": "mismatch_requires_external_confirmation",
        },
        {
            "evidence_id": "boundary_overlap_residual",
            "evidence_type": "boundary_audit_statistic",
            "source_artifact": "rh_measurement_semantics_summary.json; rh_boundary_curve_audit_summary.json",
            "measurement_scope": "OT_RH5-8 Kelvin pressure versus active OGS curve",
            "evidence_text": (
                f"Compared rows={boundary.get('compared_rows', 'n/a')}; later rows outside active curve="
                f"{boundary.get('status_counts', {}).get('outside_active_curve_time_range', 'n/a')}; "
                f"excluded low-RH outliers={boundary.get('status_counts', {}).get('excluded_low_rh_outlier', 'n/a')}; "
                f"median/mean/max absolute residual={fmt_number(boundary.get('overall_abs_residual_mpa', {}).get('median'), 3)}/"
                f"{fmt_number(boundary.get('overall_abs_residual_mpa', {}).get('mean'), 3)}/"
                f"{fmt_number(boundary.get('overall_abs_residual_mpa', {}).get('max'), 3)} MPa."
            ),
            "model_use": "boundary provenance audit",
            "readiness_or_status": "large_mismatch",
        },
        {
            "evidence_id": "curve_include_mapping",
            "evidence_type": "ogs_xml_include_audit",
            "source_artifact": "ogs_settings/08_curves.xml",
            "measurement_scope": "open/closed niche boundary curve mapping",
            "evidence_text": include_mapping_evidence(processed_dir),
            "model_use": "confirms which curve is active in the recovered setup",
            "readiness_or_status": "mapping_observed_confirmation_requested",
        },
        {
            "evidence_id": "kelvin_conversion_assumptions",
            "evidence_type": "conversion_assumption",
            "source_artifact": "rh_measurement_semantics_summary.json",
            "measurement_scope": "RH-to-pressure conversion",
            "evidence_text": (
                "Local audit uses "
                f"T={summary.get('kelvin_conversion', {}).get('assumed_temperature_K', 'n/a')} K, "
                f"rho_l={summary.get('kelvin_conversion', {}).get('assumed_liquid_density_kg_m3', 'n/a')} kg/m3, "
                "and p_l_gauge = rho_l * R * T / M_w * ln(RH_fraction)."
            ),
            "model_use": "local reproducibility convention pending external confirmation",
            "readiness_or_status": "constants_unverified_against_original_curve",
        },
    ]

    if not sensor_summary.empty:
        for _, sensor in sensor_summary.sort_values("sensor").iterrows():
            rows.append(
                {
                    "evidence_id": f"sensor_{sensor['sensor']}_summary",
                    "evidence_type": "sensor_quality_summary",
                    "source_artifact": "rh_measurement_semantics_sensor_summary.csv",
                    "measurement_scope": str(sensor["sensor"]),
                    "evidence_text": (
                        f"{sensor['sensor']} rows={sensor['rows']} from {sensor['date_min']} to {sensor['date_max']}; "
                        f"RH min/median/max={fmt_number(sensor['rh_percent_min'], 2)}/"
                        f"{fmt_number(sensor['rh_percent_median'], 2)}/{fmt_number(sensor['rh_percent_max'], 2)} percent; "
                        f"low outliers={sensor['low_rh_outlier_rows']}; >95 percent caution rows="
                        f"{sensor['above_95_percent_caution_rows']}; preferred-range rows="
                        f"{sensor['preferred_range_rows']}; recommended use: {sensor['recommended_use']}."
                    ),
                    "model_use": "sensor-selection and weighting evidence",
                    "readiness_or_status": "quality_policy_requested",
                }
            )

    source_values: list[str] = []
    for value in summary.get("source_files", {}).values():
        if not isinstance(value, str):
            continue
        path = Path(value)
        if path.suffix:
            source_values.append(str(path))
    if source_values:
        rows.append(
            {
                "evidence_id": "raw_source_workbooks",
                "evidence_type": "source_file_set",
                "source_artifact": unique_join(source_values),
                "measurement_scope": "catalogued OT_RH source files",
                "evidence_text": "The local audit is based on the copied OT_RH workbook set and location figure.",
                "model_use": "defines the currently reproducible data basis",
                "readiness_or_status": "source_files_catalogued",
            }
        )
    return pd.DataFrame(rows)


def build_summary(
    request: pd.DataFrame,
    evidence: pd.DataFrame,
    rh_summary: dict[str, Any],
    curve: pd.DataFrame,
    outputs: dict[str, str],
    copied: list[str] | None = None,
) -> dict[str, Any]:
    active = rh_summary.get("active_curve", {})
    boundary = rh_summary.get("boundary_audit", {})
    priority_counts = request["priority"].value_counts().sort_index().to_dict() if not request.empty else {}
    status_counts = (
        request["current_activation_status"].value_counts().sort_index().to_dict()
        if not request.empty
        else {}
    )
    start_date, end_date = curve_date_range(curve)
    return {
        "status": "request_package_ready_curve_provenance_still_unverified",
        "request_rows": int(request.shape[0]),
        "evidence_rows": int(evidence.shape[0]),
        "priority_counts": {str(key): int(value) for key, value in priority_counts.items()},
        "activation_status_counts": {str(key): int(value) for key, value in status_counts.items()},
        "rh_semantics_status": rh_summary.get("status"),
        "active_curve_rows": active.get("rows"),
        "active_curve_date_min": start_date,
        "active_curve_date_max": end_date,
        "active_curve_implied_rh_percent_min": active.get("implied_rh_percent_quantiles", {}).get("min"),
        "active_curve_implied_rh_percent_max": active.get("implied_rh_percent_quantiles", {}).get("max"),
        "active_curve_rows_below_clean_rh5_rh6_min": active.get(
            "rows_below_clean_rh5_rh6_collected_rh_min"
        ),
        "valid_non_low_outlier_rows": rh_summary.get("valid_non_low_outlier_rows"),
        "low_rh_outlier_rows": rh_summary.get("low_rh_outlier_rows"),
        "above_95_percent_open_twin_caution_rows": rh_summary.get(
            "above_95_percent_open_twin_caution_rows"
        ),
        "boundary_compared_rows": boundary.get("compared_rows"),
        "boundary_rows_after_active_curve_end": boundary.get("status_counts", {}).get(
            "outside_active_curve_time_range"
        ),
        "boundary_median_abs_residual_mpa": boundary.get("overall_abs_residual_mpa", {}).get("median"),
        "active_objective_rows": 0,
        "remaining_blocker": (
            "Obtain or reconstruct the generation history for 08_08_open_niche_seasonal.xml before "
            "treating the active open-niche pressure curve as verified RH-derived forcing or using RH "
            "as a retention-parameter likelihood."
        ),
        "outputs": outputs,
        "catalogue_copies": copied or [],
    }


def table_lines(request: pd.DataFrame) -> list[str]:
    lines = [
        "| Request | Priority | Category | Current status |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in request.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    str(row["priority"]),
                    str(row["request_category"]),
                    f"`{row['current_activation_status']}`",
                ]
            )
            + " |"
        )
    return lines


def write_markdown(
    path: Path,
    request: pd.DataFrame,
    evidence: pd.DataFrame,
    summary: dict[str, Any],
    raw_sources: list[Path],
) -> None:
    lines = [
        "# RH Boundary Curve Provenance Request",
        "",
        "This package turns the open RH boundary caveat into specific questions for BGR/Gesa.",
        "The local workflow can convert the copied OT_RH5-8 workbooks to Kelvin liquid pressure,",
        "but that conversion does not reproduce the active OGS open-niche pressure curve.",
        "",
        "## Current State",
        "",
        f"- Request rows: {summary['request_rows']}",
        f"- Evidence rows: {summary['evidence_rows']}",
        f"- Active objective rows from RH: {summary['active_objective_rows']}",
        f"- RH semantics status: `{summary['rh_semantics_status']}`",
        f"- Active curve date span from model time origin: {summary['active_curve_date_min']} to {summary['active_curve_date_max']}",
        f"- Active curve rows: {summary['active_curve_rows']}",
        f"- Active curve implied RH range: {fmt_number(summary['active_curve_implied_rh_percent_min'], 2)} to {fmt_number(summary['active_curve_implied_rh_percent_max'], 2)} percent",
        f"- Active curve rows below clean RH5/RH6 workbook minimum: {summary['active_curve_rows_below_clean_rh5_rh6_min']} of {summary['active_curve_rows']}",
        f"- RH rows compared to active curve: {summary['boundary_compared_rows']}",
        f"- Later RH rows outside active curve range: {summary['boundary_rows_after_active_curve_end']}",
        f"- Median absolute boundary mismatch: {fmt_number(summary['boundary_median_abs_residual_mpa'], 2)} MPa",
        "",
        "## Request Table",
        "",
        *table_lines(request),
        "",
        "## What To Ask BGR/Gesa For",
        "",
        "Email-ready text:",
        "",
        "```text",
        "Could you please help reconstruct or document how the CD-A open-niche pressure boundary curve 08_08_open_niche_seasonal.xml was generated?",
        "",
        "Using the copied OT_RH5 to OT_RH8 workbooks, we can reproduce a Kelvin-equation liquid-pressure candidate, but it does not reproduce the active OGS curve. The overlap audit compares 2,280 RH rows and gives a median absolute mismatch of about 13 MPa. Inverting the active curve with the same Kelvin coefficient gives an implied RH range of about 70.23 to 96.59 percent, and 772 of 845 active curve rows are drier than the clean RH5/RH6 workbook minimum.",
        "",
        "Could you provide the original source data and processing used for the active curve, including the script/spreadsheet if available? We need the sensor selection, time origin and timezone, interpolation or smoothing, outlier handling, pressure sign/unit convention, gauge versus absolute convention, gas pressure convention, temperature/density constants, and whether the shifted open curve is obsolete or an alternative. Please also confirm whether later RH/temperature data through 2025-09-04 should extend the boundary curve, and whether RH/suction should be used only as boundary forcing or also as retention validation/calibration.",
        "```",
        "",
        "## Detailed Requests",
        "",
    ]
    for _, row in request.iterrows():
        lines.extend(
            [
                f"### `{row['request_id']}`",
                "",
                f"- Priority: `{row['priority']}`",
                f"- Scope: {row['scope']}",
                f"- Requested files or answers: {row['requested_files_or_answers']}",
                f"- Requested details: {row['requested_details']}",
                f"- Current evidence: {row['current_evidence']}",
                f"- Model impact if resolved: {row['model_impact_if_resolved']}",
                f"- Activation gate: {row['hard_residual_gate']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Evidence Rows",
            "",
            "| Evidence id | Type | Source artifact | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for _, row in evidence.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['evidence_id']}`",
                    str(row["evidence_type"]),
                    f"`{str(row['source_artifact']).replace('|', '/')}`",
                    f"`{row['readiness_or_status']}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Source Files Checked", ""])
    for source in raw_sources:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Generated Files", ""])
    for label, output_path in summary["outputs"].items():
        lines.append(f"- `{label}`: `{output_path}`")
    lines.append("")
    lines.append(f"Remaining blocker: {summary['remaining_blocker']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_to_catalogue(paths: list[Path], catalogue_dir: Path) -> list[str]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for path in paths:
        destination = catalogue_dir / path.name
        shutil.copy2(path, destination)
        copied.append(str(destination))
    return copied


def main() -> None:
    args = parse_args()
    processed = args.processed_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    catalogue_dir = args.catalogue_dir or catalogue_dir_from(processed)

    rh_summary = read_json(processed / "rh_measurement_semantics_summary.json")
    sensor_summary = read_csv(processed / "rh_measurement_semantics_sensor_summary.csv")
    curve = read_csv(processed / "rh_boundary_curve_semantics.csv")
    if not rh_summary or sensor_summary.empty or curve.empty:
        raise SystemExit("RH semantics outputs are required before building the provenance request package")

    output_paths = {
        "request_csv": output_dir / "rh_boundary_provenance_request.csv",
        "evidence_csv": output_dir / "rh_boundary_provenance_evidence.csv",
        "summary_json": output_dir / "rh_boundary_provenance_request_summary.json",
        "markdown": output_dir / "rh_boundary_provenance_request.md",
    }
    outputs = {key: str(value) for key, value in output_paths.items()}
    request = build_request_table(rh_summary, curve)
    evidence = build_evidence_table(rh_summary, sensor_summary, curve, processed)

    request.to_csv(output_paths["request_csv"], index=False)
    evidence.to_csv(output_paths["evidence_csv"], index=False)
    summary = build_summary(request, evidence, rh_summary, curve, outputs)
    write_markdown(output_paths["markdown"], request, evidence, summary, source_files(rh_summary, processed))
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    copied = copy_to_catalogue(list(output_paths.values()), catalogue_dir)
    summary = build_summary(request, evidence, rh_summary, curve, outputs, copied)
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    shutil.copy2(output_paths["summary_json"], catalogue_dir / output_paths["summary_json"].name)

    print(f"wrote request_csv: {outputs['request_csv']}")
    print(f"wrote evidence_csv: {outputs['evidence_csv']}")
    print(f"wrote summary_json: {outputs['summary_json']}")
    print(f"wrote markdown: {outputs['markdown']}")
    print(f"catalogue copies: {len(copied)}")
    print(f"request rows: {summary['request_rows']}")
    print(f"evidence rows: {summary['evidence_rows']}")


if __name__ == "__main__":
    main()
