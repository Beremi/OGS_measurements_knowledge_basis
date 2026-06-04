#!/usr/bin/env python3
"""Audit whether Taupe/TDR trend diagnostics distinguish executed candidates.

This script reuses the run-local Taupe trend diagnostic for every run directory
that already has sampled OGS state outputs.  It does not activate Taupe/TDR in
the likelihood; it quantifies whether the existing executed permeability fields
produce meaningfully different Taupe trend scores.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import evaluate_taupe_tdr_trend_diagnostic as taupe_diag


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("inversion_workflow/runs"),
    )
    parser.add_argument(
        "--taupe-operator",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_trend_operator.csv"),
    )
    parser.add_argument(
        "--taupe-bands",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_bands.csv"),
    )
    parser.add_argument(
        "--target-samples",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_samples.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--series-output",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_series.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/taupe_tdr"),
        help="Measurement-catalogue directory where derived audit copies are stored.",
    )
    parser.add_argument(
        "--max-time-delta-days",
        type=float,
        default=20.0,
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


def diagnostic_args(args: argparse.Namespace, state_samples: Path) -> argparse.Namespace:
    run_dir = state_samples.parent
    return argparse.Namespace(
        taupe_operator=args.taupe_operator,
        taupe_bands=args.taupe_bands,
        target_samples=args.target_samples,
        ogs_state_samples=state_samples,
        state_quantity=taupe_diag.STATE_QUANTITY,
        output=run_dir / "taupe_tdr_trend_diagnostic.csv",
        series_output=run_dir / "taupe_tdr_trend_diagnostic_series.csv",
        summary_output=run_dir / "taupe_tdr_trend_diagnostic_summary.json",
        markdown_output=run_dir / "taupe_tdr_trend_diagnostic.md",
        time_origin=taupe_diag.DEFAULT_ORIGIN,
        max_time_delta_days=args.max_time_delta_days,
    )


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


def summarize_runs(runs: pd.DataFrame) -> dict[str, Any]:
    if runs.empty:
        return {
            "status": "taupe_candidate_discrimination_no_state_samples",
            "run_count": 0,
            "activation_gate": "No existing OGS state samples were found.",
        }

    direct = runs[runs["run_id"].eq("direct_fit_observation_run")]
    reference_mae = (
        float(direct["taupe_trend_mae"].iloc[0])
        if not direct.empty and finite(direct["taupe_trend_mae"].iloc[0])
        else float(pd.to_numeric(runs["taupe_trend_mae"], errors="coerce").median())
    )
    runs["taupe_mae_delta_from_reference"] = pd.to_numeric(runs["taupe_trend_mae"], errors="coerce") - reference_mae
    runs["taupe_mae_rank"] = pd.to_numeric(runs["taupe_trend_mae"], errors="coerce").rank(method="min")
    runs["combined_objective_rank"] = pd.to_numeric(runs["combined_active_objective"], errors="coerce").rank(method="min")
    best_taupe = runs.sort_values("taupe_trend_mae", na_position="last").iloc[0]
    worst_taupe = runs.sort_values("taupe_trend_mae", ascending=False, na_position="last").iloc[0]
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
    taupe_numeric = pd.to_numeric(runs["taupe_trend_mae"], errors="coerce")
    return {
        "status": "taupe_candidate_discrimination_audit_generated_not_active_likelihood",
        "run_count": int(runs.shape[0]),
        "runs_with_combined_objective": int(runs["combined_active_objective"].notna().sum()),
        "runs_with_full_active_combined_objective": int(full_combined.shape[0]),
        "compared_rows_per_run": int(pd.to_numeric(runs["compared_rows"], errors="coerce").median()),
        "compared_series_per_run": int(pd.to_numeric(runs["compared_series"], errors="coerce").median()),
        "reference_run": "direct_fit_observation_run" if not direct.empty else str(runs.iloc[0]["run_id"]),
        "reference_taupe_mae": reference_mae,
        "taupe_mae_summary": summarize_numeric(runs["taupe_trend_mae"]),
        "taupe_mae_range": float(taupe_numeric.max() - taupe_numeric.min()),
        "best_taupe_run": str(best_taupe["run_id"]),
        "best_taupe_mae": float(best_taupe["taupe_trend_mae"]),
        "worst_taupe_run": str(worst_taupe["run_id"]),
        "worst_taupe_mae": float(worst_taupe["taupe_trend_mae"]),
        "best_combined_run": str(best_combined["run_id"]),
        "best_combined_objective": float(best_combined["combined_active_objective"])
        if finite(best_combined["combined_active_objective"])
        else None,
        "best_combined_taupe_mae": float(best_combined["taupe_trend_mae"])
        if finite(best_combined["taupe_trend_mae"])
        else None,
        "combined_objective_taupe_mae_correlation": correlation(
            runs,
            "combined_active_objective",
            "taupe_trend_mae",
        ),
        "nmr_state_taupe_mae_correlation": correlation(runs, "nmr_state_objective", "taupe_trend_mae"),
        "run_kind_counts": {
            str(key): int(value) for key, value in runs["run_kind"].value_counts().sort_index().items()
        },
        "activation_gate": (
            "Use this only as cross-candidate diagnostic evidence. Taupe/TDR remains outside the active "
            "likelihood until workbook units, sensor calibration, trend uncertainty, and grouped weights are confirmed."
        ),
    }


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    state_sample_paths = sorted(args.runs_dir.glob("*/ogs_state_samples.csv"))
    run_rows: list[dict[str, Any]] = []
    series_rows: list[pd.DataFrame] = []

    for state_samples in state_sample_paths:
        run_dir = state_samples.parent
        run_id = run_dir.name
        diag_args = diagnostic_args(args, state_samples)
        diagnostic, series, taupe_summary, _markdown = taupe_diag.compare_rows(diag_args)
        combined = read_json(run_dir / "combined_objective_summary.json")
        run_rows.append(
            {
                "run_id": run_id,
                "run_kind": run_kind(run_id),
                "run_dir": str(run_dir),
                "state_sample_rows": taupe_summary.get("state_sample_rows"),
                "ogs_output_times": taupe_summary.get("ogs_output_times"),
                "diagnostic_rows": taupe_summary.get("diagnostic_rows"),
                "compared_rows": taupe_summary.get("compared_rows"),
                "compared_series": taupe_summary.get("compared_series"),
                "outside_time_tolerance_rows": taupe_summary.get("diagnostic_status_counts", {}).get(
                    "outside_time_tolerance",
                    0,
                ),
                "operator_not_mapped_rows": taupe_summary.get("diagnostic_status_counts", {}).get(
                    "operator_not_mapped_for_current_mesh",
                    0,
                ),
                "taupe_trend_residual_mean": taupe_summary.get("standardized_residual", {}).get("mean"),
                "taupe_trend_mae": taupe_summary.get("standardized_residual", {}).get("mae"),
                "taupe_trend_rmse": taupe_summary.get("standardized_residual", {}).get("rmse"),
                "taupe_trend_p50_abs": taupe_summary.get("standardized_residual", {}).get("p50_abs"),
                "taupe_trend_p90_abs": taupe_summary.get("standardized_residual", {}).get("p90_abs"),
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
        )
        if not series.empty:
            series = series.copy()
            series.insert(0, "run_id", run_id)
            series.insert(1, "run_kind", run_kind(run_id))
            series_rows.append(series)

    runs = pd.DataFrame(run_rows)
    all_series = pd.concat(series_rows, ignore_index=True) if series_rows else pd.DataFrame()
    summary = summarize_runs(runs)
    return runs, all_series, summary


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, runs: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Taupe/TDR Candidate Discrimination Audit",
        "",
        "This audit evaluates the Taupe/TDR trend diagnostic across existing executed runs with sampled OGS state outputs.",
        "It is diagnostic only and is not assembled into the active objective.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs audited: {summary['run_count']}",
        f"- Runs with combined objective: {summary.get('runs_with_combined_objective', 0)}",
        f"- Compared rows per run: {summary.get('compared_rows_per_run', 'n/a')}",
        f"- Compared series per run: {summary.get('compared_series_per_run', 'n/a')}",
        f"- Reference run: `{summary.get('reference_run', 'n/a')}`",
        f"- Taupe MAE range across audited runs: {fmt(summary.get('taupe_mae_range'))}",
        f"- Best Taupe run: `{summary.get('best_taupe_run', 'n/a')}` with MAE {fmt(summary.get('best_taupe_mae'))}",
        f"- Best active-objective run: `{summary.get('best_combined_run', 'n/a')}` with Taupe MAE {fmt(summary.get('best_combined_taupe_mae'))}",
        f"- Combined-objective/Taupe-MAE correlation: {fmt(summary.get('combined_objective_taupe_mae_correlation'))}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Top Runs By Taupe Trend MAE",
        "",
        "| Run | Kind | Taupe MAE | Delta vs reference | Combined objective | NMR objective |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in runs.sort_values("taupe_trend_mae").head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    fmt(row["taupe_trend_mae"]),
                    fmt(row["taupe_mae_delta_from_reference"]),
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
            "A small Taupe-MAE range means the currently executed permeability-field family barely changes the mapped A3/A4 Taupe trend diagnostic. That would make Taupe a weak discriminator for this candidate family even if the unit/calibration gate were later resolved.",
            "",
            "The audit deliberately keeps Taupe outside the likelihood. The remaining activation requirements are the Taupe workbook unit, sensor-specific calibration or accepted trend-only scale, grouped series weights, and collaborator acceptance of the A3/A4 support mapping.",
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
        series = pd.read_csv(args.series_output) if args.series_output.exists() else pd.DataFrame()
        summary = summarize_runs(runs)
    else:
        runs, series, summary = build_audit(args)
    output_paths = [args.output, args.series_output, args.summary_output, args.markdown_output]
    summary["catalogue_copies"] = planned_catalogue_copies(args.catalogue_dir, output_paths)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    runs.to_csv(args.output, index=False)
    series.to_csv(args.series_output, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.markdown_output, runs, summary)
    copy_catalogue_outputs(summary["catalogue_copies"])
    print(f"wrote {args.output}")
    print(f"wrote {args.series_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"copied {len(summary['catalogue_copies'])} files to {args.catalogue_dir / 'derived_files'}")
    print(f"runs audited: {summary['run_count']}")


if __name__ == "__main__":
    main()
