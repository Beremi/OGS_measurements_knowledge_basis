#!/usr/bin/env python3
"""Build an actionable playbook for closing final inversion promotion gates."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


CRITERION_BLOCKERS = {
    "P09_ert_gate": ["ert_transform_support", "ert_uncertainty"],
    "P10_taupe_gate": ["taupe_unit_calibration"],
    "P11_rh_gate": ["rh_active_curve_provenance"],
    "P12_other_hm_gate": ["hm_numeric_exports", "hm_uncertainty"],
    "P13_perm_endpoint_gate": ["perm_endpoint_geometry"],
    "P14_cte_confirmation": ["cte_value_confirmation"],
}

INTERNAL_DECISION_ROWS = {
    "P08_nmr_residual_policy": ["nmr_bound_water", "nmr_default_promotion"],
}

REFRESH_COMMANDS = {
    "provider_response": (
        "File response notes/files in the listed intake directory, then run: "
        "python inversion_workflow/scripts/build_external_gate_response_intake.py; "
        "python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; "
        "python inversion_workflow/scripts/build_external_blocker_dashboard.py; "
        "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
        "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
        "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
        "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
        "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
        "python inversion_workflow/scripts/build_objective_readiness_audit.py"
    ),
    "internal_policy": (
        "Record/edit the modelling decision, then rerun the affected NMR/objective scripts, "
        "followed by: python inversion_workflow/scripts/build_internal_gate_decision_register.py; "
        "python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; "
        "python inversion_workflow/scripts/build_current_field_selection_audit.py; "
        "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
        "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
        "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
        "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
        "python inversion_workflow/scripts/build_objective_readiness_audit.py"
    ),
    "scenario_refresh": (
        "After gates/policies are closed or explicitly excluded, run: "
        "python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; "
        "python inversion_workflow/scripts/build_conditional_field_candidate_package.py; "
        "python inversion_workflow/scripts/build_conditional_field_difference_audit.py; "
        "python inversion_workflow/scripts/build_current_field_selection_audit.py; "
        "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
        "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
        "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
        "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
        "python inversion_workflow/scripts/build_objective_readiness_audit.py"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_inversion_closeout_playbook.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_inversion_closeout_playbook_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_inversion_closeout_playbook.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive playbook copies.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def join_nonempty(values: list[Any], separator: str = "; ") -> str:
    clean = [str(value) for value in values if pd.notna(value) and str(value) not in {"", "nan", "None"}]
    return separator.join(clean)


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
        f"support-conflict audit={support_conflict.get('status')}; "
        f"active/repeated/range>=2 support cells="
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


def rows_for_blockers(blockers: pd.DataFrame, blocker_ids: list[str]) -> pd.DataFrame:
    if blockers.empty or "request_id" not in blockers.columns:
        return pd.DataFrame()
    return blockers[blockers["request_id"].isin(blocker_ids)].copy()


def rows_for_internal(internal: pd.DataFrame, request_ids: list[str]) -> pd.DataFrame:
    if internal.empty or "request_id" not in internal.columns:
        return pd.DataFrame()
    return internal[internal["request_id"].isin(request_ids)].copy()


def build_playbook_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    checklist = read_csv(Path("inversion_workflow/final_inversion_promotion_checklist.csv"))
    checklist_summary = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    blockers = read_csv(Path("inversion_workflow/external_blocker_dashboard.csv"))
    internal = read_csv(Path("inversion_workflow/internal_gate_decision_register.csv"))
    scenarios = read_json(Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"))
    current_selection = read_json(Path("inversion_workflow/current_field_selection_audit_summary.json"))
    support_conflict = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    lower_bound = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    policy_acceptance = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    next_gate = read_json(Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"))
    permeability_policy_evidence = format_permeability_policy_evidence(
        support_conflict, lower_bound, policy_acceptance, next_gate
    )

    open_ids = checklist_summary.get("open_criterion_ids", [])
    checklist = checklist[checklist["criterion_id"].isin(open_ids)].copy()
    rows: list[dict[str, Any]] = []

    for item in checklist.to_dict(orient="records"):
        criterion_id = str(item["criterion_id"])
        if criterion_id in CRITERION_BLOCKERS:
            related_blocker_ids = CRITERION_BLOCKERS[criterion_id]
            related = rows_for_blockers(blockers, related_blocker_ids)
            action_owner = "user_send_then_provider_response"
            primary_action = (
                "Review/send the existing Gmail draft(s), then file the provider response "
                "and any new files in the listed intake location."
            )
            fallback_decision = (
                "If this stream is deliberately excluded from the final objective, record that "
                "exclusion in the report/checklist before promoting a field."
            )
            acceptance = join_nonempty(related.get("acceptance_test", pd.Series(dtype=str)).tolist())
            response_locations = join_nonempty(
                related.get("response_notes_md", pd.Series(dtype=str)).tolist()
                + related.get("intake_dir", pd.Series(dtype=str)).tolist()
            )
            draft_ids = join_nonempty(related.get("gmail_draft_id", pd.Series(dtype=str)).drop_duplicates().tolist())
            suggested_to = join_nonempty(related.get("suggested_to", pd.Series(dtype=str)).drop_duplicates().tolist())
            suggested_cc = join_nonempty(related.get("suggested_cc", pd.Series(dtype=str)).drop_duplicates().tolist())
            current_evidence = join_nonempty(related.get("current_blocker_or_caveat", pd.Series(dtype=str)).tolist())
            refresh = REFRESH_COMMANDS["provider_response"]
            if criterion_id == "P13_perm_endpoint_gate":
                primary_action = (
                    "Review/send the existing permeability endpoint-geometry draft, then file the "
                    "provider response and any new traces/geometries. If no historical endpoint "
                    "geometry will be used, record that the final direct-permeability support is "
                    "limited to the current projected rows and separately decide the "
                    "support/likelihood policy."
                )
                fallback_decision = (
                    "Explicitly keep endpoint-missing historical rows inactive, and do not reopen "
                    "same-support OGS batches unless a support mapping or likelihood policy is approved."
                )
                acceptance = join_nonempty([acceptance, permeability_policy_evidence])
                response_locations = join_nonempty(
                    [
                        response_locations,
                        "inversion_workflow/permeability_support_conflict_spatial_audit.md",
                        "inversion_workflow/permeability_support_lower_bound_audit.md",
                        "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md",
                        "inversion_workflow/permeability_next_field_fit_gate.md",
                    ]
                )
                current_evidence = join_nonempty([current_evidence, permeability_policy_evidence])
        elif criterion_id in INTERNAL_DECISION_ROWS:
            related_internal_ids = INTERNAL_DECISION_ROWS[criterion_id]
            related = rows_for_internal(internal, related_internal_ids)
            action_owner = "modelling_team_policy_decision"
            primary_action = (
                "Choose and record the final NMR residual policy before final field promotion."
            )
            fallback_decision = (
                "Keep raw NMR as the active objective and explicitly exclude promoted NMR "
                "trend/anomaly from final selection, or promote trend/anomaly and rerank field selection."
            )
            acceptance = (
                "The NMR default-promotion row no longer blocks final promotion, and the "
                "conditional scenario audit is regenerated under the accepted NMR policy."
            )
            response_locations = join_nonempty(related.get("source_artifacts", pd.Series(dtype=str)).tolist())
            draft_ids = ""
            suggested_to = "internal modelling team"
            suggested_cc = ""
            current_evidence = join_nonempty(related.get("key_evidence", pd.Series(dtype=str)).tolist())
            refresh = REFRESH_COMMANDS["internal_policy"]
        elif criterion_id == "P15_conditional_field_stability":
            action_owner = "modelling_team_after_gate_resolution"
            primary_action = (
                "Regenerate conditional scenarios after external/internal gates are closed, "
                "accepted, or explicitly excluded from the final objective."
            )
            fallback_decision = (
                "Select a single final-objective scenario explicitly; do not promote a field "
                "from an unstable scenario set by implication."
            )
            acceptance = (
                "The final accepted objective has a stable winner, or the selected scenario "
                "and excluded streams are documented as an explicit modelling decision."
            )
            response_locations = "inversion_workflow/conditional_field_selection_scenarios.md"
            draft_ids = ""
            suggested_to = "internal modelling team"
            suggested_cc = ""
            current_evidence = (
                f"scenarios={scenarios.get('scenario_count')}; unique winners="
                f"{scenarios.get('unique_winner_count')}; current-field wins="
                f"{scenarios.get('current_field_winning_scenario_count')}; final decision="
                f"{scenarios.get('final_decision')}; {permeability_policy_evidence}"
            )
            acceptance = join_nonempty([acceptance, permeability_policy_evidence])
            refresh = REFRESH_COMMANDS["scenario_refresh"]
        elif criterion_id == "P16_final_field_decision":
            action_owner = "modelling_team_final_approval"
            primary_action = (
                "Approve a final all-measurement field only after the preceding open criteria "
                "are closed or explicitly waived, and after the direct-permeability support/"
                "likelihood policy has either been accepted or deliberately kept as the "
                "current rowwise Gaussian active-only default."
            )
            fallback_decision = "Keep the current field labelled as an active-objective incumbent only."
            acceptance = (
                "current_field_selection_audit records promote_to_final_all_measurement_field "
                "and final_inversion_promotion_checklist records promote_to_final_all_measurement_field."
            )
            acceptance = join_nonempty([acceptance, permeability_policy_evidence])
            response_locations = (
                "inversion_workflow/current_field_selection_audit.md; "
                "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; "
                "inversion_workflow/permeability_next_field_fit_gate.md"
            )
            draft_ids = ""
            suggested_to = "internal modelling team"
            suggested_cc = ""
            current_evidence = (
                f"current final decision={current_selection.get('final_all_measurement_decision')}; "
                f"status counts={current_selection.get('status_counts')}; {permeability_policy_evidence}"
            )
            refresh = REFRESH_COMMANDS["scenario_refresh"]
        else:
            action_owner = "unclassified"
            primary_action = "Review this criterion and add a specific close-out row."
            fallback_decision = ""
            acceptance = str(item.get("required_for_promotion", ""))
            response_locations = str(item.get("source_artifacts", ""))
            draft_ids = ""
            suggested_to = ""
            suggested_cc = ""
            current_evidence = str(item.get("evidence", ""))
            refresh = REFRESH_COMMANDS["scenario_refresh"]

        rows.append(
            {
                "criterion_id": criterion_id,
                "criterion_status": item.get("status"),
                "criterion": item.get("criterion"),
                "closeout_type": action_owner,
                "related_blocker_or_decision_ids": join_nonempty(
                    CRITERION_BLOCKERS.get(criterion_id, INTERNAL_DECISION_ROWS.get(criterion_id, [])),
                    ",",
                ),
                "gmail_draft_ids": draft_ids,
                "suggested_to": suggested_to,
                "suggested_cc": suggested_cc,
                "primary_action": primary_action,
                "explicit_exclusion_or_fallback": fallback_decision,
                "acceptance_evidence": acceptance,
                "response_or_decision_locations": response_locations,
                "refresh_commands": refresh,
                "current_evidence": current_evidence,
            }
        )

    frame = pd.DataFrame(rows)
    summary = {
        "status": "final_inversion_closeout_playbook_generated",
        "promotion_decision": checklist_summary.get("promotion_decision"),
        "open_criterion_count": int(frame.shape[0]),
        "external_closeout_count": int((frame["closeout_type"] == "user_send_then_provider_response").sum()),
        "internal_policy_closeout_count": int((frame["closeout_type"] == "modelling_team_policy_decision").sum()),
        "scenario_or_final_decision_count": int(
            frame["closeout_type"].isin(
                ["modelling_team_after_gate_resolution", "modelling_team_final_approval"]
            ).sum()
        ),
        "open_criterion_ids": frame["criterion_id"].tolist(),
        "gmail_draft_ids": sorted(
            {
                draft_id
                for value in frame["gmail_draft_ids"].dropna().tolist()
                for draft_id in str(value).split("; ")
                if draft_id
            }
        ),
        "next_actions": [
            "Review/send the six existing Gmail drafts or record an explicit decision to exclude the associated gated streams from the final objective.",
            "Record the NMR residual default-promotion decision before using NMR trend/anomaly as final objective evidence.",
            "Resolve the direct-permeability support/likelihood policy before reopening same-support OGS batches or treating the active field as final.",
            "After responses or exclusions are recorded, rerun the stream gates, conditional scenarios, current-field selection audit, final-promotion checklist, final objective decision register, and objective-readiness audit.",
            "Use the final objective scenario matrix to choose one explicit final-objective option, or to document why the current field remains active-only.",
        ],
        "source_artifacts": [
            "inversion_workflow/final_inversion_promotion_checklist.csv",
            "inversion_workflow/external_blocker_dashboard.csv",
            "inversion_workflow/internal_gate_decision_register.csv",
            "inversion_workflow/conditional_field_selection_scenarios_summary.json",
            "inversion_workflow/current_field_selection_audit_summary.json",
            "inversion_workflow/final_objective_scenario_matrix_summary.json",
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
            "inversion_workflow/permeability_support_lower_bound_audit_summary.json",
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json",
            "inversion_workflow/permeability_next_field_fit_gate_summary.json",
        ],
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Final Inversion Close-Out Playbook",
        "",
        "This playbook expands the open final-promotion criteria into concrete next",
        "actions. It does not send email and it does not waive any measurement gate.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Promotion decision: `{summary['promotion_decision']}`",
        f"- Open criteria: {summary['open_criterion_count']}",
        f"- External send/response actions: {summary['external_closeout_count']}",
        f"- Internal policy actions: {summary['internal_policy_closeout_count']}",
        f"- Scenario/final decision actions: {summary['scenario_or_final_decision_count']}",
        "",
        "## Open Criteria",
        "",
        "| Criterion | Type | Related ids | Drafts | Action | Acceptance evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['criterion']} | `{row['closeout_type']}` | "
            f"{row['related_blocker_or_decision_ids']} | {row['gmail_draft_ids']} | "
            f"{row['primary_action']} | {row['acceptance_evidence']} |"
        )
    lines.extend(["", "## Refresh Commands", ""])
    for key, command in REFRESH_COMMANDS.items():
        lines.append(f"- `{key}`: {command}")
    lines.extend(["", "## Current Evidence", ""])
    for row in frame.to_dict(orient="records"):
        if row["current_evidence"]:
            lines.append(f"- `{row['criterion_id']}`: {row['current_evidence']}")
    lines.extend(["", "## Next Actions", ""])
    for action in summary["next_actions"]:
        lines.append(f"- {action}")
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
    frame, summary = build_playbook_rows()
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
