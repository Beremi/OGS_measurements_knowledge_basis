#!/usr/bin/env python3
"""Build a draft no-new-evidence closeout package for final-objective decisions."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


DRAFT_ROW_SPEC: dict[str, dict[str, Any]] = {
    "P08_nmr_residual_policy": {
        "draft_closeout_choice": "retain_raw_absolute_theta_default_with_caveats",
        "accepted_no_new_evidence_use": "current-report active objective and narrow F01 scenario only",
        "approval_required_from": "modelling_team",
        "acceptance_text": (
            "Retain raw absolute NMR water-content residuals for the current no-new-evidence "
            "objective, with explicit bound-water/mobile-water caveats. Do not promote the "
            "within-label trend/anomaly policy, label-bias correction, or free-water correction "
            "as final unless a separate NMR policy decision is recorded."
        ),
        "decision_register_action": (
            "Record a modelling-team policy row that accepts raw absolute theta with caveats "
            "for the no-new-evidence closeout scenario only."
        ),
        "interpretation_after_acceptance": (
            "The active objective can remain raw-NMR based for the narrow no-new-evidence "
            "scenario, but the report must say that the mobile/free-water interpretation is "
            "caveated and that the trend/anomaly result is provisional evidence."
        ),
        "scenario_option_effect": "supports F01 only after explicit acceptance",
    },
    "P09_ert_gate": {
        "draft_closeout_choice": "keep_diagnostic_only_exclude_from_final_likelihood",
        "accepted_no_new_evidence_use": "diagnostic field-consistency evidence only",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Keep ERT as diagnostic log-resistivity field-consistency evidence and exclude it "
            "from final likelihood weights because the ERT-to-OGS transform/support and "
            "uncertainty/correlation model are not confirmed."
        ),
        "decision_register_action": (
            "Record ERT as diagnostic-only/excluded from final likelihood for the "
            "no-new-evidence closeout scenario."
        ),
        "interpretation_after_acceptance": (
            "The final selected field is not selected by dense ERT VTK residuals, and ERT "
            "diagnostic plots/ranks cannot be described as accepted likelihood terms."
        ),
        "scenario_option_effect": "excludes F03, F05, and F06 unless provider evidence later arrives",
    },
    "P10_taupe_gate": {
        "draft_closeout_choice": "keep_trend_diagnostic_exclude_absolute_values",
        "accepted_no_new_evidence_use": "mapped trend diagnostic evidence only",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Keep Taupe/TDR as mapped baseline-normalized trend diagnostic evidence and exclude "
            "absolute Taupe values from final water-content likelihood terms because units, "
            "calibration, and uncertainty are not confirmed."
        ),
        "decision_register_action": (
            "Record Taupe/TDR as diagnostic-only/excluded from final likelihood for the "
            "no-new-evidence closeout scenario."
        ),
        "interpretation_after_acceptance": (
            "Taupe/TDR cannot select the final field as an absolute saturation or water-content "
            "target; A3/A4 and A7/A8 remain diagnostic comparisons."
        ),
        "scenario_option_effect": "excludes F04, F05, and F06 unless provider evidence later arrives",
    },
    "P11_rh_gate": {
        "draft_closeout_choice": "keep_boundary_audit_only_no_residual_or_curve_replacement",
        "accepted_no_new_evidence_use": "boundary provenance and scenario-audit evidence only",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Keep RH/suction as boundary-provenance and scenario-audit evidence only. Do not "
            "replace, fit, or weight the active pressure curve from local RH workbooks because "
            "the active-curve provenance, constants, time axis, sensor screening, extension "
            "policy, and uncertainty are not confirmed."
        ),
        "decision_register_action": (
            "Record RH/suction as boundary-audit-only and excluded from final residual weights "
            "for the no-new-evidence closeout scenario."
        ),
        "interpretation_after_acceptance": (
            "The active pressure curve stays frozen; RH-derived candidate curves can document "
            "boundary uncertainty but cannot redefine the forward problem."
        ),
        "scenario_option_effect": "keeps F09 unscored until provider evidence later arrives",
    },
    "P12_other_hm_gate": {
        "draft_closeout_choice": "qualitative_context_only_no_hard_residual",
        "accepted_no_new_evidence_use": "qualitative validation and geometry/layout support only",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Keep other HM monitoring as qualitative or geometric context only and exclude it "
            "from final hard residuals because local files do not contain hard-residual-ready "
            "numeric exports, support definitions, metadata, and uncertainties."
        ),
        "decision_register_action": (
            "Record other-HM monitoring as qualitative-only/excluded from final likelihood for "
            "the no-new-evidence closeout scenario."
        ),
        "interpretation_after_acceptance": (
            "Geoscope, laser, levelling, extensometer, mini-piezometer, and crackmeter evidence "
            "can orient the report but cannot carry mechanical or hydraulic likelihood weights."
        ),
        "scenario_option_effect": "keeps F09 unscored until numeric exports later arrive",
    },
    "P13_perm_endpoint_gate": {
        "draft_closeout_choice": "use_current_supported_rows_keep_endpoint_missing_historical_rows_inactive",
        "accepted_no_new_evidence_use": "currently projected active pulse-test rows only",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Use only currently projected active permeability pulse-test rows and keep "
            "endpoint-missing historical BCD-A24/25/26/27 and BFM-D19 rows visible but inactive "
            "because labelled endpoint geometry or an approved digitized trace is not available."
        ),
        "decision_register_action": (
            "Record endpoint-missing historical permeability rows as inactive/excluded from "
            "the no-new-evidence final residual set."
        ),
        "interpretation_after_acceptance": (
            "The direct permeability objective remains limited to rows with accepted projection "
            "support; historical scalar values without interval geometry are not projected."
        ),
        "scenario_option_effect": "supports F01/F08 current-support interpretations only",
    },
    "P14_cte_confirmation": {
        "draft_closeout_choice": "scope_out_cte_from_permeability_objective_keep_frozen_caveat",
        "accepted_no_new_evidence_use": "frozen-source caveat outside permeability objective",
        "approval_required_from": "user_and_modelling_team",
        "acceptance_text": (
            "Scope the suspicious CTE value out of the permeability-field objective and keep "
            "it as an uninterpreted frozen-source caveat. Do not correct, calibrate, or make "
            "thermo-mechanical interpretation claims that depend on CTE=1254.74 without a "
            "provider response."
        ),
        "decision_register_action": (
            "Record CTE as scoped out of final permeability selection for the no-new-evidence "
            "closeout scenario."
        ),
        "interpretation_after_acceptance": (
            "The exchanged OGS model remains frozen; the field fit does not interpret thermal "
            "expansivity and does not create a corrected model version."
        ),
        "scenario_option_effect": "keeps CTE outside all current field-selection options",
    },
    "P15_conditional_field_stability": {
        "draft_closeout_choice": "select_F01_only_if_prior_draft_rows_are_approved_and_audits_rerun",
        "accepted_no_new_evidence_use": "narrow current raw-NMR scenario with gated streams excluded",
        "approval_required_from": "modelling_team",
        "acceptance_text": (
            "If all preceding no-new-evidence draft rows are approved, select "
            "F01_current_raw_nmr_exclude_gated_streams as the only accepted no-new-evidence "
            "final-objective scenario. This is a narrow objective, not an all-measurement "
            "likelihood, and must be regenerated through the scenario and current-field audits."
        ),
        "decision_register_action": (
            "Record F01 as the explicit no-new-evidence scenario only after the individual "
            "stream exclusions/policies are recorded."
        ),
        "interpretation_after_acceptance": (
            "The current field can only be discussed under the narrow raw-NMR/direct-permeability "
            "objective with excluded gated streams; other scenario winners remain diagnostic."
        ),
        "scenario_option_effect": "selects F01 only after prior approvals and regeneration",
    },
    "P16_final_field_decision": {
        "draft_closeout_choice": "keep_active_incumbent_label_until_post_acceptance_audits",
        "accepted_no_new_evidence_use": "active-objective incumbent unless a later approval promotes F01",
        "approval_required_from": "modelling_team_final_approval",
        "acceptance_text": (
            "This draft does not promote the current field. Keep the packaged field labelled "
            "as the active direct-permeability/raw-NMR incumbent until the no-new-evidence "
            "decisions are recorded, the scenario/current-field/promotion audits are rerun, "
            "and a separate final approval is recorded."
        ),
        "decision_register_action": (
            "Keep the final-field decision as not promoted in this draft; promote only through "
            "a later regenerated audit and approval record."
        ),
        "interpretation_after_acceptance": (
            "The report remains protected against overclaiming; any later final label must be "
            "restricted to the accepted no-new-evidence scenario and not called an "
            "all-measurement inversion."
        ),
        "scenario_option_effect": "does not promote the field by itself",
    },
}

SINGLE_BLOCK_ACCEPTANCE_TEXT = (
    "For the no-new-evidence closeout, we retain raw absolute NMR water-content "
    "residuals with bound-water/mobile-water caveats; keep ERT and Taupe/TDR as "
    "diagnostic-only evidence; keep RH/suction as boundary-audit-only evidence; keep "
    "other HM monitoring as qualitative/geometric context only; keep endpoint-missing "
    "historical permeability rows inactive; scope the suspicious CTE value out of "
    "permeability-field interpretation; and use F01_current_raw_nmr_exclude_gated_streams "
    "only as the narrow accepted scenario after the individual decisions are recorded "
    "and the scenario/current-field/promotion audits are regenerated. This decision "
    "does not include those gated streams in the likelihood, does not assert a final "
    "all-measurement inversion, and does not promote the current field without a "
    "separate post-regeneration approval."
)

REFRESH_AFTER_ACCEPTANCE = (
    "python inversion_workflow/scripts/build_internal_gate_decision_register.py; "
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
    "python inversion_workflow/scripts/build_final_objective_include_exclude_recommendations.py; "
    "python inversion_workflow/scripts/build_final_objective_no_new_evidence_closeout_draft.py; "
    "python inversion_workflow/scripts/build_objective_readiness_audit.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recommendations",
        type=Path,
        default=Path("inversion_workflow/final_objective_include_exclude_recommendations.csv"),
    )
    parser.add_argument(
        "--decision-register",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.csv"),
    )
    parser.add_argument(
        "--scenario-matrix",
        type=Path,
        default=Path("inversion_workflow/final_objective_scenario_matrix.csv"),
    )
    parser.add_argument(
        "--promotion-summary",
        type=Path,
        default=Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"),
    )
    parser.add_argument(
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_field_selection_audit_summary.json"),
    )
    parser.add_argument(
        "--external-blocker-summary",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard_summary.json"),
    )
    parser.add_argument(
        "--gmail-review-summary",
        type=Path,
        default=Path("inversion_workflow/gmail_draft_send_review_packet_summary.json"),
    )
    parser.add_argument(
        "--permeability-support-conflict-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"),
    )
    parser.add_argument(
        "--permeability-policy-acceptance-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json"),
    )
    parser.add_argument(
        "--permeability-next-field-gate-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def clean(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def join_unique(values: list[Any], separator: str = "; ") -> str:
    out: list[str] = []
    for value in values:
        text = clean(value)
        if text and text not in out:
            out.append(text)
    return separator.join(out)


def join_unique_segments(values: list[Any]) -> str:
    segments: list[str] = []
    for value in values:
        text = clean(value)
        if not text:
            continue
        for segment in text.split("; "):
            clean_segment = segment.strip()
            if clean_segment and clean_segment not in segments:
                segments.append(clean_segment)
    return "; ".join(segments)


def rows_for_id(frame: pd.DataFrame, criterion_id: str) -> list[dict[str, Any]]:
    if frame.empty or "criterion_id" not in frame.columns:
        return []
    return frame[frame["criterion_id"].astype(str) == criterion_id].to_dict(orient="records")


def first_row(frame: pd.DataFrame, column: str, value: str) -> dict[str, Any]:
    if frame.empty or column not in frame.columns:
        return {}
    match = frame[frame[column].astype(str) == value]
    return match.iloc[0].to_dict() if not match.empty else {}


def format_top_conflict_cell(top: dict[str, Any]) -> str:
    if not top:
        return ""
    return (
        f"top conflict cell={top.get('primary_cell_id')} "
        f"({top.get('segments')} at {top.get('depth_min_m')}-{top.get('depth_max_m')} m, "
        f"observed log10 range={top.get('observed_log10_range')}, "
        f"max |residual|={top.get('max_abs_residual')})"
    )


def format_permeability_support_evidence(
    support_conflict: dict[str, Any],
    policy_acceptance: dict[str, Any],
    next_field_gate: dict[str, Any],
) -> str:
    if not support_conflict and not policy_acceptance and not next_field_gate:
        return ""
    top = support_conflict.get("top_conflict_cell", {}) if support_conflict else {}
    parts = [
        f"support-conflict spatial audit={support_conflict.get('status')}",
        (
            "active/repeated/range>=2 support cells="
            f"{support_conflict.get('active_support_cell_count')}/"
            f"{support_conflict.get('repeated_support_cell_count')}/"
            f"{support_conflict.get('support_cells_observed_range_ge_2_log10')}"
        ),
        f"configured-scalar conflict cells={support_conflict.get('configured_scalar_range_conflict_cell_count')}",
        format_top_conflict_cell(top),
        (
            "permeability likelihood policy approvals="
            f"{policy_acceptance.get('primary_policy_approval_rows_recorded')}/"
            f"{policy_acceptance.get('primary_policy_approval_rows_required')}"
        ),
        f"permeability likelihood policy ready={policy_acceptance.get('ready_to_apply_policy')}",
        f"same-support active-objective batch executable now={next_field_gate.get('executable_same_support_active_objective_batch_now')}",
        f"next field-fit recommendation={next_field_gate.get('overall_recommendation')}",
    ]
    return join_unique_segments(parts)


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    recommendations = read_csv(args.recommendations)
    decision_register = read_csv(args.decision_register)
    scenario_matrix = read_csv(args.scenario_matrix)
    promotion_summary = read_json(args.promotion_summary)
    current_field_summary = read_json(args.current_field_summary)
    external_blocker_summary = read_json(args.external_blocker_summary)
    gmail_review_summary = read_json(args.gmail_review_summary)
    permeability_support_conflict_summary = read_json(args.permeability_support_conflict_summary)
    permeability_policy_acceptance_summary = read_json(args.permeability_policy_acceptance_summary)
    permeability_next_field_gate_summary = read_json(args.permeability_next_field_gate_summary)
    permeability_support_evidence = format_permeability_support_evidence(
        permeability_support_conflict_summary,
        permeability_policy_acceptance_summary,
        permeability_next_field_gate_summary,
    )

    f01 = first_row(scenario_matrix, "option_id", "F01_current_raw_nmr_exclude_gated_streams")
    rows: list[dict[str, Any]] = []
    for criterion_id, spec in DRAFT_ROW_SPEC.items():
        rec = rows_for_id(recommendations, criterion_id)
        reg = rows_for_id(decision_register, criterion_id)
        rec_row = rec[0] if rec else {}
        reg_row = reg[0] if reg else {}
        recommended_wording = clean(rec_row.get("explicit_report_wording_if_no_new_evidence"))
        exact_report_wording = recommended_wording or spec["acceptance_text"]
        current_evidence = join_unique_segments(
            [reg_row.get("current_evidence"), rec_row.get("current_evidence")]
        )
        source_locations = join_unique_segments(
            [
                reg_row.get("response_or_decision_locations"),
                rec_row.get("response_or_decision_locations"),
            ]
        )
        if criterion_id in {
            "P13_perm_endpoint_gate",
            "P15_conditional_field_stability",
            "P16_final_field_decision",
        }:
            if "support-conflict" not in current_evidence:
                current_evidence = join_unique_segments([current_evidence, permeability_support_evidence])
            source_locations = join_unique_segments(
                [
                    source_locations,
                    "inversion_workflow/permeability_support_conflict_spatial_audit.md",
                    "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md",
                    "inversion_workflow/permeability_next_field_fit_gate.md",
                ]
            )

        rows.append(
            {
                "criterion_id": criterion_id,
                "stream": clean(reg_row.get("stream")) or clean(rec_row.get("stream")),
                "decision_item": clean(reg_row.get("decision_item")) or clean(rec_row.get("decision_item")),
                "existing_decision_status": clean(reg_row.get("decision_status")) or clean(rec_row.get("decision_status")),
                "draft_acceptance_status": "draft_requires_user_or_modelling_team_approval_not_recorded",
                "draft_closeout_choice": spec["draft_closeout_choice"],
                "accepted_no_new_evidence_use": spec["accepted_no_new_evidence_use"],
                "approval_required_from": spec["approval_required_from"],
                "exact_decision_record_text": spec["acceptance_text"],
                "decision_register_action": spec["decision_register_action"],
                "exact_report_wording": exact_report_wording,
                "interpretation_after_acceptance": spec["interpretation_after_acceptance"],
                "scenario_option_effect": spec["scenario_option_effect"],
                "current_evidence": current_evidence,
                "source_locations": source_locations,
                "refresh_after_acceptance": REFRESH_AFTER_ACCEPTANCE,
            }
        )

    frame = pd.DataFrame(rows)
    external_rows = [
        "P09_ert_gate",
        "P10_taupe_gate",
        "P11_rh_gate",
        "P12_other_hm_gate",
        "P13_perm_endpoint_gate",
        "P14_cte_confirmation",
    ]
    summary: dict[str, Any] = {
        "status": "final_objective_no_new_evidence_closeout_draft_generated",
        "draft_decision_count": int(frame.shape[0]),
        "external_or_provenance_draft_count": int(frame["criterion_id"].isin(external_rows).sum()),
        "internal_policy_draft_count": int(frame["criterion_id"].eq("P08_nmr_residual_policy").sum()),
        "scenario_or_final_draft_count": int(
            frame["criterion_id"].isin(["P15_conditional_field_stability", "P16_final_field_decision"]).sum()
        ),
        "draft_acceptance_status_counts": frame["draft_acceptance_status"].value_counts().sort_index().to_dict(),
        "requires_user_or_modelling_team_approval": True,
        "records_actual_decisions": False,
        "sends_or_modifies_email": False,
        "promotes_current_field": False,
        "final_promotion_unblocked_by_this_draft": False,
        "would_select_scenario_if_all_rows_approved_and_audits_rerun": f01.get(
            "option_id", "F01_current_raw_nmr_exclude_gated_streams"
        ),
        "would_select_winner_if_all_rows_approved_and_audits_rerun": f01.get("winner_run_id"),
        "current_field_is_winner_in_draft_scenario": bool(f01.get("current_is_winner", False)),
        "promotion_decision_before_draft": promotion_summary.get("promotion_decision"),
        "current_field_final_decision_before_draft": current_field_summary.get("final_all_measurement_decision"),
        "external_blocker_count": external_blocker_summary.get("blocker_count"),
        "open_blocker_count": external_blocker_summary.get("open_blocker_count"),
        "missing_response_blocker_count": external_blocker_summary.get("missing_response_blocker_count"),
        "unsent_blocker_count": external_blocker_summary.get("unsent_blocker_count"),
        "open_blocker_ids": external_blocker_summary.get("open_blocker_ids", []),
        "gmail_draft_count": gmail_review_summary.get("draft_count"),
        "gmail_unsent_draft_count": gmail_review_summary.get("unsent_draft_count"),
        "gmail_draft_ids": gmail_review_summary.get("draft_ids", []),
        "permeability_support_conflict_spatial_audit_status": permeability_support_conflict_summary.get("status"),
        "permeability_support_conflict_spatial_active_support_cell_count": (
            permeability_support_conflict_summary.get("active_support_cell_count")
        ),
        "permeability_support_conflict_spatial_repeated_support_cell_count": (
            permeability_support_conflict_summary.get("repeated_support_cell_count")
        ),
        "permeability_support_conflict_spatial_range_ge_2_log10_cell_count": (
            permeability_support_conflict_summary.get("support_cells_observed_range_ge_2_log10")
        ),
        "permeability_support_conflict_spatial_configured_scalar_conflict_cell_count": (
            permeability_support_conflict_summary.get("configured_scalar_range_conflict_cell_count")
        ),
        "permeability_support_conflict_spatial_top_conflict_cell": (
            permeability_support_conflict_summary.get("top_conflict_cell", {})
        ),
        "permeability_likelihood_policy_primary_approvals_recorded": (
            permeability_policy_acceptance_summary.get("primary_policy_approval_rows_recorded")
        ),
        "permeability_likelihood_policy_primary_approvals_required": (
            permeability_policy_acceptance_summary.get("primary_policy_approval_rows_required")
        ),
        "permeability_likelihood_policy_ready_to_apply": (
            permeability_policy_acceptance_summary.get("ready_to_apply_policy")
        ),
        "permeability_next_field_fit_gate_same_support_batch_executable_now": (
            permeability_next_field_gate_summary.get("executable_same_support_active_objective_batch_now")
        ),
        "permeability_next_field_fit_gate_recommendation": (
            permeability_next_field_gate_summary.get("overall_recommendation")
        ),
        "single_block_acceptance_text": SINGLE_BLOCK_ACCEPTANCE_TEXT,
        "refresh_after_acceptance": REFRESH_AFTER_ACCEPTANCE,
        "next_action": (
            "Review this draft with the modelling team. If accepted, record the decisions "
            "in the decision layer, then rerun the listed audits. If not accepted, send/file "
            "provider responses before including the gated streams."
        ),
        "source_artifacts": [
            "inversion_workflow/final_objective_include_exclude_recommendations.csv",
            "inversion_workflow/final_objective_decision_register.csv",
            "inversion_workflow/final_objective_scenario_matrix.csv",
            "inversion_workflow/final_inversion_promotion_checklist_summary.json",
            "inversion_workflow/current_field_selection_audit_summary.json",
            "inversion_workflow/external_blocker_dashboard_summary.json",
            "inversion_workflow/gmail_draft_send_review_packet_summary.json",
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
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
        "# Final Objective No-New-Evidence Closeout Draft",
        "",
        "This generated packet turns the existing no-new-evidence recommendations into",
        "exact decision text that can be reviewed by the user and modelling team.",
        "It is deliberately a draft: it does not record acceptance, close provider gates,",
        "send email, change the frozen OGS model, or promote a permeability field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Draft decision rows: {summary['draft_decision_count']}",
        f"- External/provenance rows: {summary['external_or_provenance_draft_count']}",
        f"- Internal policy rows: {summary['internal_policy_draft_count']}",
        f"- Scenario/final rows: {summary['scenario_or_final_draft_count']}",
        f"- Approval required: `{summary['requires_user_or_modelling_team_approval']}`",
        f"- Actual decisions recorded: `{summary['records_actual_decisions']}`",
        f"- Sends or modifies email: `{summary['sends_or_modifies_email']}`",
        f"- Promotes current field: `{summary['promotes_current_field']}`",
        f"- Final promotion unblocked by this draft: `{summary['final_promotion_unblocked_by_this_draft']}`",
        f"- Would select scenario if every row is approved and audits are rerun: `{summary['would_select_scenario_if_all_rows_approved_and_audits_rerun']}`",
        f"- Winner in that draft scenario: `{summary['would_select_winner_if_all_rows_approved_and_audits_rerun']}`",
        f"- Current field is draft-scenario winner: `{summary['current_field_is_winner_in_draft_scenario']}`",
        f"- Open blockers before draft: {summary.get('open_blocker_count')}/{summary.get('external_blocker_count')}",
        f"- Missing-response blockers before draft: {summary.get('missing_response_blocker_count')}",
        f"- Unsent Gmail drafts before draft: {summary.get('gmail_unsent_draft_count')}",
        f"- Direct-permeability support-conflict audit: `{summary.get('permeability_support_conflict_spatial_audit_status')}`",
        (
            "- Direct-permeability active/repeated/range>=2 support cells: "
            f"{summary.get('permeability_support_conflict_spatial_active_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_repeated_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_range_ge_2_log10_cell_count')}"
        ),
        (
            "- Direct-permeability policy approvals before draft: "
            f"{summary.get('permeability_likelihood_policy_primary_approvals_recorded')}/"
            f"{summary.get('permeability_likelihood_policy_primary_approvals_required')}; "
            f"ready=`{summary.get('permeability_likelihood_policy_ready_to_apply')}`"
        ),
        (
            "- Same-support active-objective batch executable before draft: "
            f"`{summary.get('permeability_next_field_fit_gate_same_support_batch_executable_now')}`"
        ),
        "",
        "## What This Draft Does Not Do",
        "",
        "- It does not close ERT, Taupe/TDR, RH, other-HM, endpoint-geometry, or CTE provider gates.",
        "- It does not include any gated stream as a final hard likelihood term.",
        "- It does not approve a direct-permeability likelihood/support policy or reopen same-support OGS spending.",
        "- It does not select a final all-measurement inversion.",
        "- It does not change `final_objective_decision_register.csv` statuses.",
        "- It does not send or modify Gmail drafts.",
        "- Use `final_objective_no_new_evidence_acceptance_record_template.md` as the separate signoff guardrail if the draft is chosen.",
        "",
        "## Draft Decision Table",
        "",
        "| Criterion | Stream | Draft choice | Accepted no-new-evidence use | Approval |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['decision_item']} | {row['stream']} | "
            f"`{row['draft_closeout_choice']}` | {row['accepted_no_new_evidence_use']} | "
            f"{row['approval_required_from']} |"
        )

    lines.extend(["", "## Detailed Draft Rows", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['criterion_id']}` {row['decision_item']}",
                "",
                f"- Existing decision status: `{row['existing_decision_status']}`",
                f"- Draft acceptance status: `{row['draft_acceptance_status']}`",
                f"- Exact decision record text: {row['exact_decision_record_text']}",
                f"- Decision-register action: {row['decision_register_action']}",
                f"- Exact report wording: {row['exact_report_wording']}",
                f"- Interpretation after acceptance: {row['interpretation_after_acceptance']}",
                f"- Scenario effect: {row['scenario_option_effect']}",
                f"- Current evidence: {row['current_evidence'] or 'none recorded'}",
                f"- Source locations: {row['source_locations'] or 'none recorded'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Exact Single-Block Acceptance Text",
            "",
            SINGLE_BLOCK_ACCEPTANCE_TEXT,
            "",
            "## Required Refresh Commands",
            "",
            "Run these only after the draft decisions are actually accepted and recorded:",
            "",
            "```bash",
            REFRESH_AFTER_ACCEPTANCE.replace("; ", " \\\n  && "),
            "```",
            "",
            "## Interpretation",
            "",
            "- If accepted, this is a conservative narrow-objective closeout, not an all-measurement inversion.",
            "- The likely scenario is `F01_current_raw_nmr_exclude_gated_streams`, but only after each row is recorded and the audits are regenerated.",
            "- If the modelling team wants any excluded stream to enter the final likelihood, the corresponding provider response or internal policy decision must be filed first.",
            "- The direct-permeability support-conflict audit remains part of the signoff evidence: repeated support cells and the unapproved likelihood policy are blockers to more same-support active-objective batches.",
            "- Until acceptance and regeneration happen, the current field remains the active-objective incumbent only.",
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
    frame, summary = build_rows(args)
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
