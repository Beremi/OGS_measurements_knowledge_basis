#!/usr/bin/env python3
"""Audit NMR candidate ranking sensitivity to bound/interlayer-water treatment.

The current active state residual compares sampled OGS theta = porosity*saturation
directly to raw NMR volumetric water content.  The separate NMR bound-water audit
shows that this absolute comparison is physically caveated.  This script keeps the
current objective unchanged, but quantifies how executed candidate rankings would
change under simple diagnostic alternatives:

* uniform subtraction of a candidate bound/interlayer-water offset,
* fitted non-negative per-label bias terms, and
* within-label anomaly residuals where constant offsets cancel.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OFFSETS = [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10]
GROUP_COLUMNS = ["observation_family", "measurement_label"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("inversion_workflow/runs"),
    )
    parser.add_argument(
        "--bound-water-summary",
        type=Path,
        default=Path("inversion_workflow/processed_observations/nmr_bound_water_sensitivity_summary.json"),
    )
    parser.add_argument(
        "--offsets",
        default=None,
        help="Comma-separated bound-water offsets to test. Defaults to the generated NMR bound-water audit offsets.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--offset-output",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_offsets.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/nmr"),
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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_offsets(args: argparse.Namespace, bound_summary: dict[str, Any]) -> list[float]:
    if args.offsets:
        text = args.offsets
    else:
        values = bound_summary.get("offsets_tested") or DEFAULT_OFFSETS
        return sorted({float(value) for value in values})
    offsets = []
    for item in text.split(","):
        item = item.strip()
        if item:
            offsets.append(float(item))
    if not offsets:
        raise ValueError("at least one offset must be supplied")
    return sorted(set(offsets))


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


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


def objective_from_residual(residual: pd.Series, sigma: pd.Series) -> float:
    residual_values = pd.to_numeric(residual, errors="coerce").to_numpy(dtype=float)
    sigma_values = pd.to_numeric(sigma, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(residual_values) & np.isfinite(sigma_values) & (sigma_values > 0.0)
    if not mask.any():
        return np.nan
    normalized = residual_values[mask] / sigma_values[mask]
    return float(0.5 * np.sum(normalized**2))


def rmse_from_objective(objective: float, rows: int) -> float | None:
    if rows <= 0 or not finite(objective):
        return None
    return float(np.sqrt(2.0 * float(objective) / rows))


def active_nmr_rows(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    active = frame[
        bool_series(frame["used_in_objective"])
        & frame["observation_family"].astype(str).str.startswith("NMR")
        & frame["evaluation_status"].astype(str).eq("evaluated")
    ].copy()
    if active.empty:
        return active
    for column in ["observed_value", "observed_sigma", "predicted_value", "objective_contribution"]:
        active[column] = pd.to_numeric(active[column], errors="coerce")
    active["observed_sigma"] = active["observed_sigma"].where(active["observed_sigma"] > 0.0, 0.01)
    active["label_group"] = active[GROUP_COLUMNS].astype(str).agg(" | ".join, axis=1)
    return active


def uniform_offset_rows(
    run_id: str,
    kind: str,
    active: pd.DataFrame,
    direct_objective: float | None,
    offsets: list[float],
    fixed_phi: float | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset in offsets:
        adjusted_observed = active["observed_value"] - offset
        residual = active["predicted_value"] - adjusted_observed
        objective = objective_from_residual(residual, active["observed_sigma"])
        corrected_nonphysical = 0
        corrected_above_phi = None
        corrected_negative = None
        if fixed_phi is not None:
            corrected_above_phi = int(adjusted_observed.gt(fixed_phi).sum())
            corrected_negative = int(adjusted_observed.lt(0.0).sum())
            corrected_nonphysical = corrected_above_phi + corrected_negative
        rows.append(
            {
                "run_id": run_id,
                "run_kind": kind,
                "offset_fraction": offset,
                "active_nmr_rows": int(active.shape[0]),
                "nmr_offset_objective": objective,
                "nmr_offset_rmse_normalized_residual": rmse_from_objective(objective, int(active.shape[0])),
                "direct_permeability_objective": direct_objective,
                "combined_offset_objective": (direct_objective + objective)
                if finite(direct_objective) and finite(objective)
                else None,
                "corrected_rows_above_fixed_phi": corrected_above_phi,
                "corrected_negative_free_water_rows": corrected_negative,
                "corrected_nonphysical_rows": corrected_nonphysical,
            }
        )
    return rows


def fitted_label_bias(active: pd.DataFrame) -> tuple[float, float | None, pd.DataFrame]:
    rows = []
    residual_pieces = []
    sigma_pieces = []
    for label, group in active.groupby("label_group", dropna=False):
        sigma = group["observed_sigma"].to_numpy(dtype=float)
        weights = np.where(np.isfinite(sigma) & (sigma > 0.0), 1.0 / sigma**2, 0.0)
        raw_bias = np.average(
            (group["observed_value"] - group["predicted_value"]).to_numpy(dtype=float),
            weights=weights,
        )
        bias = max(0.0, float(raw_bias))
        residual = group["predicted_value"] + bias - group["observed_value"]
        residual_pieces.append(residual)
        sigma_pieces.append(group["observed_sigma"])
        rows.append(
            {
                "label_group": label,
                "row_count": int(group.shape[0]),
                "fitted_bias_fraction": bias,
                "raw_weighted_bias_fraction": float(raw_bias),
                "observed_theta_mean": float(group["observed_value"].mean()),
                "predicted_theta_mean": float(group["predicted_value"].mean()),
            }
        )
    residual_all = pd.concat(residual_pieces, ignore_index=True) if residual_pieces else pd.Series(dtype=float)
    sigma_all = pd.concat(sigma_pieces, ignore_index=True) if sigma_pieces else pd.Series(dtype=float)
    objective = objective_from_residual(residual_all, sigma_all)
    rmse = rmse_from_objective(objective, int(active.shape[0]))
    return objective, rmse, pd.DataFrame(rows)


def trend_anomaly_objective(active: pd.DataFrame) -> tuple[float, float | None, int, int]:
    residual_pieces = []
    sigma_pieces = []
    group_count = 0
    row_count = 0
    for _label, group in active.groupby("label_group", dropna=False):
        if group.shape[0] < 2:
            continue
        sigma = group["observed_sigma"].to_numpy(dtype=float)
        weights = np.where(np.isfinite(sigma) & (sigma > 0.0), 1.0 / sigma**2, 0.0)
        if weights.sum() <= 0.0:
            continue
        observed = group["observed_value"].to_numpy(dtype=float)
        predicted = group["predicted_value"].to_numpy(dtype=float)
        observed_mean = float(np.average(observed, weights=weights))
        predicted_mean = float(np.average(predicted, weights=weights))
        residual = pd.Series((predicted - predicted_mean) - (observed - observed_mean))
        residual_pieces.append(residual)
        sigma_pieces.append(group["observed_sigma"].reset_index(drop=True))
        group_count += 1
        row_count += int(group.shape[0])
    residual_all = pd.concat(residual_pieces, ignore_index=True) if residual_pieces else pd.Series(dtype=float)
    sigma_all = pd.concat(sigma_pieces, ignore_index=True) if sigma_pieces else pd.Series(dtype=float)
    objective = objective_from_residual(residual_all, sigma_all)
    return objective, rmse_from_objective(objective, row_count), row_count, group_count


def best_row(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    valid = frame[pd.to_numeric(frame[column], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    valid[column] = pd.to_numeric(valid[column], errors="coerce")
    return json_ready(valid.sort_values(column, na_position="last").iloc[0].to_dict())


def rank_correlation(frame: pd.DataFrame, x: str, y: str) -> float | None:
    clean = frame[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 3:
        return None
    return float(clean[x].rank(method="average").corr(clean[y].rank(method="average")))


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame]:
    bound_summary = read_json(args.bound_water_summary)
    fixed_phi = bound_summary.get("fixed_phi")
    fixed_phi = float(fixed_phi) if finite(fixed_phi) else None
    offsets = parse_offsets(args, bound_summary)
    run_rows: list[dict[str, Any]] = []
    offset_rows_all: list[dict[str, Any]] = []
    label_bias_rows: list[pd.DataFrame] = []

    for state_eval_path in sorted(args.runs_dir.glob("*/state_observation_evaluation.csv")):
        run_dir = state_eval_path.parent
        run_id = run_dir.name
        active = active_nmr_rows(state_eval_path)
        combined = read_json(run_dir / "combined_objective_summary.json")
        direct_objective = component_metric(combined, "direct_permeability_pulse_tests", "objective_value")
        nmr_state_objective = component_metric(combined, "state_observations", "objective_value")
        combined_objective = combined.get("total_active_objective_value")
        if active.empty:
            continue
        kind = run_kind(run_id)
        current_nmr_objective_from_rows = float(active["objective_contribution"].sum())
        offsets_for_run = uniform_offset_rows(run_id, kind, active, direct_objective, offsets, fixed_phi)
        offset_rows_all.extend(offsets_for_run)
        bias_objective, bias_rmse, bias_groups = fitted_label_bias(active)
        bias_groups.insert(0, "run_id", run_id)
        bias_groups.insert(1, "run_kind", kind)
        label_bias_rows.append(bias_groups)
        trend_objective, trend_rmse, trend_rows, trend_groups = trend_anomaly_objective(active)
        bias_values = pd.to_numeric(bias_groups["fitted_bias_fraction"], errors="coerce")
        run_rows.append(
            {
                "run_id": run_id,
                "run_kind": kind,
                "run_dir": str(run_dir),
                "active_nmr_rows": int(active.shape[0]),
                "active_nmr_label_groups": int(active["label_group"].nunique()),
                "active_nmr_weekly_rows": int(active["observation_family"].astype(str).eq("NMR weekly").sum()),
                "active_nmr_seasonal_rows": int(active["observation_family"].astype(str).eq("NMR seasonal").sum()),
                "current_nmr_objective_from_rows": current_nmr_objective_from_rows,
                "current_nmr_objective_from_summary": nmr_state_objective,
                "current_nmr_rmse_normalized_residual": rmse_from_objective(
                    current_nmr_objective_from_rows,
                    int(active.shape[0]),
                ),
                "direct_permeability_objective": direct_objective,
                "current_combined_objective": combined_objective,
                "combined_active_component_count": combined.get("active_component_count"),
                "label_bias_objective": bias_objective,
                "label_bias_rmse_normalized_residual": bias_rmse,
                "label_bias_combined_objective": (direct_objective + bias_objective)
                if finite(direct_objective) and finite(bias_objective)
                else None,
                "fitted_label_bias_mean": float(bias_values.mean()) if not bias_values.empty else np.nan,
                "fitted_label_bias_p50": float(bias_values.quantile(0.50)) if not bias_values.empty else np.nan,
                "fitted_label_bias_p90": float(bias_values.quantile(0.90)) if not bias_values.empty else np.nan,
                "fitted_label_bias_max": float(bias_values.max()) if not bias_values.empty else np.nan,
                "trend_anomaly_rows": int(trend_rows),
                "trend_anomaly_groups": int(trend_groups),
                "trend_anomaly_objective": trend_objective,
                "trend_anomaly_rmse_normalized_residual": trend_rmse,
                "trend_anomaly_combined_objective": (direct_objective + trend_objective)
                if finite(direct_objective) and finite(trend_objective)
                else None,
            }
        )

    runs = pd.DataFrame(run_rows)
    offsets_frame = pd.DataFrame(offset_rows_all)
    label_bias_frame = pd.concat(label_bias_rows, ignore_index=True) if label_bias_rows else pd.DataFrame()
    if not runs.empty:
        runs["current_combined_rank"] = pd.to_numeric(runs["current_combined_objective"], errors="coerce").rank(method="min")
        runs["label_bias_combined_rank"] = pd.to_numeric(runs["label_bias_combined_objective"], errors="coerce").rank(method="min")
        runs["trend_anomaly_combined_rank"] = pd.to_numeric(runs["trend_anomaly_combined_objective"], errors="coerce").rank(method="min")
    if not offsets_frame.empty:
        offsets_frame["combined_offset_rank"] = offsets_frame.groupby("offset_fraction")[
            "combined_offset_objective"
        ].rank(method="min")
    summary = summarize(runs, offsets_frame, bound_summary, offsets)
    return runs, offsets_frame, summary, label_bias_frame


def summarize(
    runs: pd.DataFrame,
    offsets_frame: pd.DataFrame,
    bound_summary: dict[str, Any],
    offsets: list[float],
) -> dict[str, Any]:
    if runs.empty:
        return {
            "status": "nmr_candidate_bias_sensitivity_no_active_nmr_rows",
            "run_count": 0,
            "activation_gate": "No active NMR rows were found in executed state-evaluation files.",
        }
    full_active = runs[
        pd.to_numeric(runs["combined_active_component_count"], errors="coerce").ge(2)
        & pd.to_numeric(runs["direct_permeability_objective"], errors="coerce").notna()
        & pd.to_numeric(runs["current_nmr_objective_from_summary"], errors="coerce").notna()
    ].copy()
    offset_best: dict[str, Any] = {}
    for offset, group in offsets_frame.groupby("offset_fraction"):
        full_group = group[group["run_id"].isin(set(full_active["run_id"]))].copy()
        if full_group.empty:
            continue
        offset_best[f"{float(offset):.6g}"] = best_row(full_group, "combined_offset_objective")
    return {
        "status": "nmr_candidate_bias_sensitivity_generated_current_objective_unchanged",
        "run_count": int(runs.shape[0]),
        "runs_with_full_active_combined_objective": int(full_active.shape[0]),
        "active_nmr_rows_per_run": int(pd.to_numeric(runs["active_nmr_rows"], errors="coerce").median()),
        "offsets_tested": offsets,
        "bound_water_summary": {
            "fixed_phi": bound_summary.get("fixed_phi"),
            "usable_current_mesh_rows": bound_summary.get("usable_current_mesh_rows"),
            "uncorrected_usable_rows_above_fixed_phi": bound_summary.get(
                "uncorrected_usable_rows_above_fixed_phi"
            ),
            "required_offset_quantiles_usable": bound_summary.get("required_offset_quantiles_usable"),
            "best_uniform_offset_by_simple_physical_count_usable": bound_summary.get(
                "best_uniform_offset_by_simple_physical_count_usable"
            ),
        },
        "best_current_combined": best_row(full_active, "current_combined_objective"),
        "best_label_bias_combined": best_row(full_active, "label_bias_combined_objective"),
        "best_trend_anomaly_combined": best_row(full_active, "trend_anomaly_combined_objective"),
        "best_by_uniform_offset": offset_best,
        "current_vs_label_bias_rank_correlation": rank_correlation(
            full_active,
            "current_combined_objective",
            "label_bias_combined_objective",
        ),
        "current_vs_trend_anomaly_rank_correlation": rank_correlation(
            full_active,
            "current_combined_objective",
            "trend_anomaly_combined_objective",
        ),
        "label_bias_objective_range": float(
            pd.to_numeric(full_active["label_bias_objective"], errors="coerce").max()
            - pd.to_numeric(full_active["label_bias_objective"], errors="coerce").min()
        ),
        "trend_anomaly_objective_range": float(
            pd.to_numeric(full_active["trend_anomaly_objective"], errors="coerce").max()
            - pd.to_numeric(full_active["trend_anomaly_objective"], errors="coerce").min()
        ),
        "activation_gate": (
            "Diagnostic only: current NMR objective is unchanged. Use label-bias or trend/anomaly "
            "forms only after accepting a bound/interlayer-water treatment and updating the likelihood model."
        ),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, runs: pd.DataFrame, offsets: pd.DataFrame, summary: dict[str, Any]) -> None:
    best_current = summary.get("best_current_combined", {})
    best_bias = summary.get("best_label_bias_combined", {})
    best_trend = summary.get("best_trend_anomaly_combined", {})
    lines = [
        "# NMR Candidate Bias Sensitivity Audit",
        "",
        "This audit checks whether the executed candidate ranking is robust to the documented NMR bound/interlayer-water caveat.",
        "It does not change the active objective.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs audited: {summary['run_count']}",
        f"- Runs with full active combined objective: {summary.get('runs_with_full_active_combined_objective', 0)}",
        f"- Active NMR rows per run: {summary.get('active_nmr_rows_per_run', 'n/a')}",
        f"- Current best combined run: `{best_current.get('run_id', 'n/a')}` with objective {fmt(best_current.get('current_combined_objective'))}",
        f"- Best per-label-bias run: `{best_bias.get('run_id', 'n/a')}` with diagnostic combined objective {fmt(best_bias.get('label_bias_combined_objective'))}",
        f"- Best within-label anomaly run: `{best_trend.get('run_id', 'n/a')}` with diagnostic combined objective {fmt(best_trend.get('trend_anomaly_combined_objective'))}",
        f"- Current-vs-label-bias rank correlation: {fmt(summary.get('current_vs_label_bias_rank_correlation'))}",
        f"- Current-vs-trend-anomaly rank correlation: {fmt(summary.get('current_vs_trend_anomaly_rank_correlation'))}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Top Runs By Diagnostic NMR Treatments",
        "",
        "### Per-Label Bias",
        "",
        "| Run | Kind | Bias combined | Bias NMR objective | Bias max | Current combined |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in runs.sort_values("label_bias_combined_objective").head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    fmt(row["label_bias_combined_objective"]),
                    fmt(row["label_bias_objective"]),
                    fmt(row["fitted_label_bias_max"]),
                    fmt(row["current_combined_objective"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Within-Label Anomaly",
            "",
            "| Run | Kind | Anomaly combined | Anomaly NMR objective | Rows | Groups | Current combined |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in runs.sort_values("trend_anomaly_combined_objective").head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    fmt(row["trend_anomaly_combined_objective"]),
                    fmt(row["trend_anomaly_objective"]),
                    str(int(row["trend_anomaly_rows"])),
                    str(int(row["trend_anomaly_groups"])),
                    fmt(row["current_combined_objective"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Uniform Offset Winners",
            "",
            "| Offset | Best run | Combined objective | NMR objective | Nonphysical corrected rows |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for key, row in summary.get("best_by_uniform_offset", {}).items():
        lines.append(
            "| "
            + " | ".join(
                [
                    key,
                    f"`{row.get('run_id', 'n/a')}`",
                    fmt(row.get("combined_offset_objective")),
                    fmt(row.get("nmr_offset_objective")),
                    str(row.get("corrected_nonphysical_rows", "n/a")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The per-label-bias and within-label anomaly diagnostics remove constant NMR offsets that could plausibly arise from bound/interlayer water. If their top-ranked candidates differ from the current raw absolute-theta objective, the current permeability-field ranking should be treated as conditional on the unresolved NMR interpretation.",
            "",
            "Uniform subtraction is included only as a simple stress test. The generated bound-water audit already shows that one global offset cannot make every usable NMR row physical without overcorrecting others.",
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
    runs, offsets, summary, label_bias = build_audit(args)
    label_bias_output = args.output.with_name("nmr_candidate_bias_sensitivity_label_biases.csv")
    output_paths = [args.output, args.offset_output, label_bias_output, args.summary_output, args.markdown_output]
    summary["catalogue_copies"] = planned_catalogue_copies(args.catalogue_dir, output_paths)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    runs.to_csv(args.output, index=False)
    offsets.to_csv(args.offset_output, index=False)
    label_bias.to_csv(label_bias_output, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.markdown_output, runs, offsets, summary)
    copy_catalogue_outputs(summary["catalogue_copies"])
    print(f"wrote {args.output}")
    print(f"wrote {args.offset_output}")
    print(f"wrote {label_bias_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"copied {len(summary['catalogue_copies'])} files to {args.catalogue_dir / 'derived_files'}")
    print(f"runs audited: {summary['run_count']}")


if __name__ == "__main__":
    main()
