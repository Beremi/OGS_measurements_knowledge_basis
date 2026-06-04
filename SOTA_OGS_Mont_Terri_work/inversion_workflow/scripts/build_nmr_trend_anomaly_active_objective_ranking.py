#!/usr/bin/env python3
"""Build a provisional active-objective ranking using NMR trend/anomaly residuals.

This does not overwrite the historical combined_objective_* files. It exercises
the objective assembler's nmr_within_label_trend_anomaly mode across existing
candidate run directories and writes a separate ranking package.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd

from assemble_inversion_objective import STATE_OBJECTIVE_NMR_TREND, assemble, finite, json_ready


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("inversion_workflow/runs"))
    parser.add_argument(
        "--diagnostic-audit",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective_ranking.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/nmr"),
        help="Measurement-catalogue directory where derived copies are stored.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def component(components: pd.DataFrame, name: str) -> dict[str, Any]:
    matched = components[components["component"].astype(str).eq(name)]
    if matched.empty:
        return {}
    return matched.iloc[0].to_dict()


def component_from_summary(summary: dict[str, Any], name: str) -> dict[str, Any]:
    for item in summary.get("components", []):
        if str(item.get("component")) == name:
            return item
    return {}


def number(value: Any) -> float | None:
    if not finite(value):
        return None
    return float(value)


def best_row(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    if frame.empty or column not in frame.columns:
        return {}
    valid = frame[pd.to_numeric(frame[column], errors="coerce").notna()].copy()
    if valid.empty:
        return {}
    valid[column] = pd.to_numeric(valid[column], errors="coerce")
    return json_ready(valid.sort_values(column, na_position="last").iloc[0].to_dict())


def run_assembler_for_run(run_dir: Path) -> dict[str, Any] | None:
    required = {
        "permeability_evaluation": run_dir / "permeability_fit_evaluation.csv",
        "permeability_summary": run_dir / "permeability_fit_summary.json",
        "state_evaluation": run_dir / "state_observation_evaluation.csv",
        "state_summary": run_dir / "state_observation_evaluation_summary.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        return {
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "activation_status": "missing_required_inputs",
            "missing_inputs": "; ".join(missing),
        }
    args = SimpleNamespace(
        **required,
        output=run_dir / "combined_objective_nmr_trend_anomaly_components.csv",
        summary_output=run_dir / "combined_objective_nmr_trend_anomaly_summary.json",
        state_objective_mode=STATE_OBJECTIVE_NMR_TREND,
    )
    components, summary = assemble(args)
    direct = component(components, "direct_permeability_pulse_tests")
    state = component(components, "state_observations")
    raw_summary = read_json(run_dir / "combined_objective_summary.json")
    raw_state = component_from_summary(raw_summary, "state_observations")
    return {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "activation_status": "evaluated",
        "state_objective_mode": summary.get("state_objective_mode"),
        "active_component_count": summary.get("active_component_count"),
        "nmr_trend_anomaly_active_objective": summary.get("total_active_objective_value"),
        "direct_permeability_objective": number(direct.get("objective_value")),
        "nmr_trend_anomaly_objective": number(state.get("nmr_trend_anomaly_objective_value")),
        "nmr_trend_anomaly_rmse_normalized_residual": number(state.get("primary_metric_value")),
        "nmr_trend_anomaly_rows": state.get("nmr_trend_anomaly_rows"),
        "nmr_trend_anomaly_groups": state.get("nmr_trend_anomaly_groups"),
        "nmr_trend_anomaly_excluded_singleton_groups": state.get(
            "nmr_trend_anomaly_excluded_singleton_groups"
        ),
        "raw_combined_objective": raw_summary.get("total_active_objective_value"),
        "raw_state_objective": raw_state.get("objective_value"),
        "raw_state_rmse_normalized_residual": raw_state.get("primary_metric_value"),
        "raw_nmr_objective_from_state_rows": number(state.get("raw_nmr_objective_value")),
        "non_nmr_state_objective_value": number(state.get("non_nmr_state_objective_value")),
    }


def build(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    for run_dir in sorted(path.parent for path in args.runs_dir.glob("*/state_observation_evaluation.csv")):
        rows.append(run_assembler_for_run(run_dir))
    ranking = pd.DataFrame([row for row in rows if row is not None])
    if ranking.empty:
        summary = {
            "status": "nmr_trend_anomaly_active_objective_no_runs",
            "run_count": 0,
            "activation_gate": "No state_observation_evaluation.csv files were found.",
        }
        return ranking, summary

    if args.diagnostic_audit.exists():
        diagnostic = pd.read_csv(args.diagnostic_audit)
        keep = [
            "run_id",
            "trend_anomaly_combined_objective",
            "trend_anomaly_objective",
            "trend_anomaly_combined_rank",
            "current_combined_rank",
        ]
        diagnostic = diagnostic[[column for column in keep if column in diagnostic.columns]].copy()
        diagnostic = diagnostic.rename(
            columns={
                "trend_anomaly_combined_objective": "diagnostic_trend_anomaly_combined_objective",
                "trend_anomaly_objective": "diagnostic_trend_anomaly_objective",
                "trend_anomaly_combined_rank": "diagnostic_trend_anomaly_combined_rank",
                "current_combined_rank": "diagnostic_raw_combined_rank",
            }
        )
        ranking = ranking.merge(diagnostic, on="run_id", how="left")
        ranking["diagnostic_combined_delta"] = (
            pd.to_numeric(ranking["nmr_trend_anomaly_active_objective"], errors="coerce")
            - pd.to_numeric(ranking["diagnostic_trend_anomaly_combined_objective"], errors="coerce")
        )
        ranking["diagnostic_nmr_delta"] = (
            pd.to_numeric(ranking["nmr_trend_anomaly_objective"], errors="coerce")
            - pd.to_numeric(ranking["diagnostic_trend_anomaly_objective"], errors="coerce")
        )

    ranking["nmr_trend_anomaly_active_rank"] = pd.to_numeric(
        ranking["nmr_trend_anomaly_active_objective"],
        errors="coerce",
    ).rank(method="min")
    ranking["raw_combined_rank"] = pd.to_numeric(ranking["raw_combined_objective"], errors="coerce").rank(
        method="min"
    )
    full_active_mask = (
        pd.to_numeric(ranking["active_component_count"], errors="coerce").ge(2)
        & pd.to_numeric(ranking["direct_permeability_objective"], errors="coerce").notna()
        & pd.to_numeric(ranking["nmr_trend_anomaly_objective"], errors="coerce").notna()
    )
    ranking["full_active_trend_gate"] = full_active_mask
    ranking["nmr_trend_anomaly_full_active_rank"] = pd.to_numeric(
        ranking["nmr_trend_anomaly_active_objective"].where(full_active_mask),
        errors="coerce",
    ).rank(method="min")
    ranking["raw_full_active_rank"] = pd.to_numeric(
        ranking["raw_combined_objective"].where(full_active_mask),
        errors="coerce",
    ).rank(method="min")
    ranking = ranking.sort_values(
        ["nmr_trend_anomaly_full_active_rank", "raw_full_active_rank", "run_id"],
        na_position="last",
    )

    full_active = ranking[ranking["full_active_trend_gate"].astype(bool)].copy()
    best_trend = best_row(full_active, "nmr_trend_anomaly_active_objective")
    best_raw = best_row(full_active, "raw_combined_objective")
    raw_incumbent = ranking[ranking["run_id"].astype(str).eq(str(best_raw.get("run_id")))]
    trend_best = ranking[ranking["run_id"].astype(str).eq(str(best_trend.get("run_id")))]
    deltas = []
    for column in ["diagnostic_combined_delta", "diagnostic_nmr_delta"]:
        if column in ranking.columns:
            values = pd.to_numeric(ranking[column], errors="coerce").abs().dropna()
            if not values.empty:
                deltas.append(float(values.max()))
    summary = {
        "status": "nmr_trend_anomaly_active_objective_mode_implemented_provisional",
        "state_objective_mode": STATE_OBJECTIVE_NMR_TREND,
        "run_count": int(ranking.shape[0]),
        "runs_evaluated": int(ranking["activation_status"].astype(str).eq("evaluated").sum()),
        "runs_with_full_active_trend_objective": int(full_active.shape[0]),
        "best_trend_anomaly_active_objective": best_trend,
        "best_raw_combined_objective": best_raw,
        "raw_incumbent_rank_under_trend_anomaly": number(
            raw_incumbent["nmr_trend_anomaly_full_active_rank"].iloc[0] if not raw_incumbent.empty else None
        ),
        "trend_anomaly_winner_raw_rank": number(
            trend_best["raw_full_active_rank"].iloc[0] if not trend_best.empty else None
        ),
        "diagnostic_validation_max_abs_delta": max(deltas) if deltas else None,
        "activation_gate": (
            "Executable but still provisional: this mode can be passed to evaluate_inversion_candidate.py, "
            "but promotion to the default reporting objective still needs explicit modelling acceptance because "
            "it changes the winner relative to the raw absolute NMR objective."
        ),
    }
    return ranking, summary


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, ranking: pd.DataFrame, summary: dict[str, Any]) -> None:
    best_trend = summary.get("best_trend_anomaly_active_objective", {})
    best_raw = summary.get("best_raw_combined_objective", {})
    lines = [
        "# NMR Trend/Anomaly Active Objective Ranking",
        "",
        "This package exercises `assemble_inversion_objective.py --state-objective-mode nmr_within_label_trend_anomaly` across the existing executed candidate runs.",
        "It is a provisional active-objective implementation path; it does not overwrite the historical raw-theta `combined_objective_*` files.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Runs evaluated: {summary.get('runs_evaluated', 0)} / {summary.get('run_count', 0)}",
        f"- Runs with direct permeability plus NMR trend/anomaly objective: {summary.get('runs_with_full_active_trend_objective', 0)}",
        f"- Best trend/anomaly objective run: `{best_trend.get('run_id', 'n/a')}` with objective {fmt(best_trend.get('nmr_trend_anomaly_active_objective'))}",
        f"- Raw-objective incumbent: `{best_raw.get('run_id', 'n/a')}` with raw objective {fmt(best_raw.get('raw_combined_objective'))}",
        f"- Raw incumbent rank under trend/anomaly: {fmt(summary.get('raw_incumbent_rank_under_trend_anomaly'), 0)}",
        f"- Trend/anomaly winner raw rank: {fmt(summary.get('trend_anomaly_winner_raw_rank'), 0)}",
        f"- Diagnostic validation max abs delta: {fmt(summary.get('diagnostic_validation_max_abs_delta'), 12)}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Top Candidate Runs",
        "",
        "| Rank | Run | Trend/anomaly combined | Direct permeability | NMR trend/anomaly | Raw combined | Raw rank | Rows | Groups |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    top = ranking[ranking["full_active_trend_gate"].astype(bool)].head(15)
    for _, row in top.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt(row.get("nmr_trend_anomaly_full_active_rank"), 0),
                    f"`{row['run_id']}`",
                    fmt(row.get("nmr_trend_anomaly_active_objective")),
                    fmt(row.get("direct_permeability_objective")),
                    fmt(row.get("nmr_trend_anomaly_objective")),
                    fmt(row.get("raw_combined_objective")),
                    fmt(row.get("raw_full_active_rank"), 0),
                    fmt(row.get("nmr_trend_anomaly_rows"), 0),
                    fmt(row.get("nmr_trend_anomaly_groups"), 0),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Implementation Note",
            "",
            "The executable residual is formed within each `observation_family` plus `measurement_label` NMR group as `(theta_model - weighted_group_mean(theta_model)) - (theta_NMR_obs - weighted_group_mean(theta_NMR_obs))`, using the existing NMR sigma values. Constant bound/interlayer-water and campaign offsets therefore cancel to first order, while the frozen OGS model state remains `theta = porosity * liquid_saturation`.",
            "",
            "This ranking is the practical next step after the NMR objective decision package: the code path now exists for future candidate evaluations, but the report should still call it provisional until the modelling team accepts this residual as the promoted/default NMR likelihood.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_catalogue_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    planned = []
    for path in paths:
        destination = derived / path.name
        planned.append({"source": str(path), "catalogue_copy": str(destination)})
        if path.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    return planned


def main() -> None:
    args = parse_args()
    ranking, summary = build(args)
    output_paths = [args.output, args.summary_output, args.markdown_output]
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(args.output, index=False)
    write_markdown(args.markdown_output, ranking, summary)
    summary["catalogue_copies"] = [
        {"source": str(path), "catalogue_copy": str(args.catalogue_dir / "derived_files" / path.name)}
        for path in output_paths
    ]
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    copy_catalogue_outputs(args.catalogue_dir, output_paths)
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"runs evaluated: {summary.get('runs_evaluated', 0)}")
    print(f"best run: {summary.get('best_trend_anomaly_active_objective', {}).get('run_id')}")


if __name__ == "__main__":
    main()
