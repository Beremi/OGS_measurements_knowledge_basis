#!/usr/bin/env python3
"""Build a cross-stream scorecard for executed CDA permeability candidates.

The active objective currently ranks candidates by direct pulse-test permeability
plus sampled NMR theta rows.  ERT, Taupe/TDR, and the NMR bound-water alternatives
are diagnostic gates rather than active likelihood terms.  This script joins those
diagnostics at the run level so candidate interpretation can see whether the same
field survives all currently defensible streams.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


METRIC_COLUMNS = {
    "active_objective": "current_combined_objective",
    "nmr_label_bias": "label_bias_combined_objective",
    "nmr_trend_anomaly": "trend_anomaly_combined_objective",
    "ert": "ert_residual_mae_log10",
    "taupe": "taupe_trend_mae",
}

RANK_COLUMNS = {
    "active_objective": "active_objective_rank",
    "nmr_label_bias": "nmr_label_bias_rank",
    "nmr_trend_anomaly": "nmr_trend_anomaly_rank",
    "ert": "ert_mae_rank",
    "taupe": "taupe_mae_rank",
}

DIAGNOSTIC_STREAMS = ["nmr_label_bias", "nmr_trend_anomaly", "ert", "taupe"]
ALL_STREAMS = ["active_objective", *DIAGNOSTIC_STREAMS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nmr-audit",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--ert-audit",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--taupe-audit",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/cross_stream_candidate_scorecard"),
        help="Measurement-catalogue directory where derived scorecard copies are stored.",
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


def read_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, int]]:
    nmr = pd.read_csv(args.nmr_audit)
    ert = pd.read_csv(args.ert_audit)
    taupe = pd.read_csv(args.taupe_audit)
    require_columns(
        nmr,
        args.nmr_audit,
        [
            "run_id",
            "run_kind",
            "current_combined_objective",
            "direct_permeability_objective",
            "current_nmr_objective_from_summary",
            "current_nmr_rmse_normalized_residual",
            "label_bias_combined_objective",
            "label_bias_objective",
            "label_bias_rmse_normalized_residual",
            "trend_anomaly_combined_objective",
            "trend_anomaly_objective",
            "trend_anomaly_rmse_normalized_residual",
            "active_nmr_rows",
            "combined_active_component_count",
        ],
    )
    require_columns(
        ert,
        args.ert_audit,
        [
            "run_id",
            "ert_residual_mae_log10",
            "ert_residual_rmse_log10",
            "ert_residual_mean_log10",
            "compared_rows",
            "compared_output_times",
        ],
    )
    require_columns(
        taupe,
        args.taupe_audit,
        [
            "run_id",
            "taupe_trend_mae",
            "taupe_trend_rmse",
            "taupe_trend_residual_mean",
            "compared_rows",
            "compared_series",
        ],
    )
    source_counts = {
        "nmr_rows": int(nmr.shape[0]),
        "ert_rows": int(ert.shape[0]),
        "taupe_rows": int(taupe.shape[0]),
    }
    nmr_columns = [
        "run_id",
        "run_kind",
        "current_combined_objective",
        "direct_permeability_objective",
        "current_nmr_objective_from_summary",
        "current_nmr_rmse_normalized_residual",
        "label_bias_combined_objective",
        "label_bias_objective",
        "label_bias_rmse_normalized_residual",
        "trend_anomaly_combined_objective",
        "trend_anomaly_objective",
        "trend_anomaly_rmse_normalized_residual",
        "active_nmr_rows",
        "active_nmr_label_groups",
        "combined_active_component_count",
    ]
    ert_columns = [
        "run_id",
        "ert_residual_mae_log10",
        "ert_residual_rmse_log10",
        "ert_residual_mean_log10",
        "compared_rows",
        "compared_output_times",
    ]
    taupe_columns = [
        "run_id",
        "taupe_trend_mae",
        "taupe_trend_rmse",
        "taupe_trend_residual_mean",
        "compared_rows",
        "compared_series",
    ]
    frame = nmr[nmr_columns].merge(
        ert[ert_columns].rename(
            columns={
                "compared_rows": "ert_compared_rows",
                "compared_output_times": "ert_compared_output_times",
            }
        ),
        on="run_id",
        how="inner",
    )
    frame = frame.merge(
        taupe[taupe_columns].rename(
            columns={
                "compared_rows": "taupe_compared_rows",
                "compared_series": "taupe_compared_series",
            }
        ),
        on="run_id",
        how="inner",
    )
    source_counts["joined_rows"] = int(frame.shape[0])
    return frame, source_counts


def add_ranks_and_scores(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for stream, metric_column in METRIC_COLUMNS.items():
        values = pd.to_numeric(frame[metric_column], errors="coerce")
        frame[RANK_COLUMNS[stream]] = values.rank(method="min")
        min_value = values.min()
        span = values.max() - min_value
        if finite(span) and float(span) > 0.0:
            frame[f"{stream}_normalized_loss"] = (values - min_value) / span
        else:
            frame[f"{stream}_normalized_loss"] = np.nan

    all_rank_columns = [RANK_COLUMNS[stream] for stream in ALL_STREAMS]
    diagnostic_rank_columns = [RANK_COLUMNS[stream] for stream in DIAGNOSTIC_STREAMS]
    all_loss_columns = [f"{stream}_normalized_loss" for stream in ALL_STREAMS]
    diagnostic_loss_columns = [f"{stream}_normalized_loss" for stream in DIAGNOSTIC_STREAMS]
    frame["mean_rank_all_streams"] = frame[all_rank_columns].mean(axis=1)
    frame["mean_rank_diagnostics_only"] = frame[diagnostic_rank_columns].mean(axis=1)
    frame["worst_rank_all_streams"] = frame[all_rank_columns].max(axis=1)
    frame["worst_rank_diagnostics_only"] = frame[diagnostic_rank_columns].max(axis=1)
    frame["rank_spread_all_streams"] = frame[all_rank_columns].max(axis=1) - frame[all_rank_columns].min(axis=1)
    frame["mean_normalized_loss_all_streams"] = frame[all_loss_columns].mean(axis=1)
    frame["mean_normalized_loss_diagnostics_only"] = frame[diagnostic_loss_columns].mean(axis=1)
    frame["top10_stream_count"] = frame[all_rank_columns].le(10).sum(axis=1)
    frame["top10_diagnostic_stream_count"] = frame[diagnostic_rank_columns].le(10).sum(axis=1)
    frame["pareto_all_streams"] = pareto_flags(frame, [METRIC_COLUMNS[stream] for stream in ALL_STREAMS])
    frame["pareto_diagnostics_only"] = pareto_flags(
        frame,
        [METRIC_COLUMNS[stream] for stream in DIAGNOSTIC_STREAMS],
    )
    return frame.sort_values(["mean_rank_all_streams", "worst_rank_all_streams", "run_id"]).reset_index(drop=True)


def pareto_flags(frame: pd.DataFrame, metric_columns: list[str]) -> list[bool]:
    values = frame[metric_columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    flags: list[bool] = []
    for index, row in enumerate(values):
        if not np.isfinite(row).all():
            flags.append(False)
            continue
        other = np.delete(values, index, axis=0)
        finite_other = np.isfinite(other).all(axis=1)
        other = other[finite_other]
        if other.size == 0:
            flags.append(True)
            continue
        dominated = np.any(np.all(other <= row, axis=1) & np.any(other < row, axis=1))
        flags.append(not bool(dominated))
    return flags


def best_row(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    valid = frame[pd.to_numeric(frame[column], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    valid[column] = pd.to_numeric(valid[column], errors="coerce")
    return json_ready(valid.sort_values([column, "run_id"], na_position="last").iloc[0].to_dict())


def rank_correlation(frame: pd.DataFrame, left: str, right: str) -> float | None:
    clean = frame[[left, right]].apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 3:
        return None
    if clean[left].std(ddof=1) <= 1e-12 or clean[right].std(ddof=1) <= 1e-12:
        return None
    return float(clean[left].rank(method="average").corr(clean[right].rank(method="average")))


def compact_candidate(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "run_id",
        "run_kind",
        "current_combined_objective",
        "label_bias_combined_objective",
        "trend_anomaly_combined_objective",
        "ert_residual_mae_log10",
        "taupe_trend_mae",
        "active_objective_rank",
        "nmr_label_bias_rank",
        "nmr_trend_anomaly_rank",
        "ert_mae_rank",
        "taupe_mae_rank",
        "mean_rank_all_streams",
        "mean_rank_diagnostics_only",
        "worst_rank_all_streams",
        "top10_stream_count",
        "pareto_all_streams",
        "pareto_diagnostics_only",
    ]
    return {key: row.get(key) for key in keys if key in row}


def summarize(frame: pd.DataFrame, source_counts: dict[str, int]) -> dict[str, Any]:
    if frame.empty:
        return {
            "status": "cross_stream_scorecard_no_joined_runs",
            "source_counts": source_counts,
            "activation_gate": "No common run ids were found across the NMR, ERT, and Taupe audit tables.",
        }
    stream_winners = {
        "active_objective": compact_candidate(best_row(frame, "current_combined_objective")),
        "nmr_label_bias": compact_candidate(best_row(frame, "label_bias_combined_objective")),
        "nmr_trend_anomaly": compact_candidate(best_row(frame, "trend_anomaly_combined_objective")),
        "ert": compact_candidate(best_row(frame, "ert_residual_mae_log10")),
        "taupe": compact_candidate(best_row(frame, "taupe_trend_mae")),
        "mean_rank_all_streams": compact_candidate(best_row(frame, "mean_rank_all_streams")),
        "mean_rank_diagnostics_only": compact_candidate(best_row(frame, "mean_rank_diagnostics_only")),
        "worst_rank_all_streams": compact_candidate(best_row(frame, "worst_rank_all_streams")),
        "mean_normalized_loss_all_streams": compact_candidate(best_row(frame, "mean_normalized_loss_all_streams")),
    }
    active_run = stream_winners["active_objective"].get("run_id")
    active_row = frame[frame["run_id"].eq(active_run)].iloc[0].to_dict() if active_run else {}
    correlations = {
        "active_vs_nmr_label_bias_rank": rank_correlation(
            frame,
            "current_combined_objective",
            "label_bias_combined_objective",
        ),
        "active_vs_nmr_trend_anomaly_rank": rank_correlation(
            frame,
            "current_combined_objective",
            "trend_anomaly_combined_objective",
        ),
        "active_vs_ert_rank": rank_correlation(
            frame,
            "current_combined_objective",
            "ert_residual_mae_log10",
        ),
        "active_vs_taupe_rank": rank_correlation(
            frame,
            "current_combined_objective",
            "taupe_trend_mae",
        ),
        "ert_vs_taupe_rank": rank_correlation(frame, "ert_residual_mae_log10", "taupe_trend_mae"),
    }
    return {
        "status": "cross_stream_scorecard_generated_active_objective_unchanged",
        "source_counts": source_counts,
        "joined_run_count": int(frame.shape[0]),
        "metric_columns": METRIC_COLUMNS,
        "rank_columns": RANK_COLUMNS,
        "stream_winners": stream_winners,
        "active_incumbent_cross_stream": compact_candidate(json_ready(active_row)),
        "pareto_all_streams_count": int(frame["pareto_all_streams"].sum()),
        "pareto_diagnostics_only_count": int(frame["pareto_diagnostics_only"].sum()),
        "top10_all_stream_candidates": int(frame["top10_stream_count"].eq(len(ALL_STREAMS)).sum()),
        "top10_diagnostic_stream_candidates": int(
            frame["top10_diagnostic_stream_count"].eq(len(DIAGNOSTIC_STREAMS)).sum()
        ),
        "rank_correlations": correlations,
        "activation_gate": (
            "Diagnostic only: the scorecard does not change the active objective. It shows how executed "
            "candidate fields rank under NMR offset-robust alternatives, provisional ERT log-resistivity "
            "residuals, and Taupe/TDR trend residuals so field selection is not based on the active "
            "permeability+raw-NMR objective alone."
        ),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def table_row(row: pd.Series, columns: list[str]) -> str:
    values = []
    for column in columns:
        value = row.get(column)
        if column == "run_id":
            values.append(f"`{value}`")
        elif column == "run_kind":
            values.append(str(value))
        elif isinstance(value, (bool, np.bool_)):
            values.append("yes" if bool(value) else "no")
        elif finite(value):
            values.append(fmt(value, 4 if "rank" in column or "count" in column else 6))
        else:
            values.append(str(value))
    return "| " + " | ".join(values) + " |"


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Cross-Stream Candidate Scorecard",
        "",
        "This scorecard joins the active permeability+NMR objective with the current diagnostic streams.",
        "It does not change candidate objectives or promote gated streams into the likelihood.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Joined executed runs: {summary.get('joined_run_count', 0)}",
        f"- Source rows: NMR={summary['source_counts'].get('nmr_rows')}, ERT={summary['source_counts'].get('ert_rows')}, Taupe={summary['source_counts'].get('taupe_rows')}",
        f"- Pareto candidates across active objective plus diagnostics: {summary.get('pareto_all_streams_count', 0)}",
        f"- Pareto candidates across diagnostics only: {summary.get('pareto_diagnostics_only_count', 0)}",
        f"- Candidates in the top 10 of every stream: {summary.get('top10_all_stream_candidates', 0)}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Stream Winners",
        "",
        "| Stream | Run | Active rank | NMR-bias rank | NMR-anomaly rank | ERT rank | Taupe rank | Mean rank |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    stream_labels = {
        "active_objective": "Active objective",
        "nmr_label_bias": "NMR per-label bias",
        "nmr_trend_anomaly": "NMR within-label anomaly",
        "ert": "ERT log10 MAE",
        "taupe": "Taupe trend MAE",
        "mean_rank_all_streams": "Best mean rank",
        "mean_rank_diagnostics_only": "Best diagnostic mean rank",
        "worst_rank_all_streams": "Best worst rank",
        "mean_normalized_loss_all_streams": "Best normalized loss",
    }
    for key, label in stream_labels.items():
        row = summary["stream_winners"].get(key, {})
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    f"`{row.get('run_id', 'n/a')}`",
                    fmt(row.get("active_objective_rank"), 2),
                    fmt(row.get("nmr_label_bias_rank"), 2),
                    fmt(row.get("nmr_trend_anomaly_rank"), 2),
                    fmt(row.get("ert_mae_rank"), 2),
                    fmt(row.get("taupe_mae_rank"), 2),
                    fmt(row.get("mean_rank_all_streams"), 2),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top By Mean Rank Across All Streams",
            "",
            "| Run | Kind | Active obj | NMR bias obj | ERT MAE | Taupe MAE | Active rank | Bias rank | ERT rank | Taupe rank | Mean rank | Worst rank | Pareto |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    mean_columns = [
        "run_id",
        "run_kind",
        "current_combined_objective",
        "label_bias_combined_objective",
        "ert_residual_mae_log10",
        "taupe_trend_mae",
        "active_objective_rank",
        "nmr_label_bias_rank",
        "ert_mae_rank",
        "taupe_mae_rank",
        "mean_rank_all_streams",
        "worst_rank_all_streams",
        "pareto_all_streams",
    ]
    for _, row in frame.sort_values(["mean_rank_all_streams", "worst_rank_all_streams"]).head(15).iterrows():
        lines.append(table_row(row, mean_columns))
    lines.extend(
        [
            "",
            "## Pareto Candidates Across All Streams",
            "",
            "| Run | Kind | Active rank | NMR-bias rank | NMR-anomaly rank | ERT rank | Taupe rank | Mean rank | Worst rank |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    pareto = frame[frame["pareto_all_streams"]].sort_values(["mean_rank_all_streams", "worst_rank_all_streams"])
    for _, row in pareto.head(25).iterrows():
        lines.append(
            table_row(
                row,
                [
                    "run_id",
                    "run_kind",
                    "active_objective_rank",
                    "nmr_label_bias_rank",
                    "nmr_trend_anomaly_rank",
                    "ert_mae_rank",
                    "taupe_mae_rank",
                    "mean_rank_all_streams",
                    "worst_rank_all_streams",
                ],
            )
        )
    active = summary.get("active_incumbent_cross_stream", {})
    best_mean = summary.get("stream_winners", {}).get("mean_rank_all_streams", {})
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The active incumbent `{active.get('run_id', 'n/a')}` is the best run under the current direct-permeability plus raw NMR objective, but its cross-stream ranks are ERT={fmt(active.get('ert_mae_rank'), 2)} and Taupe={fmt(active.get('taupe_mae_rank'), 2)}.",
            f"The best mean-rank compromise is `{best_mean.get('run_id', 'n/a')}` with mean rank {fmt(best_mean.get('mean_rank_all_streams'), 2)} and worst rank {fmt(best_mean.get('worst_rank_all_streams'), 2)}.",
            "This mismatch is evidence that the current permeability field should remain conditional on the unresolved stream gates rather than being reported as the final all-measurement inversion.",
            "",
            "## Source Artefacts",
            "",
            "- `nmr_candidate_bias_sensitivity_audit.csv`: active raw-theta NMR objective plus offset-robust NMR alternatives.",
            "- `ert_candidate_discrimination_audit.csv`: provisional theta-to-log-resistivity residuals over projected ERT support.",
            "- `taupe_candidate_discrimination_audit.csv`: baseline-normalized Taupe/TDR trend residuals over mapped A3/A4 EDZ-band support.",
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
    frame, source_counts = read_inputs(args)
    scorecard = add_ranks_and_scores(frame)
    summary = summarize(scorecard, source_counts)
    output_paths = [args.output, args.summary_output, args.markdown_output]
    summary["catalogue_copies"] = planned_catalogue_copies(args.catalogue_dir, output_paths)
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    scorecard.to_csv(args.output, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.markdown_output, scorecard, summary)
    copy_catalogue_outputs(summary["catalogue_copies"])
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"copied {len(summary['catalogue_copies'])} files to {args.catalogue_dir / 'derived_files'}")
    print(f"joined runs: {summary.get('joined_run_count', 0)}")


if __name__ == "__main__":
    main()
