#!/usr/bin/env python3
"""Build a Taupe/TDR trend observation-operator artifact.

The Taupe workbook is named as water-content data, but the local presentation
material describes TAUPE as differential TDR / ARDP.  This script therefore keeps
the robust part of the operator separate from candidate absolute conversions:

* baseline-normalized, within-series Taupe anomalies are ready as a trend
  diagnostic against model theta = porosity * saturation;
* absolute interpretations are reported as candidates only until the workbook unit
  and sensor-specific calibration are confirmed.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SENSOR_TO_SEGMENT = {"A3": "BCD-A3", "A4": "BCD-A4", "A7": "BCD-A7", "A8": "BCD-A8"}
EPSILON_WATER = 80.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--mesh",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05/bulk_w_projections.vtu"),
        help="Mesh containing the n_rd porosity cell field used by the OGS setup.",
    )
    parser.add_argument(
        "--baseline-rows",
        type=int,
        default=3,
        help="Number of first finite values per sensor/band used as the Taupe baseline.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_trend_operator.csv"),
    )
    parser.add_argument(
        "--series-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_series_summary.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_observation_operator_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_observation_operator.md"),
    )
    return parser.parse_args()


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_number(value: Any) -> float | None:
    if not finite(value):
        return None
    return float(value)


def json_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def physical_flag(value: Any, lower: float = 0.0, upper: float = 1.0) -> bool:
    return finite(value) and lower <= float(value) <= upper


def robust_scale(values: pd.Series, fallback_center: float) -> float:
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    numeric = numeric[np.isfinite(numeric)]
    if numeric.size == 0:
        return 1.0
    median = float(np.median(numeric))
    mad = float(1.4826 * np.median(np.abs(numeric - median)))
    if mad > 1e-12:
        return mad
    if numeric.size > 1:
        std = float(np.std(numeric, ddof=1))
        if std > 1e-12:
            return std
    return max(abs(fallback_center) * 0.01, 1.0)


def topp_theta_from_epsilon(epsilon_r: float) -> float:
    """Topp et al. empirical mineral-soil relation, treating Taupe value as epsilon_r."""
    if not finite(epsilon_r):
        return math.nan
    eps = float(epsilon_r)
    return -5.3e-2 + 2.92e-2 * eps - 5.5e-4 * eps**2 + 4.3e-6 * eps**3


def linear_mixing_theta_from_epsilon(epsilon_r: float, porosity: float, epsilon_rock: float) -> float:
    """Theta implied by the local linear mixing expression in the CD-A slides."""
    if not (finite(epsilon_r) and finite(porosity)):
        return math.nan
    phi = float(porosity)
    if phi <= 0.0:
        return math.nan
    return (float(epsilon_r) - epsilon_rock * (1.0 - phi)) / EPSILON_WATER


def saturation(theta: float, porosity: float) -> float:
    if not (finite(theta) and finite(porosity)):
        return math.nan
    phi = float(porosity)
    if phi <= 0.0:
        return math.nan
    return float(theta) / phi


def load_porosity(mesh_path: Path) -> np.ndarray:
    try:
        import meshio  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise SystemExit(
            "meshio is required for Taupe porosity diagnostics. "
            "Run with the system Python that has meshio installed."
        ) from exc

    mesh = meshio.read(mesh_path)
    try:
        porosity = mesh.cell_data_dict["n_rd"]["triangle6"]
    except KeyError as exc:
        raise SystemExit(f"{mesh_path} does not contain triangle6 cell field n_rd") from exc
    return np.asarray(porosity, dtype=float).reshape(-1)


def band_mapping_stats(
    sensor: str,
    band_min_m: float,
    band_max_m: float,
    line_samples: pd.DataFrame,
    porosity: np.ndarray,
) -> dict[str, Any]:
    segment = SENSOR_TO_SEGMENT.get(sensor, "")
    if not segment:
        return {
            "segment_label": "",
            "sample_rows": 0,
            "inside_sample_rows": 0,
            "unique_cell_count": 0,
            "mean_porosity": math.nan,
            "min_porosity": math.nan,
            "max_porosity": math.nan,
            "mapping_status": "missing_segment_mapping",
        }

    segment_rows = line_samples[line_samples["segment_label"].astype(str).eq(segment)]
    in_band = segment_rows[
        (pd.to_numeric(segment_rows["distance_along_segment_m"], errors="coerce") >= band_min_m)
        & (pd.to_numeric(segment_rows["distance_along_segment_m"], errors="coerce") <= band_max_m)
    ].copy()
    if in_band.empty:
        return {
            "segment_label": segment,
            "sample_rows": 0,
            "inside_sample_rows": 0,
            "unique_cell_count": 0,
            "mean_porosity": math.nan,
            "min_porosity": math.nan,
            "max_porosity": math.nan,
            "mapping_status": "no_segment_samples_in_band",
        }

    inside = in_band[in_band["inside_mesh_bbox"].map(bool_value)]
    ids = pd.to_numeric(inside["lookup_cell_id"], errors="coerce").dropna().astype(int)
    valid_ids = ids[(ids >= 0) & (ids < porosity.shape[0])]
    phi = porosity[valid_ids.to_numpy(dtype=int)] if not valid_ids.empty else np.array([], dtype=float)
    phi = phi[np.isfinite(phi)]
    status = "mapped_band_samples" if not inside.empty else "band_samples_outside_mesh"
    return {
        "segment_label": segment,
        "sample_rows": int(in_band.shape[0]),
        "inside_sample_rows": int(inside.shape[0]),
        "unique_cell_count": int(valid_ids.nunique()),
        "mean_porosity": float(np.mean(phi)) if phi.size else math.nan,
        "min_porosity": float(np.min(phi)) if phi.size else math.nan,
        "max_porosity": float(np.max(phi)) if phi.size else math.nan,
        "mapping_status": status,
    }


def build_operator(
    processed_dir: Path,
    mesh_path: Path,
    baseline_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    taupe = pd.read_csv(processed_dir / "taupe_tdr_bands.csv")
    line_samples = pd.read_csv(processed_dir / "borehole_line_mesh_samples.csv")
    porosity = load_porosity(mesh_path)

    taupe["date"] = pd.to_datetime(taupe["date_iso"], errors="coerce")
    taupe["taupe_value"] = pd.to_numeric(taupe["taupe_value"], errors="coerce")
    taupe["series_id"] = taupe["sensor"].astype(str) + "_" + taupe["edz_band_cm"].astype(str) + "cm"

    mapping_cache: dict[tuple[str, float, float], dict[str, Any]] = {}
    series_rows: list[dict[str, Any]] = []
    operator_rows: list[dict[str, Any]] = []

    for series_id, group in taupe.sort_values("date").groupby("series_id", sort=True):
        group = group.copy()
        finite_group = group[np.isfinite(group["taupe_value"])].copy()
        baseline_group = finite_group.head(max(1, baseline_rows))
        baseline_value = float(baseline_group["taupe_value"].mean()) if not baseline_group.empty else math.nan
        scale = robust_scale(finite_group["taupe_value"], baseline_value)
        first_date = "" if finite_group.empty else finite_group["date"].min().date().isoformat()
        last_date = "" if finite_group.empty else finite_group["date"].max().date().isoformat()
        baseline_start = "" if baseline_group.empty else baseline_group["date"].min().date().isoformat()
        baseline_end = "" if baseline_group.empty else baseline_group["date"].max().date().isoformat()
        first_value = float(finite_group["taupe_value"].iloc[0]) if not finite_group.empty else math.nan
        final_value = float(finite_group["taupe_value"].iloc[-1]) if not finite_group.empty else math.nan
        series_rows.append(
            {
                "series_id": series_id,
                "sensor": str(group["sensor"].iloc[0]),
                "edz_band_cm": str(group["edz_band_cm"].iloc[0]),
                "row_count": int(group.shape[0]),
                "date_min": first_date,
                "date_max": last_date,
                "baseline_rows": int(baseline_group.shape[0]),
                "baseline_date_min": baseline_start,
                "baseline_date_max": baseline_end,
                "baseline_taupe_value": baseline_value,
                "robust_scale_taupe_value": scale,
                "min_taupe_value": float(finite_group["taupe_value"].min()) if not finite_group.empty else math.nan,
                "max_taupe_value": float(finite_group["taupe_value"].max()) if not finite_group.empty else math.nan,
                "first_taupe_value": first_value,
                "final_taupe_value": final_value,
                "net_change_taupe_value": final_value - first_value if finite(first_value) and finite(final_value) else math.nan,
                "net_change_standardized": (
                    (final_value - first_value) / scale if finite(first_value) and finite(final_value) and scale > 0 else math.nan
                ),
            }
        )

        for _, row in group.iterrows():
            sensor = str(row["sensor"])
            band_min_m = float(row["edz_min_cm"]) / 100.0
            band_max_m = float(row["edz_max_cm"]) / 100.0
            cache_key = (sensor, band_min_m, band_max_m)
            if cache_key not in mapping_cache:
                mapping_cache[cache_key] = band_mapping_stats(sensor, band_min_m, band_max_m, line_samples, porosity)
            mapping = mapping_cache[cache_key]
            phi = float(mapping["mean_porosity"]) if finite(mapping["mean_porosity"]) else math.nan
            value = float(row["taupe_value"]) if finite(row["taupe_value"]) else math.nan
            delta = value - baseline_value if finite(value) and finite(baseline_value) else math.nan
            relative_change = 100.0 * delta / baseline_value if finite(delta) and finite(baseline_value) and baseline_value else math.nan
            standardized = delta / scale if finite(delta) and scale > 0.0 else math.nan

            theta_if_wc_percent = value / 100.0 if finite(value) else math.nan
            saturation_if_wc_percent = saturation(theta_if_wc_percent, phi)
            theta_if_topp = topp_theta_from_epsilon(value)
            saturation_if_topp = saturation(theta_if_topp, phi)
            theta_if_linear_eps6 = linear_mixing_theta_from_epsilon(value, phi, epsilon_rock=6.0)
            saturation_if_linear_eps6 = saturation(theta_if_linear_eps6, phi)
            theta_if_linear_eps5 = linear_mixing_theta_from_epsilon(value, phi, epsilon_rock=5.0)
            theta_if_linear_eps7 = linear_mixing_theta_from_epsilon(value, phi, epsilon_rock=7.0)

            operator_status = (
                "trend_operator_ready_absolute_calibration_pending"
                if mapping["mapping_status"] == "mapped_band_samples"
                else mapping["mapping_status"]
            )
            operator_rows.append(
                {
                    "source_file": row["source_file"],
                    "source_sheet": row["source_sheet"],
                    "sensor": sensor,
                    "series_id": series_id,
                    "date_iso": row["date_iso"],
                    "source_column": row["source_column"],
                    "edz_band_cm": row["edz_band_cm"],
                    "edz_min_cm": row["edz_min_cm"],
                    "edz_max_cm": row["edz_max_cm"],
                    "segment_label": mapping["segment_label"],
                    "band_sample_rows": mapping["sample_rows"],
                    "band_inside_sample_rows": mapping["inside_sample_rows"],
                    "band_unique_cell_count": mapping["unique_cell_count"],
                    "band_mean_porosity": phi,
                    "band_min_porosity": mapping["min_porosity"],
                    "band_max_porosity": mapping["max_porosity"],
                    "mapping_status": mapping["mapping_status"],
                    "operator_status": operator_status,
                    "taupe_value": value,
                    "baseline_taupe_value": baseline_value,
                    "baseline_date_min": baseline_start,
                    "baseline_date_max": baseline_end,
                    "taupe_delta_from_baseline": delta,
                    "taupe_relative_change_percent": relative_change,
                    "taupe_robust_scale": scale,
                    "taupe_standardized_anomaly": standardized,
                    "model_input_quantity": "band average theta_model = porosity * liquid_saturation",
                    "recommended_current_use": "standardized temporal Taupe anomaly diagnostic",
                    "recommended_operator": (
                        "compare observed taupe_standardized_anomaly with a same-series baseline-normalized "
                        "model theta trend; do not use absolute values as saturation until calibrated"
                    ),
                    "theta_fraction_if_taupe_value_is_vol_percent": theta_if_wc_percent,
                    "saturation_if_taupe_value_is_vol_percent": saturation_if_wc_percent,
                    "wc_percent_candidate_physical_saturation_0_1": physical_flag(saturation_if_wc_percent),
                    "theta_fraction_if_taupe_value_is_topp_epsilon": theta_if_topp,
                    "saturation_if_taupe_value_is_topp_epsilon": saturation_if_topp,
                    "topp_candidate_physical_saturation_0_1": physical_flag(saturation_if_topp),
                    "theta_fraction_if_linear_mixing_epsilon_rock_6": theta_if_linear_eps6,
                    "saturation_if_linear_mixing_epsilon_rock_6": saturation_if_linear_eps6,
                    "linear_mixing_eps6_candidate_physical_saturation_0_1": physical_flag(saturation_if_linear_eps6),
                    "theta_fraction_if_linear_mixing_epsilon_rock_5": theta_if_linear_eps5,
                    "theta_fraction_if_linear_mixing_epsilon_rock_7": theta_if_linear_eps7,
                    "absolute_calibration_note": (
                        "Taupe_WC values can be tested as volumetric-water-content percent or as dielectric/ARDP values, "
                        "but the current evidence supports only trend use without sensor-specific calibration."
                    ),
                }
            )

    operator = pd.DataFrame(operator_rows)
    series = pd.DataFrame(series_rows)
    mapped_rows = int(operator["operator_status"].eq("trend_operator_ready_absolute_calibration_pending").sum())
    physical_wc = int(operator["wc_percent_candidate_physical_saturation_0_1"].sum())
    physical_topp = int(operator["topp_candidate_physical_saturation_0_1"].sum())
    physical_linear = int(operator["linear_mixing_eps6_candidate_physical_saturation_0_1"].sum())
    phi = pd.to_numeric(operator["band_mean_porosity"], errors="coerce")
    summary = {
        "status": "trend_operator_ready_absolute_calibration_pending",
        "processed_dir": str(processed_dir),
        "mesh": str(mesh_path),
        "operator_rows": int(operator.shape[0]),
        "series_rows": int(series.shape[0]),
        "baseline_rows_per_series": baseline_rows,
        "date_min": str(pd.to_datetime(operator["date_iso"], errors="coerce").min().date()),
        "date_max": str(pd.to_datetime(operator["date_iso"], errors="coerce").max().date()),
        "mapped_trend_operator_rows": mapped_rows,
        "taupe_value_range": {
            "min": json_number(operator["taupe_value"].min()),
            "max": json_number(operator["taupe_value"].max()),
        },
        "standardized_anomaly_range": {
            "min": json_number(operator["taupe_standardized_anomaly"].min()),
            "max": json_number(operator["taupe_standardized_anomaly"].max()),
        },
        "band_mean_porosity_range": {
            "min": json_number(phi.min()),
            "max": json_number(phi.max()),
        },
        "candidate_absolute_interpretation_physical_rows": {
            "taupe_value_as_vol_percent": physical_wc,
            "taupe_value_as_topp_epsilon": physical_topp,
            "linear_mixing_epsilon_rock_6": physical_linear,
        },
        "recommended_numerical_role": "trend diagnostic; not an active absolute saturation likelihood",
        "remaining_blocker": (
            "Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, "
            "apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute residual weights."
        ),
        "notes": [
            "Trend anomalies are baseline-normalized within each sensor/EDZ-band series and can be compared to model theta trends after OGS outputs exist.",
            "The value-as-water-content-percent candidate is plausible enough to track, but not strong enough to use as a hard likelihood without confirmation.",
            "Topp and linear-mixing dielectric conversions are included only as sensitivity diagnostics; Topp is not Opalinus-Clay-specific.",
            "Band porosity diagnostics use the OGS n_rd mesh field and the Taupe line-sample mapping already used by state_observation_targets.csv.",
        ],
    }
    markdown = write_markdown_text(summary, series, operator)
    return operator, series, summary, markdown


def write_markdown_text(summary: dict[str, Any], series: pd.DataFrame, operator: pd.DataFrame) -> str:
    lines = [
        "# Taupe/TDR Observation Operator",
        "",
        "This file documents the current model-facing use of the Taupe/TDR workbook.",
        "",
        "## Current Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Operator rows: {summary['operator_rows']}",
        f"- Sensor/band series: {summary['series_rows']}",
        f"- Date range: {summary['date_min']} to {summary['date_max']}",
        f"- Rows with mapped trend operator: {summary['mapped_trend_operator_rows']}",
        f"- Recommended numerical role: {summary['recommended_numerical_role']}.",
        "",
        "The robust operator is a within-series temporal anomaly.  For each sensor and EDZ band, the first finite workbook values define a baseline, and later values are stored as raw, relative, and robustly standardized anomalies.  The model-side quantity is the same band average of `theta_model = porosity * liquid_saturation`; its change from the matching baseline output should be compared to the Taupe trend.  This supports trend diagnostics without assuming that the workbook value is already an absolute saturation.",
        "",
        "## Absolute Candidate Conversions",
        "",
        "The CSV also records three candidate absolute interpretations for every row:",
        "",
        "- `theta_fraction_if_taupe_value_is_vol_percent`: treats the workbook value as volumetric water-content percent.",
        "- `theta_fraction_if_taupe_value_is_topp_epsilon`: treats the value as dielectric permittivity in the Topp et al. empirical soil relation.",
        "- `theta_fraction_if_linear_mixing_epsilon_rock_6`: treats the value as dielectric permittivity in the local linear mixing formula with `epsilon_rock = 6` and `epsilon_water = 80`.",
        "",
        "These are diagnostics, not default likelihoods.  The workbook name suggests water-content processing, but the presentation material describes TAUPE as differential TDR / ARDP, so the absolute unit must be confirmed before assigning residual weights.",
        "",
        "## Series Summary",
        "",
        "| Series | Rows | Baseline | Scale | First | Final | Net standardized change |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in series.sort_values("series_id").iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["series_id"]),
                    str(int(row["row_count"])),
                    f"{float(row['baseline_taupe_value']):.6g}",
                    f"{float(row['robust_scale_taupe_value']):.6g}",
                    f"{float(row['first_taupe_value']):.6g}",
                    f"{float(row['final_taupe_value']):.6g}",
                    f"{float(row['net_change_standardized']):.3f}",
                ]
            )
            + " |"
        )
    phys = summary["candidate_absolute_interpretation_physical_rows"]
    total = max(1, int(summary["operator_rows"]))
    lines.extend(
        [
            "",
            "## Candidate Sanity Counts",
            "",
            f"- Value as water-content percent gives saturation within [0, 1] for {phys['taupe_value_as_vol_percent']} of {total} rows.",
            f"- Topp epsilon interpretation gives saturation within [0, 1] for {phys['taupe_value_as_topp_epsilon']} of {total} rows.",
            f"- Linear-mixing epsilon interpretation with `epsilon_rock = 6` gives saturation within [0, 1] for {phys['linear_mixing_epsilon_rock_6']} of {total} rows.",
            "",
            "These counts are only physical-range diagnostics.  They do not prove the correct calibration.",
            "",
            "## Remaining Blocker",
            "",
            summary["remaining_blocker"],
            "",
            "After OGS state outputs exist, this operator can be used immediately for Taupe trend diagnostics.  Promoting it to an active numerical objective needs a documented Taupe unit/calibration choice or a defensible trend-only likelihood.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    operator, series, summary, markdown = build_operator(
        args.processed_dir,
        args.mesh,
        args.baseline_rows,
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    operator.to_csv(args.output_csv, index=False)
    series.to_csv(args.series_output, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.series_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"operator rows: {summary['operator_rows']}")


if __name__ == "__main__":
    main()
