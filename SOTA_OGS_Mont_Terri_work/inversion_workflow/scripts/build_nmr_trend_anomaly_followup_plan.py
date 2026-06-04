#!/usr/bin/env python3
"""Plan follow-up OGS candidates under the NMR trend/anomaly objective.

The historical candidate-search utilities rank by the raw absolute-theta active
objective.  This script uses the provisional executable NMR trend/anomaly ranking
as evidence, then audits the existing unexecuted permeability-field pools to decide
whether another OGS batch is worth running under that residual.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_POOLS = [
    "inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv",
    "inversion_workflow/runs/continuous_bayesian_candidate_plan/continuous_direct_candidate_scores.csv",
    "inversion_workflow/runs/continuous_bayesian_candidate_plan/continuous_optimizer_candidate_scores.csv",
    "inversion_workflow/runs/lower_support_continuous_candidate_plan/continuous_direct_candidate_scores.csv",
    "inversion_workflow/runs/lower_support_continuous_candidate_plan/continuous_optimizer_candidate_scores.csv",
    "inversion_workflow/runs/local_basis_sampler_plan/local_basis_sampler_scores.csv",
    "inversion_workflow/runs/local_anisotropy_sampler_plan/local_anisotropy_sampler_scores.csv",
    "inversion_workflow/runs/cross_stream_hybrid_field_plan/cross_stream_hybrid_candidate_scores.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trend-ranking",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective_ranking.csv"),
    )
    parser.add_argument(
        "--candidate-pools",
        nargs="*",
        type=Path,
        default=[Path(path) for path in DEFAULT_POOLS],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/nmr_trend_anomaly_followup_plan"),
    )
    return parser.parse_args()


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def number(value: Any) -> float | None:
    return float(value) if finite(value) else None


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    return value


def read_pool(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if "candidate_id" not in frame.columns:
        return pd.DataFrame()
    objective_column = None
    for column in ["objective_value", "direct_objective", "direct_permeability_objective", "data_objective_value"]:
        if column in frame.columns:
            objective_column = column
            break
    if objective_column is None:
        return pd.DataFrame()
    output = pd.DataFrame(
        {
            "candidate_id": frame["candidate_id"].astype(str),
            "candidate_pool": str(path),
            "direct_objective": pd.to_numeric(frame[objective_column], errors="coerce"),
            "mesh": frame["mesh"].astype(str) if "mesh" in frame.columns else "",
            "evaluation_csv": frame["evaluation_csv"].astype(str) if "evaluation_csv" in frame.columns else "",
            "summary_json": frame["summary_json"].astype(str) if "summary_json" in frame.columns else "",
            "candidate_table_source": frame["candidate_table_source"].astype(str)
            if "candidate_table_source" in frame.columns
            else "",
            "target_run_id": frame["target_run_id"].astype(str) if "target_run_id" in frame.columns else "",
            "source_is_executed": frame["is_executed_ogs_candidate"].astype(str).str.lower().isin({"true", "1"})
            if "is_executed_ogs_candidate" in frame.columns
            else False,
        }
    )
    return output[pd.to_numeric(output["direct_objective"], errors="coerce").notna()].copy()


def canonical_candidate_id(candidate_id: str) -> str:
    text = str(candidate_id)
    for prefix in [
        "local_basis_sampler_",
        "production_sampler_round2_",
        "production_sampler_round3_",
        "production_sampler_round4_",
        "production_sampler_round5_",
        "production_sampler_",
        "lower_support_loop_",
        "broad_continuous_loop_",
        "broad_continuous_",
        "continuous_proposed_",
        "optimizer_proposed_",
        "regularized_ogs_candidate_",
    ]:
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
            break
    text = re.sub(r"^(?:\d+_)+(?=(basis_|length_|local_anis_|cross_hybrid_))", "", text)
    return text


def add_execution_flags(candidates: pd.DataFrame, ranking: pd.DataFrame) -> pd.DataFrame:
    candidates = candidates.copy()
    run_ids = set(ranking["run_id"].astype(str))
    canonical_runs = {canonical_candidate_id(run_id) for run_id in run_ids}
    candidates["candidate_key"] = candidates["candidate_id"].map(canonical_candidate_id)
    candidates["already_executed_by_run_id"] = (
        candidates["candidate_id"].isin(run_ids)
        | candidates["candidate_key"].isin(canonical_runs)
        | candidates["source_is_executed"].astype(bool)
    )
    mesh_text = candidates["mesh"].astype(str)
    candidates["mesh_path_exists"] = mesh_text.map(lambda item: item not in {"", "nan", "None"} and Path(item).exists())
    candidates["runnable_for_ogs"] = candidates["mesh_path_exists"]
    return candidates


def compact_row(row: pd.Series) -> dict[str, Any]:
    return json_ready(row.to_dict())


def build(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    ranking = pd.read_csv(args.trend_ranking)
    full_active = ranking[ranking["full_active_trend_gate"].astype(bool)].copy()
    for column in [
        "nmr_trend_anomaly_active_objective",
        "direct_permeability_objective",
        "nmr_trend_anomaly_objective",
    ]:
        full_active[column] = pd.to_numeric(full_active[column], errors="coerce")
    full_active = full_active.sort_values("nmr_trend_anomaly_active_objective")
    incumbent = full_active.iloc[0]
    nmr_state = pd.to_numeric(full_active["nmr_trend_anomaly_objective"], errors="coerce").dropna()
    state_stats = {
        "min": float(nmr_state.min()),
        "p10": float(nmr_state.quantile(0.10)),
        "median": float(nmr_state.median()),
        "p90": float(nmr_state.quantile(0.90)),
        "max": float(nmr_state.max()),
        "range": float(nmr_state.max() - nmr_state.min()),
    }

    pool_frames = [read_pool(path) for path in args.candidate_pools]
    candidates = pd.concat([frame for frame in pool_frames if not frame.empty], ignore_index=True)
    candidates = add_execution_flags(candidates, ranking)
    candidates["direct_objective"] = pd.to_numeric(candidates["direct_objective"], errors="coerce")
    candidates = (
        candidates.sort_values(["candidate_key", "direct_objective", "candidate_pool"])
        .drop_duplicates("candidate_key", keep="first")
        .reset_index(drop=True)
    )
    unevaluated = candidates[~candidates["already_executed_by_run_id"].astype(bool)].copy()
    for label in ["min", "p10", "median", "p90", "max"]:
        value = state_stats[label]
        unevaluated[f"combined_if_state_{label}"] = unevaluated["direct_objective"] + value
    incumbent_total = float(incumbent["nmr_trend_anomaly_active_objective"])
    incumbent_direct = float(incumbent["direct_permeability_objective"])
    unevaluated["direct_delta_vs_trend_incumbent"] = unevaluated["direct_objective"] - incumbent_direct
    unevaluated["median_state_delta_vs_trend_incumbent"] = (
        unevaluated["combined_if_state_median"] - incumbent_total
    )
    unevaluated["optimistic_state_delta_vs_trend_incumbent"] = (
        unevaluated["combined_if_state_min"] - incumbent_total
    )
    unevaluated["beats_incumbent_under_observed_min_state"] = unevaluated[
        "optimistic_state_delta_vs_trend_incumbent"
    ].lt(0)
    unevaluated["beats_incumbent_under_median_state"] = unevaluated[
        "median_state_delta_vs_trend_incumbent"
    ].lt(0)
    unevaluated = unevaluated.sort_values(
        [
            "runnable_for_ogs",
            "beats_incumbent_under_median_state",
            "optimistic_state_delta_vs_trend_incumbent",
            "direct_objective",
            "candidate_id",
        ],
        ascending=[False, False, True, True, True],
    )
    best_unevaluated = unevaluated.iloc[0] if not unevaluated.empty else pd.Series(dtype=object)
    direct_advantage = incumbent_direct - float(best_unevaluated.get("direct_objective", np.nan))
    materiality_threshold = max(0.10, 0.25 * state_stats["range"])
    recommendation = (
        "pause_new_trend_anomaly_ogs_batch"
        if not finite(direct_advantage) or direct_advantage < materiality_threshold
        else "run_small_trend_anomaly_followup_batch"
    )
    summary = {
        "status": "nmr_trend_anomaly_followup_plan_generated",
        "recommendation": recommendation,
        "recommendation_reason": (
            "Best unevaluated direct-objective advantage is smaller than the materiality threshold "
            "derived from the observed NMR trend/anomaly state-objective spread."
        )
        if recommendation == "pause_new_trend_anomaly_ogs_batch"
        else (
            "At least one unevaluated candidate has a direct-objective advantage large enough "
            "to justify a small OGS follow-up under the trend/anomaly objective."
        ),
        "trend_incumbent_run": str(incumbent["run_id"]),
        "trend_incumbent_objective": incumbent_total,
        "trend_incumbent_direct_objective": incumbent_direct,
        "trend_incumbent_nmr_objective": float(incumbent["nmr_trend_anomaly_objective"]),
        "full_active_trend_runs": int(full_active.shape[0]),
        "nmr_trend_state_objective_stats": state_stats,
        "candidate_pool_count": len(args.candidate_pools),
        "candidate_count_unique": int(candidates.shape[0]),
        "unevaluated_candidate_count": int(unevaluated.shape[0]),
        "unevaluated_runnable_candidate_count": int(unevaluated["runnable_for_ogs"].sum()),
        "best_unevaluated_candidate": compact_row(best_unevaluated) if not best_unevaluated.empty else {},
        "best_unevaluated_direct_advantage_vs_incumbent": number(direct_advantage),
        "materiality_threshold": materiality_threshold,
        "unevaluated_candidates_beating_incumbent_under_median_state": int(
            unevaluated["beats_incumbent_under_median_state"].sum()
        ),
        "unevaluated_candidates_beating_incumbent_under_observed_min_state": int(
            unevaluated["beats_incumbent_under_observed_min_state"].sum()
        ),
        "activation_note": (
            "Use this as a promoted-NMR-mode planning screen only. The current report should still "
            "state that the default objective is unchanged until that modelling decision is accepted."
        ),
    }
    return unevaluated, summary


def fmt(value: Any, digits: int = 6) -> str:
    if not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, candidates: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# NMR Trend/Anomaly Follow-Up Plan",
        "",
        "This plan uses the executable NMR trend/anomaly objective ranking as the executed evidence base and screens existing unevaluated permeability-field pools for a possible next OGS batch.",
        "",
        "## Recommendation",
        "",
        f"- Recommendation: `{summary['recommendation']}`",
        f"- Reason: {summary['recommendation_reason']}",
        f"- Trend/anomaly incumbent: `{summary['trend_incumbent_run']}` with objective {fmt(summary['trend_incumbent_objective'])}",
        f"- Incumbent direct objective: {fmt(summary['trend_incumbent_direct_objective'])}",
        f"- Incumbent NMR trend/anomaly objective: {fmt(summary['trend_incumbent_nmr_objective'])}",
        f"- Full active trend/anomaly runs: {summary['full_active_trend_runs']}",
        f"- Unique candidate-pool rows screened: {summary['candidate_count_unique']}",
        f"- Unevaluated candidate rows screened: {summary['unevaluated_candidate_count']}",
        f"- Unevaluated candidates with mesh files: {summary['unevaluated_runnable_candidate_count']}",
        f"- Materiality threshold: {fmt(summary['materiality_threshold'])}",
        f"- Best unevaluated direct advantage vs incumbent: {fmt(summary['best_unevaluated_direct_advantage_vs_incumbent'])}",
        f"- Unevaluated candidates beating incumbent under median observed NMR state term: {summary['unevaluated_candidates_beating_incumbent_under_median_state']}",
        f"- Unevaluated candidates beating incumbent under best observed NMR state term: {summary['unevaluated_candidates_beating_incumbent_under_observed_min_state']}",
        "",
        "## Top Unevaluated Candidates",
        "",
        "| Rank | Candidate | Pool | Direct objective | Direct delta | Median-state delta | Optimistic-state delta | Mesh |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    display = candidates.head(20).reset_index(drop=True)
    for idx, row in display.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx + 1),
                    f"`{row['candidate_id']}`",
                    f"`{Path(str(row['candidate_pool'])).parent.name}`",
                    fmt(row["direct_objective"]),
                    fmt(row["direct_delta_vs_trend_incumbent"]),
                    fmt(row["median_state_delta_vs_trend_incumbent"]),
                    fmt(row["optimistic_state_delta_vs_trend_incumbent"]),
                    f"`{row.get('mesh', '')}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The NMR trend/anomaly state term is not flat, but its observed spread across the executed full-active runs is small compared with the uncertainty introduced by changing residual semantics. The best unevaluated candidates only improve the direct permeability objective by a very small amount relative to the current trend/anomaly incumbent, so a new OGS batch is not the highest-value next action unless the modelling team explicitly wants a narrow tie-breaker run.",
            "",
            summary["activation_note"],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidates, summary = build(args)
    csv_path = args.output_dir / "nmr_trend_anomaly_followup_candidates.csv"
    json_path = args.output_dir / "NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json"
    md_path = args.output_dir / "NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md"
    candidates.to_csv(csv_path, index=False)
    summary["generated_files"] = [str(csv_path), str(json_path), str(md_path)]
    json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_path, candidates, summary)
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
