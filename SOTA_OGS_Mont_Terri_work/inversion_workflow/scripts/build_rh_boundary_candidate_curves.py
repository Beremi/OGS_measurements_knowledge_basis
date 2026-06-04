#!/usr/bin/env python3
"""Build local RH-derived open-niche boundary-curve candidates.

The generated curves are reproducible candidate forcings, not verified
replacements for the active OGS curve. They are meant to make the remaining RH
provenance gate concrete: which locally available sensor combinations would
produce which liquid-pressure histories, how much they disagree with the active
curve over the overlap, and how far they extend beyond the active curve.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


DEFAULT_ORIGIN = "2019-09-18T00:00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rh-table",
        type=Path,
        default=Path("inversion_workflow/processed_observations/rh_open_twin_kelvin.csv"),
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run"),
    )
    parser.add_argument(
        "--time-origin",
        default=DEFAULT_ORIGIN,
        help="Calendar origin corresponding to OGS model time 0 s.",
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
        help="Optional catalogue directory where derived_files copies are written.",
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
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {key: None for key in ["min", "p10", "p25", "p50", "p75", "p90", "max"]}
    return {
        "min": float(values.min()),
        "p10": float(values.quantile(0.10)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p90": float(values.quantile(0.90)),
        "max": float(values.max()),
    }


def metric_summary(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {"min": None, "median": None, "mean": None, "mae": None, "rmse": None, "max": None}
    return {
        "min": float(values.min()),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "mae": float(values.abs().mean()),
        "rmse": float(np.sqrt(np.mean(np.square(values)))),
        "max": float(values.max()),
    }


def active_open_curve_file(run_dir: Path) -> Path:
    curves_path = run_dir / "08_curves.xml"
    text = curves_path.read_text(encoding="utf-8")
    active_block = re.search(r"<curve>(.*?)</curve>", text, flags=re.DOTALL)
    if not active_block:
        raise ValueError(f"no active <curve> block found in {curves_path}")
    include = re.search(r'<include\s+file=["\']([^"\']+)["\']', active_block.group(1))
    if not include:
        raise ValueError(f"no active curve include found in {curves_path}")
    rel = include.group(1).replace("./", "")
    return run_dir / rel


def read_curve(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8")
    coords_match = re.search(r"<coords>(.*?)</coords>", text, flags=re.DOTALL)
    values_match = re.search(r"<values>(.*?)</values>", text, flags=re.DOTALL)
    if not coords_match or not values_match:
        raise ValueError(f"curve file must contain <coords> and <values>: {path}")
    coords = np.array([float(item) for item in coords_match.group(1).split()], dtype=float)
    values = np.array([float(item) for item in values_match.group(1).split()], dtype=float)
    if coords.shape != values.shape:
        raise ValueError(f"curve coord/value length mismatch in {path}: {coords.shape} vs {values.shape}")
    if coords.size == 0:
        raise ValueError(f"empty curve in {path}")
    return pd.DataFrame({"model_time_s": coords, "active_ogs_pressure_pa": values})


def candidate_definitions() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "rh5_only",
            "description": "RH5 valid non-low-outlier Kelvin pressure, daily values.",
            "aggregation": "single_sensor_daily",
            "sensors": ["RH5"],
            "exclude_above_95": False,
            "method": "mean",
        },
        {
            "candidate_id": "rh6_only",
            "description": "RH6 valid non-low-outlier Kelvin pressure, daily values.",
            "aggregation": "single_sensor_daily",
            "sensors": ["RH6"],
            "exclude_above_95": False,
            "method": "mean",
        },
        {
            "candidate_id": "rh5_rh6_mean",
            "description": "Daily mean of clean RH5/RH6 Kelvin pressures.",
            "aggregation": "daily_mean",
            "sensors": ["RH5", "RH6"],
            "exclude_above_95": False,
            "method": "mean",
        },
        {
            "candidate_id": "rh5_rh6_median",
            "description": "Daily median of clean RH5/RH6 Kelvin pressures.",
            "aggregation": "daily_median",
            "sensors": ["RH5", "RH6"],
            "exclude_above_95": False,
            "method": "median",
        },
        {
            "candidate_id": "rh5_rh6_below95_median",
            "description": "Daily median of RH5/RH6 rows below the open-twin 95 percent caution threshold.",
            "aggregation": "daily_median",
            "sensors": ["RH5", "RH6"],
            "exclude_above_95": True,
            "method": "median",
        },
        {
            "candidate_id": "all_valid_median",
            "description": "Daily median of all valid non-low-outlier RH5-8 Kelvin pressures.",
            "aggregation": "daily_median",
            "sensors": ["RH5", "RH6", "RH7", "RH8"],
            "exclude_above_95": False,
            "method": "median",
        },
    ]


def prepare_rh(path: Path, time_origin: str) -> pd.DataFrame:
    rh = pd.read_csv(path)
    dates = pd.to_datetime(rh["date_iso"], errors="coerce")
    origin = pd.Timestamp(datetime.fromisoformat(time_origin))
    rh["date"] = dates.dt.date.astype(str)
    rh["model_time_s"] = (dates - origin).dt.total_seconds()
    rh["valid_non_low_outlier"] = [
        bool_value(valid) and not bool_value(low)
        for valid, low in zip(rh["valid_rh_0_100"], rh["low_outlier_rh_lt_50"])
    ]
    rh["above_95_percent_open_twin_caution_bool"] = [
        bool_value(value) for value in rh["above_95_percent_open_twin_caution"]
    ]
    rh["liquid_pressure_gauge_mpa_kelvin"] = rh["liquid_pressure_gauge_pa_kelvin"] / 1.0e6
    return rh


def aggregate_series(frame: pd.DataFrame, method: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    agg_func: Callable[[pd.Series], float]
    if method == "median":
        agg_func = lambda values: float(pd.to_numeric(values, errors="coerce").median())
    elif method == "mean":
        agg_func = lambda values: float(pd.to_numeric(values, errors="coerce").mean())
    else:
        raise ValueError(f"unknown aggregation method: {method}")

    rows: list[dict[str, Any]] = []
    for date, group in frame.groupby("date", sort=True):
        pressure_pa = agg_func(group["liquid_pressure_gauge_pa_kelvin"])
        pressure_mpa = pressure_pa / 1.0e6
        rows.append(
            {
                "date_iso": f"{date}T00:00:00",
                "date": date,
                "model_time_s": float(pd.to_numeric(group["model_time_s"], errors="coerce").mean()),
                "rh_percent_aggregate": agg_func(group["rh_percent"]),
                "liquid_pressure_gauge_pa_kelvin": pressure_pa,
                "liquid_pressure_gauge_mpa_kelvin": pressure_mpa,
                "source_row_count": int(group.shape[0]),
                "sensor_count": int(group["sensor"].nunique()),
                "source_sensors": "+".join(sorted(map(str, group["sensor"].unique()))),
                "above_95_percent_open_twin_caution_source_rows": int(
                    group["above_95_percent_open_twin_caution_bool"].sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def build_candidates(rh: pd.DataFrame, active_curve: pd.DataFrame) -> pd.DataFrame:
    curve_min = float(active_curve["model_time_s"].min())
    curve_max = float(active_curve["model_time_s"].max())
    rows: list[pd.DataFrame] = []
    for definition in candidate_definitions():
        selected = rh[
            rh["sensor"].astype(str).isin(definition["sensors"])
            & rh["valid_non_low_outlier"]
            & np.isfinite(pd.to_numeric(rh["model_time_s"], errors="coerce"))
        ].copy()
        if definition["exclude_above_95"]:
            selected = selected[~selected["above_95_percent_open_twin_caution_bool"]].copy()
        aggregated = aggregate_series(selected, str(definition["method"]))
        if aggregated.empty:
            continue
        aggregated.insert(0, "candidate_id", definition["candidate_id"])
        aggregated["candidate_description"] = definition["description"]
        aggregated["aggregation"] = definition["aggregation"]
        aggregated["sensor_policy"] = ",".join(definition["sensors"])
        aggregated["excludes_above_95_percent_caution"] = bool(definition["exclude_above_95"])
        aggregated["comparison_status"] = np.where(
            aggregated["model_time_s"].lt(curve_min),
            "before_active_curve_time_range",
            np.where(
                aggregated["model_time_s"].gt(curve_max),
                "after_active_curve_time_range_requires_curve_extension_or_new_forcing",
                "compared_to_active_curve",
            ),
        )
        compared = aggregated["comparison_status"].eq("compared_to_active_curve")
        aggregated["active_ogs_pressure_pa_interp"] = math.nan
        aggregated.loc[compared, "active_ogs_pressure_pa_interp"] = np.interp(
            aggregated.loc[compared, "model_time_s"].to_numpy(dtype=float),
            active_curve["model_time_s"].to_numpy(dtype=float),
            active_curve["active_ogs_pressure_pa"].to_numpy(dtype=float),
        )
        aggregated["residual_candidate_minus_active_pa"] = (
            aggregated["liquid_pressure_gauge_pa_kelvin"]
            - aggregated["active_ogs_pressure_pa_interp"]
        )
        aggregated["residual_candidate_minus_active_mpa"] = (
            aggregated["residual_candidate_minus_active_pa"] / 1.0e6
        )
        aggregated["abs_residual_mpa"] = aggregated["residual_candidate_minus_active_mpa"].abs()
        rows.append(aggregated)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def write_curve_xml(path: Path, candidate_id: str, frame: pd.DataFrame) -> None:
    coords = " ".join(f"{value:.12g}" for value in frame["model_time_s"].to_numpy(dtype=float))
    values = " ".join(f"{value:.12g}" for value in frame["liquid_pressure_gauge_pa_kelvin"].to_numpy(dtype=float))
    text = (
        f"<name>{candidate_id}</name>\n"
        f"<coords>{coords}</coords>\n"
        f"<values>{values}</values>\n"
    )
    path.write_text(text, encoding="utf-8")


def build_summary(candidates: pd.DataFrame, xml_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id, group in candidates.groupby("candidate_id", sort=True):
        compared = group[group["comparison_status"].eq("compared_to_active_curve")]
        xml_path = xml_dir / f"{candidate_id}.xml"
        rows.append(
            {
                "candidate_id": candidate_id,
                "description": str(group["candidate_description"].iloc[0]),
                "rows": int(group.shape[0]),
                "date_min": str(group["date"].min()),
                "date_max": str(group["date"].max()),
                "source_row_count": int(group["source_row_count"].sum()),
                "median_sensor_count": float(pd.to_numeric(group["sensor_count"], errors="coerce").median()),
                "above_95_percent_caution_source_rows": int(
                    group["above_95_percent_open_twin_caution_source_rows"].sum()
                ),
                "compared_to_active_curve_rows": int(compared.shape[0]),
                "after_active_curve_rows": int(
                    group["comparison_status"]
                    .eq("after_active_curve_time_range_requires_curve_extension_or_new_forcing")
                    .sum()
                ),
                "rh_percent_p50": quantiles(group["rh_percent_aggregate"])["p50"],
                "pressure_mpa_p50": quantiles(group["liquid_pressure_gauge_mpa_kelvin"])["p50"],
                "overlap_residual_mpa_mean": metric_summary(compared["residual_candidate_minus_active_mpa"])["mean"],
                "overlap_abs_residual_mpa_median": metric_summary(compared["abs_residual_mpa"])["median"],
                "overlap_abs_residual_mpa_mae": metric_summary(compared["residual_candidate_minus_active_mpa"])["mae"],
                "overlap_residual_mpa_rmse": metric_summary(compared["residual_candidate_minus_active_mpa"])["rmse"],
                "candidate_xml": str(xml_path),
                "activation_status": "candidate_curve_generated_not_verified_boundary_forcing",
            }
        )
    summary = pd.DataFrame(rows).sort_values("candidate_id").reset_index(drop=True)
    if summary.empty:
        best_id = None
        preferred_id = None
    else:
        best_id = str(summary.sort_values("overlap_abs_residual_mpa_mae").iloc[0]["candidate_id"])
        preferred_id = "rh5_rh6_median" if "rh5_rh6_median" in set(summary["candidate_id"]) else str(summary.iloc[0]["candidate_id"])
    summary_json = {
        "status": "rh_boundary_candidate_curves_generated_provenance_still_unverified",
        "candidate_count": int(summary.shape[0]),
        "candidate_curve_rows": int(candidates.shape[0]),
        "preferred_policy_candidate": preferred_id,
        "lowest_overlap_mae_candidate": best_id,
        "activation_gate": (
            "Do not replace the active OGS boundary curve or release RH/retention likelihoods "
            "until BGR/Gesa confirm curve provenance, sensor selection, time axis, conversion "
            "constants, and extension policy."
        ),
        "summary_rows": json_ready(summary.to_dict(orient="records")),
        "comparison_status_counts": {
            str(key): int(value)
            for key, value in candidates["comparison_status"].value_counts().sort_index().items()
        },
    }
    return summary, summary_json


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, summary: pd.DataFrame, summary_json: dict[str, Any], outputs: dict[str, Path]) -> None:
    lines = [
        "# RH Boundary Candidate Curves",
        "",
        "This file records local RH-derived open-niche pressure-boundary curve candidates from the copied OT_RH5-8 workbooks.",
        "The curves are reproducible candidate forcings and extension evidence, not verified replacements for the active OGS curve.",
        "",
        "## Status",
        "",
        f"- Status: `{summary_json['status']}`",
        f"- Candidate curves: {summary_json['candidate_count']}",
        f"- Candidate curve rows: {summary_json['candidate_curve_rows']}",
        f"- Preferred policy candidate: `{summary_json['preferred_policy_candidate']}`",
        f"- Lowest overlap-MAE candidate: `{summary_json['lowest_overlap_mae_candidate']}`",
        f"- Activation gate: {summary_json['activation_gate']}",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Rows | Date range | Compared | After active curve | P50 RH % | P50 pressure MPa | Median abs mismatch MPa | MAE MPa | RMSE MPa |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            "| "
            f"`{row['candidate_id']}` | {int(row['rows'])} | {row['date_min']} to {row['date_max']} | "
            f"{int(row['compared_to_active_curve_rows'])} | {int(row['after_active_curve_rows'])} | "
            f"{fmt(row['rh_percent_p50'])} | {fmt(row['pressure_mpa_p50'])} | "
            f"{fmt(row['overlap_abs_residual_mpa_median'])} | "
            f"{fmt(row['overlap_abs_residual_mpa_mae'])} | {fmt(row['overlap_residual_mpa_rmse'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The policy-preferred local curve is the RH5/RH6 median because RH5/RH6 are the cleanest copied open-twin thermo-hygrometer streams. Matching the active OGS curve is not used as the selection rule: the current evidence already shows that the active curve is not a direct reconstruction of these copied workbooks.",
            "",
            "The generated XML files start only where local RH data exist. They therefore cannot replace the full active OGS boundary without an explicit pre-2021 policy and a post-2023 extension policy.",
            "",
            "## Generated Files",
            "",
        ]
    )
    for key, output in outputs.items():
        lines.append(f"- `{key}`: `{output}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_catalogue(outputs: dict[str, Path], xml_dir: Path, catalogue_dir: Path) -> list[str]:
    if not catalogue_dir.exists():
        return []
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for output in outputs.values():
        if output.exists() and output.is_file():
            dest = derived / output.name
            shutil.copy2(output, dest)
            copied.append(str(dest))
    if xml_dir.exists():
        dest_xml = derived / xml_dir.name
        dest_xml.mkdir(parents=True, exist_ok=True)
        for xml in sorted(xml_dir.glob("*.xml")):
            dest = dest_xml / xml.name
            shutil.copy2(xml, dest)
            copied.append(str(dest))
    return copied


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    xml_dir = output_dir / "rh_boundary_candidate_curve_xml"
    output_dir.mkdir(parents=True, exist_ok=True)
    xml_dir.mkdir(parents=True, exist_ok=True)

    active_curve = read_curve(active_open_curve_file(args.run_dir))
    rh = prepare_rh(args.rh_table, args.time_origin)
    candidates = build_candidates(rh, active_curve)
    if candidates.empty:
        raise SystemExit("no RH candidate rows generated")

    for candidate_id, group in candidates.groupby("candidate_id", sort=True):
        write_curve_xml(xml_dir / f"{candidate_id}.xml", str(candidate_id), group.sort_values("model_time_s"))

    summary, summary_json = build_summary(candidates, xml_dir)
    outputs = {
        "candidate_curves_csv": output_dir / "rh_boundary_candidate_curves.csv",
        "summary_csv": output_dir / "rh_boundary_candidate_curve_summary.csv",
        "summary_json": output_dir / "rh_boundary_candidate_curve_summary.json",
        "markdown": output_dir / "rh_boundary_candidate_curves.md",
    }
    candidates.to_csv(outputs["candidate_curves_csv"], index=False)
    summary.to_csv(outputs["summary_csv"], index=False)
    summary_json["outputs"] = {key: str(path) for key, path in outputs.items()}
    summary_json["xml_dir"] = str(xml_dir)
    write_markdown(outputs["markdown"], summary, summary_json, outputs)
    copied = copy_catalogue(outputs, xml_dir, args.catalogue_dir)
    summary_json["catalogue_copies"] = copied
    outputs["summary_json"].write_text(json.dumps(json_ready(summary_json), indent=2, sort_keys=True), encoding="utf-8")

    for key, path in outputs.items():
        print(f"wrote {path}")
    print(f"wrote {xml_dir}")
    print(f"candidate curves: {summary_json['candidate_count']}")
    print(f"preferred policy candidate: {summary_json['preferred_policy_candidate']}")


if __name__ == "__main__":
    main()
