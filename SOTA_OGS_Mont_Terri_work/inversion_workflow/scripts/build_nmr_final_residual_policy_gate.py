#!/usr/bin/env python3
"""Build the final-policy gate for NMR residual semantics."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--objective-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_objective_decision_summary.json"),
    )
    parser.add_argument(
        "--activation-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective_summary.json"),
    )
    parser.add_argument(
        "--followup-summary",
        type=Path,
        default=Path("inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json"),
    )
    parser.add_argument(
        "--scenario-summary",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"),
    )
    parser.add_argument(
        "--promotion-summary",
        type=Path,
        default=Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/nmr/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{number:.{digits}g}"


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    objective = read_json(args.objective_summary)
    activation = read_json(args.activation_summary)
    followup = read_json(args.followup_summary)
    scenario = read_json(args.scenario_summary)
    promotion = read_json(args.promotion_summary)

    trend_best = activation.get("best_trend_anomaly_active_objective", {})
    raw_best = activation.get("best_raw_combined_objective", {})
    top_by_scenario = scenario.get("top_by_scenario", {})
    promoted_nmr_winner = None
    if isinstance(top_by_scenario, dict):
        promoted_rows = top_by_scenario.get("S02_promoted_nmr_trend_anomaly", [])
        if isinstance(promoted_rows, list) and promoted_rows:
            promoted_nmr_winner = promoted_rows[0].get("run_id")
        elif isinstance(promoted_rows, dict):
            promoted_nmr_winner = promoted_rows.get("run_id")

    rows = [
        {
            "gate_id": "NMR01_current_report_default",
            "gate_type": "default_policy_gate",
            "current_status": "raw_absolute_nmr_retained_as_current_report_default_not_final",
            "decision": (
                "Keep the historical raw absolute-theta NMR objective as the current-report default for reproducibility, "
                "but do not call it final without an accepted bound/free-water or model-error policy."
            ),
            "evidence": (
                f"active_objective_changed={objective.get('active_objective_changed')}; "
                f"raw incumbent={objective.get('best_current_raw_run')} objective={objective.get('best_current_raw_objective')}; "
                f"raw incumbent rank under trend/anomaly={objective.get('current_incumbent_recommended_rank')}; "
                f"usable mapped rows above fixed porosity={objective.get('uncorrected_usable_rows_above_fixed_phi')}/"
                f"{objective.get('usable_current_mesh_rows')}"
            ),
            "required_acceptance": (
                "A final decision must either accept raw absolute theta with explicit bound/free-water/model-error caveats, "
                "or select another NMR residual policy."
            ),
            "source_artifacts": "inversion_workflow/nmr_objective_decision.md",
        },
        {
            "gate_id": "NMR02_promoted_trend_anomaly_option",
            "gate_type": "candidate_final_policy_gate",
            "current_status": "executable_trend_anomaly_policy_available_requires_acceptance",
            "decision": (
                "Within-label trend/anomaly is the preferred provisional final NMR likelihood candidate if the modelling "
                "team accepts that NMR contributes changes/anomalies rather than absolute mobile water content."
            ),
            "evidence": (
                f"mode={activation.get('state_objective_mode')}; status={activation.get('status')}; "
                f"full-active runs={activation.get('runs_with_full_active_trend_objective')}; "
                f"best trend run={trend_best.get('run_id')} objective={trend_best.get('nmr_trend_anomaly_active_objective')}; "
                f"validation max abs delta={activation.get('diagnostic_validation_max_abs_delta')}; "
                f"trend winner raw rank={activation.get('trend_anomaly_winner_raw_rank')}"
            ),
            "required_acceptance": (
                "Record promotion to the reporting/search default, regenerate conditional field selection, and state "
                "that absolute NMR water content is not being fitted."
            ),
            "source_artifacts": "inversion_workflow/nmr_trend_anomaly_active_objective.md",
        },
        {
            "gate_id": "NMR03_promoted_mode_new_ogs_spending",
            "gate_type": "execution_gate",
            "current_status": "no_new_trend_anomaly_ogs_batch_recommended_now",
            "decision": (
                "Do not spend a new OGS batch solely to refine the promoted-NMR trend/anomaly mode until the final "
                "NMR policy is accepted and the materiality threshold is met."
            ),
            "evidence": (
                f"follow-up recommendation={followup.get('recommendation')}; "
                f"materiality threshold={followup.get('materiality_threshold')}; "
                f"best unevaluated direct advantage={followup.get('best_unevaluated_direct_advantage_vs_incumbent')}; "
                f"median-state beating candidates={followup.get('unevaluated_candidates_beating_incumbent_under_median_state')}; "
                f"runnable unevaluated candidates={followup.get('unevaluated_runnable_candidate_count')}"
            ),
            "required_acceptance": (
                "Reopen only after final NMR semantics are chosen and a candidate has a material improvement under that accepted objective."
            ),
            "source_artifacts": "inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md",
        },
        {
            "gate_id": "NMR04_final_promotion_dependency",
            "gate_type": "final_promotion_gate",
            "current_status": "blocks_final_promotion_until_nmr_policy_selected",
            "decision": (
                "Do not promote any permeability field as final while the final NMR residual policy is still open."
            ),
            "evidence": (
                f"scenario decision={scenario.get('final_decision')}; scenarios={scenario.get('scenario_count')}; "
                f"unique winners={scenario.get('unique_winner_count')}; current-field wins="
                f"{scenario.get('current_field_winning_scenario_count')}; promoted-NMR scenario winner="
                f"{promoted_nmr_winner}; promotion decision={promotion.get('promotion_decision')}; "
                f"open promotion criteria={promotion.get('open_criterion_ids')}"
            ),
            "required_acceptance": (
                "Choose raw absolute theta, within-label trend/anomaly, label-bias/free-water correction, or explicit NMR exclusion; "
                "then rerun scenario and promotion audits."
            ),
            "source_artifacts": (
                "inversion_workflow/conditional_field_selection_scenarios.md; "
                "inversion_workflow/final_inversion_promotion_checklist.md"
            ),
        },
    ]

    summary = {
        "status": "nmr_final_residual_policy_gate_generated",
        "gate_count": len(rows),
        "final_nmr_policy_selected": False,
        "current_report_default_policy": "retain_raw_absolute_theta_current_report_default_with_caveats",
        "recommended_candidate_policy": objective.get("recommended_option_id"),
        "recommended_candidate_policy_run": objective.get("best_recommended_run"),
        "recommended_candidate_policy_objective": objective.get("best_recommended_combined_objective"),
        "active_objective_changed": objective.get("active_objective_changed"),
        "current_raw_incumbent_run": objective.get("best_current_raw_run"),
        "current_raw_incumbent_objective": objective.get("best_current_raw_objective"),
        "current_raw_incumbent_rank_under_trend_anomaly": objective.get("current_incumbent_recommended_rank"),
        "trend_anomaly_winner_raw_rank": activation.get("trend_anomaly_winner_raw_rank"),
        "trend_anomaly_mode_status": activation.get("status"),
        "trend_anomaly_validation_max_abs_delta": activation.get("diagnostic_validation_max_abs_delta"),
        "trend_anomaly_full_active_runs": activation.get("runs_with_full_active_trend_objective"),
        "followup_recommendation": followup.get("recommendation"),
        "followup_materiality_threshold": followup.get("materiality_threshold"),
        "followup_best_unevaluated_direct_advantage": followup.get(
            "best_unevaluated_direct_advantage_vs_incumbent"
        ),
        "followup_median_state_beating_candidates": followup.get(
            "unevaluated_candidates_beating_incumbent_under_median_state"
        ),
        "conditional_scenario_decision": scenario.get("final_decision"),
        "conditional_unique_winner_count": scenario.get("unique_winner_count"),
        "current_field_winning_scenario_count": scenario.get("current_field_winning_scenario_count"),
        "promotion_decision": promotion.get("promotion_decision"),
        "next_decision_sequence": [
            "Keep raw absolute theta as the current-report default for reproducibility until a final NMR policy is selected.",
            "If promoted, use within-label trend/anomaly as the preferred provisional final NMR residual and state that absolute water content is not fitted.",
            "Do not run a new trend/anomaly OGS batch now because the best unevaluated direct advantage is below the materiality threshold.",
            "After selecting the final NMR policy, regenerate conditional field selection, final promotion, final objective, and readiness audits.",
        ],
        "source_artifacts": [
            str(args.objective_summary),
            str(args.activation_summary),
            str(args.followup_summary),
            str(args.scenario_summary),
            str(args.promotion_summary),
        ],
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "gate_id",
        "gate_type",
        "current_status",
        "decision",
        "evidence",
        "required_acceptance",
        "source_artifacts",
    ]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# NMR Final Residual Policy Gate",
        "",
        "This gate separates the current-report NMR default from a future final NMR",
        "likelihood decision. It does not change the active objective, run OGS, or",
        "modify the frozen GESA model.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Final NMR policy selected: {summary['final_nmr_policy_selected']}",
        f"- Current-report default policy: `{summary['current_report_default_policy']}`",
        f"- Recommended candidate policy: `{summary['recommended_candidate_policy']}`",
        f"- Recommended candidate run: `{summary['recommended_candidate_policy_run']}`",
        f"- Current raw incumbent rank under trend/anomaly: {summary['current_raw_incumbent_rank_under_trend_anomaly']}",
        f"- Trend/anomaly winner raw rank: {summary['trend_anomaly_winner_raw_rank']}",
        f"- Follow-up recommendation: `{summary['followup_recommendation']}`",
        "",
        "## Gate Table",
        "",
        "| Gate | Type | Status | Decision | Evidence | Required acceptance |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate_id']}` | `{row['gate_type']}` | `{row['current_status']}` | "
            f"{md_cell(row['decision'])} | {md_cell(row['evidence'])} | "
            f"{md_cell(row['required_acceptance'])} |"
        )

    lines.extend(["", "## Next Decision Sequence", ""])
    for item in summary["next_decision_sequence"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The executable within-label trend/anomaly residual is the safer provisional NMR policy because constant bound/interlayer-water and campaign offsets cancel to first order. It is not automatically the final default because it changes the selected field relative to the raw absolute-theta objective. Use `nmr_final_residual_policy_acceptance_record_template.md` as the separate signoff guardrail before treating any NMR residual option as accepted. The follow-up screen also says not to spend another OGS batch merely to refine this mode before the policy is accepted.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.catalogue_dir:
        args.catalogue_dir.mkdir(parents=True, exist_ok=True)
        generated = [args.output_csv, args.output_json, args.output_md]
        copies = []
        for path in generated:
            target = args.catalogue_dir / path.name
            shutil.copy2(path, target)
            copies.append({"source": str(path), "catalogue_copy": str(target)})
        summary["catalogue_copies"] = copies
        args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


def main() -> None:
    args = parse_args()
    rows, summary = build_rows(args)
    write_outputs(rows, summary, args)


if __name__ == "__main__":
    main()
