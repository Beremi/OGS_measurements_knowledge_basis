#!/usr/bin/env python3
"""Audit ERT diagnostic sensitivity to the provisional near-niche support mask.

The current ERT diagnostic uses an approximate 1.5 m centre-radius support because
the exact agreed "near tunnel" ERT/FEM support contour is not available.  This
script does not claim to resolve that gate.  It quantifies how selected executed
candidate comparisons change when the same row-level residuals are restricted to
tighter radial caps inside the current support.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_ert_resistivity_diagnostic as ert_diag  # noqa: E402


DEFAULT_RUN_IDS = [
    "direct_fit_observation_run",
    "local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000",
    "local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000",
    "broad_continuous_001_001_length_0p023m_shift_1p004",
    "broad_continuous_001_003_length_0p021m",
    "adaptive_combined_001_length_0p050m",
]

RADIUS_CAPS = [1.20, 1.25, 1.30, 1.35, 1.40, 1.45, 1.50]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("inversion_workflow/runs"))
    parser.add_argument(
        "--run-ids",
        default=",".join(DEFAULT_RUN_IDS),
        help="Comma-separated run ids to audit. Defaults to stream winners and reference runs.",
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
        help="Base boolean lookup column used by the ERT diagnostic before radial sensitivity filters.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/ert_support_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--timestep-output",
        type=Path,
        default=Path("inversion_workflow/ert_support_sensitivity_timesteps.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/ert_support_sensitivity_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/ert_support_sensitivity.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/ert"),
        help="Measurement-catalogue directory where derived audit copies are stored.",
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


def run_kind(run_id: str) -> str:
    if run_id == "direct_fit_observation_run":
        return "direct_reference"
    if run_id.startswith("local_basis"):
        return "local_basis"
    if run_id.startswith("production_sampler_round"):
        return "production_sampler_round"
    if run_id.startswith("lower_support"):
        return "lower_support"
    if run_id.startswith("broad_continuous"):
        return "broad_continuous"
    if run_id.startswith("adaptive_combined"):
        return "adaptive_combined"
    return "other"


def parse_run_ids(text: str) -> list[str]:
    run_ids = [item.strip() for item in text.split(",") if item.strip()]
    if not run_ids:
        raise ValueError("at least one run id must be supplied")
    return run_ids


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


def weighted_stats(frame: pd.DataFrame) -> dict[str, float | None]:
    residual = pd.to_numeric(frame["residual_log10_pred_minus_ert"], errors="coerce").to_numpy(dtype=float)
    weights = pd.to_numeric(frame["ert_cell_area_m2_transformed"], errors="coerce").to_numpy(dtype=float)
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


def read_existing_diagnostic(run_dir: Path) -> pd.DataFrame | None:
    path = run_dir / "ert_resistivity_diagnostic.csv"
    if not path.is_file():
        return None
    frame = pd.read_csv(path)
    required = {
        "model_x",
        "model_y",
        "diagnostic_status",
        "output_file",
        "ert_cell_id",
        "ert_cell_area_m2_transformed",
        "residual_log10_pred_minus_ert",
    }
    if required.issubset(set(frame.columns)):
        return frame
    return None


def evaluate_run(args: argparse.Namespace, run_dir: Path) -> pd.DataFrame:
    existing = read_existing_diagnostic(run_dir)
    if existing is not None:
        return existing
    output_dir = run_dir / "ogs_output"
    support_mesh = run_dir / "bulk_w_projections.vtu"
    if not output_dir.is_dir() or not support_mesh.is_file():
        raise FileNotFoundError(f"{run_dir.name} lacks OGS output or support mesh")
    eval_args = argparse.Namespace(
        ogs_output_dir=output_dir,
        support_mesh=support_mesh,
        processed_dir=args.processed_dir,
        ert_zip=args.ert_zip,
        porosity_field=args.porosity_field,
        time_origin=args.time_origin,
        max_time_delta_days=args.max_time_delta_days,
        support_column=args.support_column,
        output=Path("/dev/null"),
        timestep_output=Path("/dev/null"),
        summary_output=Path("/dev/null"),
        markdown_output=Path("/dev/null"),
    )
    diagnostic, _timesteps, _summary, _markdown = ert_diag.evaluate(eval_args)
    return diagnostic


def support_variants(frame: pd.DataFrame) -> list[tuple[str, str, pd.Series]]:
    radius = np.sqrt(
        pd.to_numeric(frame["model_x"], errors="coerce") ** 2
        + pd.to_numeric(frame["model_y"], errors="coerce") ** 2
    )
    variants: list[tuple[str, str, pd.Series]] = []
    for cap in RADIUS_CAPS:
        label = f"radius_le_{str(cap).replace('.', 'p')}m"
        description = f"cumulative radial cap r <= {cap:.2f} m inside the current ERT support"
        variants.append((label, description, radius <= cap))
    variants.append(
        (
            "inner_annulus_1p15_1p30m",
            "inner available annulus 1.15 m < r <= 1.30 m",
            (radius > 1.15) & (radius <= 1.30),
        )
    )
    variants.append(
        (
            "outer_annulus_1p30_1p50m",
            "outer available annulus 1.30 m < r <= 1.50 m",
            (radius > 1.30) & (radius <= 1.50),
        )
    )
    return variants


def summarize_variant(run_id: str, kind: str, variant_id: str, description: str, frame: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    compared = frame[frame["diagnostic_status"].astype(str).eq("diagnostic_compared")].copy()
    stats = weighted_stats(compared)
    timestep_rows: list[dict[str, Any]] = []
    for output_file, group in compared.groupby("output_file", sort=True):
        output_stats = weighted_stats(group)
        first = group.iloc[0]
        timestep_rows.append(
            {
                "run_id": run_id,
                "run_kind": kind,
                "support_variant": variant_id,
                "output_file": output_file,
                "model_time_s": first.get("model_time_s"),
                "model_datetime": first.get("model_datetime"),
                "ert_timestamp_iso": first.get("ert_timestamp_iso"),
                "time_delta_days_ert_minus_model": first.get("time_delta_days_ert_minus_model"),
                "finite_residual_rows": int(group.shape[0]),
                "support_cell_count": int(group["ert_cell_id"].nunique()),
                "area_weighted_mean_residual_log10": output_stats["mean"],
                "area_weighted_mae_log10": output_stats["mae"],
                "area_weighted_rmse_log10": output_stats["rmse"],
            }
        )
    timestep_frame = pd.DataFrame(timestep_rows)
    time_mae = pd.to_numeric(timestep_frame.get("area_weighted_mae_log10"), errors="coerce")
    row = {
        "run_id": run_id,
        "run_kind": kind,
        "support_variant": variant_id,
        "support_description": description,
        "support_cell_count": int(compared["ert_cell_id"].nunique()) if not compared.empty else 0,
        "compared_output_times": int(compared["output_file"].nunique()) if not compared.empty else 0,
        "compared_rows": int(compared.shape[0]),
        "area_weighted_mean_residual_log10": stats["mean"],
        "area_weighted_mae_log10": stats["mae"],
        "area_weighted_rmse_log10": stats["rmse"],
        "area_weighted_p50_abs_log10": stats["p50_abs"],
        "area_weighted_p90_abs_log10": stats["p90_abs"],
        "mean_output_mae_log10": float(time_mae.mean()) if not time_mae.empty else None,
        "std_output_mae_log10": float(time_mae.std(ddof=1)) if time_mae.shape[0] > 1 else 0.0,
        "p90_output_mae_log10": float(time_mae.quantile(0.90)) if not time_mae.empty else None,
    }
    return row, timestep_rows


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    ert_diag.patch_meshio_vtu_compressed_appended_reader()
    run_rows: list[dict[str, Any]] = []
    timestep_rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for run_id in parse_run_ids(args.run_ids):
        run_dir = args.runs_dir / run_id
        if not run_dir.is_dir():
            skipped.append({"run_id": run_id, "reason": "run_directory_missing"})
            continue
        try:
            diagnostic = evaluate_run(args, run_dir)
        except Exception as exc:  # noqa: BLE001 - keep audit going and record failed run.
            skipped.append({"run_id": run_id, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        kind = run_kind(run_id)
        for variant_id, description, mask in support_variants(diagnostic):
            selected = diagnostic[mask].copy()
            if selected.empty:
                continue
            row, rows = summarize_variant(run_id, kind, variant_id, description, selected)
            run_rows.append(row)
            timestep_rows.extend(rows)
    runs = pd.DataFrame(run_rows)
    timesteps = pd.DataFrame(timestep_rows)
    if not runs.empty:
        runs["ert_mae_rank_within_support"] = runs.groupby("support_variant")[
            "area_weighted_mae_log10"
        ].rank(method="min")
        default_variant = "radius_le_1p5m"
        default = runs[runs["support_variant"].eq(default_variant)][
            ["run_id", "ert_mae_rank_within_support", "area_weighted_mae_log10"]
        ].rename(
            columns={
                "ert_mae_rank_within_support": "default_support_rank",
                "area_weighted_mae_log10": "default_support_mae_log10",
            }
        )
        runs = runs.merge(default, on="run_id", how="left")
        runs["rank_delta_vs_default"] = runs["ert_mae_rank_within_support"] - runs["default_support_rank"]
    summary = summarize(runs, skipped)
    return runs, timesteps, summary


def best_row(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    valid = frame[pd.to_numeric(frame[column], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    valid[column] = pd.to_numeric(valid[column], errors="coerce")
    return json_ready(valid.sort_values([column, "run_id"], na_position="last").iloc[0].to_dict())


def rank_correlation(frame: pd.DataFrame, variant: str) -> float | None:
    default = frame[frame["support_variant"].eq("radius_le_1p5m")][["run_id", "ert_mae_rank_within_support"]]
    other = frame[frame["support_variant"].eq(variant)][["run_id", "ert_mae_rank_within_support"]]
    joined = default.merge(other, on="run_id", suffixes=("_default", "_variant"))
    if joined.shape[0] < 3:
        return None
    return float(joined["ert_mae_rank_within_support_default"].corr(joined["ert_mae_rank_within_support_variant"]))


def summarize(runs: pd.DataFrame, skipped: list[dict[str, str]]) -> dict[str, Any]:
    if runs.empty:
        return {
            "status": "ert_support_sensitivity_no_runs",
            "skipped_runs": skipped,
            "activation_gate": "No selected runs could be evaluated.",
        }
    winners: dict[str, dict[str, Any]] = {}
    rank_correlations: dict[str, float | None] = {}
    for variant, group in runs.groupby("support_variant"):
        winners[str(variant)] = best_row(group, "area_weighted_mae_log10")
        if variant != "radius_le_1p5m":
            rank_correlations[str(variant)] = rank_correlation(runs, str(variant))
    mean_ranks = (
        runs.groupby(["run_id", "run_kind"], as_index=False)["ert_mae_rank_within_support"]
        .mean()
        .rename(columns={"ert_mae_rank_within_support": "mean_ert_support_rank"})
    )
    worst_ranks = (
        runs.groupby(["run_id"], as_index=False)["ert_mae_rank_within_support"]
        .max()
        .rename(columns={"ert_mae_rank_within_support": "worst_ert_support_rank"})
    )
    rank_summary = mean_ranks.merge(worst_ranks, on="run_id")
    return {
        "status": "ert_support_sensitivity_generated_transform_still_unconfirmed",
        "run_count": int(runs["run_id"].nunique()),
        "support_variant_count": int(runs["support_variant"].nunique()),
        "support_variants": sorted(runs["support_variant"].unique().tolist()),
        "skipped_runs": skipped,
        "winners_by_support_variant": winners,
        "best_mean_support_rank": best_row(rank_summary, "mean_ert_support_rank"),
        "rank_correlations_vs_default_support": rank_correlations,
        "activation_gate": (
            "Diagnostic only: this audit quantifies sensitivity inside the current approximate ERT support. "
            "It does not confirm the ERT-to-OGS transform, exact tunnel-contour support mask, or ERT "
            "inversion uncertainty/correlation model."
        ),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, runs: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# ERT Support Sensitivity Audit",
        "",
        "This audit quantifies how selected executed OGS candidates rank under tighter radial subsets of the current provisional ERT support.",
        "It does not activate ERT in the likelihood.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs evaluated: {summary.get('run_count', 0)}",
        f"- Support variants: {summary.get('support_variant_count', 0)}",
        f"- Best mean support-rank run: `{summary.get('best_mean_support_rank', {}).get('run_id', 'n/a')}` with mean rank {fmt(summary.get('best_mean_support_rank', {}).get('mean_ert_support_rank'), 2)}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Winners By Support Variant",
        "",
        "| Support variant | Winner | Cells/output | MAE log10 | RMSE log10 | Rank correlation to default |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for variant, row in summary.get("winners_by_support_variant", {}).items():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{variant}`",
                    f"`{row.get('run_id', 'n/a')}`",
                    str(row.get("support_cell_count", "n/a")),
                    fmt(row.get("area_weighted_mae_log10")),
                    fmt(row.get("area_weighted_rmse_log10")),
                    fmt(summary.get("rank_correlations_vs_default_support", {}).get(variant), 3)
                    if variant != "radius_le_1p5m"
                    else "1.000",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Selected Run Scores",
            "",
            "| Run | Kind | Support | Cells/output | MAE log10 | RMSE log10 | Rank | Rank delta vs default |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    shown = runs.sort_values(["support_variant", "ert_mae_rank_within_support", "run_id"])
    for _, row in shown.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    f"`{row['support_variant']}`",
                    str(int(row["support_cell_count"])),
                    fmt(row["area_weighted_mae_log10"]),
                    fmt(row["area_weighted_rmse_log10"]),
                    fmt(row["ert_mae_rank_within_support"], 2),
                    fmt(row["rank_delta_vs_default"], 2),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The radial caps are a local sensitivity proxy inside the already documented `ready_for_residual_after_ogs_output` mask. They are not a substitute for the missing agreed ERT/FEM tunnel-contour support definition.",
            "If the ERT winner or ranking changes strongly across these variants, the ERT stream should remain a diagnostic screen until the exact support and covariance model are fixed.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def planned_catalogue_copies(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    derived_dir = catalogue_dir / "derived_files"
    return [{"source": str(path), "catalogue_copy": str(derived_dir / path.name)} for path in paths]


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
    print(f"runs evaluated: {summary.get('run_count', 0)}")


if __name__ == "__main__":
    main()
