#!/usr/bin/env python3
"""Build the final-objective include/exclude decision register."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


EXTERNAL_STREAM_ROWS = {
    "P09_ert_gate": {
        "stream": "ERT resistivity",
        "decision_item": "ERT transform/support and uncertainty",
        "blocker_ids": ["ert_transform_support", "ert_uncertainty"],
        "current_use": "diagnostic_only",
        "include_effect": (
            "If the transform/support mask and covariance model are accepted, ERT can move "
            "from provisional log-resistivity diagnostic evidence into a weighted final "
            "stream or accepted scenario screen."
        ),
        "exclude_effect": (
            "If excluded, keep ERT as diagnostic field-consistency evidence only and state "
            "that the final objective is not selected by the dense ERT VTK series."
        ),
        "report_requirement": (
            "State whether the final permeability field includes ERT, keeps it diagnostic, "
            "or excludes it; keep the provisional-transform caveat unless the provider closes it."
        ),
    },
    "P10_taupe_gate": {
        "stream": "Taupe/TDR",
        "decision_item": "Taupe/TDR unit calibration and uncertainty",
        "blocker_ids": ["taupe_unit_calibration"],
        "current_use": "diagnostic_only",
        "include_effect": (
            "If units/calibration and uncertainty are accepted, Taupe can become a grouped "
            "trend residual over mapped A3/A4 EDZ bands or an explicitly calibrated absolute "
            "water-content residual."
        ),
        "exclude_effect": (
            "If excluded, keep Taupe as mapped trend-diagnostic evidence and do not let A3/A4 "
            "or A7/A8 select the final field."
        ),
        "report_requirement": (
            "State whether Taupe workbook values are final water-content evidence, trend-only "
            "evidence, or excluded from the final likelihood."
        ),
    },
    "P11_rh_gate": {
        "stream": "RH/suction",
        "decision_item": "RH active boundary-curve provenance and uncertainty",
        "blocker_ids": ["rh_active_curve_provenance"],
        "current_use": "boundary_audit_only",
        "include_effect": (
            "If provenance, constants, time axis, sensor screening, and uncertainty are accepted, "
            "RH can drive accepted boundary-forcing scenarios or a later retention/boundary release."
        ),
        "exclude_effect": (
            "If excluded from the final objective, keep RH as boundary-provenance evidence and "
            "do not replace or fit the active open-niche pressure curve from local workbook curves."
        ),
        "report_requirement": (
            "State whether RH is a final boundary condition source, a scenario-only forcing, "
            "or a provenance audit with no residual weight."
        ),
    },
    "P12_other_hm_gate": {
        "stream": "Other HM monitoring",
        "decision_item": "Other-HM numeric exports, metadata, and uncertainty",
        "blocker_ids": ["hm_numeric_exports", "hm_uncertainty"],
        "current_use": "not_ready_for_hard_residual",
        "include_effect": (
            "If numeric exports and uncertainty metadata arrive, selected extensometer, "
            "mini-piezometer, crackmeter, laser, levelling, or Geoscope rows can become "
            "mechanical/hydraulic validation or residual streams."
        ),
        "exclude_effect": (
            "If excluded, keep the report, slides, Tecplot layout, and levelling snippets as "
            "qualitative validation context only."
        ),
        "report_requirement": (
            "State that other-HM streams are not final likelihood terms unless hard-residual-ready "
            "time series, support definitions, and weights are accepted."
        ),
    },
    "P13_perm_endpoint_gate": {
        "stream": "Historical permeability pulse tests",
        "decision_item": "Historical permeability endpoint geometry/provenance",
        "blocker_ids": ["perm_endpoint_geometry"],
        "current_use": "partial_active_support",
        "include_effect": (
            "If endpoint traces/geometries are accepted, the blocked historical BCD-A24/25/26/27 "
            "and BFM-D19 rows can be projected to OGS support cells or interval traces."
        ),
        "exclude_effect": (
            "If excluded, the final permeability objective stays limited to currently projected "
            "active pulse-test rows and the historical rows remain visible but inactive."
        ),
        "report_requirement": (
            "State whether historical endpoint-missing rows enter the final fit, remain inactive, "
            "or are superseded by the current active support definition."
        ),
    },
    "P14_cte_confirmation": {
        "stream": "Frozen OGS model provenance",
        "decision_item": "Suspicious CTE value confirmation",
        "blocker_ids": ["cte_value_confirmation"],
        "current_use": "frozen_uninterpreted_caveat",
        "include_effect": (
            "If confirmed, record whether CTE=1254.74 is intended, inactive, copied heat capacity, "
            "or another convention; keep the exchanged model frozen unless a separate approved "
            "model-version decision is made."
        ),
        "exclude_effect": (
            "If scoped out, state that the final permeability fit does not interpret or calibrate "
            "thermal expansivity and that CTE remains a frozen-source caveat."
        ),
        "report_requirement": (
            "State the CTE response or the explicit scope-out decision before making broad "
            "thermo-mechanical interpretation claims."
        ),
    },
}

INTERNAL_ROWS = {
    "P08_nmr_residual_policy": {
        "stream": "NMR water content",
        "decision_item": "Final NMR residual policy",
        "decision_ids": ["nmr_bound_water", "nmr_default_promotion"],
        "current_use": "active_raw_absolute_theta_with_provisional_trend_scenario",
        "include_effect": (
            "The final objective must choose raw absolute theta with caveats, within-label "
            "trend/anomaly residuals, a label-bias/free-water correction, or another recorded "
            "NMR policy before promotion."
        ),
        "exclude_effect": (
            "If NMR is excluded from final field selection, the report must say the active "
            "raw-NMR incumbent is no longer an all-measurement field and must rerun selection "
            "without NMR."
        ),
        "report_requirement": (
            "State the final NMR free-water/bound-water policy and the exact residual form "
            "used for final selection."
        ),
    },
}

SCENARIO_ROWS = {
    "P15_conditional_field_stability": {
        "stream": "Final objective scenario set",
        "decision_item": "Accepted scenario set and winner stability",
        "current_use": "unstable_scenario_winners",
        "include_effect": (
            "After every stream decision is recorded, rerun the conditional scenarios. The final "
            "objective can promote a field only if the accepted scenario has a documented winner "
            "or the selected scenario is explicitly chosen."
        ),
        "exclude_effect": (
            "If a stream is excluded, remove it from the accepted final scenario rather than "
            "leaving it as an unresolved blocker."
        ),
        "report_requirement": (
            "Report the accepted scenario set and explain why the selected field is stable or "
            "why a single scenario was chosen."
        ),
    },
    "P16_final_field_decision": {
        "stream": "Final field approval",
        "decision_item": "Promote or keep active-only field label",
        "current_use": "active_objective_incumbent_only",
        "include_effect": (
            "Promote only after previous gate decisions are pass, closed, or explicitly waived "
            "and the field-selection audit changes to final promotion."
        ),
        "exclude_effect": (
            "Keep the packaged field labelled as the active direct-permeability/raw-NMR incumbent, "
            "not a final all-measurement inversion result."
        ),
        "report_requirement": (
            "The final report must not call the current field final unless the promotion checklist "
            "and current-field selection audit both record final promotion."
        ),
    },
}

COMMON_EXTERNAL_CHOICES = [
    "wait_for_provider_response_then_include_if_acceptance_passes",
    "keep_diagnostic_or_boundary_only_and_exclude_from_final_objective",
    "accept_current_provisional_evidence_as_final_with_explicit_waiver_not_recommended",
    "reopen_request_or_collect_more_evidence",
]

NMR_CHOICES = [
    "retain_raw_absolute_theta_default_with_caveats",
    "promote_within_label_trend_anomaly_default",
    "use_label_bias_or_free_water_correction_policy",
    "exclude_nmr_from_final_selection_and_rerun_without_nmr",
]

SCENARIO_CHOICES = [
    "rerun_after_recorded_gate_decisions_and_promote_only_if_stable",
    "select_one_explicit_final_scenario_and_document_exclusions",
    "keep_current_field_active_only_until_scenario_instability_is_resolved",
]

FINAL_CHOICES = [
    "promote_to_final_all_measurement_field_after_all_criteria_close",
    "keep_active_objective_incumbent_label",
]

REFRESH_AFTER_PROVIDER = (
    "python inversion_workflow/scripts/build_external_gate_response_intake.py; "
    "python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; "
    "python inversion_workflow/scripts/build_external_blocker_dashboard.py; "
    "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
    "python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; "
    "python inversion_workflow/scripts/build_current_field_selection_audit.py; "
    "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
    "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
    "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
    "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
    "python inversion_workflow/scripts/build_objective_readiness_audit.py"
)

REFRESH_AFTER_POLICY = (
    "python inversion_workflow/scripts/build_internal_gate_decision_register.py; "
    "python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; "
    "python inversion_workflow/scripts/build_current_field_selection_audit.py; "
    "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
    "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
    "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
    "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
    "python inversion_workflow/scripts/build_objective_readiness_audit.py"
)

REFRESH_AFTER_SCENARIO = (
    "python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; "
    "python inversion_workflow/scripts/build_conditional_field_candidate_package.py; "
    "python inversion_workflow/scripts/build_conditional_field_difference_audit.py; "
    "python inversion_workflow/scripts/build_current_field_selection_audit.py; "
    "python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; "
    "python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; "
    "python inversion_workflow/scripts/build_final_objective_decision_register.py; "
    "python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; "
    "python inversion_workflow/scripts/build_objective_readiness_audit.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive register copies.",
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


def join_values(values: list[Any], separator: str = "; ") -> str:
    clean: list[str] = []
    for value in values:
        if pd.isna(value):
            continue
        text = str(value)
        if text and text not in {"nan", "None"} and text not in clean:
            clean.append(text)
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


def rows_for_ids(frame: pd.DataFrame, ids: list[str], column: str = "request_id") -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return pd.DataFrame()
    return frame[frame[column].astype(str).isin(ids)].copy()


def external_decision_status(related: pd.DataFrame) -> str:
    if related.empty:
        return "missing_blocker_rows"
    if "blocker_status" in related.columns and related["blocker_status"].astype(str).str.contains("blocked").any():
        return "pending_user_send_and_provider_response_or_explicit_exclusion"
    if "response_status" in related.columns and (related["response_status"] == "accepted").any():
        return "provider_response_recorded_review_acceptance"
    return "review_required"


def build_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    checklist = read_csv(Path("inversion_workflow/final_inversion_promotion_checklist.csv"))
    checklist_summary = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    closeout = read_csv(Path("inversion_workflow/final_inversion_closeout_playbook.csv"))
    blockers = read_csv(Path("inversion_workflow/external_blocker_dashboard.csv"))
    internal = read_csv(Path("inversion_workflow/internal_gate_decision_register.csv"))
    scenarios = read_json(Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"))
    current_selection = read_json(Path("inversion_workflow/current_field_selection_audit_summary.json"))
    gmail_packet = read_json(Path("inversion_workflow/gmail_draft_send_review_packet_summary.json"))
    support_conflict = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    lower_bound = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    policy_acceptance = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    next_gate = read_json(Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"))
    permeability_policy_evidence = format_permeability_policy_evidence(
        support_conflict, lower_bound, policy_acceptance, next_gate
    )

    open_criteria = checklist_summary.get("open_criterion_ids", [])
    rows: list[dict[str, Any]] = []

    for criterion_id in open_criteria:
        criterion_rows = rows_for_ids(checklist, [criterion_id], "criterion_id")
        criterion = (
            str(criterion_rows.iloc[0].get("criterion", ""))
            if not criterion_rows.empty
            else ""
        )
        criterion_status = (
            str(criterion_rows.iloc[0].get("status", "missing"))
            if not criterion_rows.empty
            else "missing"
        )
        closeout_rows = rows_for_ids(closeout, [criterion_id], "criterion_id")
        closeout_type = (
            str(closeout_rows.iloc[0].get("closeout_type", ""))
            if not closeout_rows.empty
            else ""
        )

        if criterion_id in EXTERNAL_STREAM_ROWS:
            spec = EXTERNAL_STREAM_ROWS[criterion_id]
            related = rows_for_ids(blockers, spec["blocker_ids"])
            status = external_decision_status(related)
            choices = COMMON_EXTERNAL_CHOICES
            related_ids = spec["blocker_ids"]
            draft_ids = join_values(related.get("gmail_draft_id", pd.Series(dtype=str)).drop_duplicates().tolist())
            response_locations = join_values(
                related.get("response_notes_md", pd.Series(dtype=str)).tolist()
                + related.get("intake_dir", pd.Series(dtype=str)).tolist()
            )
            acceptance = join_values(related.get("acceptance_test", pd.Series(dtype=str)).tolist())
            current_evidence = join_values(related.get("current_blocker_or_caveat", pd.Series(dtype=str)).tolist())
            refresh = REFRESH_AFTER_PROVIDER
            default_decision = (
                "do_not_include_in_final_objective_until_provider_response_or_explicit_exclusion_is_recorded"
            )
            decision_owner = "user_and_modelling_team"
            if criterion_id == "P13_perm_endpoint_gate":
                acceptance = join_values([acceptance, permeability_policy_evidence])
                response_locations = join_values(
                    [
                        response_locations,
                        "inversion_workflow/permeability_support_conflict_spatial_audit.md",
                        "inversion_workflow/permeability_support_lower_bound_audit.md",
                        "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md",
                        "inversion_workflow/permeability_next_field_fit_gate.md",
                    ]
                )
                current_evidence = join_values([current_evidence, permeability_policy_evidence])
        elif criterion_id in INTERNAL_ROWS:
            spec = INTERNAL_ROWS[criterion_id]
            related = rows_for_ids(internal, spec["decision_ids"])
            status = "pending_modelling_team_final_policy"
            choices = NMR_CHOICES
            related_ids = spec["decision_ids"]
            draft_ids = ""
            response_locations = join_values(related.get("source_artifacts", pd.Series(dtype=str)).tolist())
            acceptance = (
                "Internal register must record the final NMR default policy, and conditional "
                "scenario/current-field audits must be regenerated under that policy."
            )
            current_evidence = join_values(related.get("key_evidence", pd.Series(dtype=str)).tolist())
            refresh = REFRESH_AFTER_POLICY
            default_decision = "current_report_state_keeps_raw_absolute_nmr_default_and_trend_anomaly_scenario_only"
            decision_owner = "modelling_team"
        elif criterion_id in SCENARIO_ROWS:
            spec = SCENARIO_ROWS[criterion_id]
            related_ids = []
            draft_ids = ""
            response_locations = (
                "inversion_workflow/conditional_field_selection_scenarios.md; "
                "inversion_workflow/current_field_selection_audit.md"
            )
            acceptance = (
                "Final scenario decision and field-selection audit are regenerated after all "
                "include/exclude choices are recorded."
            )
            if criterion_id == "P15_conditional_field_stability":
                status = "pending_after_stream_include_exclude_decisions"
                choices = SCENARIO_CHOICES
                current_evidence = (
                    f"scenarios={scenarios.get('scenario_count')}; unique winners="
                    f"{scenarios.get('unique_winner_count')}; current-field wins="
                    f"{scenarios.get('current_field_winning_scenario_count')}; final decision="
                    f"{scenarios.get('final_decision')}; {permeability_policy_evidence}"
                )
                default_decision = "do_not_promote_while_scenario_winners_are_unstable"
            else:
                status = "not_ready_for_final_approval"
                choices = FINAL_CHOICES
                current_evidence = (
                    f"active decision={current_selection.get('active_objective_decision')}; "
                    f"final decision={current_selection.get('final_all_measurement_decision')}; "
                    f"status counts={current_selection.get('status_counts')}; {permeability_policy_evidence}"
                )
                default_decision = "keep_current_field_as_active_objective_incumbent_only"
            acceptance = join_values([acceptance, permeability_policy_evidence])
            response_locations = join_values(
                [
                    response_locations,
                    "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md",
                    "inversion_workflow/permeability_next_field_fit_gate.md",
                ]
            )
            refresh = REFRESH_AFTER_SCENARIO
            decision_owner = "modelling_team"
        else:
            spec = {
                "stream": "unclassified",
                "decision_item": criterion_id,
                "current_use": "unclassified",
                "include_effect": "Add a stream-specific include path.",
                "exclude_effect": "Add a stream-specific exclude path.",
                "report_requirement": "Add report wording requirement.",
            }
            related_ids = []
            draft_ids = ""
            response_locations = ""
            acceptance = str(criterion_rows.iloc[0].get("required_for_promotion", "")) if not criterion_rows.empty else ""
            current_evidence = str(criterion_rows.iloc[0].get("evidence", "")) if not criterion_rows.empty else ""
            status = "unclassified"
            choices = ["classify_decision_row"]
            refresh = REFRESH_AFTER_SCENARIO
            default_decision = "unclassified"
            decision_owner = "modelling_team"

        rows.append(
            {
                "criterion_id": criterion_id,
                "criterion_status": criterion_status,
                "criterion": criterion,
                "stream": spec["stream"],
                "decision_item": spec["decision_item"],
                "closeout_type": closeout_type,
                "decision_status": status,
                "default_current_decision": default_decision,
                "decision_owner": decision_owner,
                "related_blocker_or_decision_ids": join_values(related_ids, ","),
                "gmail_draft_ids": draft_ids,
                "current_allowed_use": spec["current_use"],
                "decision_choices": join_values(choices),
                "include_path_consequence": spec["include_effect"],
                "exclude_path_consequence": spec["exclude_effect"],
                "acceptance_evidence": acceptance,
                "response_or_decision_locations": response_locations,
                "refresh_after_decision": refresh,
                "report_wording_requirement": spec["report_requirement"],
                "current_evidence": current_evidence,
            }
        )

    frame = pd.DataFrame(rows)
    external_count = int(frame["criterion_id"].isin(EXTERNAL_STREAM_ROWS).sum()) if not frame.empty else 0
    internal_count = int(frame["criterion_id"].isin(INTERNAL_ROWS).sum()) if not frame.empty else 0
    scenario_count = int(frame["criterion_id"].isin(SCENARIO_ROWS).sum()) if not frame.empty else 0
    pending_count = int(frame["decision_status"].astype(str).str.startswith(("pending", "not_ready")).sum()) if not frame.empty else 0
    explicit_exclusion_possible_count = int(
        frame["decision_choices"].astype(str).str.contains("exclude").sum()
    ) if not frame.empty else 0
    summary = {
        "status": "final_objective_decision_register_generated",
        "promotion_decision": checklist_summary.get("promotion_decision"),
        "decision_count": int(frame.shape[0]),
        "external_stream_decision_count": external_count,
        "internal_policy_decision_count": internal_count,
        "scenario_or_final_decision_count": scenario_count,
        "pending_or_not_ready_decision_count": pending_count,
        "explicit_exclusion_possible_count": explicit_exclusion_possible_count,
        "open_criterion_ids": frame["criterion_id"].tolist() if not frame.empty else [],
        "decision_status_counts": frame["decision_status"].value_counts().sort_index().to_dict()
        if not frame.empty
        else {},
        "gmail_draft_ids": sorted(
            {
                draft_id
                for value in frame.get("gmail_draft_ids", pd.Series(dtype=str)).dropna().tolist()
                for draft_id in str(value).split("; ")
                if draft_id
            }
        ),
        "gmail_packet_status": gmail_packet.get("status"),
        "gmail_packet_unsent_draft_count": gmail_packet.get("unsent_draft_count"),
        "current_field_final_decision": current_selection.get("final_all_measurement_decision"),
        "conditional_unique_winner_count": scenarios.get("unique_winner_count"),
        "conditional_scenario_count": scenarios.get("scenario_count"),
        "permeability_support_conflict_spatial_audit_status": support_conflict.get("status"),
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
        "next_action": (
            "For each row, either close the evidence gate and include the stream, record a "
            "diagnostic-only/exclusion decision, or leave final promotion blocked."
        ),
        "source_artifacts": [
            "inversion_workflow/final_inversion_promotion_checklist.csv",
            "inversion_workflow/final_inversion_closeout_playbook.csv",
            "inversion_workflow/external_blocker_dashboard.csv",
            "inversion_workflow/internal_gate_decision_register.csv",
            "inversion_workflow/conditional_field_selection_scenarios_summary.json",
            "inversion_workflow/current_field_selection_audit_summary.json",
            "inversion_workflow/gmail_draft_send_review_packet_summary.json",
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
        "# Final Objective Decision Register",
        "",
        "This register is the explicit include/exclude layer for final field promotion.",
        "It does not send email, close provider gates, or modify the frozen OGS model.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Promotion decision: `{summary.get('promotion_decision')}`",
        f"- Decisions: {summary['decision_count']}",
        f"- External stream decisions: {summary['external_stream_decision_count']}",
        f"- Internal policy decisions: {summary['internal_policy_decision_count']}",
        f"- Scenario/final decisions: {summary['scenario_or_final_decision_count']}",
        f"- Pending or not-ready decisions: {summary['pending_or_not_ready_decision_count']}",
        f"- Gmail packet status: `{summary.get('gmail_packet_status')}`",
        f"- Unsent Gmail drafts: {summary.get('gmail_packet_unsent_draft_count')}",
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
        "## Decision Rows",
        "",
        "| Criterion | Stream | Decision status | Current use | Default decision | Choices |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['decision_item']} | {row['stream']} | "
            f"`{row['decision_status']}` | `{row['current_allowed_use']}` | "
            f"`{row['default_current_decision']}` | {row['decision_choices']} |"
        )

    lines.extend(["", "## Consequences", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['criterion_id']}` {row['decision_item']}",
                "",
                f"- Current evidence: {row['current_evidence']}",
                f"- Include path: {row['include_path_consequence']}",
                f"- Exclude/diagnostic path: {row['exclude_path_consequence']}",
                f"- Acceptance evidence: {row['acceptance_evidence']}",
                f"- Decision locations: {row['response_or_decision_locations']}",
                f"- Report wording requirement: {row['report_wording_requirement']}",
                f"- Refresh after decision: `{row['refresh_after_decision']}`",
                "",
            ]
        )

    lines.extend(["## Interpretation", ""])
    lines.extend(
        [
            "- The current active field remains inspectable, but the register keeps it from being promoted by implication.",
            "- Final promotion requires a recorded include, diagnostic-only, exclusion, or waiver decision for every open row.",
            "- If a stream is excluded, that exclusion must be explicit in the report and the scenario/current-field audits must be rerun.",
            "- If a stream is included, the relevant acceptance evidence and weighting/support policy must be recorded first.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
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
    frame, summary = build_rows()
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
