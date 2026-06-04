#!/usr/bin/env python3
"""Build a detailed semantics/provenance audit for suction/RH observations."""

from __future__ import annotations

import argparse
import json
import math
import re
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
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/suction_relative_humidity"),
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


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def bool_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {
        str(key): int(value)
        for key, value in frame[column].fillna("missing").value_counts().sort_index().items()
    }


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


def active_open_curve_file(run_dir: Path) -> Path | None:
    curves_path = run_dir / "08_curves.xml"
    if not curves_path.exists():
        return None
    text = curves_path.read_text(encoding="utf-8")
    active_block = re.search(r"<curve>(.*?)</curve>", text, flags=re.DOTALL)
    if not active_block:
        return None
    include = re.search(r'<include\s+file=["\']([^"\']+)["\']', active_block.group(1))
    if not include:
        return None
    rel = include.group(1).replace("./", "")
    return run_dir / rel


def read_curve(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    text = path.read_text(encoding="utf-8")
    coords_match = re.search(r"<coords>(.*?)</coords>", text, flags=re.DOTALL)
    values_match = re.search(r"<values>(.*?)</values>", text, flags=re.DOTALL)
    if not coords_match or not values_match:
        return pd.DataFrame()
    coords = np.array([float(item) for item in coords_match.group(1).split()], dtype=float)
    values = np.array([float(item) for item in values_match.group(1).split()], dtype=float)
    if coords.shape != values.shape:
        return pd.DataFrame()
    return pd.DataFrame({"model_time_s": coords, "ogs_open_niche_pressure_pa": values})


def rh_targets(state_targets: pd.DataFrame) -> pd.DataFrame:
    if state_targets.empty or "observation_family" not in state_targets.columns:
        return pd.DataFrame()
    return state_targets[state_targets["observation_family"].astype(str).eq("Suction/RH")].copy()


def reliability_gate(row: pd.Series) -> str:
    if not bool_value(row.get("valid_rh_0_100", False)):
        return "invalid_rh_outside_0_100"
    if bool_value(row.get("low_outlier_rh_lt_50", False)):
        return "excluded_low_rh_outlier_lt_50"
    if bool_value(row.get("above_95_percent_open_twin_caution", False)):
        return "valid_but_open_twin_thermohygrometer_above_95_percent_caution"
    return "preferred_open_twin_thermohygrometer_range_below_95_percent"


def boundary_gate(row: pd.Series) -> str:
    rel = reliability_gate(row)
    if rel.startswith("invalid") or rel.startswith("excluded_low"):
        return rel
    status = str(row.get("audit_status", "missing_boundary_curve_audit"))
    if status == "compared_to_active_curve":
        return "compared_to_active_curve_for_provenance_audit_not_point_residual"
    if status == "outside_active_curve_time_range":
        return "valid_rh_after_active_curve_end_requires_curve_extension_or_new_forcing"
    return status


def build_row_audit(
    rh: pd.DataFrame,
    boundary_audit: pd.DataFrame,
    state_rh: pd.DataFrame,
) -> pd.DataFrame:
    if rh.empty:
        return pd.DataFrame()
    frame = rh.copy()
    if not boundary_audit.empty:
        audit_columns = [
            "model_time_s",
            "audit_status",
            "ogs_open_niche_pressure_pa",
            "residual_rh_kelvin_minus_ogs_pa",
            "residual_rh_kelvin_minus_ogs_mpa",
            "abs_residual_mpa",
        ]
        if boundary_audit.shape[0] == frame.shape[0]:
            for column in audit_columns:
                if column in boundary_audit.columns:
                    frame[column] = boundary_audit[column].to_numpy()
        else:
            frame = frame.merge(
                boundary_audit[
                    ["date_iso", "sensor"] + [column for column in audit_columns if column in boundary_audit.columns]
                ],
                on=["date_iso", "sensor"],
                how="left",
                validate="one_to_one",
            )
    if not state_rh.empty:
        state = state_rh.copy()
        state["source_row_key_numeric"] = pd.to_numeric(state["source_row_key"], errors="coerce")
        frame["source_row_key_numeric"] = np.arange(frame.shape[0])
        frame = frame.merge(
            state[
                [
                    "source_row_key_numeric",
                    "target_id",
                    "target_status",
                    "usable_for_current_state_fit",
                    "uncertainty_note",
                    "caveat",
                ]
            ],
            on="source_row_key_numeric",
            how="left",
        )
        frame = frame.drop(columns=["source_row_key_numeric"])
    frame["liquid_pressure_gauge_mpa_kelvin"] = (
        pd.to_numeric(frame["liquid_pressure_gauge_pa_kelvin"], errors="coerce") / 1.0e6
    )
    frame["liquid_pressure_abs_mpa_if_gas_101325pa"] = (
        pd.to_numeric(frame["liquid_pressure_abs_pa_if_gas_101325pa"], errors="coerce") / 1.0e6
    )
    frame["instrument_reliability_gate"] = [reliability_gate(row) for _, row in frame.iterrows()]
    frame["boundary_curve_gate"] = [boundary_gate(row) for _, row in frame.iterrows()]
    frame["measured_physical_quantity"] = "relative humidity in suction/RH borehole sensor"
    frame["derived_model_quantity"] = "Kelvin-equation gauge liquid pressure or capillary suction"
    frame["recommended_model_role"] = (
        "boundary-condition provenance/reconstruction and retention validation; not a mesh-cell point residual"
    )
    frame["not_a_direct_measurement_of"] = "permeability; liquid saturation; OGS cell pressure; tensor parameter field"
    frame["kelvin_formula_used"] = "p_l_gauge = rho_l * R * T / M_w * ln(RH_fraction)"
    frame["likelihood_activation_gate"] = np.where(
        frame["instrument_reliability_gate"].astype(str).str.startswith(("invalid", "excluded_low")),
        "excluded_from_numeric_use",
        "boundary_forcing_evidence_only_active_curve_provenance_not_verified",
    )
    keep = [
        "source_file",
        "source_sheet",
        "sensor",
        "date_iso",
        "rh_percent",
        "valid_rh_0_100",
        "low_outlier_rh_lt_50",
        "above_95_percent_open_twin_caution",
        "instrument_reliability_gate",
        "liquid_pressure_gauge_pa_kelvin",
        "liquid_pressure_gauge_mpa_kelvin",
        "liquid_pressure_abs_pa_if_gas_101325pa",
        "liquid_pressure_abs_mpa_if_gas_101325pa",
        "assumed_temperature_K",
        "assumed_liquid_density_kg_m3",
        "kelvin_coefficient_pa",
        "kelvin_formula_used",
        "model_time_s",
        "audit_status",
        "boundary_curve_gate",
        "ogs_open_niche_pressure_pa",
        "residual_rh_kelvin_minus_ogs_pa",
        "residual_rh_kelvin_minus_ogs_mpa",
        "abs_residual_mpa",
        "target_id",
        "target_status",
        "usable_for_current_state_fit",
        "uncertainty_note",
        "caveat",
        "measured_physical_quantity",
        "derived_model_quantity",
        "recommended_model_role",
        "not_a_direct_measurement_of",
        "likelihood_activation_gate",
    ]
    return frame[[column for column in keep if column in frame.columns]]


def build_sensor_summary(row_audit: pd.DataFrame) -> pd.DataFrame:
    if row_audit.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for sensor, group in row_audit.groupby("sensor", sort=True):
        dates = pd.to_datetime(group["date_iso"], errors="coerce")
        compared = group[group["audit_status"].astype(str).eq("compared_to_active_curve")]
        rows.append(
            {
                "sensor": sensor,
                "rows": int(group.shape[0]),
                "date_min": str(dates.min().date()) if dates.notna().any() else "",
                "date_max": str(dates.max().date()) if dates.notna().any() else "",
                "valid_rh_rows": bool_count(group, "valid_rh_0_100"),
                "low_rh_outlier_rows": bool_count(group, "low_outlier_rh_lt_50"),
                "above_95_percent_caution_rows": bool_count(group, "above_95_percent_open_twin_caution"),
                "preferred_range_rows": int(
                    group["instrument_reliability_gate"]
                    .astype(str)
                    .eq("preferred_open_twin_thermohygrometer_range_below_95_percent")
                    .sum()
                ),
                "compared_to_active_curve_rows": int(compared.shape[0]),
                "outside_active_curve_range_rows": int(
                    group["audit_status"].astype(str).eq("outside_active_curve_time_range").sum()
                ),
                "rh_percent_min": quantiles(group["rh_percent"])["min"],
                "rh_percent_median": quantiles(group["rh_percent"])["p50"],
                "rh_percent_max": quantiles(group["rh_percent"])["max"],
                "kelvin_pressure_mpa_min": quantiles(group["liquid_pressure_gauge_mpa_kelvin"])["min"],
                "kelvin_pressure_mpa_median": quantiles(group["liquid_pressure_gauge_mpa_kelvin"])["p50"],
                "kelvin_pressure_mpa_max": quantiles(group["liquid_pressure_gauge_mpa_kelvin"])["max"],
                "residual_mpa_median": quantiles(compared["residual_rh_kelvin_minus_ogs_mpa"])["p50"]
                if not compared.empty
                else None,
                "abs_residual_mpa_median": quantiles(compared["abs_residual_mpa"])["p50"]
                if not compared.empty
                else None,
                "recommended_use": (
                    "preferred RH boundary evidence"
                    if sensor in {"RH5", "RH6"}
                    else "retain with stronger quality screening because low/suspicious values occur"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_curve_semantics(curve: pd.DataFrame, coefficient_pa: float, row_audit: pd.DataFrame) -> pd.DataFrame:
    if curve.empty or not finite(coefficient_pa) or coefficient_pa == 0:
        return pd.DataFrame()
    output = curve.copy()
    output["ogs_open_niche_pressure_mpa"] = output["ogs_open_niche_pressure_pa"] / 1.0e6
    output["implied_rh_percent_at_assumed_T_rho"] = 100.0 * np.exp(
        output["ogs_open_niche_pressure_pa"] / coefficient_pa
    )
    valid = row_audit[~row_audit["instrument_reliability_gate"].astype(str).str.startswith(("invalid", "excluded_low"))]
    clean_open = valid[valid["sensor"].astype(str).isin({"RH5", "RH6"})]
    valid_min = float(pd.to_numeric(valid["rh_percent"], errors="coerce").min()) if not valid.empty else math.nan
    valid_max = float(pd.to_numeric(valid["rh_percent"], errors="coerce").max()) if not valid.empty else math.nan
    clean_open_min = (
        float(pd.to_numeric(clean_open["rh_percent"], errors="coerce").min()) if not clean_open.empty else math.nan
    )
    clean_open_max = (
        float(pd.to_numeric(clean_open["rh_percent"], errors="coerce").max()) if not clean_open.empty else math.nan
    )
    output["below_valid_collected_rh_min"] = output["implied_rh_percent_at_assumed_T_rho"].lt(valid_min)
    output["above_valid_collected_rh_max"] = output["implied_rh_percent_at_assumed_T_rho"].gt(valid_max)
    output["below_clean_rh5_rh6_collected_rh_min"] = output["implied_rh_percent_at_assumed_T_rho"].lt(clean_open_min)
    output["above_clean_rh5_rh6_collected_rh_max"] = output["implied_rh_percent_at_assumed_T_rho"].gt(clean_open_max)
    output["curve_role"] = "active OGS open-niche liquid-pressure boundary condition"
    output["provenance_status"] = "not_verified_as_direct_reconstruction_of_OT_RH5_to_OT_RH8"
    return output


def build_summary(
    *,
    row_audit: pd.DataFrame,
    sensor_summary: pd.DataFrame,
    curve_semantics: pd.DataFrame,
    boundary_summary: dict[str, Any],
    state_rh: pd.DataFrame,
    outputs: dict[str, str],
    catalogue_dir: Path,
    active_curve_path: Path | None,
) -> dict[str, Any]:
    valid_non_low = row_audit[
        ~row_audit["instrument_reliability_gate"].astype(str).str.startswith(("invalid", "excluded_low"))
    ]
    coefficient = (
        float(pd.to_numeric(row_audit["kelvin_coefficient_pa"], errors="coerce").dropna().iloc[0])
        if not row_audit.empty and pd.to_numeric(row_audit["kelvin_coefficient_pa"], errors="coerce").notna().any()
        else None
    )
    source_dir = catalogue_dir / "source_files"
    summary = {
        "status": "boundary_forcing_semantics_ready_curve_provenance_unverified",
        "rh_rows": int(row_audit.shape[0]),
        "valid_rh_rows": bool_count(row_audit, "valid_rh_0_100"),
        "valid_non_low_outlier_rows": int(valid_non_low.shape[0]),
        "low_rh_outlier_rows": bool_count(row_audit, "low_outlier_rh_lt_50"),
        "above_95_percent_open_twin_caution_rows": bool_count(row_audit, "above_95_percent_open_twin_caution"),
        "preferred_open_twin_range_rows": int(
            row_audit["instrument_reliability_gate"]
            .astype(str)
            .eq("preferred_open_twin_thermohygrometer_range_below_95_percent")
            .sum()
        )
        if not row_audit.empty
        else 0,
        "date_min": str(pd.to_datetime(row_audit["date_iso"], errors="coerce").min().date()) if not row_audit.empty else "",
        "date_max": str(pd.to_datetime(row_audit["date_iso"], errors="coerce").max().date()) if not row_audit.empty else "",
        "sensor_count": int(row_audit["sensor"].nunique()) if not row_audit.empty else 0,
        "sensors": sorted(row_audit["sensor"].dropna().astype(str).unique()) if not row_audit.empty else [],
        "instrument_reliability_gate_counts": value_counts(row_audit, "instrument_reliability_gate"),
        "boundary_curve_gate_counts": value_counts(row_audit, "boundary_curve_gate"),
        "state_target_rows": int(state_rh.shape[0]),
        "state_target_status_counts": value_counts(state_rh, "target_status"),
        "state_target_usable_rows": bool_count(state_rh, "usable_for_current_state_fit"),
        "kelvin_conversion": {
            "formula": "p_l_gauge = rho_l * R * T / M_w * ln(RH_fraction)",
            "assumed_temperature_K": quantiles(row_audit["assumed_temperature_K"])["p50"] if not row_audit.empty else None,
            "assumed_liquid_density_kg_m3": quantiles(row_audit["assumed_liquid_density_kg_m3"])["p50"]
            if not row_audit.empty
            else None,
            "coefficient_pa": coefficient,
            "rh_percent_quantiles": quantiles(row_audit["rh_percent"]) if not row_audit.empty else {},
            "liquid_pressure_gauge_mpa_quantiles": quantiles(row_audit["liquid_pressure_gauge_mpa_kelvin"])
            if not row_audit.empty
            else {},
        },
        "active_curve": {
            "path": str(active_curve_path) if active_curve_path else None,
            "rows": int(curve_semantics.shape[0]),
            "pressure_mpa_quantiles": quantiles(curve_semantics["ogs_open_niche_pressure_mpa"])
            if not curve_semantics.empty
            else {},
            "implied_rh_percent_quantiles": quantiles(curve_semantics["implied_rh_percent_at_assumed_T_rho"])
            if not curve_semantics.empty
            else {},
            "rows_below_valid_collected_rh_min": bool_count(curve_semantics, "below_valid_collected_rh_min"),
            "rows_above_valid_collected_rh_max": bool_count(curve_semantics, "above_valid_collected_rh_max"),
            "rows_below_clean_rh5_rh6_collected_rh_min": bool_count(
                curve_semantics, "below_clean_rh5_rh6_collected_rh_min"
            ),
            "rows_above_clean_rh5_rh6_collected_rh_max": bool_count(
                curve_semantics, "above_clean_rh5_rh6_collected_rh_max"
            ),
        },
        "boundary_audit": {
            "compared_rows": boundary_summary.get("compared_rows"),
            "status_counts": boundary_summary.get("status_counts", {}),
            "overall_abs_residual_mpa": boundary_summary.get("overall_abs_residual_mpa", {}),
            "overall_residual_rh_kelvin_minus_ogs_mpa": boundary_summary.get(
                "overall_residual_rh_kelvin_minus_ogs_mpa", {}
            ),
        },
        "source_files": {
            "catalogue": str(catalogue_dir.resolve()),
            "ot_rh5": str((source_dir / "OT_RH5.xlsx").resolve()),
            "ot_rh6": str((source_dir / "OT_RH6.xlsx").resolve()),
            "ot_rh7": str((source_dir / "OT_RH7.xlsx").resolve()),
            "ot_rh8": str((source_dir / "OT_RH8.xlsx").resolve()),
            "location_figure": str((source_dir / "Location_suc.png").resolve()),
        },
        "remaining_blocker": (
            "Reconstruct or document the provenance/preprocessing of 08_08_open_niche_seasonal.xml before treating "
            "the active OGS open-niche curve as a verified RH-derived forcing."
        ),
        "outputs": outputs,
        "activation_rules": [
            "RH measures vapour relative humidity, not saturation, permeability, or a cell pressure directly.",
            "The Kelvin conversion gives a boundary liquid-pressure/capillary-suction candidate under assumed T and liquid density.",
            "Low RH values below 50 percent in RH7/RH8 are excluded as likely sensor/logger outliers.",
            "Open-twin thermo-hygrometer values above 95 percent RH are retained but flagged with a reliability caution.",
            "The active OGS pressure curve is kept as an existing boundary condition until its provenance is reconstructed.",
        ],
    }
    return summary


def link(path: Path, label: str | None = None) -> str:
    rendered = path.resolve()
    return f"[{label or rendered.name}]({rendered})"


def write_markdown_text(
    summary: dict[str, Any],
    sensor_summary: pd.DataFrame,
    catalogue_dir: Path,
) -> str:
    source_dir = catalogue_dir / "source_files"
    kelvin = summary["kelvin_conversion"]
    curve = summary["active_curve"]
    boundary = summary["boundary_audit"]
    abs_residual = boundary.get("overall_abs_residual_mpa", {})
    lines = [
        "# Suction/RH Measurement Semantics Audit",
        "",
        "This audit separates the raw relative-humidity measurements, Kelvin-equation pressure conversion, active OGS boundary-curve comparison, and likelihood activation gates.",
        "",
        "## Source Files",
        "",
        f"- RH workbooks: {link(source_dir / 'OT_RH5.xlsx')}, {link(source_dir / 'OT_RH6.xlsx')}, {link(source_dir / 'OT_RH7.xlsx')}, {link(source_dir / 'OT_RH8.xlsx')}",
        f"- Suction/RH location figure: {link(source_dir / 'Location_suc.png')}",
        f"- Phase 30 report: {link(source_dir / 'RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf')}",
        f"- TD minutes: {link(source_dir / '2026-05-11_TD517_CD-A_260507__Minutes.pdf')}",
        f"- TD modelling slides: {link(source_dir / 'CD-A_Slides_TD_260427x.pdf')}",
        "",
        "## Current Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- RH rows: {summary['rh_rows']}",
        f"- Date range: {summary['date_min']} to {summary['date_max']}",
        f"- Sensors: {', '.join(summary['sensors'])}",
        f"- Valid non-low-outlier rows: {summary['valid_non_low_outlier_rows']}",
        f"- Low-RH outlier rows: {summary['low_rh_outlier_rows']}",
        f"- Open-twin >95% RH caution rows: {summary['above_95_percent_open_twin_caution_rows']}",
        f"- State-target rows: {summary['state_target_rows']} ({summary['state_target_usable_rows']} boundary-forcing rows marked usable in the target table).",
        "",
        "The data should be used as boundary-condition evidence and retention-curve validation context, not as a mesh-cell point residual.  The active OGS open-niche pressure curve remains a provenance item until its preprocessing can be reproduced from RH/T data or documented by BGR/Gesa.",
        "",
        "## Kelvin Conversion",
        "",
        f"- Formula used: `{kelvin['formula']}`",
        f"- Assumed temperature: {kelvin['assumed_temperature_K']} K",
        f"- Assumed liquid density: {kelvin['assumed_liquid_density_kg_m3']} kg/m3",
        f"- Kelvin coefficient: {kelvin['coefficient_pa']} Pa",
        "",
        "| Quantity | Min | P50 | Max |",
        "| --- | ---: | ---: | ---: |",
        f"| RH (%) | {kelvin['rh_percent_quantiles']['min']:.6g} | {kelvin['rh_percent_quantiles']['p50']:.6g} | {kelvin['rh_percent_quantiles']['max']:.6g} |",
        f"| Kelvin gauge liquid pressure (MPa) | {kelvin['liquid_pressure_gauge_mpa_quantiles']['min']:.6g} | {kelvin['liquid_pressure_gauge_mpa_quantiles']['p50']:.6g} | {kelvin['liquid_pressure_gauge_mpa_quantiles']['max']:.6g} |",
        "",
        "## Active OGS Boundary Curve",
        "",
        f"- Active curve path: `{curve['path']}`",
        f"- Curve rows: {curve['rows']}",
        f"- Curve pressure range: {curve['pressure_mpa_quantiles']['min']:.6g} to {curve['pressure_mpa_quantiles']['max']:.6g} MPa",
        f"- Curve-implied RH range at the same assumed T/rho: {curve['implied_rh_percent_quantiles']['min']:.6g}% to {curve['implied_rh_percent_quantiles']['max']:.6g}%",
        f"- Curve rows below the clean RH5/RH6 collected RH minimum: {curve['rows_below_clean_rh5_rh6_collected_rh_min']}",
        f"- Compared RH rows inside the active curve time range: {boundary['compared_rows']}",
        f"- Median absolute RH-minus-OGS pressure mismatch: {abs_residual.get('median')} MPa",
        f"- Mean absolute RH-minus-OGS pressure mismatch: {abs_residual.get('mean')} MPa",
        "",
        "The active curve spans much drier implied RH than the cleaner RH5/RH6 workbook evidence for much of its duration.  This supports the current interpretation: it is an existing model boundary condition, not yet a verified direct reconstruction of the collected RH workbooks.",
        "",
        "## Sensor Summary",
        "",
        "| Sensor | Rows | Date min | Date max | Low outliers | >95% caution | Preferred range | Compared | Outside curve | RH min | RH median | RH max | Median abs mismatch MPa | Recommended use |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not sensor_summary.empty:
        for _, row in sensor_summary.sort_values("sensor").iterrows():
            mismatch = row["abs_residual_mpa_median"]
            mismatch_text = "" if pd.isna(mismatch) else f"{float(mismatch):.3f}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["sensor"]),
                        str(int(row["rows"])),
                        str(row["date_min"]),
                        str(row["date_max"]),
                        str(int(row["low_rh_outlier_rows"])),
                        str(int(row["above_95_percent_caution_rows"])),
                        str(int(row["preferred_range_rows"])),
                        str(int(row["compared_to_active_curve_rows"])),
                        str(int(row["outside_active_curve_range_rows"])),
                        f"{float(row['rh_percent_min']):.6g}",
                        f"{float(row['rh_percent_median']):.6g}",
                        f"{float(row['rh_percent_max']):.6g}",
                        mismatch_text,
                        str(row["recommended_use"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Activation Rules",
            "",
            "- Treat RH as vapour relative humidity converted to a boundary-pressure candidate; it is not measured permeability, saturation, or OGS cell pressure.",
            "- Exclude the RH7/RH8 values below 50% RH unless the logger/sensor provenance is confirmed.",
            "- Retain open-twin values above 95% RH with a reliability caution; they are not a clean calibration subset for thermo-hygrometers.",
            "- Use RH5/RH6 preferentially for open-twin boundary reconstruction checks, because they do not contain the low-RH outlier episodes.",
            "- Do not treat `08_08_open_niche_seasonal.xml` as a verified RH-derived forcing until the curve-generation workflow is reconstructed.",
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
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rh = read_csv(args.processed_dir / "rh_open_twin_kelvin.csv")
    boundary_audit = read_csv(args.run_dir / "rh_boundary_curve_audit.csv")
    boundary_summary = read_json(args.run_dir / "rh_boundary_curve_audit_summary.json")
    state_targets = read_csv(args.processed_dir / "state_observation_targets.csv")
    state_rh = rh_targets(state_targets)
    active_curve_path = active_open_curve_file(args.run_dir)
    curve = read_curve(active_curve_path)

    row_audit = build_row_audit(rh, boundary_audit, state_rh)
    sensor_summary = build_sensor_summary(row_audit)
    coefficient = (
        float(pd.to_numeric(row_audit["kelvin_coefficient_pa"], errors="coerce").dropna().iloc[0])
        if not row_audit.empty and pd.to_numeric(row_audit["kelvin_coefficient_pa"], errors="coerce").notna().any()
        else math.nan
    )
    curve_semantics = build_curve_semantics(curve, coefficient, row_audit)

    outputs = {
        "row_audit": str(args.output_dir / "rh_measurement_semantics_row_audit.csv"),
        "sensor_summary": str(args.output_dir / "rh_measurement_semantics_sensor_summary.csv"),
        "curve_semantics": str(args.output_dir / "rh_boundary_curve_semantics.csv"),
        "summary": str(args.output_dir / "rh_measurement_semantics_summary.json"),
        "markdown": str(args.output_dir / "rh_measurement_semantics.md"),
    }
    summary = build_summary(
        row_audit=row_audit,
        sensor_summary=sensor_summary,
        curve_semantics=curve_semantics,
        boundary_summary=boundary_summary,
        state_rh=state_rh,
        outputs=outputs,
        catalogue_dir=args.catalogue_dir,
        active_curve_path=active_curve_path,
    )
    markdown = write_markdown_text(summary, sensor_summary, args.catalogue_dir)

    row_audit.to_csv(outputs["row_audit"], index=False)
    sensor_summary.to_csv(outputs["sensor_summary"], index=False)
    curve_semantics.to_csv(outputs["curve_semantics"], index=False)
    Path(outputs["summary"]).write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    Path(outputs["markdown"]).write_text(markdown, encoding="utf-8")
    for path in outputs.values():
        print(f"wrote {path}")
    print(f"RH rows: {summary['rh_rows']}")


if __name__ == "__main__":
    main()
