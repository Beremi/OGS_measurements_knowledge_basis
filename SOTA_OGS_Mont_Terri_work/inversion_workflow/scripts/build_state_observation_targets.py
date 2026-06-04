#!/usr/bin/env python3
"""Build model-facing state-observation target tables for non-permeability data."""

from __future__ import annotations

import argparse
import json
import math
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
        "--targets-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_targets.csv"),
    )
    parser.add_argument(
        "--samples-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_samples.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_target_summary.json"),
    )
    return parser.parse_args()


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def nmr_position_to_label(position: str) -> str | None:
    position = str(position).strip()
    special = {
        "4S": "NMR_S",
        "S": "NMR_S",
    }
    if position in special:
        return special[position]
    if position.startswith("NMR_"):
        return position
    if len(position) >= 2 and position[0] == "4":
        return f"NMR_{position}"
    return None


def sigma_from_ci95_percent(ci95_percent: Any, floor_fraction: float = 0.01) -> float:
    try:
        value = float(ci95_percent)
    except (TypeError, ValueError):
        return floor_fraction
    if not np.isfinite(value):
        return floor_fraction
    return max(value / 100.0 / 1.96, floor_fraction)


def target_template(target_id: str, family: str) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "observation_family": family,
        "source_file": "",
        "source_member": "",
        "source_sheet": "",
        "source_row_key": "",
        "measurement_label": "",
        "date_iso": "",
        "observed_quantity": "",
        "observed_value": math.nan,
        "observed_unit": "",
        "observed_sigma": math.nan,
        "model_quantity": "",
        "operator_type": "",
        "sample_strategy": "",
        "mapping_label": "",
        "target_status": "",
        "usable_for_current_state_fit": False,
        "uncertainty_note": "",
        "caveat": "",
    }


def add_sample(
    rows: list[dict[str, Any]],
    target_id: str,
    lookup_table: str,
    sample_source: str,
    lookup_label: str,
    lookup_cell_id: int,
    lookup_status: str,
    cell_weight: float,
    lookup_x: float,
    lookup_y: float,
    lookup_material_id: Any,
    distance_along_m: float = math.nan,
    band_min_m: float = math.nan,
    band_max_m: float = math.nan,
) -> None:
    rows.append(
        {
            "target_id": target_id,
            "lookup_table": lookup_table,
            "sample_source": sample_source,
            "lookup_label": lookup_label,
            "lookup_cell_id": int(lookup_cell_id),
            "lookup_status": lookup_status,
            "lookup_x": lookup_x,
            "lookup_y": lookup_y,
            "lookup_material_id": lookup_material_id,
            "cell_weight": cell_weight,
            "distance_along_segment_m": distance_along_m,
            "band_min_m": band_min_m,
            "band_max_m": band_max_m,
        }
    )


