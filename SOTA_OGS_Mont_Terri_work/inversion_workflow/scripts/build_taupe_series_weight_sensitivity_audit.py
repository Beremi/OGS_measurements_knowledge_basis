#!/usr/bin/env python3
"""Audit Taupe/TDR trend-score sensitivity to series grouping and weights.

The Taupe/TDR diagnostic is currently a trend-only screen.  Absolute workbook units,
sensor calibration, and residual weights are not confirmed.  This script uses the
existing cross-run series diagnostics to quantify the part of that gate that can be
tested locally: whether candidate ranking depends on row/series/sensor/EDZ-band
weighting choices.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCORE_COLUMNS = {
    "aggregate_row_weighted": "aggregate_taupe_trend_mae",
    "equal_series": "equal_series_mae",
    "equal_sensor": "equal_sensor_mae",
    "equal_edz_band": "equal_edz_band_mae",
    "a3_only_equal_series": "a3_only_equal_series_mae",
    "a4_only_equal_series": "a4_only_equal_series_mae",
    "drop_worst_series": "drop_worst_series_mae",
    "trim_best_worst_series": "trim_best_worst_series_mae",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-audit",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--series-audit",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_series.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/taupe_series_weight_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--series-output",
        type=Path,
        default=Path("inversion_workflow/taupe_series_weight_sensitivity_series.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/taupe_series_weight_sensitivity_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/taupe_series_weight_sensitivity.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/taupe_tdr"),
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


def require_columns(frame: pd.DataFrame, path: Path, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} lacks required columns: {', '.join(missing)}")


def read_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    runs = pd.read_csv(args.run_audit)
    series = pd.read_csv(args.series_audit)
    require_columns(
        runs,
        args.run_audit,
        ["run_id", "run_kind", "taupe_trend_mae", "combined_active_objective", "taupe_mae_rank"],
    )
    require_columns(
        series,
        args.series_audit,
        [
            "run_id",
            "run_kind",
            "series_id",
            "sensor",
            "edz_band_cm",
            "compared_rows",
            "standardized_residual_mae",
            "standardized_residual_rmse",
            "model_taupe_standardized_pearson",
            "delta_sign_agreement_fraction",
        ],
    )
    compared = series[
        pd.to_numeric(series["compared_rows"], errors="coerce").gt(0)
        & pd.to_numeric(series["standardized_residual_mae"], errors="coerce").notna()
    ].copy()
    compared["standardized_residual_mae"] = pd.to_numeric(compared["standardized_residual_mae"], errors="coerce")
    compared["standardized_residual_rmse"] = pd.to_numeric(compared["standardized_residual_rmse"], errors="coerce")
    compared["compared_rows"] = pd.to_numeric(compared["compared_rows"], errors="coerce")
    common_run_ids = sorted(set(compared["run_id"]) & set(runs["run_id"]))
    compared = compared[compared["run_id"].isin(common_run_ids)].copy()
    runs = runs[runs["run_id"].isin(common_run_ids)].copy()
    return runs, series, compared


def mean_or_nan(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return np.nan
    return float(clean.mean())


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    value_array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    weight_array = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0.0)
    if not mask.any():
        return np.nan
    return float(np.average(value_array[mask], weights=weight_array[mask]))


def trimmed_mean(values: pd.Series, *, drop_best: bool, drop_worst: bool) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna().sort_values()
    if clean.empty:
        return np.nan
    start = 1 if drop_best and clean.shape[0] > 2 else 0
    end = -1 if drop_worst and clean.shape[0] > 2 else None
    selected = clean.iloc[start:end]
    if selected.empty:
        selected = clean
    return float(selected.mean())


def grouped_mean(frame: pd.DataFrame, group_column: str) -> float:
    grouped = frame.groupby(group_column)["standardized_residual_mae"].mean()
    return mean_or_nan(grouped)


def build_run_scores(runs: pd.DataFrame, compared: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    run_lookup = runs.set_index("run_id").to_dict(orient="index")
    for run_id, group in compared.groupby("run_id", sort=True):
        run = run_lookup.get(run_id, {})
        a3 = group[group["sensor"].astype(str).eq("A3")]
        a4 = group[group["sensor"].astype(str).eq("A4")]
        row = {
            "run_id": run_id,
            "run_kind": run.get("run_kind", group["run_kind"].iloc[0]),
            "compared_series_count": int(group["series_id"].nunique()),
            "compared_sensor_count": int(group["sensor"].nunique()),
            "compared_edz_band_count": int(group["edz_band_cm"].nunique()),
            "compared_rows_total": int(pd.to_numeric(group["compared_rows"], errors="coerce").sum()),
            "aggregate_taupe_trend_mae": run.get("taupe_trend_mae"),
            "aggregate_taupe_mae_rank": run.get("taupe_mae_rank"),
            "combined_active_objective": run.get("combined_active_objective"),
            "equal_series_mae": mean_or_nan(group["standardized_residual_mae"]),
            "row_weighted_from_series_mae": weighted_mean(
                group["standardized_residual_mae"],
                group["compared_rows"],
            ),
            "equal_sensor_mae": grouped_mean(group, "sensor"),
            "equal_edz_band_mae": grouped_mean(group, "edz_band_cm"),
            "a3_only_equal_series_mae": mean_or_nan(a3["standardized_residual_mae"]),
            "a4_only_equal_series_mae": mean_or_nan(a4["standardized_residual_mae"]),
            "drop_worst_series_mae": trimmed_mean(group["standardized_residual_mae"], drop_best=False, drop_worst=True),
            "trim_best_worst_series_mae": trimmed_mean(
                group["standardized_residual_mae"],
                drop_best=True,
                drop_worst=True,
            ),
            "series_mae_min": float(group["standardized_residual_mae"].min()),
            "series_mae_max": float(group["standardized_residual_mae"].max()),
            "series_mae_range": float(group["standardized_residual_mae"].max() - group["standardized_residual_mae"].min()),
            "series_mae_std": float(group["standardized_residual_mae"].std(ddof=1)),
            "mean_delta_sign_agreement_fraction": mean_or_nan(group["delta_sign_agreement_fraction"]),
            "mean_model_taupe_standardized_pearson": mean_or_nan(group["model_taupe_standardized_pearson"]),
        }
        rows.append(row)
    score = pd.DataFrame(rows)
    for mode, column in SCORE_COLUMNS.items():
        score[f"{mode}_rank"] = pd.to_numeric(score[column], errors="coerce").rank(method="min")
    score["rank_spread_across_weighting_modes"] = score[[f"{mode}_rank" for mode in SCORE_COLUMNS]].max(axis=1) - score[
        [f"{mode}_rank" for mode in SCORE_COLUMNS]
    ].min(axis=1)
    score["mean_rank_across_weighting_modes"] = score[[f"{mode}_rank" for mode in SCORE_COLUMNS]].mean(axis=1)
    score["worst_rank_across_weighting_modes"] = score[[f"{mode}_rank" for mode in SCORE_COLUMNS]].max(axis=1)
    return score.sort_values(["mean_rank_across_weighting_modes", "worst_rank_across_weighting_modes", "run_id"])


def rank_correlation(frame: pd.DataFrame, left: str, right: str) -> float | None:
    clean = frame[[left, right]].apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 3:
        return None
    if clean[left].std(ddof=1) <= 1e-12 or clean[right].std(ddof=1) <= 1e-12:
        return None
    return float(clean[left].rank(method="average").corr(clean[right].rank(method="average")))


def best_row(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    valid = frame[pd.to_numeric(frame[column], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    valid[column] = pd.to_numeric(valid[column], errors="coerce")
    return json_ready(valid.sort_values([column, "run_id"], na_position="last").iloc[0].to_dict())


def compact_run(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "run_id",
        "run_kind",
        "aggregate_taupe_trend_mae",
        "equal_series_mae",
        "equal_sensor_mae",
        "equal_edz_band_mae",
        "a3_only_equal_series_mae",
        "a4_only_equal_series_mae",
        "drop_worst_series_mae",
        "trim_best_worst_series_mae",
        "aggregate_row_weighted_rank",
        "equal_series_rank",
        "equal_sensor_rank",
        "equal_edz_band_rank",
        "a3_only_equal_series_rank",
        "a4_only_equal_series_rank",
        "drop_worst_series_rank",
        "trim_best_worst_series_rank",
        "mean_rank_across_weighting_modes",
        "worst_rank_across_weighting_modes",
        "rank_spread_across_weighting_modes",
    ]
    return {key: row.get(key) for key in keys if key in row}


def build_series_summary(score: pd.DataFrame, compared: pd.DataFrame) -> pd.DataFrame:
    aggregate = score[["run_id", "aggregate_taupe_trend_mae", "aggregate_row_weighted_rank"]]
    rows: list[dict[str, Any]] = []
    for series_id, group in compared.groupby("series_id", sort=True):
        group = group.merge(aggregate, on="run_id", how="left")
        best = group.sort_values(["standardized_residual_mae", "run_id"]).iloc[0]
        worst = group.sort_values(["standardized_residual_mae", "run_id"], ascending=[False, True]).iloc[0]
        rows.append(
            {
                "series_id": series_id,
                "sensor": best["sensor"],
                "edz_band_cm": best["edz_band_cm"],
                "run_count": int(group["run_id"].nunique()),
                "compared_rows_per_run": int(pd.to_numeric(group["compared_rows"], errors="coerce").median()),
                "mae_min": float(group["standardized_residual_mae"].min()),
                "mae_p50": float(group["standardized_residual_mae"].median()),
                "mae_max": float(group["standardized_residual_mae"].max()),
                "mae_range": float(group["standardized_residual_mae"].max() - group["standardized_residual_mae"].min()),
                "mae_std": float(group["standardized_residual_mae"].std(ddof=1)),
                "best_run_id": best["run_id"],
                "best_run_kind": best["run_kind"],
                "best_run_series_mae": float(best["standardized_residual_mae"]),
                "best_run_aggregate_taupe_mae": best.get("aggregate_taupe_trend_mae"),
                "best_run_aggregate_rank": best.get("aggregate_row_weighted_rank"),
                "worst_run_id": worst["run_id"],
                "worst_run_series_mae": float(worst["standardized_residual_mae"]),
                "series_vs_aggregate_rank_correlation": rank_correlation(
                    group,
                    "standardized_residual_mae",
                    "aggregate_taupe_trend_mae",
                ),
                "mean_delta_sign_agreement_fraction": mean_or_nan(group["delta_sign_agreement_fraction"]),
                "mean_model_taupe_standardized_pearson": mean_or_nan(group["model_taupe_standardized_pearson"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["mae_range", "series_id"], ascending=[False, True])


def summarize(
    score: pd.DataFrame,
    series_summary: pd.DataFrame,
    all_series: pd.DataFrame,
    compared: pd.DataFrame,
) -> dict[str, Any]:
    if score.empty:
        return {
            "status": "taupe_series_weight_sensitivity_no_compared_series",
            "activation_gate": "No compared Taupe/TDR series were found.",
        }
    winners = {
        mode: compact_run(best_row(score, column))
        for mode, column in SCORE_COLUMNS.items()
    }
    aggregate_col = SCORE_COLUMNS["aggregate_row_weighted"]
    correlations = {
        mode: rank_correlation(score, aggregate_col, column)
        for mode, column in SCORE_COLUMNS.items()
        if mode != "aggregate_row_weighted"
    }
    compared_series = set(compared["series_id"])
    all_series_ids = set(all_series["series_id"])
    return {
        "status": "taupe_series_weight_sensitivity_generated_not_active_likelihood",
        "run_count": int(score["run_id"].nunique()),
        "all_series_count": int(len(all_series_ids)),
        "compared_series_count": int(len(compared_series)),
        "uncompared_series_count": int(len(all_series_ids - compared_series)),
        "uncompared_series": sorted(all_series_ids - compared_series),
        "compared_series": sorted(compared_series),
        "weighting_mode_winners": winners,
        "best_mean_weighting_rank": compact_run(best_row(score, "mean_rank_across_weighting_modes")),
        "series_best_run_distinct_count": int(series_summary["best_run_id"].nunique()),
        "series_best_runs": sorted(series_summary["best_run_id"].unique().tolist()),
        "max_series_mae_range": float(series_summary["mae_range"].max()),
        "most_discriminating_series": json_ready(series_summary.iloc[0].to_dict()),
        "rank_correlations_vs_aggregate": correlations,
        "activation_gate": (
            "Diagnostic only: this audit quantifies local sensitivity to Taupe/TDR trend grouping and "
            "weights. It does not confirm workbook units, sensor calibration, absolute saturation mapping, "
            "or residual uncertainty."
        ),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, score: pd.DataFrame, series_summary: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Taupe/TDR Series Weight Sensitivity Audit",
        "",
        "This audit checks whether the Taupe/TDR trend diagnostic ranking changes when compared A3/A4 series, sensors, or EDZ bands are grouped differently.",
        "It is diagnostic only and does not activate Taupe/TDR in the likelihood.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs evaluated: {summary.get('run_count', 0)}",
        f"- Compared series: {summary.get('compared_series_count', 0)}",
        f"- Uncompared series: {summary.get('uncompared_series_count', 0)}",
        f"- Distinct per-series winner runs: {summary.get('series_best_run_distinct_count', 0)}",
        f"- Best mean weighting-rank run: `{summary.get('best_mean_weighting_rank', {}).get('run_id', 'n/a')}` with mean rank {fmt(summary.get('best_mean_weighting_rank', {}).get('mean_rank_across_weighting_modes'), 2)}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Weighting Mode Winners",
        "",
        "| Weighting mode | Winner | Aggregate rank | Mode rank | Aggregate MAE | Mode MAE |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for mode, row in summary.get("weighting_mode_winners", {}).items():
        mode_column = SCORE_COLUMNS[mode]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{mode}`",
                    f"`{row.get('run_id', 'n/a')}`",
                    fmt(row.get("aggregate_row_weighted_rank"), 2),
                    fmt(row.get(f"{mode}_rank"), 2),
                    fmt(row.get("aggregate_taupe_trend_mae")),
                    fmt(row.get(mode_column)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top Runs By Mean Rank Across Weighting Modes",
            "",
            "| Run | Kind | Aggregate MAE | Equal-series MAE | A3-only | A4-only | Drop-worst | Mean rank | Worst rank |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in score.sort_values(["mean_rank_across_weighting_modes", "worst_rank_across_weighting_modes"]).head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['run_id']}`",
                    str(row["run_kind"]),
                    fmt(row["aggregate_taupe_trend_mae"]),
                    fmt(row["equal_series_mae"]),
                    fmt(row["a3_only_equal_series_mae"]),
                    fmt(row["a4_only_equal_series_mae"]),
                    fmt(row["drop_worst_series_mae"]),
                    fmt(row["mean_rank_across_weighting_modes"], 2),
                    fmt(row["worst_rank_across_weighting_modes"], 2),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Most Discriminating Series",
            "",
            "| Series | Sensor | EDZ band | MAE range | Best run | Best series MAE | Aggregate rank of best | Series/aggregate rank corr |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in series_summary.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['series_id']}`",
                    str(row["sensor"]),
                    str(row["edz_band_cm"]),
                    fmt(row["mae_range"]),
                    f"`{row['best_run_id']}`",
                    fmt(row["best_run_series_mae"]),
                    fmt(row["best_run_aggregate_rank"], 2),
                    fmt(row["series_vs_aggregate_rank_correlation"], 3),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A stable winner across weighting modes would support using Taupe/TDR as a simple trend screen once calibration is accepted. A changing winner means grouped weights and uncertainty are part of the scientific gate, not an implementation detail.",
            "A7/A8 remain unmapped in the current local OGS mesh support, so this audit is limited to the compared A3/A4 series.",
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
    runs, all_series, compared = read_inputs(args)
    score = build_run_scores(runs, compared)
    series_summary = build_series_summary(score, compared)
    summary = summarize(score, series_summary, all_series, compared)
    output_paths = [args.output, args.series_output, args.summary_output, args.markdown_output]
    summary["catalogue_copies"] = planned_catalogue_copies(args.catalogue_dir, output_paths)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    score.to_csv(args.output, index=False)
    series_summary.to_csv(args.series_output, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.markdown_output, score, series_summary, summary)
    copy_catalogue_outputs(summary["catalogue_copies"])
    print(f"wrote {args.output}")
    print(f"wrote {args.series_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"copied {len(summary['catalogue_copies'])} files to {args.catalogue_dir / 'derived_files'}")
    print(f"runs evaluated: {summary.get('run_count', 0)}")


if __name__ == "__main__":
    main()
