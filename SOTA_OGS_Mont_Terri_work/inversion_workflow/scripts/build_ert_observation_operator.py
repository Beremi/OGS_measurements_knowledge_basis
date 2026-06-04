#!/usr/bin/env python3
"""Build the first-pass ERT water-content/resistivity observation operator."""

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
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_water_content_resistivity_operator.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_observation_operator_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_observation_operator.md"),
    )
    return parser.parse_args()


def finite_array(values: pd.Series) -> np.ndarray:
    return pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)


def json_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fit_power_law(
    relation_id: str,
    source_table: str,
    source_subset: str,
    theta: pd.Series,
    resistivity: pd.Series,
    recommended_for_current_niche: bool = False,
) -> dict[str, Any]:
    theta_values = finite_array(theta)
    rho_values = finite_array(resistivity)
    mask = np.isfinite(theta_values) & np.isfinite(rho_values) & (theta_values > 0.0) & (rho_values > 0.0)
    x = theta_values[mask]
    y = rho_values[mask]
    row: dict[str, Any] = {
        "relation_id": relation_id,
        "source_table": source_table,
        "source_subset": source_subset,
        "recommended_for_current_niche": recommended_for_current_niche,
        "model_input_quantity": "theta_model = porosity * liquid_saturation",
        "predicted_quantity": "bulk electrical resistivity",
        "relation_form": "rho_ohm_m = coefficient_a * theta_fraction ** exponent_b",
        "inverse_form": "theta_fraction = (rho_ohm_m / coefficient_a) ** (1 / exponent_b)",
        "n_points": int(mask.sum()),
        "coefficient_a": math.nan,
        "exponent_b": math.nan,
        "intercept_log10_a": math.nan,
        "slope_log10": math.nan,
        "rmse_log10_resistivity": math.nan,
        "mean_abs_log10_residual": math.nan,
        "r2_log10": math.nan,
        "theta_min": json_number(np.nanmin(x) if x.size else math.nan),
        "theta_max": json_number(np.nanmax(x) if x.size else math.nan),
        "resistivity_min_ohm_m": json_number(np.nanmin(y) if y.size else math.nan),
        "resistivity_max_ohm_m": json_number(np.nanmax(y) if y.size else math.nan),
        "use_caveat": (
            "Empirical local Archie-type relation.  It maps water content to resistivity "
            "only before ERT-mesh/common-mesh projection and ERT inversion support effects."
        ),
    }
    if x.size < 3:
        row["use_caveat"] = "Insufficient positive finite points for a stable power-law fit."
        return row

    log_theta = np.log10(x)
    log_rho = np.log10(y)
    slope, intercept = np.polyfit(log_theta, log_rho, 1)
    predicted = intercept + slope * log_theta
    residual = predicted - log_rho
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((log_rho - np.mean(log_rho)) ** 2))

    row.update(
        {
            "coefficient_a": float(10**intercept),
            "exponent_b": float(slope),
            "intercept_log10_a": float(intercept),
            "slope_log10": float(slope),
            "rmse_log10_resistivity": float(np.sqrt(np.mean(residual**2))),
            "mean_abs_log10_residual": float(np.mean(np.abs(residual))),
            "r2_log10": float(1.0 - ss_res / ss_tot) if ss_tot > 0.0 else math.nan,
        }
    )
    return row


