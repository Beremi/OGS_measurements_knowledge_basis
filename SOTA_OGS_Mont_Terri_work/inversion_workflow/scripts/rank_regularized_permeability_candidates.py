#!/usr/bin/env python3
"""Rank direct permeability candidates with explicit complexity/regularization proxies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_SCENARIOS = [
    ("data_only", None),
    ("weak_field_update_penalty_sigma3", 3.0),
    ("moderate_field_update_penalty_sigma2", 2.0),
    ("strong_field_update_penalty_sigma1", 1.0),
]
SCENARIO_ORDER = {scenario_id: index for index, (scenario_id, _) in enumerate(DEFAULT_SCENARIOS)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("inversion_workflow/runs/smooth_permeability_candidate_search/smooth_fit_results.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("inversion_workflow/runs/smooth_permeability_candidate_search/SMOOTH_FIT_SUMMARY.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/regularized_permeability_candidate_ranking"),
    )
    parser.add_argument(
        "--pareto-metrics",
        default="objective_value,sum_squared_applied_log10_shift_all_cells",
        help="Comma-separated metrics to minimize for the main Pareto flag.",
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
        return json_number(value)
    if value is pd.NA or value is None:
        return None
    return value


def pareto_flags(frame: pd.DataFrame, metrics: list[str]) -> list[bool]:
    values = frame[metrics].to_numpy(dtype=float)
    flags: list[bool] = []
    for index, row in enumerate(values):
        dominated = False
        for other_index, other in enumerate(values):
            if index == other_index:
                continue
            if np.all(other <= row) and np.any(other < row):
                dominated = True
                break
        flags.append(not dominated)
    return flags


def scenario_scores(results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scenario_id, sigma in DEFAULT_SCENARIOS:
        for _, row in results.iterrows():
            data_objective = float(row["objective_value"])
            sum_squared = float(row["sum_squared_applied_log10_shift_all_cells"])
            if sigma is None:
                penalty = 0.0
                score = data_objective
                description = "direct permeability likelihood only; no complexity penalty"
            else:
                penalty = 0.5 * sum_squared / (sigma**2)
                score = data_objective + penalty
                description = (
                    "mesh-resolution-dependent Gaussian prior proxy on the cell-wise "
                    f"log10 permeability update with sigma={sigma:g}"
                )
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_order": SCENARIO_ORDER[scenario_id],
                    "scenario_description": description,
                    "candidate_id": row["candidate_id"],
                    "length_scale_m": row["length_scale_m"],
                    "shift_scale": row["shift_scale"],
                    "data_objective_value": data_objective,
                    "field_update_penalty": penalty,
                    "regularized_score": score,
                    "weighted_rmse_log10": row["weighted_rmse_log10"],
                    "affected_cells": row["affected_cells"],
                    "rms_applied_log10_shift_affected": row["rms_applied_log10_shift_affected"],
                    "sum_squared_applied_log10_shift_all_cells": sum_squared,
                    "max_abs_log10_residual": row["max_abs_log10_residual"],
                    "mesh": row["mesh"],
                    "evaluation_csv": row["evaluation_csv"],
                    "summary_json": row["summary_json"],
                }
            )
    scores = pd.DataFrame(rows)
    scores["rank_in_scenario"] = (
        scores.sort_values(["scenario_order", "regularized_score", "data_objective_value", "candidate_id"])
        .groupby("scenario_id")
        .cumcount()
        + 1
    )
    return scores.sort_values(["scenario_order", "rank_in_scenario"]).reset_index(drop=True)


def summarize(results: pd.DataFrame, scores: pd.DataFrame, metrics: list[str], source_summary: dict[str, Any]) -> dict[str, Any]:
    winners = (
        scores[scores["rank_in_scenario"].eq(1)]
        .sort_values("scenario_order")
        .to_dict(orient="records")
    )
    pareto = results[results["pareto_tradeoff_candidate"]].copy()
    return {
        "source_results": str(source_summary.get("results_csv", "")),
        "source_summary": source_summary,
        "candidate_count": int(results.shape[0]),
        "pareto_metrics": metrics,
        "pareto_candidate_count": int(pareto.shape[0]),
        "pareto_candidates": json_ready(pareto.to_dict(orient="records")),
        "scenario_winners": json_ready(winners),
        "notes": [
            "The regularized scores are selection aids for the direct-permeability-only candidate set.",
            "The field-update penalty is a mesh-resolution-dependent proxy, not a calibrated geostatistical prior.",
            "Use the Pareto front and scenario winners to choose candidates for OGS state-observation testing.",
            "A production inversion should replace these proxies with a parameter prior and OGS-backed likelihood.",
        ],
    }


def write_markdown(path: Path, results: pd.DataFrame, scores: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Regularized Permeability Candidate Ranking",
        "",
        "This ranking separates direct pulse-test misfit from field-update complexity.",
        "It does not execute OGS and is not a production prior.  Its purpose is to",
        "identify candidate permeability fields worth carrying into the OGS-backed",
        "state-observation stage once the executable is available.",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Main Pareto metrics: {', '.join(summary['pareto_metrics'])}",
        f"- Pareto candidates: {summary['pareto_candidate_count']}",
        "",
        "## Scenario Winners",
        "",
        "| Scenario | Winner | Score | Data objective | Penalty | RMSE log10(k) | Affected cells | RMS shift |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    winners = scores[scores["rank_in_scenario"].eq(1)].sort_values("scenario_order")
    for _, row in winners.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scenario_id"]),
                    f"`{row['candidate_id']}`",
                    f"{float(row['regularized_score']):.2f}",
                    f"{float(row['data_objective_value']):.2f}",
                    f"{float(row['field_update_penalty']):.2f}",
                    f"{float(row['weighted_rmse_log10']):.2f}",
                    str(int(row["affected_cells"])),
                    f"{float(row['rms_applied_log10_shift_affected']):.2f}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Pareto Tradeoff Candidates",
            "",
            "| Candidate | Objective | Sum-squared update | RMSE log10(k) | Affected cells | RMS shift |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    pareto = results[results["pareto_tradeoff_candidate"]].sort_values(
        ["objective_value", "sum_squared_applied_log10_shift_all_cells"]
    )
    for _, row in pareto.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['candidate_id']}`",
                    f"{float(row['objective_value']):.2f}",
                    f"{float(row['sum_squared_applied_log10_shift_all_cells']):.2f}",
                    f"{float(row['weighted_rmse_log10']):.2f}",
                    str(int(row["affected_cells"])),
                    f"{float(row['rms_applied_log10_shift_affected']):.2f}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `data_only` selects the lowest direct pulse-test objective.",
            "- The weak/moderate/strong scenarios add a transparent penalty on the",
            "  cell-wise log10 permeability update; this discourages selecting a highly",
            "  localized or high-amplitude field solely because it fits direct pulse tests.",
            "- The penalty depends on the current mesh and should not be presented as a",
            "  calibrated geological prior.",
            "- The main practical use is to carry at least the data-only winner and one",
            "  regularized winner into OGS state-output comparison.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    results = pd.read_csv(args.results)
    source_summary = json.loads(args.summary.read_text(encoding="utf-8")) if args.summary.exists() else {}
    metrics = [item.strip() for item in args.pareto_metrics.split(",") if item.strip()]
    missing = [metric for metric in metrics if metric not in results.columns]
    if missing:
        raise SystemExit(f"missing Pareto metric columns: {missing}")

    results = results.copy()
    results["pareto_tradeoff_candidate"] = pareto_flags(results, metrics)
    scores = scenario_scores(results)
    summary = summarize(results, scores, metrics, source_summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "regularized_candidate_tradeoffs.csv"
    scores_path = args.output_dir / "regularized_candidate_scenario_scores.csv"
    summary_path = args.output_dir / "REGULARIZED_CANDIDATE_RANKING.json"
    md_path = args.output_dir / "REGULARIZED_CANDIDATE_RANKING.md"
    results.to_csv(results_path, index=False)
    scores.to_csv(scores_path, index=False)
    summary["outputs"] = {
        "tradeoffs_csv": str(results_path),
        "scenario_scores_csv": str(scores_path),
        "summary_json": str(summary_path),
        "summary_markdown": str(md_path),
    }
    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(md_path, results, scores, summary)

    print(f"wrote {results_path}")
    print(f"wrote {scores_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {md_path}")
    print(f"pareto candidates: {summary['pareto_candidate_count']}")
    for winner in summary["scenario_winners"]:
        print(f"{winner['scenario_id']}: {winner['candidate_id']} score={winner['regularized_score']:.6g}")


if __name__ == "__main__":
    main()