def build_nmr_weekly(
    processed_dir: Path,
    target_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> None:
    nmr = pd.read_csv(processed_dir / "nmr_weekly.csv")
    lookup = pd.read_csv(processed_dir / "borehole_mesh_lookup.csv")
    lookup_by_label = {str(row["label"]): row for _, row in lookup.iterrows()}

    station_mapping = {"4E": "NMR_4E", "4S": "NMR_S"}
    for index, row in nmr.iterrows():
        target_id = f"nmr_weekly_{index:04d}"
        target = target_template(target_id, "NMR weekly")
        label = station_mapping.get(str(row["station"]), "")
        target.update(
            {
                "source_file": row["source_file"],
                "source_row_key": str(index),
                "measurement_label": str(row["station"]),
                "date_iso": row["date_iso"],
                "observed_quantity": "NMR volumetric water content",
                "observed_value": float(row["water_content_vol_percent"]) / 100.0,
                "observed_unit": "fraction",
                "observed_sigma": sigma_from_ci95_percent(row["wc_ci95_vol_percent"]),
                "model_quantity": "theta_model = porosity * liquid_saturation",
                "operator_type": "point_sample",
                "sample_strategy": "sample OGS state at mapped NMR label cell",
                "mapping_label": label,
                "uncertainty_note": (
                    "NMR observes total hydrogen-bearing water; no bound/interlayer-water correction is applied."
                ),
                "caveat": "" if pd.isna(row.get("caveat")) else str(row.get("caveat")),
            }
        )
        lookup_row = lookup_by_label.get(label)
        if lookup_row is None:
            target["target_status"] = "missing_coordinate_label"
        else:
            target["target_status"] = str(lookup_row["lookup_status"])
            target["usable_for_current_state_fit"] = bool_value(lookup_row["inside_mesh_bbox"])
            add_sample(
                sample_rows,
                target_id,
                "borehole_mesh_lookup.csv",
                "NMR weekly point",
                label,
                lookup_row["lookup_cell_id"],
                lookup_row["lookup_status"],
                1.0,
                lookup_row["lookup_x"],
                lookup_row["lookup_y"],
                lookup_row["lookup_material_id"],
            )
        target_rows.append(target)


def build_nmr_seasonal(
    processed_dir: Path,
    target_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> None:
    nmr = pd.read_csv(processed_dir / "nmr_seasonal_profiles.csv")
    lookup = pd.read_csv(processed_dir / "borehole_mesh_lookup.csv")
    lookup_by_label = {str(row["label"]): row for _, row in lookup.iterrows()}

    for index, row in nmr.iterrows():
        target_id = f"nmr_seasonal_{index:04d}"
        target = target_template(target_id, "NMR seasonal")
        label = nmr_position_to_label(row["position"]) if str(row["niche"]) == "Niche 4" else None
        target.update(
            {
                "source_file": row["source_file"],
                "source_member": row["source_member"],
                "source_row_key": str(index),
                "measurement_label": str(row["position"]),
                "date_iso": row["campaign_date"],
                "observed_quantity": "NMR volumetric water content",
                "observed_value": float(row["water_content_vol_percent"]) / 100.0,
                "observed_unit": "fraction",
                "observed_sigma": sigma_from_ci95_percent(row["wc_ci95_vol_percent"]),
                "model_quantity": "theta_model = porosity * liquid_saturation",
                "operator_type": "point_sample",
                "sample_strategy": "sample OGS state at mapped NMR label cell",
                "mapping_label": "" if label is None else label,
                "uncertainty_note": (
                    "NMR seasonal campaigns are sparse profiles; Niche 3 rows are retained but outside the current Niche 4 model scope."
                ),
            }
        )
        if str(row["niche"]) != "Niche 4":
            target["target_status"] = "outside_current_niche_model_scope"
        elif label is None:
            target["target_status"] = "missing_coordinate_label"
        else:
            lookup_row = lookup_by_label.get(label)
            if lookup_row is None:
                target["target_status"] = "missing_coordinate_label"
            else:
                target["target_status"] = str(lookup_row["lookup_status"])
                target["usable_for_current_state_fit"] = bool_value(lookup_row["inside_mesh_bbox"])
                add_sample(
                    sample_rows,
                    target_id,
                    "borehole_mesh_lookup.csv",
                    "NMR seasonal point",
                    label,
                    lookup_row["lookup_cell_id"],
                    lookup_row["lookup_status"],
                    1.0,
                    lookup_row["lookup_x"],
                    lookup_row["lookup_y"],
                    lookup_row["lookup_material_id"],
                )
        target_rows.append(target)


def build_taupe(
    processed_dir: Path,
    target_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> None:
    taupe = pd.read_csv(processed_dir / "taupe_tdr_bands.csv")
    line_samples = pd.read_csv(processed_dir / "borehole_line_mesh_samples.csv")
    sensor_to_segment = {"A3": "BCD-A3", "A4": "BCD-A4", "A7": "BCD-A7", "A8": "BCD-A8"}

    for index, row in taupe.iterrows():
        target_id = f"taupe_{index:05d}"
        segment = sensor_to_segment.get(str(row["sensor"]), "")
        band_min_m = float(row["edz_min_cm"]) / 100.0
        band_max_m = float(row["edz_max_cm"]) / 100.0
        target = target_template(target_id, "Taupe/TDR")
        target.update(
            {
                "source_file": row["source_file"],
                "source_sheet": row["source_sheet"],
                "source_row_key": str(index),
                "measurement_label": f"{row['sensor']} {row['edz_band_cm']} cm",
                "date_iso": row["date_iso"],
                "observed_quantity": "Taupe EDZ-band value",
                "observed_value": float(row["taupe_value"]),
                "observed_unit": "unconfirmed Taupe/TDR workbook unit",
                "model_quantity": "band average of theta_model; use taupe_tdr_trend_operator.csv for baseline-normalized trends",
                "operator_type": "band_average_trend_diagnostic",
                "sample_strategy": "average OGS state samples along mapped Taupe segment within EDZ band",
                "mapping_label": segment,
                "usable_for_current_state_fit": False,
                "uncertainty_note": (
                    "Taupe trend operator is ready for diagnostic use; absolute workbook unit/conversion is not confirmed."
                ),
                "caveat": row["quantity_note"],
            }
        )
        if not segment:
            target["target_status"] = "missing_segment_mapping"
            target_rows.append(target)
            continue

        segment_samples = line_samples[line_samples["segment_label"].astype(str) == segment].copy()
        in_band = segment_samples[
            (segment_samples["distance_along_segment_m"] >= band_min_m)
            & (segment_samples["distance_along_segment_m"] <= band_max_m)
        ]
        if in_band.empty:
            target["target_status"] = "no_segment_samples_in_band"
        else:
            inside = in_band[in_band["inside_mesh_bbox"].map(bool_value)]
            target["target_status"] = "mapped_band_samples" if not inside.empty else "band_samples_outside_mesh"
            weight_denominator = float(len(in_band))
            for _, sample in in_band.iterrows():
                add_sample(
                    sample_rows,
                    target_id,
                    "borehole_line_mesh_samples.csv",
                    "Taupe band line sample",
                    segment,
                    sample["lookup_cell_id"],
                    sample["lookup_status"],
                    1.0 / weight_denominator,
                    sample["lookup_x"],
                    sample["lookup_y"],
                    sample["lookup_material_id"],
                    sample["distance_along_segment_m"],
                    band_min_m,
                    band_max_m,
                )
        target_rows.append(target)


def build_rh(processed_dir: Path, target_rows: list[dict[str, Any]]) -> None:
    rh = pd.read_csv(processed_dir / "rh_open_twin_kelvin.csv")
    for index, row in rh.iterrows():
        target_id = f"rh_kelvin_{index:05d}"
        target = target_template(target_id, "Suction/RH")
        valid = bool_value(row["valid_rh_0_100"]) and not bool_value(row["low_outlier_rh_lt_50"])
        caution = bool_value(row["above_95_percent_open_twin_caution"])
        target.update(
            {
                "source_file": row["source_file"],
                "source_sheet": row["source_sheet"],
                "source_row_key": str(index),
                "measurement_label": str(row["sensor"]),
                "date_iso": row["date_iso"],
                "observed_quantity": "Kelvin-equation liquid pressure from RH",
                "observed_value": float(row["liquid_pressure_gauge_pa_kelvin"]),
                "observed_unit": "Pa gauge relative to gas pressure",
                "model_quantity": "liquid pressure boundary or capillary-pressure validation",
                "operator_type": "boundary_forcing",
                "sample_strategy": "use as time-dependent hydraulic boundary forcing; no cell sample required",
                "mapping_label": str(row["sensor"]),
                "target_status": "boundary_forcing_valid" if valid else "excluded_invalid_or_low_rh",
                "usable_for_current_state_fit": bool(valid),
                "uncertainty_note": (
                    "Thermo-hygrometer data above 95 percent RH in the open twin are flagged as caution."
                    if caution
                    else "Kelvin conversion assumes constant temperature and liquid density from processed table."
                ),
                "caveat": "low RH outlier excluded" if bool_value(row["low_outlier_rh_lt_50"]) else "",
            }
        )
        target_rows.append(target)


def build_ert(processed_dir: Path, target_rows: list[dict[str, Any]]) -> None:
    ert = pd.read_csv(processed_dir / "ert_timesteps.csv")
    for index, row in ert.iterrows():
        target_id = f"ert_open_{index:05d}"
        target = target_template(target_id, "ERT open-niche time series")
        has_vtk = bool_value(row["has_matching_vtk"])
        target.update(
            {
                "source_file": row["source_file"],
                "source_member": row["source_member"],
                "source_row_key": str(row["timestep_index_in_file"]),
                "measurement_label": row["data_filename"],
                "date_iso": row["timestamp_iso"],
                "observed_quantity": "ERT resistivity field",
                "observed_unit": "external ERT VTK field",
                "model_quantity": "theta_model or saturation projected to ERT/comparison mesh then converted to resistivity",
                "operator_type": "external_field_projection",
                "sample_strategy": "project OGS state field to ERT mesh or common mesh; no direct OGS lookup cell yet",
                "mapping_label": "" if pd.isna(row["matching_vtk_member"]) else row["matching_vtk_member"],
                "target_status": "has_matching_ert_vtk" if has_vtk else "missing_matching_ert_vtk",
                "usable_for_current_state_fit": False,
                "uncertainty_note": (
                    "ERT is indirect; calibration and spatial lookup artifacts exist, but transform/support confirmation and OGS state outputs are still required before numerical residuals."
                ),
            }
        )
        target_rows.append(target)


def main() -> None:
    args = parse_args()
    target_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []

    build_nmr_weekly(args.processed_dir, target_rows, sample_rows)
    build_nmr_seasonal(args.processed_dir, target_rows, sample_rows)
    build_taupe(args.processed_dir, target_rows, sample_rows)
    build_rh(args.processed_dir, target_rows)
    build_ert(args.processed_dir, target_rows)

    targets = pd.DataFrame(target_rows)
    samples = pd.DataFrame(sample_rows)
    args.targets_output.parent.mkdir(parents=True, exist_ok=True)
    targets.to_csv(args.targets_output, index=False)
    samples.to_csv(args.samples_output, index=False)

    summary = {
        "target_rows": int(targets.shape[0]),
        "sample_rows": int(samples.shape[0]),
        "targets_by_family": targets.groupby("observation_family").size().to_dict(),
        "targets_by_status": targets.groupby(["observation_family", "target_status"]).size().to_dict(),
        "sample_rows_by_family": (
            samples.merge(targets[["target_id", "observation_family"]], on="target_id", how="left")
            .groupby("observation_family")
            .size()
            .to_dict()
            if not samples.empty
            else {}
        ),
        "usable_for_current_state_fit_rows": int(targets["usable_for_current_state_fit"].sum()),
        "outputs": {
            "targets": str(args.targets_output),
            "samples": str(args.samples_output),
        },
        "notes": [
            "Permeability pulse-test targets are handled separately by build_permeability_observation_targets.py.",
            "Taupe/TDR targets are mapped to line-sample bands; taupe_tdr_trend_operator.csv provides baseline-normalized trend diagnostics while absolute calibration remains pending.",
            "RH targets are boundary-forcing targets and intentionally do not require OGS cell samples.",
            "ERT targets have theta-to-resistivity calibration and ERT-to-OGS spatial lookup artifacts, but require transform/support confirmation and OGS state outputs before numerical residuals.",
            "NMR theta targets compare to porosity*saturation and do not correct bound/interlayer water.",
        ],
    }
    # JSON object keys from a pandas MultiIndex are tuples; stringify for portability.
    summary["targets_by_status"] = {str(key): value for key, value in summary["targets_by_status"].items()}
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"state observation targets: {targets.shape[0]}")
    print(f"state observation samples: {samples.shape[0]}")
    print(f"wrote {args.targets_output}")
    print(f"wrote {args.samples_output}")
    print(f"wrote {args.summary_output}")


if __name__ == "__main__":
    main()
