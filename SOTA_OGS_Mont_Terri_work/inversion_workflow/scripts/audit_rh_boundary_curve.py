#!/usr/bin/env python3
"""Compare RH-derived Kelvin pressure with the active OGS open-niche curve."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_ORIGIN = "2019-09-18T00:00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run"),
    )
    parser.add_argument(
        "--rh-table",
        type=Path,
        default=Path("inversion_workflow/processed_observations/rh_open_twin_kelvin.csv"),
    )
    parser.add_argument(
        "--time-origin",
        default=DEFAULT_ORIGIN,
        help="Calendar origin corresponding to OGS model time 0 s.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="CSV output path. Defaults to <run-dir>/rh_boundary_curve_audit.csv.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="JSON output path. Defaults to <run-dir>/rh_boundary_curve_audit_summary.json.",
    )
    return parser.parse_args()


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_number(value: Any) -> float | None:
    if not finite(value):
        return None
    return float(value)


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


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
    return pd.DataFrame({"model_time_s": coords, "ogs_open_niche_pressure_pa": values})


def status_for_row(row: pd.Series, curve_min: float, curve_max: float) -> str:
    if not bool_value(row["valid_rh_0_100"]):
        return "invalid_rh"
    if bool_value(row["low_outlier_rh_lt_50"]):
        return "excluded_low_rh_outlier"
    if not finite(row["model_time_s"]):
        return "missing_measurement_date"
    time_s = float(row["model_time_s"])
    if time_s < curve_min or time_s > curve_max:
        return "outside_active_curve_time_range"
    return "compared_to_active_curve"


def summarize_numeric(frame: pd.DataFrame, column: str) -> dict[str, float | None]:
    values = pd.to_numeric(frame[column], errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {"min": None, "median": None, "mean": None, "max": None}
    return {
        "min": float(values.min()),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "max": float(values.max()),
    }


def audit(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    output = args.output or (args.run_dir / "rh_boundary_curve_audit.csv")
    summary_output = args.summary_output or (args.run_dir / "rh_boundary_curve_audit_summary.json")
    curve_path = active_open_curve_file(args.run_dir)
    curve = read_curve(curve_path)
    rh = pd.read_csv(args.rh_table)
    origin = pd.Timestamp(datetime.fromisoformat(args.time_origin))

    dates = pd.to_datetime(rh["date_iso"], errors="coerce")
    rh["model_time_s"] = (dates - origin).dt.total_seconds()
    curve_min = float(curve["model_time_s"].min())
    curve_max = float(curve["model_time_s"].max())
    rh["audit_status"] = [status_for_row(row, curve_min, curve_max) for _, row in rh.iterrows()]

    comparable = rh["audit_status"].eq("compared_to_active_curve")
    rh["ogs_open_niche_pressure_pa"] = math.nan
    rh.loc[comparable, "ogs_open_niche_pressure_pa"] = np.interp(
        rh.loc[comparable, "model_time_s"].to_numpy(dtype=float),
        curve["model_time_s"].to_numpy(dtype=float),
        curve["ogs_open_niche_pressure_pa"].to_numpy(dtype=float),
    )
    rh["residual_rh_kelvin_minus_ogs_pa"] = (
        pd.to_numeric(rh["liquid_pressure_gauge_pa_kelvin"], errors="coerce")
        - pd.to_numeric(rh["ogs_open_niche_pressure_pa"], errors="coerce")
    )
    rh["residual_rh_kelvin_minus_ogs_mpa"] = rh["residual_rh_kelvin_minus_ogs_pa"] / 1.0e6
    rh["abs_residual_mpa"] = rh["residual_rh_kelvin_minus_ogs_mpa"].abs()

    sensor_summary: dict[str, Any] = {}
    for sensor, group in rh.groupby("sensor"):
        compared = group[group["audit_status"].eq("compared_to_active_curve")]
        sensor_summary[str(sensor)] = {
            "rows": int(group.shape[0]),
            "compared_rows": int(compared.shape[0]),
            "status_counts": {str(key): int(value) for key, value in group["audit_status"].value_counts().to_dict().items()},
            "rh_percent": summarize_numeric(group, "rh_percent"),
            "rh_kelvin_pressure_mpa": summarize_numeric(group.assign(p_mpa=group["liquid_pressure_gauge_pa_kelvin"] / 1.0e6), "p_mpa"),
            "residual_rh_kelvin_minus_ogs_mpa": summarize_numeric(compared, "residual_rh_kelvin_minus_ogs_mpa"),
            "abs_residual_mpa": summarize_numeric(compared, "abs_residual_mpa"),
        }

    compared = rh[rh["audit_status"].eq("compared_to_active_curve")]
    summary = {
        "rh_table": str(args.rh_table),
        "run_dir": str(args.run_dir),
        "active_curve_include": str(curve_path),
        "time_origin": args.time_origin,
        "curve_rows": int(curve.shape[0]),
        "curve_time_start_s": json_number(curve_min),
        "curve_time_end_s": json_number(curve_max),
        "curve_pressure_pa": summarize_numeric(curve, "ogs_open_niche_pressure_pa"),
        "rh_rows": int(rh.shape[0]),
        "compared_rows": int(compared.shape[0]),
        "status_counts": {str(key): int(value) for key, value in rh["audit_status"].value_counts().to_dict().items()},
        "sensor_summary": sensor_summary,
        "overall_residual_rh_kelvin_minus_ogs_mpa": summarize_numeric(compared, "residual_rh_kelvin_minus_ogs_mpa"),
        "overall_abs_residual_mpa": summarize_numeric(compared, "abs_residual_mpa"),
        "notes": [
            "Residual is RH-derived Kelvin gauge liquid pressure minus the active OGS open-niche pressure curve.",
            "Rows above 95 percent RH are compared but retain the processed-table reliability caution flag.",
            "Low RH rows below 50 percent are excluded as likely outliers/sensor failures.",
            "Rows after the active curve end are retained and flagged as outside_active_curve_time_range.",
        ],
    }
    return rh, summary, output, summary_output


def main() -> None:
    args = parse_args()
    audit_table, summary, output, summary_output = audit(args)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_table.to_csv(output, index=False)
    summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {output}")
    print(f"wrote {summary_output}")
    print(f"compared rows: {summary['compared_rows']}")


if __name__ == "__main__":
    main()
