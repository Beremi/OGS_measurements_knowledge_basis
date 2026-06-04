#!/usr/bin/env python3
"""Build conservative include/exclude recommendations for open final-objective rows."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "P08_nmr_residual_policy": {
        "recommendation_class": "internal_policy_not_final",
        "recommended_final_use_without_new_evidence": (
            "Retain raw absolute NMR theta only as the current-report active-objective "
            "default with caveats; keep within-label trend/anomaly as the preferred "
            "provisional final-policy candidate, not as a promoted default."
        ),
        "conservative_local_recommendation": (
            "Do not change the NMR default or call the current raw-NMR residual final "
            "until the modelling team records the free-water/bound-water policy and "
            "regenerates the scenario/current-field audits."
        ),
        "include_requires": (
            "A recorded final NMR residual policy: raw absolute theta with caveats, "
            "within-label trend/anomaly, label/campaign bias, explicit free-water "
            "correction, or exclusion from final field selection."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "NMR is retained in the current active objective as raw absolute water "
            "content with bound-water caveats.  No final NMR residual policy is selected; "
            "within-label trend/anomaly remains the preferred provisional candidate."
        ),
        "waiver_position": "not_applicable_internal_policy_required",
        "why_waiver_not_recommended": (
            "The unresolved issue is not missing provider evidence but the physical "
            "semantics of total versus mobile/free water in the OGS state residual."
        ),
    },
    "P09_ert_gate": {
        "recommendation_class": "diagnostic_only_until_provider_acceptance",
        "recommended_final_use_without_new_evidence": (
            "Keep ERT as log-resistivity field-consistency diagnostic evidence only; "
            "exclude it from the final likelihood and final field-selection weights."
        ),
        "conservative_local_recommendation": (
            "Do not use the dense ERT VTK pixels as independent final residual rows "
            "until the coordinate transform, near-niche support mask, and uncertainty/"
            "correlation model are accepted."
        ),
        "include_requires": (
            "Provider or modelling-team acceptance of the ERT-to-OGS transform, exact "
            "support mask, and covariance/weighting model."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "ERT was retained as diagnostic field-consistency evidence and excluded "
            "from the final likelihood because the ERT-to-OGS transform/support and "
            "uncertainty/correlation model were not confirmed."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "The current bridge is provisional and the VTK cells are spatially dense, "
            "correlated inversion outputs rather than independent measurements."
        ),
    },
    "P10_taupe_gate": {
        "recommendation_class": "diagnostic_only_until_provider_acceptance",
        "recommended_final_use_without_new_evidence": (
            "Keep Taupe/TDR as baseline-normalized trend diagnostic evidence only; "
            "exclude absolute Taupe values from final water-content likelihood terms."
        ),
        "conservative_local_recommendation": (
            "Do not activate Taupe/TDR as an absolute saturation or water-content "
            "residual until units, calibration, and uncertainty are confirmed."
        ),
        "include_requires": (
            "Provider confirmation of whether workbook values are volumetric water "
            "content, dielectric/permittivity proxy, ARDP-derived index, or trend-only "
            "quantity, plus uncertainty/weighting guidance."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "Taupe/TDR was retained as a mapped trend diagnostic and excluded from the "
            "final likelihood because unit calibration and residual uncertainty were "
            "not confirmed."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "The same workbook values can imply different physical residuals depending "
            "on calibration; treating them as absolute water content would overstate "
            "the current evidence."
        ),
    },
    "P11_rh_gate": {
        "recommendation_class": "boundary_audit_only_until_provenance_acceptance",
        "recommended_final_use_without_new_evidence": (
            "Keep RH/suction as boundary provenance and scenario-audit evidence only; "
            "do not replace, fit, or weight the active pressure curve from local RH "
            "workbooks in the final objective."
        ),
        "conservative_local_recommendation": (
            "Do not release retention or boundary parameters from RH until the active "
            "curve provenance, constants, time axis, sensor screening, extension policy, "
            "and uncertainty are accepted."
        ),
        "include_requires": (
            "Accepted provenance for the active XML pressure curve and an uncertainty "
            "model for any RH-derived boundary forcing or retention target."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "RH/suction was retained as boundary-provenance and scenario evidence only; "
            "it was not used as a weighted residual or to replace the active pressure "
            "curve because the active-curve provenance and uncertainty remain unconfirmed."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "Changing boundary forcing changes the forward problem, and the current "
            "active curve is not yet reproducible from confirmed local RH processing."
        ),
    },
    "P12_other_hm_gate": {
        "recommendation_class": "qualitative_context_until_numeric_exports_arrive",
        "recommended_final_use_without_new_evidence": (
            "Keep other HM monitoring as qualitative validation context and geometry/"
            "layout support only; exclude it from final hard residuals."
        ),
        "conservative_local_recommendation": (
            "Do not assign mechanical/hydraulic likelihood weights to Geoscope, laser, "
            "levelling, extensometer, mini-piezometer, or crackmeter evidence until "
            "numeric time series, support definitions, metadata, and uncertainty arrive."
        ),
        "include_requires": (
            "Hard-residual-ready numeric exports with timestamps or epochs, units, "
            "instrument/support definitions, coordinate frame, quality flags, and "
            "uncertainty/registration metadata."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "Other HM streams were retained as qualitative or geometric context only "
            "and excluded from the final likelihood because hard-residual-ready numeric "
            "exports, support definitions, and uncertainties were not available locally."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "The local bundle does not yet contain enough numeric support and uncertainty "
            "metadata to define a reproducible OGS residual."
        ),
    },
    "P13_perm_endpoint_gate": {
        "recommendation_class": "partial_support_keep_endpoint_missing_rows_inactive",
        "recommended_final_use_without_new_evidence": (
            "Use only currently projected active pulse-test rows for the final direct "
            "permeability objective; keep historical endpoint-missing rows visible but inactive, "
            "and keep the current rowwise-Gaussian support/likelihood policy active-only until "
            "a policy decision is approved."
        ),
        "conservative_local_recommendation": (
            "Do not include BCD-A24/25/26/27 or BFM-D19 historical rows as hard residuals "
            "until labelled endpoint geometry or an approved digitized trace is accepted."
        ),
        "include_requires": (
            "Label-resolved start/end or collar/tip geometry, coordinate frame, depth-zero "
            "reference, interval-position convention, and uncertainty for the blocked "
            "historical traces; plus an explicit support/likelihood policy if the final "
            "objective is meant to change the current one-value-per-support-cell treatment."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "Endpoint-missing historical permeability rows were kept inactive and excluded "
            "from the final hard residual set; the direct permeability objective used only "
            "rows with current accepted projection support."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "A scalar interval permeability value cannot be projected defensibly to an OGS "
            "support cell or trace without the missing borehole endpoint geometry, and the "
            "current active support map already contains repeated-row conflicts that require "
            "a separate likelihood/support decision."
        ),
    },
    "P14_cte_confirmation": {
        "recommendation_class": "model_provenance_scope_out",
        "recommended_final_use_without_new_evidence": (
            "Scope the suspicious CTE value out of the final permeability objective; keep "
            "the exchanged OGS model frozen and record CTE as an uninterpreted source caveat."
        ),
        "conservative_local_recommendation": (
            "Do not interpret, calibrate, or correct thermal expansivity locally.  The "
            "permeability-field result must avoid claims that depend on the suspicious "
            "CTE value unless a provider response confirms it."
        ),
        "include_requires": (
            "Provider confirmation of whether CTE=1254.74 is intended, inactive, copied "
            "from heat capacity, or subject to a convention not visible in the XML."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "The CTE value remains a frozen-source caveat and was not interpreted or "
            "calibrated in the permeability-field objective."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "The model is required to remain frozen; local correction would create a new "
            "model version rather than documenting the exchanged model."
        ),
    },
    "P15_conditional_field_stability": {
        "recommendation_class": "do_not_promote_until_scenario_explicit",
        "recommended_final_use_without_new_evidence": (
            "Keep the current field active-only; no final scenario is stable enough for "
            "implicit promotion."
        ),
        "conservative_local_recommendation": (
            "If the conservative exclusions above are accepted, record them explicitly "
            "and rerun the conditional scenario and current-field audits before changing "
            "any field label."
        ),
        "include_requires": (
            "A single accepted final objective scenario or a regenerated scenario matrix "
            "showing a stable winner after all include/exclude decisions are recorded."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "The accepted final objective scenario was not selected; therefore the current "
            "field remains an active-objective incumbent, not a final all-measurement field."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "Current scored scenarios select multiple winners, so implicit promotion would "
            "hide a real objective-dependence."
        ),
    },
    "P16_final_field_decision": {
        "recommendation_class": "keep_active_incumbent_label",
        "recommended_final_use_without_new_evidence": (
            "Do not promote the packaged field.  Keep it labelled as the active direct-"
            "permeability/raw-NMR incumbent."
        ),
        "conservative_local_recommendation": (
            "Only promote a field after the promotion checklist and current-field selection "
            "audit both record final approval under an accepted final objective."
        ),
        "include_requires": (
            "Closed, explicitly excluded, or explicitly waived upstream rows plus regenerated "
            "promotion and current-field selection audits recording final approval."
        ),
        "explicit_report_wording_if_no_new_evidence": (
            "The current field is not a final all-measurement inversion result; it is the "
            "active-objective incumbent under the current direct-permeability/raw-NMR setup."
        ),
        "waiver_position": "not_recommended",
        "why_waiver_not_recommended": (
            "The promotion checklist still contains open criteria and the current-field "
            "selection audit currently rejects final promotion."
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decision-register",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.csv"),
    )
    parser.add_argument(
        "--external-blockers",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard.csv"),
    )
    parser.add_argument(
        "--external-blocker-summary",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard_summary.json"),
    )
    parser.add_argument(
        "--nmr-policy-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"),
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
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_include_exclude_recommendations.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_objective_include_exclude_recommendations_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_objective_include_exclude_recommendations.md"),
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


def split_ids(value: Any) -> list[str]:
    text = clean(value)
    if not text:
        return []
    return [item.strip() for item in text.replace(";", ",").split(",") if item.strip()]


def join_unique(values: list[Any], separator: str = "; ") -> str:
    out: list[str] = []
    for value in values:
        text = clean(value)
        if text and text not in out:
            out.append(text)
    return separator.join(out)


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


def blocker_notes(blockers: pd.DataFrame, ids: list[str]) -> dict[str, str]:
    if blockers.empty or not ids or "request_id" not in blockers.columns:
        return {
            "open_blocker_ids": "",
            "blocker_statuses": "",
            "send_statuses": "",
            "response_statuses": "",
            "acceptance_tests": "",
            "current_blocker_evidence": "",
            "response_locations": "",
        }
    related = blockers[blockers["request_id"].astype(str).isin(ids)].copy()
    if related.empty:
        return {
            "open_blocker_ids": "",
            "blocker_statuses": "",
            "send_statuses": "",
            "response_statuses": "",
            "acceptance_tests": "",
            "current_blocker_evidence": "",
            "response_locations": "",
        }
    return {
        "open_blocker_ids": join_unique(related.get("request_id", pd.Series(dtype=str)).tolist(), ", "),
        "blocker_statuses": join_unique(related.get("blocker_status", pd.Series(dtype=str)).tolist()),
        "send_statuses": join_unique(related.get("gmail_send_status", pd.Series(dtype=str)).tolist()),
        "response_statuses": join_unique(related.get("response_status", pd.Series(dtype=str)).tolist()),
        "acceptance_tests": join_unique(related.get("acceptance_test", pd.Series(dtype=str)).tolist()),
        "current_blocker_evidence": join_unique(related.get("current_blocker_or_caveat", pd.Series(dtype=str)).tolist()),
        "response_locations": join_unique(
            related.get("response_notes_md", pd.Series(dtype=str)).tolist()
            + related.get("intake_dir", pd.Series(dtype=str)).tolist()
        ),
    }


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    decision_register = read_csv(args.decision_register)
    blockers = read_csv(args.external_blockers)
    blocker_summary = read_json(args.external_blocker_summary)
    nmr_summary = read_json(args.nmr_policy_summary)
    promotion_summary = read_json(args.promotion_summary)
    current_field_summary = read_json(args.current_field_summary)
    support_conflict = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    lower_bound = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    policy_acceptance = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    next_gate = read_json(Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"))
    permeability_policy_evidence = format_permeability_policy_evidence(
        support_conflict, lower_bound, policy_acceptance, next_gate
    )

    rows: list[dict[str, Any]] = []
    for _, register_row in decision_register.iterrows():
        criterion_id = clean(register_row.get("criterion_id"))
        recommendation = RECOMMENDATIONS.get(criterion_id)
        if not recommendation:
            continue
        related_ids = split_ids(register_row.get("related_blocker_or_decision_ids"))
        blocker_info = blocker_notes(blockers, related_ids)
        include_requires = recommendation["include_requires"]
        if blocker_info["acceptance_tests"]:
            include_requires = f"{include_requires} Acceptance tests: {blocker_info['acceptance_tests']}"
        current_evidence = clean(register_row.get("current_evidence"))
        if blocker_info["current_blocker_evidence"] and blocker_info["current_blocker_evidence"] not in current_evidence:
            current_evidence = join_unique([current_evidence, blocker_info["current_blocker_evidence"]])
        if criterion_id == "P08_nmr_residual_policy":
            current_evidence = join_unique(
                [
                    current_evidence,
                    (
                        f"NMR final policy selected={nmr_summary.get('final_nmr_policy_selected')}; "
                        f"recommended candidate={nmr_summary.get('recommended_candidate_policy')}; "
                        f"recommended run={nmr_summary.get('recommended_candidate_policy_run')}; "
                        f"follow-up={nmr_summary.get('followup_recommendation')}"
                    ),
                ]
            )
        if criterion_id == "P16_final_field_decision":
            current_evidence = join_unique(
                [
                    current_evidence,
                    (
                        f"current-field final decision="
                        f"{current_field_summary.get('final_all_measurement_decision')}"
                    ),
                ]
            )
        if criterion_id in {
            "P13_perm_endpoint_gate",
            "P15_conditional_field_stability",
            "P16_final_field_decision",
        }:
            if "support-conflict" not in current_evidence:
                current_evidence = join_unique([current_evidence, permeability_policy_evidence])
            include_requires = join_unique(
                [
                    include_requires,
                    f"Direct-permeability policy evidence: {permeability_policy_evidence}",
                ]
            )

        rows.append(
            {
                "criterion_id": criterion_id,
                "stream": clean(register_row.get("stream")),
                "decision_item": clean(register_row.get("decision_item")),
                "decision_status": clean(register_row.get("decision_status")),
                "current_allowed_use": clean(register_row.get("current_allowed_use")),
                "recommendation_class": recommendation["recommendation_class"],
                "recommended_final_use_without_new_evidence": recommendation[
                    "recommended_final_use_without_new_evidence"
                ],
                "conservative_local_recommendation": recommendation["conservative_local_recommendation"],
                "include_requires": include_requires,
                "explicit_report_wording_if_no_new_evidence": recommendation[
                    "explicit_report_wording_if_no_new_evidence"
                ],
                "waiver_position": recommendation["waiver_position"],
                "why_waiver_not_recommended": recommendation["why_waiver_not_recommended"],
                "related_blocker_or_decision_ids": clean(register_row.get("related_blocker_or_decision_ids")),
                "open_blocker_ids": blocker_info["open_blocker_ids"],
                "blocker_statuses": blocker_info["blocker_statuses"],
                "send_statuses": blocker_info["send_statuses"],
                "response_statuses": blocker_info["response_statuses"],
                "response_or_decision_locations": join_unique(
                    [
                        clean(register_row.get("response_or_decision_locations")),
                        ""
                        if blocker_info["response_locations"]
                        and blocker_info["response_locations"]
                        in clean(register_row.get("response_or_decision_locations"))
                        else blocker_info["response_locations"],
                    ]
                ),
                "current_evidence": current_evidence,
                "effect_on_final_promotion": (
                    "This packet does not unblock promotion. It provides a conservative "
                    "recommendation that still must be recorded as a modelling decision, "
                    "then refreshed through scenario/current-field/promotion audits."
                ),
                "refresh_after_decision": clean(register_row.get("refresh_after_decision")),
            }
        )

    frame = pd.DataFrame(rows)
    waiver_not_recommended_count = int(frame["waiver_position"].eq("not_recommended").sum()) if not frame.empty else 0
    provider_required = int(
        frame["recommendation_class"].astype(str).str.contains("until_|model_provenance").sum()
    ) if not frame.empty else 0
    diagnostic_or_exclude = int(
        frame["recommended_final_use_without_new_evidence"].astype(str).str.contains(
            "diagnostic|exclude|inactive|qualitative|scope", case=False, regex=True
        ).sum()
    ) if not frame.empty else 0
    summary: dict[str, Any] = {
        "status": "final_objective_include_exclude_recommendations_generated",
        "recommendation_count": int(frame.shape[0]),
        "external_measurement_or_provenance_recommendation_count": int(
            frame["criterion_id"].isin(
                [
                    "P09_ert_gate",
                    "P10_taupe_gate",
                    "P11_rh_gate",
                    "P12_other_hm_gate",
                    "P13_perm_endpoint_gate",
                    "P14_cte_confirmation",
                ]
            ).sum()
        )
        if not frame.empty
        else 0,
        "internal_policy_recommendation_count": int(frame["criterion_id"].eq("P08_nmr_residual_policy").sum())
        if not frame.empty
        else 0,
        "scenario_or_final_recommendation_count": int(
            frame["criterion_id"].isin(["P15_conditional_field_stability", "P16_final_field_decision"]).sum()
        )
        if not frame.empty
        else 0,
        "recommendation_class_counts": frame["recommendation_class"].value_counts().sort_index().to_dict()
        if not frame.empty
        else {},
        "diagnostic_or_exclude_without_new_evidence_count": diagnostic_or_exclude,
        "waiver_not_recommended_count": waiver_not_recommended_count,
        "provider_or_internal_evidence_required_for_include_count": provider_required,
        "final_promotion_unblocked_by_this_packet": False,
        "promotion_decision_before_packet": promotion_summary.get("promotion_decision"),
        "current_field_final_decision_before_packet": current_field_summary.get("final_all_measurement_decision"),
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
        "open_blocker_count": blocker_summary.get("open_blocker_count"),
        "open_blocker_ids": blocker_summary.get("open_blocker_ids", []),
        "missing_response_blocker_count": blocker_summary.get("missing_response_blocker_count"),
        "unsent_blocker_count": blocker_summary.get("unsent_blocker_count"),
        "recommended_current_field_label": "active_objective_incumbent_only",
        "next_action": (
            "If the user/model team accepts the conservative recommendations, record the "
            "explicit exclusions or diagnostic-only decisions in the decision layer and rerun "
            "scenario/current-field/promotion audits. Otherwise send the existing provider "
            "drafts and file responses before inclusion."
        ),
        "source_artifacts": [
            "inversion_workflow/final_objective_decision_register.csv",
            "inversion_workflow/external_blocker_dashboard.csv",
            "inversion_workflow/nmr_final_residual_policy_gate_summary.json",
            "inversion_workflow/final_inversion_promotion_checklist_summary.json",
            "inversion_workflow/current_field_selection_audit_summary.json",
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
        "# Final Objective Include/Exclude Recommendations",
        "",
        "This generated packet converts the open final-objective decision register into",
        "conservative local recommendations for the current no-new-provider-evidence state.",
        "It does not send email, close gates, record user approval, change OGS inputs,",
        "or promote a permeability field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Recommendations: {summary['recommendation_count']}",
        f"- External measurement/provenance recommendations: {summary['external_measurement_or_provenance_recommendation_count']}",
        f"- Internal policy recommendations: {summary['internal_policy_recommendation_count']}",
        f"- Scenario/final recommendations: {summary['scenario_or_final_recommendation_count']}",
        f"- Diagnostic or exclude without new evidence: {summary['diagnostic_or_exclude_without_new_evidence_count']}",
        f"- Waivers not recommended: {summary['waiver_not_recommended_count']}",
        f"- Final promotion unblocked by this packet: `{summary['final_promotion_unblocked_by_this_packet']}`",
        f"- Open blockers before packet: {summary.get('open_blocker_count')} ({', '.join(summary.get('open_blocker_ids', []))})",
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
        "## Recommendation Table",
        "",
        "| Criterion | Stream | Current use | Recommendation class | Recommended use without new evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['decision_item']} | {row['stream']} | "
            f"`{row['current_allowed_use']}` | `{row['recommendation_class']}` | "
            f"{row['recommended_final_use_without_new_evidence']} |"
        )

    lines.extend(["", "## Detailed Recommendations", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['criterion_id']}` {row['decision_item']}",
                "",
                f"- Conservative recommendation: {row['conservative_local_recommendation']}",
                f"- Include requires: {row['include_requires']}",
                f"- Report wording if no new evidence: {row['explicit_report_wording_if_no_new_evidence']}",
                f"- Waiver position: `{row['waiver_position']}`",
                f"- Why waiver is not recommended: {row['why_waiver_not_recommended']}",
                f"- Current evidence: {row['current_evidence']}",
                f"- Related blockers/decisions: {row['related_blocker_or_decision_ids'] or 'none'}",
                f"- Response or decision locations: {row['response_or_decision_locations'] or 'none'}",
                f"- Promotion effect: {row['effect_on_final_promotion']}",
                f"- Refresh after decision: `{row['refresh_after_decision']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Without new provider evidence, the conservative local position is to keep ERT, Taupe/TDR, RH/suction, other-HM monitoring, endpoint-missing historical permeability rows, and CTE out of final hard likelihood weights.",
            "- The direct-permeability current-support objective is also policy-gated: repeated support-cell conflicts and zero same-support reducible gap require an explicit support/likelihood decision before more same-support OGS spending or final promotion.",
            "- NMR remains an internal policy decision: the report can keep the current raw-theta default with caveats, but final promotion still needs an accepted NMR residual policy.",
            "- Recording these recommendations as actual decisions would still require a rerun of the scenario, current-field, and final-promotion audits.",
            "- Until that happens, the current field label remains active-objective incumbent only.",
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