def build_operator(processed_dir: Path) -> tuple[pd.DataFrame, dict[str, Any], str]:
    pairs = pd.read_csv(processed_dir / "ert_nmr_resistivity_pairs.csv")
    kruschwitz = pd.read_csv(processed_dir / "ert_kruschwitz2004_relation.csv")
    timesteps = pd.read_csv(processed_dir / "ert_timesteps.csv")

    rows: list[dict[str, Any]] = []
    rows.append(
        fit_power_law(
            "nmr_pairs_all",
            "ert_nmr_resistivity_pairs.csv",
            "all N3+N4 paired NMR/resistivity rows",
            pairs["nmr_water_content_fraction"],
            pairs["resistivity_ohm_m"],
        )
    )
    for niche, group in pairs.groupby("niche"):
        rows.append(
            fit_power_law(
                f"nmr_pairs_{niche}",
                "ert_nmr_resistivity_pairs.csv",
                f"{niche} paired NMR/resistivity rows",
                group["nmr_water_content_fraction"],
                group["resistivity_ohm_m"],
            )
        )
    for column in ["resistivity", "model_data2019", "old_fit"]:
        rows.append(
            fit_power_law(
                f"kruschwitz_{column}",
                "ert_kruschwitz2004_relation.csv",
                f"Kruschwitz2004 workbook column {column}",
                kruschwitz["water_content"],
                kruschwitz[column],
                recommended_for_current_niche=(column == "model_data2019"),
            )
        )

    operator = pd.DataFrame(rows)
    recommended = operator[operator["recommended_for_current_niche"]].iloc[0].to_dict()
    matched_vtk = int(timesteps["has_matching_vtk"].astype(str).str.lower().isin({"true", "1", "yes"}).sum())
    missing_vtk = int(timesteps.shape[0] - matched_vtk)
    spatial = read_json(processed_dir / "ert_spatial_projection_summary.json")
    spatial_ready = bool(spatial)
    status = (
        "calibration_operator_ready_spatial_lookup_available_transform_assumed"
        if spatial_ready
        else "calibration_operator_ready_mesh_projection_pending"
    )
    remaining_blocker = (
        "Confirm the ERT-to-OGS coordinate transform and exact near-niche support mask, then sample OGS theta outputs and form log-resistivity residuals."
        if spatial_ready
        else "Project/interpolate OGS theta to the ERT inversion mesh or a documented common mesh before numerical ERT residuals are active."
    )

    summary = {
        "status": status,
        "processed_dir": str(processed_dir),
        "operator_rows": int(operator.shape[0]),
        "recommended_relation_id": recommended["relation_id"],
        "recommended_relation": {
            "coefficient_a": json_number(recommended["coefficient_a"]),
            "exponent_b": json_number(recommended["exponent_b"]),
            "rmse_log10_resistivity": json_number(recommended["rmse_log10_resistivity"]),
            "n_points": int(recommended["n_points"]),
            "theta_min": json_number(recommended["theta_min"]),
            "theta_max": json_number(recommended["theta_max"]),
            "resistivity_min_ohm_m": json_number(recommended["resistivity_min_ohm_m"]),
            "resistivity_max_ohm_m": json_number(recommended["resistivity_max_ohm_m"]),
        },
        "ert_timesteps": int(timesteps.shape[0]),
        "ert_timesteps_with_matching_vtk": matched_vtk,
        "ert_timesteps_missing_matching_vtk": missing_vtk,
        "operator_equation": "rho_ohm_m = coefficient_a * theta_fraction ** exponent_b",
        "model_theta_definition": "theta_fraction = porosity * liquid_saturation from OGS outputs",
        "spatial_projection": {
            "status": spatial.get("status"),
            "lookup_rows": spatial.get("ert_cells"),
            "projection_ready_rows": spatial.get("ready_for_residual_after_ogs_output_rows"),
            "reference_vtk_member": spatial.get("reference_vtk_member"),
            "transform": spatial.get("transform"),
        } if spatial_ready else {},
        "remaining_blocker": remaining_blocker,
        "notes": [
            "The workbook model_data2019 power law is the default first-test conversion because it is the smooth local workbook relation.",
            "The N4 paired NMR/resistivity fit is retained as a calibration diagnostic but is much more scattered.",
            "The relation is empirical and local; it must be combined with the ERT spatial/support operator before residuals are active.",
            "Use log-resistivity residuals after OGS theta is sampled and projected because the fitted relation is multiplicative.",
        ],
    }
    markdown = write_markdown_text(operator, summary)
    return operator, summary, markdown


def write_markdown_text(operator: pd.DataFrame, summary: dict[str, Any]) -> str:
    rec = summary["recommended_relation"]
    lines = [
        "# ERT Observation Operator",
        "",
        "This file documents the current first-pass operator for using OGS water-content output in ERT comparisons.",
        "",
        "## Recommended Relation",
        "",
        f"- Relation id: `{summary['recommended_relation_id']}`",
        "- Model input: `theta = porosity * liquid_saturation` from sampled OGS output.",
        "- Prediction: `rho_ohm_m = a * theta_fraction ** b`.",
        f"- `a = {rec['coefficient_a']:.6g}`",
        f"- `b = {rec['exponent_b']:.6g}`",
        f"- Fit rows: {rec['n_points']}",
        f"- Fit RMSE: {rec['rmse_log10_resistivity']:.4f} log10(ohm m)",
        f"- Calibrated theta range: {rec['theta_min']:.4f} to {rec['theta_max']:.4f}",
        "",
        "The recommended relation is the smooth local workbook conversion column.  The Niche-4 paired NMR/resistivity fit is retained in the table as a diagnostic, but it has larger scatter and should not be treated as a finished ERT forward model.",
        "",
        "## Spatial Projection Status",
        "",
        summary["remaining_blocker"],
        "",
        "ERT residuals should be formed in log-resistivity space and should retain explicit uncertainty for ERT inversion smoothing, electrode coverage, fractures, and mesh mismatch.",
        "",
        "## Fitted Relations",
        "",
        "| Relation id | Source subset | n | a | b | RMSE log10 rho | Recommended |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in operator.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['relation_id']}`",
                    str(row["source_subset"]).replace("|", "/"),
                    str(int(row["n_points"])),
                    f"{float(row['coefficient_a']):.6g}" if np.isfinite(float(row["coefficient_a"])) else "nan",
                    f"{float(row['exponent_b']):.6g}" if np.isfinite(float(row["exponent_b"])) else "nan",
                    f"{float(row['rmse_log10_resistivity']):.4f}" if np.isfinite(float(row["rmse_log10_resistivity"])) else "nan",
                    "yes" if bool(row["recommended_for_current_niche"]) else "no",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- ERT timestep rows: {summary['ert_timesteps']}",
            f"- Rows with matching VTK member: {summary['ert_timesteps_with_matching_vtk']}",
            f"- Rows missing matching VTK member: {summary['ert_timesteps_missing_matching_vtk']}",
        ]
    )
    spatial = summary.get("spatial_projection") or {}
    if spatial:
        lines.extend(
            [
                f"- Spatial lookup rows: {spatial.get('lookup_rows')}",
                f"- Spatial projection-ready rows: {spatial.get('projection_ready_rows')}",
                f"- Reference VTK: `{spatial.get('reference_vtk_member')}`",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    operator, summary, markdown = build_operator(args.processed_dir)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    operator.to_csv(args.output_csv, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"recommended relation: {summary['recommended_relation_id']}")


if __name__ == "__main__":
    main()
