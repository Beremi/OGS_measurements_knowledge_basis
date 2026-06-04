#!/usr/bin/env python3
"""Build conditional field-selection scenarios from the cross-stream scorecard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCENARIOS = [
    {
        "scenario_id": "S01_current_active_raw_nmr",
        "title": "Current active objective",
        "gate_status": "active_now",
        "columns": ["active_objective_normalized_loss"],
        "description": "Current objective: direct gas-pulse permeability plus raw absolute NMR theta residual.",
    },
    {
        "scenario_id": "S02_promoted_nmr_trend_anomaly",
        "title": "Promoted NMR trend/anomaly",
        "gate_status": "internal_promotion_decision_required",
        "columns": ["nmr_trend_anomaly_normalized_loss"],
        "description": "Conditional objective if the preferred within-label NMR trend/anomaly residual replaces raw NMR.",
    },
    {
        "scenario_id": "S03_active_plus_ert_screen",
        "title": "Active objective plus ERT screen",
        "gate_status": "external_ert_gate_required",
        "columns": ["active_objective_normalized_loss", "ert_normalized_loss"],
        "description": "Equal-normalized screen using the current active objective and provisional ERT log-resistivity MAE.",
    },
    {
        "scenario_id": "S04_active_plus_taupe_screen",
        "title": "Active objective plus Taupe screen",
        "gate_status": "external_taupe_gate_required",
        "columns": ["active_objective_normalized_loss", "taupe_normalized_loss"],
        "description": "Equal-normalized screen using the current active objective and provisional Taupe/TDR trend MAE.",
    },
    {
        "scenario_id": "S05_active_plus_ert_taupe_screen",
        "title": "Active objective plus ERT and Taupe",
        "gate_status": "external_ert_taupe_gates_required",
        "columns": ["active_objective_normalized_loss", "ert_normalized_loss", "taupe_normalized_loss"],
        "description": "Equal-normalized screen if ERT and Taupe/TDR diagnostics were both accepted as screening evidence.",
    },
    {
        "scenario_id": "S06_active_plus_promoted_nmr_ert_taupe",
        "title": "Active plus promoted NMR, ERT, and Taupe",
        "gate_status": "internal_and_external_gates_required",
        "columns": [
            "active_objective_normalized_loss",
            "nmr_trend_anomaly_normalized_loss",
            "ert_normalized_loss",
            "taupe_normalized_loss",
        ],
        "description": "Equal-normalized all-available numeric screen without duplicating the NMR label-bias variant.",
    },
    {
        "scenario_id": "S07_diagnostics_only_nmr_ert_taupe",
        "title": "Diagnostics-only screen",
        "gate_status": "diagnostic_only_not_active_likelihood",
        "columns": ["nmr_trend_anomaly_normalized_loss", "ert_normalized_loss", "taupe_normalized_loss"],
        "description": "Equal-normalized screen using NMR trend/anomaly, ERT, and Taupe diagnostics only.",
    },
    {
        "scenario_id": "S08_rank_consensus_all_streams",
        "title": "Rank consensus across all streams",
        "gate_status": "diagnostic_consensus_not_active_likelihood",
        "columns": ["mean_rank_all_streams"],
        "score_mode": "existing_score",
        "description": "Mean-rank consensus from the cross-stream scorecard, including active objective and diagnostics.",
    },
]


DISPLAY_RANK_COLUMNS = [
    "active_objective_rank",
    "nmr_trend_anomaly_rank",
    "ert_mae_rank",
    "taupe_mae_rank",
    "mean_rank_all_streams",
    "worst_rank_all_streams",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument(
        "--stream-gate-summary",
        type=Path,
        default=Path("inversion_workflow/measurement_stream_activation_gate_audit_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios.md"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def require_columns(frame: pd.DataFrame, columns: list[str], path: Path) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} lacks required columns: {', '.join(missing)}")


def scenario_score(frame: pd.DataFrame, scenario: dict[str, Any]) -> pd.Series:
    columns = scenario["columns"]
    require_columns(frame, columns, Path("scorecard"))
    values = frame[columns].apply(pd.to_numeric, errors="coerce")
    if scenario.get("score_mode") == "existing_score":
        return values.iloc[:, 0]
    return values.mean(axis=1)


def build_scenarios(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    scorecard = pd.read_csv(args.scorecard)
    field = read_json(args.current_field_summary)
    gate = read_json(args.stream_gate_summary)
    current_run_id = str(field.get("run_id", ""))
    require_columns(scorecard, ["run_id", "run_kind", *DISPLAY_RANK_COLUMNS], args.scorecard)
    if current_run_id not in set(scorecard["run_id"]):
        raise ValueError(f"current run {current_run_id} is not present in {args.scorecard}")

    rows: list[dict[str, Any]] = []
    top_by_scenario: dict[str, list[dict[str, Any]]] = {}
    current_wins = 0
    unique_winners: set[str] = set()
    conditional_winner_count: dict[str, int] = {}
    for scenario in SCENARIOS:
        frame = scorecard.copy()
        score_col = f"{scenario['scenario_id']}_score"
        rank_col = f"{scenario['scenario_id']}_rank"
        frame[score_col] = scenario_score(frame, scenario)
        frame[rank_col] = frame[score_col].rank(method="min", ascending=True)
        ranked = frame.sort_values([score_col, "active_objective_rank", "run_id"], na_position="last")
        winner = ranked.iloc[0].to_dict()
        current = frame.loc[frame["run_id"] == current_run_id].iloc[0].to_dict()
        unique_winners.add(str(winner["run_id"]))
        conditional_winner_count[str(winner["run_id"])] = conditional_winner_count.get(str(winner["run_id"]), 0) + 1
        current_winner = str(winner["run_id"]) == current_run_id
        current_wins += int(current_winner)
        top_rows = []
        for _, top in ranked.head(5).iterrows():
            top_rows.append(
                {
                    "run_id": top["run_id"],
                    "run_kind": top["run_kind"],
                    "scenario_score": top[score_col],
                    "scenario_rank": top[rank_col],
                    "active_rank": top["active_objective_rank"],
                    "nmr_trend_rank": top["nmr_trend_anomaly_rank"],
                    "ert_rank": top["ert_mae_rank"],
                    "taupe_rank": top["taupe_mae_rank"],
                    "mean_rank_all_streams": top["mean_rank_all_streams"],
                    "worst_rank_all_streams": top["worst_rank_all_streams"],
                }
            )
        top_by_scenario[scenario["scenario_id"]] = top_rows
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "title": scenario["title"],
                "gate_status": scenario["gate_status"],
                "score_columns": ";".join(scenario["columns"]),
                "winner_run_id": winner["run_id"],
                "winner_run_kind": winner["run_kind"],
                "winner_score": winner[score_col],
                "winner_active_rank": winner["active_objective_rank"],
                "winner_nmr_trend_rank": winner["nmr_trend_anomaly_rank"],
                "winner_ert_rank": winner["ert_mae_rank"],
                "winner_taupe_rank": winner["taupe_mae_rank"],
                "winner_mean_rank_all_streams": winner["mean_rank_all_streams"],
                "winner_worst_rank_all_streams": winner["worst_rank_all_streams"],
                "current_run_id": current_run_id,
                "current_is_winner": current_winner,
                "current_score": current[score_col],
                "current_scenario_rank": current[rank_col],
                "current_active_rank": current["active_objective_rank"],
                "current_nmr_trend_rank": current["nmr_trend_anomaly_rank"],
                "current_ert_rank": current["ert_mae_rank"],
                "current_taupe_rank": current["taupe_mae_rank"],
                "score_delta_current_minus_winner": current[score_col] - winner[score_col],
                "description": scenario["description"],
            }
        )
    scenario_frame = pd.DataFrame(rows)
    final_decision = (
        "single_field_not_stable_across_gate_scenarios"
        if len(unique_winners) > 1
        else "single_field_stable_across_defined_scenarios"
    )
    summary = {
        "status": "conditional_field_selection_scenarios_generated",
        "current_run_id": current_run_id,
        "scenario_count": len(rows),
        "unique_winner_count": len(unique_winners),
        "unique_winners": sorted(unique_winners),
        "current_field_winning_scenario_count": current_wins,
        "conditional_winner_count": conditional_winner_count,
        "final_decision": final_decision,
        "gate_context": {
            "stream_gate_status": gate.get("status"),
            "required_gate_fail_count": gate.get("required_gate_fail_count"),
            "required_gate_warn_count": gate.get("required_gate_warn_count"),
            "promotion_decision_counts": gate.get("promotion_decision_counts"),
        },
        "interpretation": [
            "The current packaged field wins only the active raw-NMR objective scenario.",
            "Different defensible diagnostic or promoted-NMR scenarios select different fields.",
            "Use this as a conditional selection map; it does not promote ERT, Taupe/TDR, RH, or other-HM into the likelihood.",
        ],
        "top_by_scenario": top_by_scenario,
        "source_artifacts": [
            str(args.scorecard),
            str(args.current_field_summary),
            str(args.stream_gate_summary),
        ],
    }
    return scenario_frame, json_ready(summary)


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Conditional Field Selection Scenarios",
        "",
        "This audit asks which executed field would be selected under each currently",
        "defensible objective or diagnostic-gate scenario. It is a map of conditional",
        "decisions, not a promotion of gated streams into the active likelihood.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Current packaged run: `{summary['current_run_id']}`",
        f"- Scenarios: {summary['scenario_count']}",
        f"- Unique winners: {summary['unique_winner_count']}",
        f"- Current field winning scenarios: {summary['current_field_winning_scenario_count']}",
        f"- Final decision: `{summary['final_decision']}`",
        f"- Required stream-gate failures: {summary['gate_context'].get('required_gate_fail_count')}",
        "",
        "## Scenario Winners",
        "",
        "| Scenario | Gate status | Winner | Current rank | Current winner? | Winner ranks (active/NMR/ERT/Taupe) |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            f"| `{row['scenario_id']}` {row['title']} | `{row['gate_status']}` | "
            f"`{row['winner_run_id']}` | {row['current_scenario_rank']:.0f} | "
            f"{'yes' if row['current_is_winner'] else 'no'} | "
            f"{row['winner_active_rank']:.0f}/{row['winner_nmr_trend_rank']:.0f}/"
            f"{row['winner_ert_rank']:.0f}/{row['winner_taupe_rank']:.0f} |"
        )
    lines.extend(["", "## Interpretation", ""])
    for item in summary["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Top Candidates By Scenario",
            "",
        ]
    )
    for _, row in frame.iterrows():
        lines.extend(
            [
                f"### {row['scenario_id']} - {row['title']}",
                "",
                row["description"],
                "",
                "| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for top in summary["top_by_scenario"][row["scenario_id"]]:
            lines.append(
                f"| {top['scenario_rank']:.0f} | `{top['run_id']}` | {top['scenario_score']:.6g} | "
                f"{top['active_rank']:.0f} | {top['nmr_trend_rank']:.0f} | "
                f"{top['ert_rank']:.0f} | {top['taupe_rank']:.0f} |"
            )
        lines.append("")
    lines.extend(["## Source Artifacts", ""])
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    frame, summary = build_scenarios(args)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.output_md, frame, summary)


if __name__ == "__main__":
    main()
