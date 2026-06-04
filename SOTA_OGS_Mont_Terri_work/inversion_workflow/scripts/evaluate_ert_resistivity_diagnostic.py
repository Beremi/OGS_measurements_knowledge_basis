#!/usr/bin/env python3
"""Evaluate a diagnostic ERT log-resistivity comparison for sampled OGS outputs.

The ERT projection transform and exact near-niche support are still provisional, so
this script deliberately writes diagnostics only.  It samples OGS
theta = porosity * liquid_saturation on the existing ERT-to-OGS lookup, converts
theta to resistivity with the documented local power law, and compares against the
nearest-in-time ERT VTK inversion field in log10 resistivity space.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sample_ogs_state_outputs import (  # noqa: E402
    data_dict_for_first_block,
    first_cell_block,
    patch_meshio_vtu_compressed_appended_reader,
    parse_output_name,
)


DEFAULT_ORIGIN = "2019-09-18T00:00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ogs-output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_output"),
        help="Directory with OGS result .vtu files.",
    )
    parser.add_argument(
        "--support-mesh",
        type=Path,
        help="Prepared bulk mesh with fixed porosity field. Defaults to <ogs-output-dir>/../bulk_w_projections.vtu.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--ert-zip",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip"),
    )
    parser.add_argument("--porosity-field", default="n_rd")
    parser.add_argument("--time-origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--max-time-delta-days", type=float, default=10.0)
    parser.add_argument(
        "--support-column",
        default="ready_for_residual_after_ogs_output",
        help="Boolean lookup column selecting ERT cells for the diagnostic support.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic.csv"),
    )
    parser.add_argument(
        "--timestep-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_timesteps.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic.md"),
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


def default_support_mesh(output_dir: Path) -> Path | None:
    candidate = output_dir.parent / "bulk_w_projections.vtu"
    return candidate if candidate.is_file() else None


def load_support_porosity(path: Path, field: str) -> np.ndarray:
    mesh = meshio.read(path)
    cell_type, _ = first_cell_block(mesh)
    try:
        values = mesh.cell_data_dict[field][cell_type]
    except KeyError as exc:
        raise SystemExit(f"{path} does not contain cell field {field!r} for {cell_type}") from exc
    return np.asarray(values, dtype=float).reshape(-1)


def relation(processed_dir: Path) -> dict[str, Any]:
    operator = pd.read_csv(processed_dir / "ert_water_content_resistivity_operator.csv")
    chosen = operator[operator["recommended_for_current_niche"].map(bool_value)]
    if chosen.empty:
        chosen = operator[operator["relation_id"].astype(str).eq("kruschwitz_model_data2019")]
    if chosen.empty:
        raise SystemExit("No recommended ERT theta-resistivity relation found.")
    row = chosen.iloc[0]
    return {
        "relation_id": str(row["relation_id"]),
        "coefficient_a": float(row["coefficient_a"]),
        "exponent_b": float(row["exponent_b"]),
        "theta_min": float(row["theta_min"]),
        "theta_max": float(row["theta_max"]),
    }


def output_rows(output_dir: Path, origin: datetime) -> pd.DataFrame:
    rows = []
    for path in sorted(output_dir.glob("*.vtu")):
        metadata = parse_output_name(path)
        if not finite(metadata["time_s"]):
            continue
        rows.append(
            {
                "output_path": path,
                "output_file": path.name,
                "time_s": float(metadata["time_s"]),
                "simulated_datetime": origin + timedelta(seconds=float(metadata["time_s"])),
            }
        )
    return pd.DataFrame(rows).sort_values("time_s")


def nearest_ert_timesteps(ogs_outputs: pd.DataFrame, timesteps: pd.DataFrame) -> pd.DataFrame:
    matched = timesteps[timesteps["has_matching_vtk"].map(bool_value)].copy()
    matched["timestamp"] = pd.to_datetime(matched["timestamp_iso"], errors="coerce")
    rows = []
    for _, output in ogs_outputs.iterrows():
        target = pd.Timestamp(output["simulated_datetime"])
        deltas = matched["timestamp"].map(lambda value: abs((pd.Timestamp(value) - target).total_seconds()))
        index = deltas.idxmin()
        ert = matched.loc[index]
        delta_seconds = float((pd.Timestamp(ert["timestamp"]) - target).total_seconds())
        rows.append(
            {
                "output_file": output["output_file"],
                "output_path": output["output_path"],
                "model_time_s": float(output["time_s"]),
                "model_datetime": target.isoformat(),
                "ert_timestamp_iso": str(ert["timestamp_iso"]),
                "ert_matching_vtk_member": str(ert["matching_vtk_member"]),
                "time_delta_days_ert_minus_model": delta_seconds / 86400.0,
            }
        )
    return pd.DataFrame(rows)


def read_ert_log10(zip_path: Path, member: str) -> np.ndarray:
    with zipfile.ZipFile(zip_path) as zf, tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "ert.vtk"
        tmp_path.write_bytes(zf.read(member))
        mesh = meshio.read(tmp_path)
    cell_type, _ = first_cell_block(mesh)
    try:
        values = mesh.cell_data_dict["Resistivity(log10)"][cell_type]
    except KeyError as exc:
        raise SystemExit(f"{member} lacks ERT cell field Resistivity(log10)") from exc
    return np.asarray(values, dtype=float).reshape(-1)


def ogs_theta_for_cells(path: Path, cell_ids: np.ndarray, porosity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mesh = meshio.read(path)
    _, cells = first_cell_block(mesh)
    if "saturation" not in mesh.point_data:
        raise SystemExit(f"{path} lacks point field 'saturation'")
    saturation = np.asarray(mesh.point_data["saturation"], dtype=float)
    sampled_saturation = saturation[cells[cell_ids]].mean(axis=1)
    sampled_porosity = porosity[cell_ids]
    return sampled_porosity * sampled_saturation, sampled_saturation


def weighted_stats(frame: pd.DataFrame, residual_column: str, weight_column: str) -> dict[str, float | None]:
    residual = pd.to_numeric(frame[residual_column], errors="coerce").to_numpy(dtype=float)
    weights = pd.to_numeric(frame[weight_column], errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(residual) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return {"mean": None, "mae": None, "rmse": None, "p50_abs": None, "p90_abs": None}
    residual = residual[mask]
    weights = weights[mask] / weights[mask].sum()
    abs_residual = np.abs(residual)
    order = np.argsort(abs_residual)
    sorted_abs = abs_residual[order]
    cdf = np.cumsum(weights[order])
    return {
        "mean": float(np.sum(weights * residual)),
        "mae": float(np.sum(weights * abs_residual)),
        "rmse": float(np.sqrt(np.sum(weights * residual**2))),
        "p50_abs": float(sorted_abs[np.searchsorted(cdf, 0.50, side="left")]),
        "p90_abs": float(sorted_abs[np.searchsorted(cdf, 0.90, side="left")]),
    }


def evaluate(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    patch_meshio_vtu_compressed_appended_reader()
    support_mesh = args.support_mesh or default_support_mesh(args.ogs_output_dir)
    if support_mesh is None:
        raise SystemExit("No support mesh supplied and no bulk_w_projections.vtu next to the OGS output directory.")

    lookup = pd.read_csv(args.processed_dir / "ert_spatial_projection_lookup.csv")
    if args.support_column not in lookup.columns:
        raise SystemExit(f"Lookup table lacks support column {args.support_column!r}")
    support = lookup[lookup[args.support_column].map(bool_value)].copy()
    if support.empty:
        raise SystemExit("No ERT lookup rows selected for diagnostic support.")
    support["ert_cell_area_m2_transformed"] = pd.to_numeric(
        support["ert_cell_area_m2_transformed"], errors="coerce"
    )

    rel = relation(args.processed_dir)
    porosity = load_support_porosity(support_mesh, args.porosity_field)
    cell_ids = pd.to_numeric(support["ogs_lookup_cell_id"], errors="coerce").astype(int).to_numpy()
    ert_cell_ids = pd.to_numeric(support["ert_cell_id"], errors="coerce").astype(int).to_numpy()
    areas = support["ert_cell_area_m2_transformed"].to_numpy(dtype=float)

    origin = datetime.fromisoformat(args.time_origin)
    outputs = output_rows(args.ogs_output_dir, origin)
    timesteps = pd.read_csv(args.processed_dir / "ert_timesteps.csv")
    matched = nearest_ert_timesteps(outputs, timesteps)
    max_delta = float(args.max_time_delta_days)

    row_frames: list[pd.DataFrame] = []
    timestep_rows: list[dict[str, Any]] = []
    ert_cache: dict[str, np.ndarray] = {}

    for _, match in matched.iterrows():
        within_time = abs(float(match["time_delta_days_ert_minus_model"])) <= max_delta
        if not within_time:
            timestep_rows.append(
                {
                    **match.drop(labels=["output_path"]).to_dict(),
                    "diagnostic_status": "outside_time_tolerance",
                    "support_cell_rows": int(support.shape[0]),
                    "finite_residual_rows": 0,
                    "area_weighted_mean_residual_log10": math.nan,
                    "area_weighted_mae_log10": math.nan,
                    "area_weighted_rmse_log10": math.nan,
                    "theta_model_min": math.nan,
                    "theta_model_median": math.nan,
                    "theta_model_max": math.nan,
                    "ert_log10_median": math.nan,
                    "pred_log10_median": math.nan,
                }
            )
            continue

        member = str(match["ert_matching_vtk_member"])
        if member not in ert_cache:
            ert_cache[member] = read_ert_log10(args.ert_zip, member)
        ert_log10 = ert_cache[member][ert_cell_ids]
        theta, saturation = ogs_theta_for_cells(Path(match["output_path"]), cell_ids, porosity)
        pred_log10 = np.full(theta.shape, np.nan, dtype=float)
        valid_theta = np.isfinite(theta) & (theta > 0.0)
        pred_log10[valid_theta] = np.log10(rel["coefficient_a"]) + rel["exponent_b"] * np.log10(theta[valid_theta])
        residual = pred_log10 - ert_log10
        status = np.where(np.isfinite(residual), "diagnostic_compared", "missing_model_or_ert_value")

        frame = pd.DataFrame(
            {
                "output_file": match["output_file"],
                "model_time_s": float(match["model_time_s"]),
                "model_datetime": match["model_datetime"],
                "ert_timestamp_iso": match["ert_timestamp_iso"],
                "ert_matching_vtk_member": member,
                "time_delta_days_ert_minus_model": float(match["time_delta_days_ert_minus_model"]),
                "diagnostic_status": status,
                "ert_cell_id": ert_cell_ids,
                "ogs_lookup_cell_id": cell_ids,
                "model_x": support["model_x"].to_numpy(dtype=float),
                "model_y": support["model_y"].to_numpy(dtype=float),
                "ert_cell_area_m2_transformed": areas,
                "theta_model": theta,
                "saturation": saturation,
                "porosity": porosity[cell_ids],
                "ert_log10_resistivity": ert_log10,
                "predicted_log10_resistivity": pred_log10,
                "residual_log10_pred_minus_ert": residual,
                "abs_residual_log10": np.abs(residual),
                "theta_inside_calibration_range": (theta >= rel["theta_min"]) & (theta <= rel["theta_max"]),
                "support_column": args.support_column,
            }
        )
        row_frames.append(frame)
        stats = weighted_stats(frame, "residual_log10_pred_minus_ert", "ert_cell_area_m2_transformed")
        timestep_rows.append(
            {
                **match.drop(labels=["output_path"]).to_dict(),
                "diagnostic_status": "diagnostic_compared",
                "support_cell_rows": int(frame.shape[0]),
                "finite_residual_rows": int(np.isfinite(residual).sum()),
                "area_weighted_mean_residual_log10": stats["mean"],
                "area_weighted_mae_log10": stats["mae"],
                "area_weighted_rmse_log10": stats["rmse"],
                "theta_model_min": json_number(np.nanmin(theta)),
                "theta_model_median": json_number(np.nanmedian(theta)),
                "theta_model_max": json_number(np.nanmax(theta)),
                "ert_log10_median": json_number(np.nanmedian(ert_log10)),
                "pred_log10_median": json_number(np.nanmedian(pred_log10)),
            }
        )

    diagnostic = pd.concat(row_frames, ignore_index=True) if row_frames else pd.DataFrame()
    timestep_summary = pd.DataFrame(timestep_rows)
    compared = diagnostic[diagnostic["diagnostic_status"].eq("diagnostic_compared")]
    stats = weighted_stats(compared, "residual_log10_pred_minus_ert", "ert_cell_area_m2_transformed")
    summary = {
        "status": "ert_resistivity_diagnostic_generated_transform_support_unconfirmed",
        "ogs_output_dir": str(args.ogs_output_dir),
        "support_mesh": str(support_mesh),
        "processed_dir": str(args.processed_dir),
        "ert_zip": str(args.ert_zip),
        "support_column": args.support_column,
        "time_origin": args.time_origin,
        "max_time_delta_days": args.max_time_delta_days,
        "relation_id": rel["relation_id"],
        "relation": {
            "coefficient_a": rel["coefficient_a"],
            "exponent_b": rel["exponent_b"],
            "theta_min": rel["theta_min"],
            "theta_max": rel["theta_max"],
        },
        "ogs_output_count": int(outputs.shape[0]),
        "ert_timestep_rows": int(timesteps.shape[0]),
        "support_cell_rows": int(support.shape[0]),
        "diagnostic_rows": int(diagnostic.shape[0]),
        "compared_rows": int(compared.shape[0]),
        "compared_output_times": int(timestep_summary["diagnostic_status"].eq("diagnostic_compared").sum())
        if not timestep_summary.empty
        else 0,
        "outside_time_tolerance_output_times": int(
            timestep_summary["diagnostic_status"].eq("outside_time_tolerance").sum()
        )
        if not timestep_summary.empty
        else 0,
        "area_weighted_residual_log10": stats,
        "mean_abs_time_delta_days": json_number(
            pd.to_numeric(timestep_summary["time_delta_days_ert_minus_model"], errors="coerce").abs().mean()
        )
        if not timestep_summary.empty
        else None,
        "theta_inside_calibration_rows": int(compared["theta_inside_calibration_range"].map(bool_value).sum())
        if not compared.empty
        else 0,
        "notes": [
            "Diagnostic only: ERT-to-OGS transform remains the documented +500 m assumption and exact near-niche support still needs confirmation.",
            "Residuals are log10(rho_pred) - log10(rho_ERT) using the recommended local theta-resistivity relation.",
            "Area-weighted summaries reduce, but do not eliminate, the correlation problem in neighbouring ERT inversion cells.",
            "Do not add this diagnostic to the active objective until transform, support mask, and ERT uncertainty are accepted.",
        ],
    }
    markdown = write_markdown(summary, timestep_summary)
    return diagnostic, timestep_summary, summary, markdown


def write_markdown(summary: dict[str, Any], timestep_summary: pd.DataFrame) -> str:
    residual = summary["area_weighted_residual_log10"]
    lines = [
        "# ERT Resistivity Diagnostic",
        "",
        "This run-local diagnostic compares sampled OGS water content to the open-niche ERT inversion fields on the current provisional ERT-to-OGS support. It is not part of the active objective.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- OGS output directory: `{summary['ogs_output_dir']}`",
        f"- Relation: `{summary['relation_id']}` with `rho = {summary['relation']['coefficient_a']} * theta^{summary['relation']['exponent_b']}`",
        f"- OGS output times: {summary['ogs_output_count']}",
        f"- Support cells per compared output: {summary['support_cell_rows']}",
        f"- Compared output times: {summary['compared_output_times']}",
        f"- Compared diagnostic rows: {summary['compared_rows']}",
        f"- Output times outside time tolerance: {summary['outside_time_tolerance_output_times']}",
        f"- Mean absolute time mismatch: {summary['mean_abs_time_delta_days']} days",
        "",
        "## Area-Weighted Log10 Residual",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Mean | {residual['mean']} |",
        f"| MAE | {residual['mae']} |",
        f"| RMSE | {residual['rmse']} |",
        f"| Median absolute | {residual['p50_abs']} |",
        f"| 90th percentile absolute | {residual['p90_abs']} |",
        "",
        "The residual is `log10(rho_pred(theta_model)) - log10(rho_ERT)`. It is a field-consistency diagnostic under the current transform/support assumptions, not a calibrated ERT likelihood.",
        "",
        "## Per-Output Summary",
        "",
        "| Model date | ERT date | dt days | Rows | MAE log10 | RMSE log10 | theta median | ERT median | Pred median |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    shown = timestep_summary[timestep_summary["diagnostic_status"].eq("diagnostic_compared")]
    for _, row in shown.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["model_datetime"])[:10],
                    str(row["ert_timestamp_iso"])[:10],
                    f"{float(row['time_delta_days_ert_minus_model']):.2f}",
                    str(int(row["finite_residual_rows"])),
                    f"{float(row['area_weighted_mae_log10']):.4f}",
                    f"{float(row['area_weighted_rmse_log10']):.4f}",
                    f"{float(row['theta_model_median']):.5f}",
                    f"{float(row['ert_log10_median']):.4f}",
                    f"{float(row['pred_log10_median']):.4f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Gate",
            "",
            "This diagnostic closes the local OGS-output sampling part of the ERT operator, but the ERT stream remains gated. The coordinate transform, exact near-niche support mask, and uncertainty/correlation model must be accepted before these rows can become objective terms.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    diagnostic, timestep_summary, summary, markdown = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    diagnostic.to_csv(args.output, index=False)
    timestep_summary.to_csv(args.timestep_output, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {args.timestep_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"compared rows: {summary['compared_rows']}")


if __name__ == "__main__":
    main()
