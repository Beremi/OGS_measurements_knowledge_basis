#!/usr/bin/env python3
"""Audit whether ERT log-resistivity diagnostics distinguish executed candidates.

This script applies the existing ERT diagnostic to every executed run directory
with OGS output files, but it stores only compact run-level and timestep-level
summaries.  It does not activate ERT in the likelihood; it quantifies whether the
currently executed permeability fields produce meaningfully different ERT scores
under the provisional transform/support assumptions.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import evaluate_ert_resistivity_diagnostic as ert_diag


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("inversion_workflow/runs"),
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
    parser.add_argument("--time-origin", default=ert_diag.DEFAULT_ORIGIN)
    parser.add_argument("--max-time-delta-days", type=float, default=10.0)
    parser.add_argument(
        "--support-column",
        default="ready_for_residual_after_ogs_output",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--timestep-output",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination_timesteps.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/ert"),
        help="Measurement-catalogue directory where derived audit copies are stored.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Rebuild summary/markdown from existing audit CSV outputs without recomputing diagnostics.",
    )
    return parser.parse_args()


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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def component_metric(combined: dict[str, Any], component_name: str, metric_key: str) -> float | None:
    for component in combined.get("components", []):
        if str(component.get("component")) == component_name:
            value = component.get(metric_key)
            return float(value) if finite(value) else None
    return None


def run_kind(run_id: str) -> str:
    if run_id == "direct_fit_observation_run":
        return "direct_reference"
    if run_id.startswith("local_basis"):
        return "local_basis"
    if run_id.startswith("production_sampler_round"):
        return "production_sampler_round"
    if run_id.startswith("production_sampler_"):
        return "production_sampler"
    if run_id.startswith("lower_support"):
        return "lower_support"
    if run_id.startswith("broad_continuous"):
        return "broad_continuous"
    if run_id.startswith("continuous_proposed"):
        return "continuous_proposed"
    if run_id.startswith("optimizer_proposed"):
        return "optimizer_proposed"
    if run_id.startswith("local_"):
        return "local_smooth"
    if run_id.startswith("adaptive_combined"):
        return "adaptive_combined"
    if run_id.startswith("regularized_ogs"):
        return "regularized_ogs"
    if run_id.startswith("candidate_"):
        return "candidate_driver"
    return "other"


def summarize_numeric(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {"min": None, "p10": None, "p50": None, "p90": None, "max": None, "mean": None, "std": None}
    return {
        "min": float(values.min()),
        "p10": float(values.quantile(0.10)),
        "p50": float(values.quantile(0.50)),
        "p90": float(values.quantile(0.90)),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)) if values.shape[0] > 1 else 0.0,
    }


def correlation(frame: pd.DataFrame, x: str, y: str) -> float | None:
    clean = frame[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 3:
        return None
    if clean[x].std(ddof=1) <= 1e-12 or clean[y].std(ddof=1) <= 1e-12:
        return None
    return float(clean[x].corr(clean[y]))


def weighted_quantile_abs(abs_residual: np.ndarray, weights: np.ndarray, quantile: float) -> float | None:
    mask = np.isfinite(abs_residual) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return None
    values = abs_residual[mask]
    selected_weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    selected_weights = selected_weights[order] / selected_weights.sum()
    cdf = np.cumsum(selected_weights)
    return float(values[np.searchsorted(cdf, quantile, side="left")])


def weighted_stats_arrays(residual: np.ndarray, weights: np.ndarray) -> dict[str, float | None]:
    mask = np.isfinite(residual) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return {"mean": None, "mae": None, "rmse": None, "p50_abs": None, "p90_abs": None}
    residual = residual[mask]
    weights = weights[mask]
    norm_weights = weights / weights.sum()
    abs_residual = np.abs(residual)
    return {
        "mean": float(np.sum(norm_weights * residual)),
        "mae": float(np.sum(norm_weights * abs_residual)),
        "rmse": float(np.sqrt(np.sum(norm_weights * residual**2))),
        "p50_abs": weighted_quantile_abs(abs_residual, weights, 0.50),
        "p90_abs": weighted_quantile_abs(abs_residual, weights, 0.90),
    }


def load_static_inputs(args: argparse.Namespace) -> dict[str, Any]:
    lookup = pd.read_csv(args.processed_dir / "ert_spatial_projection_lookup.csv")
    if args.support_column not in lookup.columns:
        raise SystemExit(f"Lookup table lacks support column {args.support_column!r}")
    support = lookup[lookup[args.support_column].map(ert_diag.bool_value)].copy()
    if support.empty:
        raise SystemExit("No ERT lookup rows selected for diagnostic support.")
    support["ert_cell_area_m2_transformed"] = pd.to_numeric(
        support["ert_cell_area_m2_transformed"], errors="coerce"
    )
    timesteps = pd.read_csv(args.processed_dir / "ert_timesteps.csv")
    return {
        "support": support,
        "relation": ert_diag.relation(args.processed_dir),
        "timesteps": timesteps,
        "cell_ids": pd.to_numeric(support["ogs_lookup_cell_id"], errors="coerce").astype(int).to_numpy(),
        "ert_cell_ids": pd.to_numeric(support["ert_cell_id"], errors="coerce").astype(int).to_numpy(),
        "areas": support["ert_cell_area_m2_transformed"].to_numpy(dtype=float),
    }


def evaluate_run(
    args: argparse.Namespace,
    run_dir: Path,
    static: dict[str, Any],
    ert_cache: dict[str, np.ndarray],
) -> tuple[dict[str, Any], pd.DataFrame]:
    run_id = run_dir.name
    output_dir = run_dir / "ogs_output"
    support_mesh = run_dir / "bulk_w_projections.vtu"
    if not output_dir.is_dir() or not support_mesh.is_file():
        raise ValueError(f"{run_id} lacks OGS output or support mesh")

    origin = datetime.fromisoformat(args.time_origin)
    outputs = ert_diag.output_rows(output_dir, origin)
    if outputs.empty:
        raise ValueError(f"{run_id} has no parseable OGS .vtu outputs")

    rel = static["relation"]
    porosity = ert_diag.load_support_porosity(support_mesh, args.porosity_field)
    matched = ert_diag.nearest_ert_timesteps(outputs, static["timesteps"])
    max_delta = float(args.max_time_delta_days)

    residual_parts: list[np.ndarray] = []
    weight_parts: list[np.ndarray] = []
    timestep_rows: list[dict[str, Any]] = []
    theta_inside_rows = 0

    for _, match in matched.iterrows():
        time_delta = float(match["time_delta_days_ert_minus_model"])
        within_time = abs(time_delta) <= max_delta
        base_row = {
            "run_id": run_id,
            "run_kind": run_kind(run_id),
            "output_file": match["output_file"],
            "model_time_s": float(match["model_time_s"]),
            "model_datetime": match["model_datetime"],
            "ert_timestamp_iso": match["ert_timestamp_iso"],
            "ert_matching_vtk_member": match["ert_matching_vtk_member"],
            "time_delta_days_ert_minus_model": time_delta,
        }
        if not within_time:
            timestep_rows.append(
                {
                    **base_row,
                    "diagnostic_status": "outside_time_tolerance",
                    "support_cell_rows": int(static["support"].shape[0]),
                    "finite_residual_rows": 0,
                    "area_weighted_mean_residual_log10": np.nan,
                    "area_weighted_mae_log10": np.nan,
                    "area_weighted_rmse_log10": np.nan,
                    "theta_model_min": np.nan,
                    "theta_model_median": np.nan,
                    "theta_model_max": np.nan,
                    "ert_log10_median": np.nan,
                    "pred_log10_median": np.nan,
                }
            )
            continue

        member = str(match["ert_matching_vtk_member"])
        if member not in ert_cache:
            ert_cache[member] = ert_diag.read_ert_log10(args.ert_zip, member)
        ert_log10 = ert_cache[member][static["ert_cell_ids"]]
        theta, _saturation = ert_diag.ogs_theta_for_cells(
            Path(match["output_path"]),
            static["cell_ids"],
            porosity,
        )
        pred_log10 = np.full(theta.shape, np.nan, dtype=float)
        valid_theta = np.isfinite(theta) & (theta > 0.0)
        pred_log10[valid_theta] = np.log10(rel["coefficient_a"]) + rel["exponent_b"] * np.log10(theta[valid_theta])
        residual = pred_log10 - ert_log10
        weights = static["areas"]
        stats = weighted_stats_arrays(residual, weights)
        finite_residual = np.isfinite(residual)
        theta_inside_rows += int(
            np.sum(finite_residual & (theta >= rel["theta_min"]) & (theta <= rel["theta_max"]))
        )
        residual_parts.append(residual[finite_residual])
        weight_parts.append(weights[finite_residual])
        timestep_rows.append(
            {
                **base_row,
                "diagnostic_status": "diagnostic_compared",
                "support_cell_rows": int(static["support"].shape[0]),
                "finite_residual_rows": int(finite_residual.sum()),
                "area_weighted_mean_residual_log10": stats["mean"],
                "area_weighted_mae_log10": stats["mae"],
                "area_weighted_rmse_log10": stats["rmse"],
                "theta_model_min": ert_diag.json_number(np.nanmin(theta)),
                "theta_model_median": ert_diag.json_number(np.nanmedian(theta)),
                "theta_model_max": ert_diag.json_number(np.nanmax(theta)),
                "ert_log10_median": ert_diag.json_number(np.nanmedian(ert_log10)),
                "pred_log10_median": ert_diag.json_number(np.nanmedian(pred_log10)),
            }
        )

    if residual_parts:
        all_residual = np.concatenate(residual_parts)
        all_weights = np.concatenate(weight_parts)
    else:
        all_residual = np.array([], dtype=float)
        all_weights = np.array([], dtype=float)
    stats = weighted_stats_arrays(all_residual, all_weights)
    timestep_frame = pd.DataFrame(timestep_rows)
    combined = read_json(run_dir / "combined_objective_summary.json")
    compared_times = int(timestep_frame["diagnostic_status"].eq("diagnostic_compared").sum())
    run_row = {
        "run_id": run_id,
        "run_kind": run_kind(run_id),
        "run_dir": str(run_dir),
        "ogs_output_count": int(outputs.shape[0]),
        "support_cell_rows": int(static["support"].shape[0]),
        "diagnostic_rows": int(static["support"].shape[0] * compared_times),
        "compared_rows": int(np.isfinite(all_residual).sum()),
        "compared_output_times": compared_times,
        "outside_time_tolerance_output_times": int(
            timestep_frame["diagnostic_status"].eq("outside_time_tolerance").sum()
        ),
        "mean_abs_time_delta_days": float(
            pd.to_numeric(timestep_frame["time_delta_days_ert_minus_model"], errors="coerce").abs().mean()
        )
        if not timestep_frame.empty
        else np.nan,
        "theta_inside_calibration_rows": int(theta_inside_rows),
        "ert_residual_mean_log10": stats["mean"],
        "ert_residual_mae_log10": stats["mae"],
        "ert_residual_rmse_log10": stats["rmse"],
        "ert_residual_p50_abs_log10": stats["p50_abs"],
        "ert_residual_p90_abs_log10": stats["p90_abs"],
        "combined_active_objective": combined.get("total_active_objective_value"),
        "combined_active_component_count": combined.get("active_component_count"),
        "direct_permeability_objective": component_metric(
            combined,
            "direct_permeability_pulse_tests",
            "objective_value",
        ),
        "nmr_state_objective": component_metric(combined, "state_observations", "objective_value"),
        "nmr_state_rmse": component_metric(combined, "state_observations", "primary_metric_value"),
    }
    return run_row, timestep_frame


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    ert_diag.patch_meshio_vtu_compressed_appended_reader()
    static = load_static_inputs(args)
    ert_cache: dict[str, np.ndarray] = {}
    run_rows: list[dict[str, Any]] = []
    timestep_frames: list[pd.DataFrame] = []
    run_dirs = sorted(path.parent for path in args.runs_dir.glob("*/ogs_output"))

    for run_dir in run_dirs:
        if not (run_dir / "bulk_w_projections.vtu").is_file():
            continue
        run_row, timestep_frame = evaluate_run(args, run_dir, static, ert_cache)
        run_rows.append(run_row)
        timestep_frames.append(timestep_frame)
        print(
            f"{run_dir.name}: compared {run_row['compared_rows']} rows, "
            f"MAE={run_row['ert_residual_mae_log10']:.6f}",
            flush=True,
        )

    runs = pd.DataFrame(run_rows)
    timesteps = pd.concat(timestep_frames, ignore_index=True) if timestep_frames else pd.DataFrame()
    summary = summarize_runs(runs)
    summary["candidate_output_run_dirs_found"] = int(len(run_dirs))
    summary["support_column"] = args.support_column
    summary["max_time_delta_days"] = args.max_time_delta_days
    return runs, timesteps, summary


def summarize_runs(runs: pd.DataFrame) -> dict[str, Any]:
    if runs.empty:
        return {
            "status": "ert_candidate_discrimination_no_ogs_outputs",
            "run_count": 0,
            "activation_gate": "No existing OGS output directories were found.",
        }

    direct = runs[runs["run_id"].eq("direct_fit_observation_run")]
    reference_mae = (
        float(direct["ert_residual_mae_log10"].iloc[0])
        if not direct.empty and finite(direct["ert_residual_mae_log10"].iloc[0])
        else float(pd.to_numeric(runs["ert_residual_mae_log10"], errors="coerce").median())
    )
    runs["ert_mae_delta_from_reference"] = pd.to_numeric(runs["ert_residual_mae_log10"], errors="coerce") - reference_mae
    runs["ert_mae_rank"] = pd.to_numeric(runs["ert_residual_mae_log10"], errors="coerce").rank(method="min")
    runs["combined_objective_rank"] = pd.to_numeric(runs["combined_active_objective"], errors="coerce").rank(method="min")
    best_ert = runs.sort_values("ert_residual_mae_log10", na_position="last").iloc[0]
    worst_ert = runs.sort_values("ert_residual_mae_log10", ascending=False, na_position="last").iloc[0]
    full_combined = runs[
        pd.to_numeric(runs["combined_active_component_count"], errors="coerce").ge(2)
        & pd.to_numeric(runs["nmr_state_objective"], errors="coerce").notna()
        & pd.to_numeric(runs["combined_active_objective"], errors="coerce").notna()
    ].copy()
    best_combined = (
        full_combined.sort_values("combined_active_objective", na_position="last").iloc[0]
        if not full_combined.empty
        else runs.sort_values("combined_active_objective", na_position="last").iloc[0]
    )
    ert_numeric = pd.to_numeric(runs["ert_residual_mae_log10"], errors="coerce")
    return {
        "status": "ert_candidate_discrimination_audit_generated_transform_support_unconfirmed",
        "run_count": int(runs.shape[0]),
        "runs_with_combined_objective": int(runs["combined_active_objective"].notna().sum()),
        "runs_with_full_active_combined_objective": int(full_combined.shape[0]),
        "compared_rows_per_run": int(pd.to_numeric(runs["compared_rows"], errors="coerce").median()),
        "compared_output_times_per_run": int(pd.to_numeric(runs["compared_output_times"], errors="coerce").median()),
        "support_cell_rows": int(pd.to_numeric(runs["support_cell_rows"], errors="coerce").median()),
        "reference_run": "direct_fit_observation_run" if not direct.empty else str(runs.iloc[0]["run_id"]),
        "reference_ert_mae_log10": reference_mae,
        "ert_mae_log10_summary": summarize_numeric(runs["ert_residual_mae_log10"]),
        "ert_mae_log10_range": float(ert_numeric.max() - ert_numeric.min()),
        "best_ert_run": str(best_ert["run_id"]),
        "best_ert_mae_log10": float(best_ert["ert_residual_mae_log10"]),
        "worst_ert_run": str(worst_ert["run_id"]),
        "worst_ert_mae_log10": float(worst_ert["ert_residual_mae_log10"]),
        "best_combined_run": str(best_combined["run_id"]),
        "best_combined_objective": float(best_combined["combined_active_objective"])
        if finite(best_combined["combined_active_objective"])
        else None,
        "best_combined_ert_mae_log10": float(best_combined["ert_residual_mae_log10"])
        if finite(best_combined["ert_residual_mae_log10"])
        else None,
        "combined_objective_ert_mae_correlation": correlation(
            runs,
            "combined_active_objective",
            "ert_residual_mae_log10",
        ),
        "nmr_state_ert_mae_correlation": correlation(runs, "nmr_state_objective", "ert_residual_mae_log10"),
        "run_kind_counts": {
            str(key): int(value) for key, value in runs["run_kind"].value_counts().sort_index().items()
        },
        "activation_gate": (
            "Use this only as cross-candidate diagnostic evidence. ERT remains outside the active "
            "likelihood until the ERT-to-OGS transform, exact support mask, and uncertainty/correlation "
            "model are accepted."
        ),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, runs: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# ERT Candidate Discrimination Audit",
        "",
        "This audit evaluates the ERT log-resistivity diagnostic across existing executed runs with OGS output fields.",
        "It is diagnostic only and is not assembled into the active objective.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs audited: {summary['run_count']}",
        f"- Runs with combined objective: {summary.get('runs_with_combined_objective', 0)}",
        f"- Runs with full active combined objective: {summary.get('runs_with_full_active_combined_objective', 0)}",
        f"- Support cells per compared output: {summary.get('support_cell_rows', 'n/a')}",
        f"- Compared rows per run: {summary.get('compared_rows_per_run', 'n/a')}",
        f"- Compared output times per run: {summary.get('compared_output_times_per_run', 'n/a')}",
        f"- Reference run: `{summary.get('reference_run', 'n/a')}`",
        f"- ERT MAE range across audited runs: {fmt(summary.get('ert_mae_log10_range'))} log10 units",
        f"- Best ERT run: `{summary.get('best_ert_run', 'n/a')}` with MAE {fmt(summary.get('best_ert_mae_log10'))}",
        f"- Best active-objective run: `{summary.get('best_combined_run', 'n/a')}` with ERT MAE {fmt(summary.get('best_combined_ert_mae_log10'))}",
        f"- Combined-objective/ERT-MAE correlation: {fmt(summary.get('combined_objective_ert_mae_correlation'))}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Top Runs By ERT Log-Resistivity MAE",
        "",
        "| Run | Kind | ERT MAE | Delta vs reference | Combined objective | NMR objective |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in runs.sort_values("ert_residual_mae_log10").head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    fmt(row["ert_residual_mae_log10"]),
                    fmt(row["ert_mae_delta_from_reference"]),
                    fmt(row["combined_active_objective"]),
                    fmt(row["nmr_state_objective"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The ERT range measures how much the currently executed permeability-field family changes the provisional OGS-to-ERT log-resistivity diagnostic. A small range means the family barely changes ERT under the present support and transform assumptions; a larger range would justify using ERT as a stronger candidate-screening diagnostic after the geometry and uncertainty gates are accepted.",
            "",
            "The audit deliberately keeps ERT outside the likelihood. The remaining activation requirements are collaborator acceptance of the ERT-to-OGS coordinate transform, the exact near-niche support mask, and an uncertainty/correlation model for the ERT inversion cells.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def planned_catalogue_copies(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    derived_dir = catalogue_dir / "derived_files"
    return [
        {
            "source": str(path),
            "catalogue_copy": str(derived_dir / path.name),
        }
        for path in paths
    ]


def copy_catalogue_outputs(planned: list[dict[str, str]]) -> None:
    for item in planned:
        source = Path(item["source"])
        destination = Path(item["catalogue_copy"])
        if not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> None:
    args = parse_args()
    if args.reuse_existing:
        if not args.output.exists():
            raise SystemExit(f"cannot reuse missing audit CSV: {args.output}")
        runs = pd.read_csv(args.output)
        timesteps = pd.read_csv(args.timestep_output) if args.timestep_output.exists() else pd.DataFrame()
        summary = summarize_runs(runs)
        summary["candidate_output_run_dirs_found"] = int(runs.shape[0])
        summary["support_column"] = args.support_column
        summary["max_time_delta_days"] = args.max_time_delta_days
    else:
        runs, timesteps, summary = build_audit(args)
    output_paths = [args.output, args.timestep_output, args.summary_output, args.markdown_output]
    summary["catalogue_copies"] = planned_catalogue_copies(args.catalogue_dir, output_paths)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    runs.to_csv(args.output, index=False)
    timesteps.to_csv(args.timestep_output, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.markdown_output, runs, summary)
    copy_catalogue_outputs(summary["catalogue_copies"])
    print(f"wrote {args.output}")
    print(f"wrote {args.timestep_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"copied {len(summary['catalogue_copies'])} files to {args.catalogue_dir / 'derived_files'}")
    print(f"runs audited: {summary['run_count']}")


if __name__ == "__main__":
    main()
