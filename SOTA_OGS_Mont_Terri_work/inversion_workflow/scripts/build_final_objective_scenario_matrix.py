#!/usr/bin/env python3
"""Map final-objective include/exclude choices to scenario consequences."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCENARIO_OPTIONS = [
    {
        "option_id": "F01_current_raw_nmr_exclude_gated_streams",
        "scenario_id": "S01_current_active_raw_nmr",
        "title": "Current raw-NMR active objective, all gated streams excluded or diagnostic-only",
        "classification": "eligible_only_after_explicit_exclusions",
        "required_decisions": (
            "retain raw absolute NMR default with caveats; keep ERT diagnostic-only; keep Taupe "
            "diagnostic-only; keep RH boundary-audit-only; exclude other-HM hard residuals; "
            "exclude endpoint-missing historical permeability rows or accept current support; "
            "scope out CTE from field selection"
        ),
        "blocked_by": "all explicit exclusions/diagnostic-only decisions are still pending",
        "promotion_consequence": (
            "The current packaged field can only become final under this narrow objective if the "
            "report explicitly says the final field does not include ERT, Taupe/TDR, RH, other-HM, "
            "or endpoint-missing historical rows."
        ),
    },
    {
        "option_id": "F02_promoted_nmr_trend_only",
        "scenario_id": "S02_promoted_nmr_trend_anomaly",
        "title": "Promote NMR trend/anomaly, exclude external diagnostics from final objective",
        "classification": "requires_internal_policy_change",
        "required_decisions": (
            "promote within-label NMR trend/anomaly as final NMR residual; keep ERT/Taupe/RH/"
            "other-HM diagnostic-only or excluded; exclude endpoint-missing historical permeability rows"
        ),
        "blocked_by": "NMR default-promotion decision is still pending",
        "promotion_consequence": (
            "The current raw-NMR field would not be the selected field; the promoted-NMR winner "
            "would need a field package and current-field selection refresh."
        ),
    },
    {
        "option_id": "F03_raw_nmr_plus_ert",
        "scenario_id": "S03_active_plus_ert_screen",
        "title": "Raw-NMR active objective plus accepted ERT screen",
        "classification": "requires_external_ert_gate",
        "required_decisions": (
            "accept ERT transform/support and uncertainty; retain raw NMR default; keep Taupe/RH/"
            "other-HM diagnostic-only or excluded; decide endpoint-missing historical rows"
        ),
        "blocked_by": "ERT transform/support and uncertainty gates are unanswered",
        "promotion_consequence": (
            "The current field is close but not the scenario winner; the ERT-screen winner would "
            "need to be treated as the candidate selected by this objective."
        ),
    },
    {
        "option_id": "F04_raw_nmr_plus_taupe",
        "scenario_id": "S04_active_plus_taupe_screen",
        "title": "Raw-NMR active objective plus accepted Taupe/TDR screen",
        "classification": "requires_external_taupe_gate",
        "required_decisions": (
            "accept Taupe/TDR unit calibration and uncertainty; retain raw NMR default; keep ERT/RH/"
            "other-HM diagnostic-only or excluded; decide endpoint-missing historical rows"
        ),
        "blocked_by": "Taupe/TDR unit/calibration gate is unanswered",
        "promotion_consequence": (
            "The current field is not selected; the Taupe-screen winner is a broader smooth-family "
            "field and would need field packaging before any promotion."
        ),
    },
    {
        "option_id": "F05_raw_nmr_plus_ert_taupe",
        "scenario_id": "S05_active_plus_ert_taupe_screen",
        "title": "Raw-NMR active objective plus accepted ERT and Taupe/TDR screens",
        "classification": "requires_external_ert_and_taupe_gates",
        "required_decisions": (
            "accept ERT transform/support/uncertainty; accept Taupe/TDR calibration/uncertainty; "
            "retain raw NMR default; keep RH/other-HM diagnostic-only or excluded; decide endpoint rows"
        ),
        "blocked_by": "ERT and Taupe/TDR external gates are unanswered",
        "promotion_consequence": (
            "The current field is not selected; the production-round winner would need a field "
            "package and promotion audit under the accepted ERT/Taupe objective."
        ),
    },
    {
        "option_id": "F06_promoted_nmr_plus_ert_taupe",
        "scenario_id": "S06_active_plus_promoted_nmr_ert_taupe",
        "title": "Promoted NMR trend/anomaly plus accepted ERT and Taupe/TDR",
        "classification": "requires_internal_and_external_gate_closure",
        "required_decisions": (
            "promote NMR trend/anomaly; accept ERT and Taupe/TDR gates; keep RH/other-HM "
            "diagnostic-only or excluded; decide endpoint-missing historical rows"
        ),
        "blocked_by": "NMR policy, ERT, and Taupe/TDR gates are open",
        "promotion_consequence": (
            "The current field is not selected; this is the closest currently scored all-numeric "
            "scenario but still excludes RH, other-HM, and endpoint-missing historical rows."
        ),
    },
    {
        "option_id": "F07_rank_consensus_diagnostic_selection",
        "scenario_id": "S08_rank_consensus_all_streams",
        "title": "Explicit diagnostic rank-consensus selection",
        "classification": "not_a_likelihood_without_explicit_waiver",
        "required_decisions": (
            "record a modelling-team waiver that diagnostic ranks, not a likelihood, are the final "
            "selection rule; keep all gated streams labelled diagnostic-only"
        ),
        "blocked_by": "no waiver has been recorded; diagnostics are not accepted hard residuals",
        "promotion_consequence": (
            "The current field is not the rank-consensus winner. This option should remain a "
            "screening aid unless the report explicitly chooses a diagnostic-consensus final rule."
        ),
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-csv",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios.csv"),
    )
    parser.add_argument(
        "--scenario-summary",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"),
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--decision-register-summary",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register_summary.json"),
    )
    parser.add_argument(
        "--current-selection-summary",
        type=Path,
        default=Path("inversion_workflow/current_field_selection_audit_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_scenario_matrix.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_objective_scenario_matrix_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_objective_scenario_matrix.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive matrix copies.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def format_top_conflict_cell(top: dict[str, Any]) -> str:
    if not top:
        return "top conflict cell not recorded"
    return (
        f"top conflict cell={top.get('primary_cell_id')} "
        f"({top.get('segments')} {top.get('depth_min_m')}-{top.get('depth_max_m')} m, "
        f"observed range={top.get('observed_log10_range')})"
    )


def format_permeability_policy_evidence(
    support_conflict: dict[str, Any],
    lower_bound: dict[str, Any],
    policy_acceptance: dict[str, Any],
    next_gate: dict[str, Any],
) -> str:
    return (
        f"support-conflict active/repeated/range>=2 cells="
        f"{support_conflict.get('active_support_cell_count')}/"
        f"{support_conflict.get('repeated_support_cell_count')}/"
        f"{support_conflict.get('support_cells_observed_range_ge_2_log10')}; "
        f"{format_top_conflict_cell(support_conflict.get('top_conflict_cell', {}))}; "
        f"same-support lower-bound gap={lower_bound.get('same_support_reducible_objective_gap')}; "
        f"current at lower bound={lower_bound.get('current_at_single_support_lower_bound')}; "
        f"policy approvals={policy_acceptance.get('primary_policy_approval_rows_recorded')}/"
        f"{policy_acceptance.get('primary_policy_approval_rows_required')}; "
        f"policy ready={policy_acceptance.get('ready_to_apply_policy')}; "
        f"same-support batch executable="
        f"{next_gate.get('executable_same_support_active_objective_batch_now')}; "
        f"next recommendation={next_gate.get('overall_recommendation')}"
    )


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


def direct_only_row(scorecard: pd.DataFrame, current_run_id: str) -> dict[str, Any]:
    frame = scorecard.copy()
    frame["direct_permeability_objective"] = pd.to_numeric(
        frame["direct_permeability_objective"], errors="coerce"
    )
    frame["direct_only_rank"] = frame["direct_permeability_objective"].rank(method="min")
    ranked = frame.sort_values(["direct_permeability_objective", "active_objective_rank", "run_id"])
    winner = ranked.iloc[0].to_dict()
    current = frame.loc[frame["run_id"] == current_run_id].iloc[0].to_dict()
    min_direct = float(ranked["direct_permeability_objective"].iloc[0])
    tie_count = int(np.isclose(frame["direct_permeability_objective"], min_direct, rtol=0, atol=1e-12).sum())
    return {
        "option_id": "F08_exclude_nmr_direct_permeability_only",
        "scenario_id": "direct_permeability_only_not_in_conditional_scenarios",
        "title": "Exclude NMR and select by direct permeability only",
        "classification": "requires_new_selection_policy_or_tie_break",
        "required_decisions": (
            "explicitly exclude NMR from final field selection; decide tie-breaking across direct-only "
            "best fields; keep ERT/Taupe/RH/other-HM diagnostic-only or excluded"
        ),
        "blocked_by": "no final NMR-exclusion scenario or direct-only tie-break policy is recorded",
        "winner_run_id": winner["run_id"],
        "winner_score": winner["direct_permeability_objective"],
        "current_is_winner": bool(np.isclose(current["direct_permeability_objective"], min_direct, rtol=0, atol=1e-12)),
        "current_rank": current["direct_only_rank"],
        "current_score": current["direct_permeability_objective"],
        "score_delta_current_minus_winner": current["direct_permeability_objective"] - winner["direct_permeability_objective"],
        "best_tie_count": tie_count,
        "promotion_consequence": (
            "Direct-only selection is not stable without a tie-break: multiple fields share the "
            "same direct objective at numerical precision, including the current field."
        ),
    }


def future_unscored_row() -> dict[str, Any]:
    return {
        "option_id": "F09_wait_for_rh_other_hm_endpoint_expansion",
        "scenario_id": "not_currently_scored",
        "title": "Wait for RH, other-HM, or endpoint-missing historical permeability expansion",
        "classification": "requires_new_data_and_new_scenario_build",
        "required_decisions": (
            "obtain RH provenance/uncertainty if it should become accepted forcing; obtain other-HM "
            "numeric exports/metadata if they should become residuals; obtain endpoint geometry if "
            "historical permeability rows should enter the final fit"
        ),
        "blocked_by": "external provider responses/files are missing",
        "winner_run_id": "",
        "winner_score": "",
        "current_is_winner": False,
        "current_rank": "",
        "current_score": "",
        "score_delta_current_minus_winner": "",
        "best_tie_count": "",
        "promotion_consequence": (
            "No final winner can be selected for this option from the current scenario audit; the "
            "observation tables and scenario audit must be rebuilt after new evidence is filed."
        ),
    }


def build_matrix(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    scenarios = pd.read_csv(args.scenario_csv)
    scorecard = pd.read_csv(args.scorecard)
    scenario_summary = read_json(args.scenario_summary)
    decision_summary = read_json(args.decision_register_summary)
    current_selection = read_json(args.current_selection_summary)
    support_conflict = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    lower_bound = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    policy_acceptance = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    next_gate = read_json(Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"))
    permeability_policy_evidence = format_permeability_policy_evidence(
        support_conflict, lower_bound, policy_acceptance, next_gate
    )
    current_run_id = scenario_summary.get("current_run_id", "")

    scenario_lookup = {row["scenario_id"]: row for row in scenarios.to_dict(orient="records")}
    rows: list[dict[str, Any]] = []
    for option in SCENARIO_OPTIONS:
        source = scenario_lookup.get(option["scenario_id"], {})
        rows.append(
            {
                **option,
                "winner_run_id": source.get("winner_run_id", ""),
                "winner_score": source.get("winner_score", ""),
                "current_is_winner": bool(source.get("current_is_winner", False)),
                "current_rank": source.get("current_scenario_rank", ""),
                "current_score": source.get("current_score", ""),
                "score_delta_current_minus_winner": source.get("score_delta_current_minus_winner", ""),
                "best_tie_count": "",
                "direct_permeability_support_policy_evidence": permeability_policy_evidence,
            }
        )
    direct_row = direct_only_row(scorecard, str(current_run_id))
    direct_row["direct_permeability_support_policy_evidence"] = permeability_policy_evidence
    rows.append(direct_row)
    future_row = future_unscored_row()
    future_row["direct_permeability_support_policy_evidence"] = permeability_policy_evidence
    rows.append(future_row)

    frame = pd.DataFrame(rows)
    current_winner_count = int(frame["current_is_winner"].astype(bool).sum())
    unscored_count = int((frame["scenario_id"] == "not_currently_scored").sum())
    not_final_likelihood_count = int(
        frame["classification"].isin(
            [
                "not_a_likelihood_without_explicit_waiver",
                "requires_new_selection_policy_or_tie_break",
                "requires_new_data_and_new_scenario_build",
            ]
        ).sum()
    )
    unique_winners = sorted({str(value) for value in frame["winner_run_id"].tolist() if str(value)})
    summary = {
        "status": "final_objective_scenario_matrix_generated",
        "option_count": int(frame.shape[0]),
        "current_run_id": current_run_id,
        "current_field_winning_option_count": current_winner_count,
        "unique_winner_count": len(unique_winners),
        "unique_winners": unique_winners,
        "unscored_future_option_count": unscored_count,
        "not_final_likelihood_or_needs_new_policy_count": not_final_likelihood_count,
        "conditional_scenario_count": scenario_summary.get("scenario_count"),
        "conditional_unique_winner_count": scenario_summary.get("unique_winner_count"),
        "final_objective_decision_register_pending_count": decision_summary.get(
            "pending_or_not_ready_decision_count"
        ),
        "current_field_final_decision": current_selection.get("final_all_measurement_decision"),
        "permeability_support_conflict_spatial_active_support_cell_count": support_conflict.get(
            "active_support_cell_count"
        ),
        "permeability_support_conflict_spatial_repeated_support_cell_count": support_conflict.get(
            "repeated_support_cell_count"
        ),
        "permeability_support_conflict_spatial_range_ge_2_log10_cell_count": support_conflict.get(
            "support_cells_observed_range_ge_2_log10"
        ),
        "permeability_likelihood_policy_primary_approvals_recorded": policy_acceptance.get(
            "primary_policy_approval_rows_recorded"
        ),
        "permeability_likelihood_policy_primary_approvals_required": policy_acceptance.get(
            "primary_policy_approval_rows_required"
        ),
        "permeability_likelihood_policy_ready_to_apply": policy_acceptance.get("ready_to_apply_policy"),
        "permeability_next_field_fit_gate_same_support_batch_executable_now": next_gate.get(
            "executable_same_support_active_objective_batch_now"
        ),
        "interpretation": [
            "The current field wins only the current raw-NMR option and ties the direct-only option.",
            "Every option that includes promoted NMR, ERT, or Taupe selects a different field.",
            "RH, other-HM, and endpoint-missing historical permeability cannot select a field yet because their required evidence is not in the scored scenario set.",
            "The direct-permeability support/likelihood policy is not approved, and the same-support active-objective batch gate remains closed.",
        ],
        "source_artifacts": [
            str(args.scenario_csv),
            str(args.scenario_summary),
            str(args.scorecard),
            str(args.decision_register_summary),
            str(args.current_selection_summary),
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
            "inversion_workflow/permeability_support_lower_bound_audit_summary.json",
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json",
            "inversion_workflow/permeability_next_field_fit_gate_summary.json",
        ],
    }
    return frame, json_ready(summary)


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Final Objective Scenario Matrix",
        "",
        "This matrix maps explicit final-objective include/exclude choices to the",
        "currently scored scenario consequences. It is not a promotion decision and it",
        "does not change the frozen OGS model.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Options: {summary['option_count']}",
        f"- Current field winning options: {summary['current_field_winning_option_count']}",
        f"- Unique winners: {summary['unique_winner_count']}",
        f"- Unscored future options: {summary['unscored_future_option_count']}",
        f"- Current field final decision: `{summary.get('current_field_final_decision')}`",
        (
            "- Direct-permeability active/repeated/range>=2 support cells: "
            f"{summary.get('permeability_support_conflict_spatial_active_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_repeated_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_range_ge_2_log10_cell_count')}"
        ),
        (
            "- Direct-permeability policy approvals: "
            f"{summary.get('permeability_likelihood_policy_primary_approvals_recorded')}/"
            f"{summary.get('permeability_likelihood_policy_primary_approvals_required')}; "
            f"ready=`{summary.get('permeability_likelihood_policy_ready_to_apply')}`"
        ),
        (
            "- Same-support active-objective batch executable: "
            f"`{summary.get('permeability_next_field_fit_gate_same_support_batch_executable_now')}`"
        ),
        "",
        "## Options",
        "",
        "| Option | Classification | Winner | Current rank | Current wins? | Blocked by |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['option_id']}` {row['title']} | `{row['classification']}` | "
            f"`{row['winner_run_id']}` | {row['current_rank']} | {row['current_is_winner']} | "
            f"{row['blocked_by']} |"
        )
    lines.extend(["", "## Decision Consequences", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['option_id']}` {row['title']}",
                "",
                f"- Required decisions: {row['required_decisions']}",
                f"- Scenario source: `{row['scenario_id']}`",
                f"- Winner: `{row['winner_run_id']}`",
                f"- Current score/rank: `{row['current_score']}` / `{row['current_rank']}`",
                f"- Score delta current minus winner: `{row['score_delta_current_minus_winner']}`",
                f"- Best-tie count: `{row['best_tie_count']}`",
                (
                    "- Direct-permeability support/likelihood evidence: "
                    f"{row['direct_permeability_support_policy_evidence']}"
                ),
                f"- Promotion consequence: {row['promotion_consequence']}",
                "",
            ]
        )
    lines.extend(["## Interpretation", ""])
    for item in summary["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source Artifacts", ""])
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    generated = [args.output_csv, args.output_json, args.output_md]
    if args.catalogue_dir:
        args.catalogue_dir.mkdir(parents=True, exist_ok=True)
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
    frame, summary = build_matrix(args)
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
