#!/usr/bin/env python3
"""Build a consolidated resolution matrix for report and modelling open questions."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/open_question_resolution_matrix.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/open_question_resolution_matrix_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/open_question_resolution_matrix.md"),
    )
    parser.add_argument(
        "--kb-output-md",
        type=Path,
        default=Path("../cda_knowledge_base/open_questions_resolution_matrix.md"),
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


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def lookup(frame: pd.DataFrame, key_column: str, key: str) -> dict[str, Any]:
    if frame.empty or key_column not in frame.columns:
        return {}
    matched = frame[frame[key_column] == key]
    if matched.empty:
        return {}
    return matched.iloc[0].fillna("").to_dict()


def value(row: dict[str, Any], key: str, fallback: str = "") -> str:
    item = row.get(key, fallback)
    if item is None:
        return fallback
    text = str(item)
    if text == "nan":
        return fallback
    return text


def format_top_conflict_cell(top: dict[str, Any]) -> str:
    if not top:
        return ""
    return (
        f"top_conflict_cell={top.get('primary_cell_id')} "
        f"({top.get('segments')} {top.get('depth_min_m')}-{top.get('depth_max_m')} m, "
        f"observed_range={top.get('observed_log10_range')})"
    )


def permeability_support_conflict_evidence(
    support_conflict: dict[str, Any],
    policy_acceptance: dict[str, Any],
) -> str:
    if not support_conflict and not policy_acceptance:
        return "support_conflict_spatial_audit=missing"
    return (
        f"support_conflict_spatial_audit={support_conflict.get('status')}; "
        f"active/repeated/range>=2 support cells="
        f"{support_conflict.get('active_support_cell_count')}/"
        f"{support_conflict.get('repeated_support_cell_count')}/"
        f"{support_conflict.get('support_cells_observed_range_ge_2_log10')}; "
        f"configured_scalar_conflict_cells="
        f"{support_conflict.get('configured_scalar_range_conflict_cell_count')}; "
        f"{format_top_conflict_cell(support_conflict.get('top_conflict_cell', {}))}; "
        f"policy_approvals="
        f"{policy_acceptance.get('primary_policy_approval_rows_recorded')}/"
        f"{policy_acceptance.get('primary_policy_approval_rows_required')}; "
        f"policy_ready={policy_acceptance.get('ready_to_apply_policy')}; "
        f"same_support_batch_executable_now="
        f"{policy_acceptance.get('same_support_batch_executable_now')}"
    )


def bullet_count(markdown: Path) -> int:
    if not markdown.exists():
        return 0
    return sum(
        1
        for line in markdown.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.startswith("- ")
    )


def heading_count(markdown: Path) -> int:
    if not markdown.exists():
        return 0
    return sum(
        1
        for line in markdown.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.startswith("## ")
    )


def add_row(
    rows: list[dict[str, str]],
    *,
    question_id: str,
    question_area: str,
    representative_question: str,
    resolution_status: str,
    current_answer: str,
    local_evidence: str,
    remaining_action: str,
    model_consequence: str,
    authoritative_artifacts: str,
    related_ids: str = "",
) -> None:
    rows.append(
        {
            "question_id": question_id,
            "question_area": question_area,
            "representative_question": representative_question,
            "resolution_status": resolution_status,
            "current_answer": current_answer,
            "local_evidence": local_evidence,
            "remaining_action": remaining_action,
            "model_consequence": model_consequence,
            "authoritative_artifacts": authoritative_artifacts,
            "related_ids": related_ids,
        }
    )


def external_gate_row(
    *,
    question_id: str,
    question_area: str,
    representative_question: str,
    gate_ids: list[str],
    decision_id: str,
    request_rows: pd.DataFrame,
    decision_rows: pd.DataFrame,
    artifacts: str,
    model_consequence: str,
) -> dict[str, str]:
    gate_summaries = []
    blockers = []
    for gate_id in gate_ids:
        gate = lookup(request_rows, "request_id", gate_id)
        if gate:
            gate_summaries.append(
                f"{gate_id}: {value(gate, 'gate_status', 'unknown')} - "
                f"{value(gate, 'current_blocker_or_caveat')}"
            )
            blockers.append(value(gate, "current_blocker_or_caveat"))
        else:
            gate_summaries.append(f"{gate_id}: not found in request table")
    decision = lookup(decision_rows, "criterion_id", decision_id)
    current_answer = value(
        decision,
        "default_current_decision",
        "do_not_include_in_final_objective_until_provider_response_or_explicit_exclusion_is_recorded",
    )
    remaining = value(
        decision,
        "acceptance_evidence",
        "Provider response or explicit exclusion/waiver decision is required.",
    )
    return {
        "question_id": question_id,
        "question_area": question_area,
        "representative_question": representative_question,
        "resolution_status": "external_provider_response_required",
        "current_answer": current_answer,
        "local_evidence": "; ".join(gate_summaries),
        "remaining_action": remaining,
        "model_consequence": model_consequence,
        "authoritative_artifacts": artifacts,
        "related_ids": ",".join(gate_ids + [decision_id]),
    }


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    report = read_json(Path("inversion_workflow/report_open_comment_audit_summary.json"))
    citations = read_json(Path("Library/citation_locator_audit_summary.json"))
    traceability = read_json(Path("inversion_workflow/measurement_report_traceability_audit_summary.json"))
    objective = read_json(Path("inversion_workflow/objective_readiness_audit_summary.json"))
    final_promotion = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    external = read_json(Path("inversion_workflow/external_blocker_dashboard_summary.json"))
    final_decision = read_json(Path("inversion_workflow/final_objective_decision_register_summary.json"))
    final_recommend = read_json(
        Path("inversion_workflow/final_objective_include_exclude_recommendations_summary.json")
    )
    final_no_new = read_json(Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json"))
    final_acceptance_template = read_json(
        Path("inversion_workflow/final_objective_no_new_evidence_acceptance_record_template_summary.json")
    )
    permeability = read_json(
        Path("inversion_workflow/permeability_likelihood_support_recommendations_summary.json")
    )
    permeability_support_conflict = read_json(
        Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json")
    )
    permeability_acceptance_template = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    permeability_support_evidence = permeability_support_conflict_evidence(
        permeability_support_conflict,
        permeability_acceptance_template,
    )
    nmr = read_json(Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"))
    nmr_acceptance_template = read_json(
        Path("inversion_workflow/nmr_final_residual_policy_acceptance_record_template_summary.json")
    )
    cte = read_json(Path("inversion_workflow/cte_confirmation_request_summary.json"))
    internal = read_json(Path("inversion_workflow/internal_gate_decision_register_summary.json"))
    local_recovery = read_json(Path("inversion_workflow/local_gate_recovery_audit_summary.json"))
    download_recovery = read_json(Path("inversion_workflow/download_gate_recovery_audit_summary.json"))

    request_rows = read_csv(Path("inversion_workflow/measurement_gate_closure_request.csv"))
    decision_rows = read_csv(Path("inversion_workflow/final_objective_decision_register.csv"))

    rows: list[dict[str, str]] = []

    add_row(
        rows,
        question_id="Q01_report_formula_comments",
        question_area="Report formulation",
        representative_question="Are collaborator/comment markers or formulation comments still open in the active report?",
        resolution_status="resolved_locally",
        current_answer=(
            f"No active report markers remain; {report.get('resolved_formulation_comment_count', 0)} "
            "formulation comments are resolved in the active LaTeX sources."
        ),
        local_evidence=(
            f"active_report_unresolved_marker_count={report.get('active_report_unresolved_marker_count', 0)}; "
            f"tracked_external_gate_count={report.get('tracked_external_blocker_count', 0)}; "
            f"active_open_item_ids={report.get('active_report_open_item_ids', [])}"
        ),
        remaining_action="Keep the gate/provenance items in readiness trackers rather than as unresolved LaTeX comments.",
        model_consequence="Report hygiene is not the limiting factor for final promotion.",
        authoritative_artifacts="inversion_workflow/report_open_comment_audit.md; main.tex; measurement_chapter.tex",
        related_ids="report_open_comment_audit",
    )

    add_row(
        rows,
        question_id="Q02_sources_citations",
        question_area="Sources and citations",
        representative_question="Are all cited sources, fulltexts, and locators sufficiently traceable?",
        resolution_status="resolved_locally",
        current_answer=(
            "All active citations have BibTeX entries and checkable locators; unavailable active "
            "fulltexts are tracked."
        ),
        local_evidence=(
            f"citation_instances={citations.get('citation_key_instance_count', 0)}; "
            f"unique_keys={citations.get('unique_cited_key_count', 0)}; "
            f"missing_or_weak_locators={citations.get('missing_or_weak_locator_count', 0)}; "
            f"missing_bib_entries={citations.get('missing_bib_entry_count', 0)}; "
            f"unavailable_missing_log={citations.get('unavailable_fulltext_missing_log_count', 0)}"
        ),
        remaining_action="Only refresh if new cited sources are added.",
        model_consequence="Literature/source tracking does not block current readiness; scientific gates still do.",
        authoritative_artifacts="Library/citation_locator_audit.md; Library/source_coverage_audit.md; opalinus_clay.bib",
        related_ids="citation_locator_audit",
    )

    add_row(
        rows,
        question_id="Q03_measurement_catalogue",
        question_area="Data location and catalogue",
        representative_question="Are measurement emails, transfers, zip contents, and copied source files catalogued?",
        resolution_status="resolved_locally",
        current_answer=(
            "The local catalogue is traceable for all nine measurement groups; the known scanned "
            "Gmail/Thunderbird/TeamBeam scope has no missing CD-A/HERMES attachments."
        ),
        local_evidence=(
            f"traceability_status={traceability.get('status')}; "
            f"observations={traceability.get('observation_count', 0)}; "
            f"all_traceable={traceability.get('all_observations_traceable')}; "
            f"manifest_failures={traceability.get('manifest_validation_failures', 0)}"
        ),
        remaining_action="Regenerate only after adding new local files or provider-response attachments.",
        model_consequence="The catalogue itself is not blocking final promotion; activation semantics are.",
        authoritative_artifacts=(
            "../cda_knowledge_base/measurements/README.md; "
            "inversion_workflow/measurement_report_traceability_audit.md"
        ),
        related_ids="measurement_report_traceability_audit",
    )

    add_row(
        rows,
        question_id="Q04_model_baseline_projection",
        question_area="OGS model provenance",
        representative_question="Which transferred OGS model is the baseline and can projected fields be read?",
        resolution_status="resolved_locally_with_frozen_model_caveat",
        current_answer=(
            "The May 2025 transferred model remains the scanned-scope baseline; heterogeneous "
            "fields are introduced through run-local mesh-field replacements while the exchanged model stays frozen."
        ),
        local_evidence=(
            "The projection workflow shows OGS can read k_i_rd and n_rd mesh-cell fields; "
            "the formulation and run-input audits record run-local substitutions without changing the source model."
        ),
        remaining_action="Confirm only if Gesa/BGR provides a newer out-of-scope baseline.",
        model_consequence="Run-local heterogeneous permeability fitting is allowed; source XML edits remain out of scope.",
        authoritative_artifacts=(
            "inversion_workflow/ogs_formulation_consistency_audit.md; "
            "inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.md; "
            "GESA_model_original/projection_on_mesh_2025-09-05"
        ),
        related_ids="projection_workflow,ogs_formulation",
    )

    rows.append(
        external_gate_row(
            question_id="Q05_ert_transform_support",
            question_area="ERT processing",
            representative_question="Which ERT-to-OGS transform and near-niche support mask should be used?",
            gate_ids=["ert_transform_support"],
            decision_id="P09_ert_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/ert_spatial_projection_operator.md; "
                "inversion_workflow/ert_support_sensitivity.md; "
                "../cda_knowledge_base/measurements/ert/source_files/provider_responses"
            ),
            model_consequence="ERT remains diagnostic until support geometry is accepted.",
        )
    )

    rows.append(
        external_gate_row(
            question_id="Q06_ert_uncertainty",
            question_area="ERT processing",
            representative_question="What ERT uncertainty/correlation model should weight dense resistivity fields?",
            gate_ids=["ert_uncertainty"],
            decision_id="P09_ert_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts="inversion_workflow/ert_candidate_discrimination.md; inversion_workflow/measurement_likelihood_model.md",
            model_consequence="Dense ERT VTK cells must not become independent final residual rows yet.",
        )
    )

    rows.append(
        external_gate_row(
            question_id="Q07_taupe_units",
            question_area="Taupe/TDR",
            representative_question="Are Taupe workbook values calibrated water content, dielectric/permittivity, or a trend proxy?",
            gate_ids=["taupe_unit_calibration"],
            decision_id="P10_taupe_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/taupe_tdr_semantics.md; "
                "inversion_workflow/taupe_series_weight_sensitivity.md; "
                "../cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses"
            ),
            model_consequence="Taupe/TDR remains a mapped trend diagnostic, not an absolute final water-content residual.",
        )
    )

    add_row(
        rows,
        question_id="Q08_taupe_support_weights",
        question_area="Taupe/TDR",
        representative_question="How should Taupe/TDR sensor support and grouped weights be handled?",
        resolution_status="internal_policy_after_calibration",
        current_answer=(
            "A3/A4 mapped trend diagnostics are available; A7/A8 and series/group weighting stay excluded "
            "or diagnostic until support and calibration choices are accepted."
        ),
        local_evidence=(
            "taupe_group_weights and taupe_support are warning-level method decisions in the gate-closure request table; "
            "the series-weight audit found multiple distinct per-series winners."
        ),
        remaining_action="Choose series/group weighting and support mask after unit/calibration confirmation.",
        model_consequence="Taupe can influence final field selection only after calibration plus weighting policy are explicit.",
        authoritative_artifacts=(
            "inversion_workflow/taupe_series_weight_sensitivity.md; "
            "inversion_workflow/processed_observations/taupe_tdr_semantics.md"
        ),
        related_ids="taupe_group_weights,taupe_support,P10_taupe_gate",
    )

    rows.append(
        external_gate_row(
            question_id="Q09_rh_curve_provenance",
            question_area="RH/suction boundary",
            representative_question="What is the provenance and processing chain for the active OGS pressure curve?",
            gate_ids=["rh_active_curve_provenance"],
            decision_id="P11_rh_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; "
                "inversion_workflow/processed_observations/rh_boundary_uncertainty.md; "
                "../cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses"
            ),
            model_consequence="RH remains boundary-provenance/scenario evidence and does not replace the active curve yet.",
        )
    )

    add_row(
        rows,
        question_id="Q10_rh_uncertainty_policy",
        question_area="RH/suction boundary",
        representative_question="Should RH enter as boundary forcing, retention validation, or calibration target?",
        resolution_status="internal_policy_with_provider_confirmation",
        current_answer=(
            "Local RH-derived envelopes are quantified but not accepted as replacement forcing or a retention likelihood."
        ),
        local_evidence=(
            value(lookup(request_rows, "request_id", "rh_uncertainty"), "current_evidence")
            or "RH uncertainty policy is tracked as an internal method decision with optional BGR confirmation."
        ),
        remaining_action="Select boundary/retention uncertainty policy only after active-curve provenance is resolved.",
        model_consequence="Retention and boundary parameters remain unreleased.",
        authoritative_artifacts=(
            "inversion_workflow/processed_observations/rh_boundary_uncertainty.md; "
            "inversion_workflow/processed_observations/rh_boundary_provenance_request.md"
        ),
        related_ids="rh_uncertainty,P11_rh_gate",
    )

    rows.append(
        external_gate_row(
            question_id="Q11_other_hm_numeric_exports",
            question_area="Other HM monitoring",
            representative_question="Are hard-residual-ready Geoscope, laser, levelling, extensometer, or crackmeter exports available?",
            gate_ids=["hm_numeric_exports"],
            decision_id="P12_other_hm_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; "
                "inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; "
                "../cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses"
            ),
            model_consequence="Other-HM streams stay qualitative/contextual and cannot receive hard residual weights.",
        )
    )

    rows.append(
        external_gate_row(
            question_id="Q12_other_hm_uncertainty",
            question_area="Other HM monitoring",
            representative_question="Do other-HM exports include units, epochs, support definitions, quality flags, and uncertainty?",
            gate_ids=["hm_uncertainty"],
            decision_id="P12_other_hm_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; "
                "../cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses"
            ),
            model_consequence="Even found numeric values cannot become hard residuals without metadata and weights.",
        )
    )

    rows.append(
        external_gate_row(
            question_id="Q13_perm_endpoint_geometry",
            question_area="Permeability pulse tests",
            representative_question="Can older historical permeability rows be projected to the OGS support?",
            gate_ids=["perm_endpoint_geometry"],
            decision_id="P13_perm_endpoint_gate",
            request_rows=request_rows,
            decision_rows=decision_rows,
            artifacts=(
                "inversion_workflow/processed_observations/permeability_missing_geometry_audit.md; "
                "inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md; "
                "../cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses"
            ),
            model_consequence="Historical endpoint-missing rows remain visible but inactive.",
        )
    )

    add_row(
        rows,
        question_id="Q14_perm_error_model",
        question_area="Permeability pulse tests",
        representative_question="How should gas-pulse scalar interval measurements relate to the anisotropic tensor field?",
        resolution_status="tracked_caveat_current_policy_recorded",
        current_answer=(
            "Active direct pulse-test rows are log10 intrinsic-permeability likelihood terms with duplicate-aware "
            "weights and broad sigma; they are not hard water-conductivity constraints or full tensor measurements."
        ),
        local_evidence=(
            value(lookup(request_rows, "request_id", "perm_error_model"), "current_evidence")
            or "The measurement semantics audit records the gas/slip/liquid-equivalent and scalar-to-tensor caveats."
        ),
        remaining_action="Reopen only if the modelling team changes sigma, slip correction, or tensor projection semantics.",
        model_consequence="The current fit can use scalar pulse-test intervals as magnitude/support evidence with explicit caveats.",
        authoritative_artifacts=(
            "inversion_workflow/processed_observations/permeability_measurement_semantics.md; "
            "inversion_workflow/measurement_likelihood_model.md"
        ),
        related_ids="perm_error_model",
    )

    add_row(
        rows,
        question_id="Q15_perm_likelihood_support",
        question_area="Permeability objective",
        representative_question="Should direct permeability use rowwise Gaussian, robust rows, or support-cell aggregation?",
        resolution_status="internal_policy_decision_required",
        current_answer=(
            f"Current-report default remains {permeability.get('current_report_policy')}; "
            "non-default robust/support-cell policies are decision scenarios, not silent replacements."
        ),
        local_evidence=(
            f"recommendations={permeability.get('recommendation_count', 0)}; "
            f"active_direct_rows={permeability.get('active_direct_rows', 0)}; "
            f"support_groups={permeability.get('support_group_count', 0)}; "
            f"same_support_gap={permeability.get('same_support_reducible_objective_gap')}; "
            f"batch_executable_now={permeability.get('same_support_active_objective_batch_executable_now')}; "
            f"acceptance_template_status={permeability_acceptance_template.get('status')}; "
            f"primary_policy_approvals_recorded="
            f"{permeability_acceptance_template.get('primary_policy_approval_rows_recorded')}; "
            f"ready_to_apply_policy={permeability_acceptance_template.get('ready_to_apply_policy')}; "
            f"{permeability_support_evidence}"
        ),
        remaining_action=permeability_acceptance_template.get(
            "next_action",
            permeability.get(
                "next_action",
                "Record a likelihood/support/outlier/bounds/tensor-shape decision before more OGS spending.",
            ),
        ),
        model_consequence="More same-support active-objective OGS sampling is paused until policy/support changes.",
        authoritative_artifacts=(
            "inversion_workflow/permeability_likelihood_support_recommendations.md; "
            "inversion_workflow/permeability_next_field_fit_gate.md; "
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md"
        ),
        related_ids="perm_likelihood_policy",
    )

    add_row(
        rows,
        question_id="Q16_nmr_residual_policy",
        question_area="NMR water content",
        representative_question="How should NMR total water content relate to mobile/free water in the OGS state?",
        resolution_status="internal_policy_decision_required",
        current_answer=(
            f"Current report keeps {nmr.get('current_report_default_policy')}; "
            f"recommended provisional candidate is {nmr.get('recommended_candidate_policy')}; "
            f"final policy selected={nmr.get('final_nmr_policy_selected')}."
        ),
        local_evidence=(
            f"trend_anomaly_status={nmr.get('trend_anomaly_mode_status')}; "
            f"recommended_run={nmr.get('recommended_candidate_policy_run')}; "
            f"current_raw_incumbent_rank_under_trend={nmr.get('current_raw_incumbent_rank_under_trend_anomaly')}; "
            f"followup={nmr.get('followup_recommendation')}; "
            f"acceptance_template_status={nmr_acceptance_template.get('status')}; "
            f"primary_policy_approvals_recorded="
            f"{nmr_acceptance_template.get('primary_policy_approval_rows_recorded')}; "
            f"ready_to_apply_policy={nmr_acceptance_template.get('ready_to_apply_policy')}"
        ),
        remaining_action=nmr_acceptance_template.get(
            "next_action",
            "Record the final NMR residual semantics before claiming an all-measurement field.",
        ),
        model_consequence="NMR remains active in the current objective but not a final settled residual policy.",
        authoritative_artifacts=(
            "inversion_workflow/nmr_final_residual_policy_gate.md; "
            "inversion_workflow/nmr_objective_decision.md; "
            "inversion_workflow/nmr_trend_anomaly_active_objective.md; "
            "inversion_workflow/nmr_final_residual_policy_acceptance_record_template.md"
        ),
        related_ids="nmr_bound_water,P08_nmr_residual_policy",
    )

    add_row(
        rows,
        question_id="Q17_inversion_parameter_set",
        question_area="Inversion setup",
        representative_question="What is the first inversion parameter set?",
        resolution_status="resolved_current_scope",
        current_answer=(
            "Permeability only is the first active release; porosity, retention, boundary, and "
            "mechanical releases are deferred until state residuals and gate evidence justify them."
        ),
        local_evidence=(
            f"internal_policy_status={internal.get('status')}; "
            f"active_or_ready_internal_policy_count={internal.get('active_or_ready_internal_policy_count', 0)}; "
            f"still_gated={internal.get('still_external_or_activation_gated_count', 0)}"
        ),
        remaining_action="Only release additional parameter families through explicit gates and regenerated audits.",
        model_consequence="The current workflow remains a permeability-field fitting workflow, not a broad THM calibration.",
        authoritative_artifacts="inversion_workflow/internal_gate_decision_register.md; measurement_chapter.tex",
        related_ids="parameter_release_policy",
    )

    add_row(
        rows,
        question_id="Q18_bedding_anisotropy",
        question_area="Inversion setup",
        representative_question="Should bedding angle be hard-coded as the anisotropy direction?",
        resolution_status="resolved_current_scope",
        current_answer=(
            "Bedding angle is structural prior/candidate context, not an unquestioned hard constraint; "
            "local anisotropy release is not justified by current direct-objective screens."
        ),
        local_evidence=(
            "The anisotropy and local-anisotropy sampler audits did not justify changing the active field "
            "solely through tensor direction/ratio release."
        ),
        remaining_action="Reopen only after likelihood/support or stream gates change the objective.",
        model_consequence="Anisotropy remains represented through the current tensor-field workflow and candidate diagnostics.",
        authoritative_artifacts=(
            "inversion_workflow/runs/anisotropy_sensitivity_plan; "
            "inversion_workflow/runs/local_anisotropy_sampler_plan; measurement_chapter.tex"
        ),
        related_ids="bedding_angle,anisotropy_sensitivity",
    )

    cte_decision = lookup(decision_rows, "criterion_id", "P14_cte_confirmation")
    add_row(
        rows,
        question_id="Q19_cte_value",
        question_area="Frozen OGS model provenance",
        representative_question="Is the suspicious CTE=1254.74 value intended, inactive, or a copied heat-capacity entry?",
        resolution_status="external_provider_response_required",
        current_answer=value(
            cte_decision,
            "default_current_decision",
            "do_not_include_in_final_objective_until_provider_response_or_explicit_exclusion_is_recorded",
        ),
        local_evidence=(
            f"request_status={cte.get('request_status')}; "
            f"response_status={cte.get('response_status')}; "
            f"gmail_draft_id={cte.get('gmail_draft_id')}; "
            f"to={cte.get('suggested_to')}; cc={cte.get('suggested_cc')}; "
            f"current_evidence={value(cte_decision, 'current_evidence')}"
        ),
        remaining_action=value(
            cte_decision,
            "acceptance_evidence",
            "File the provider response and keep the exchanged model frozen unless an approved model-version decision exists.",
        ),
        model_consequence="The value remains a frozen-source caveat and is scoped out of permeability-field claims.",
        authoritative_artifacts=(
            "inversion_workflow/cte_confirmation_request.md; "
            "inversion_workflow/thermal_expansivity_parameter_audit.md"
        ),
        related_ids="cte_value_confirmation,P14_cte_confirmation",
    )

    add_row(
        rows,
        question_id="Q20_final_scenario_field",
        question_area="Final promotion",
        representative_question="Can the current field be promoted to a final all-measurement permeability field?",
        resolution_status="not_ready_final_decision_required",
        current_answer=(
            f"promotion_decision={final_promotion.get('promotion_decision')}; "
            f"current_field_final_decision={final_promotion.get('current_field_final_decision')}; "
            f"open_criteria={final_promotion.get('open_criterion_ids', [])}"
        ),
        local_evidence=(
            f"final_decision_status={final_decision.get('status')}; "
            f"pending_or_not_ready={final_decision.get('pending_or_not_ready_decision_count', 0)}; "
            f"conditional_unique_winners={final_decision.get('conditional_unique_winner_count', 0)}; "
            f"include_exclude_unblocks={final_recommend.get('final_promotion_unblocked_by_this_packet')}; "
            f"no_new_evidence_draft_status={final_no_new.get('status')}; "
            f"no_new_evidence_draft_records_decisions={final_no_new.get('records_actual_decisions')}; "
            f"no_new_evidence_draft_promotes_field={final_no_new.get('promotes_current_field')}; "
            f"{permeability_support_evidence}"
        ),
        remaining_action=(
            "Close, explicitly exclude, or explicitly waive upstream rows, then rerun scenario and promotion audits. "
            "If the conservative no-new-evidence path is chosen, record the draft decisions first rather than "
            "treating the draft as approval."
        ),
        model_consequence="The packaged field remains an active-objective incumbent only.",
        authoritative_artifacts=(
            "inversion_workflow/final_inversion_promotion_checklist.md; "
            "inversion_workflow/final_objective_decision_register.md; "
            "inversion_workflow/final_objective_scenario_matrix.md; "
            "inversion_workflow/final_objective_no_new_evidence_closeout_draft.md"
        ),
        related_ids="P15_conditional_field_stability,P16_final_field_decision",
    )

    add_row(
        rows,
        question_id="Q21_external_response_state",
        question_area="External request workflow",
        representative_question="Are the provider request drafts sent and are replies filed?",
        resolution_status="waiting_user_send_and_provider_response",
        current_answer=(
            f"{external.get('open_blocker_count', 0)}/{external.get('blocker_count', 0)} blockers remain open; "
            f"{external.get('unsent_blocker_count', 0)} are unsent and "
            f"{external.get('missing_response_blocker_count', 0)} are missing responses."
        ),
        local_evidence=(
            f"draft_ids={external.get('draft_ids', [])}; "
            f"all_expected_drafts_observed={external.get('all_expected_drafts_observed')}; "
            f"gmail_live_state_checked_at={external.get('gmail_live_state_checked_at')}; "
            f"local_possible_closure={local_recovery.get('possible_closure_evidence_count', 0)}; "
            f"download_possible_closure={download_recovery.get('possible_closure_evidence_count', 0)}"
        ),
        remaining_action=external.get(
            "next_action",
            "Review/send drafts, file provider responses, and rerun gate/readiness audits.",
        ),
        model_consequence="Provider-gated streams cannot become final hard likelihood terms yet.",
        authoritative_artifacts=(
            "inversion_workflow/external_blocker_dashboard.md; "
            "inversion_workflow/gmail_draft_send_review_packet.md; "
            "inversion_workflow/external_gate_response_intake.md"
        ),
        related_ids="external_blocker_dashboard",
    )

    add_row(
        rows,
        question_id="Q23_no_new_evidence_closeout",
        question_area="Final promotion",
        representative_question="Should the modelling team accept the conservative no-new-evidence closeout instead of waiting for provider replies?",
        resolution_status="internal_policy_decision_required",
        current_answer=(
            "A review-only no-new-evidence draft exists. It would select "
            f"{final_no_new.get('would_select_scenario_if_all_rows_approved_and_audits_rerun')} with winner "
            f"{final_no_new.get('would_select_winner_if_all_rows_approved_and_audits_rerun')} only after "
            "explicit approval and regenerated audits."
        ),
        local_evidence=(
            f"draft_status={final_no_new.get('status')}; "
            f"draft_rows={final_no_new.get('draft_decision_count', 0)}; "
            f"external_or_provenance_rows={final_no_new.get('external_or_provenance_draft_count', 0)}; "
            f"internal_policy_rows={final_no_new.get('internal_policy_draft_count', 0)}; "
            f"scenario_or_final_rows={final_no_new.get('scenario_or_final_draft_count', 0)}; "
            f"requires_approval={final_no_new.get('requires_user_or_modelling_team_approval')}; "
            f"records_decisions={final_no_new.get('records_actual_decisions')}; "
            f"promotes_current_field={final_no_new.get('promotes_current_field')}; "
            f"unblocks_promotion={final_no_new.get('final_promotion_unblocked_by_this_draft')}; "
            f"open_blockers={final_no_new.get('open_blocker_count')}; "
            f"missing_responses={final_no_new.get('missing_response_blocker_count')}; "
            f"unsent_gmail_drafts={final_no_new.get('gmail_unsent_draft_count')}; "
            f"acceptance_template_status={final_acceptance_template.get('status')}; "
            f"approval_rows_recorded={final_acceptance_template.get('approval_rows_recorded')}; "
            f"ready_to_apply_decisions={final_acceptance_template.get('ready_to_apply_decisions')}; "
            f"{permeability_support_evidence}"
        ),
        remaining_action=(
            "Either approve and record the exact draft decisions, then rerun scenario/current-field/promotion "
            "audits, or keep the external requests open and wait for provider evidence before including gated streams."
        ),
        model_consequence=(
            "Accepting this path would be a narrow raw-NMR/direct-permeability closeout with gated streams "
            "diagnostic or excluded, not a final all-measurement likelihood."
        ),
        authoritative_artifacts=(
            "inversion_workflow/final_objective_no_new_evidence_closeout_draft.md; "
            "inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.md; "
            "inversion_workflow/final_objective_include_exclude_recommendations.md; "
            "inversion_workflow/final_objective_scenario_matrix.md"
        ),
        related_ids="F01_current_raw_nmr_exclude_gated_streams,P08_nmr_residual_policy,P09_ert_gate,P10_taupe_gate,P11_rh_gate,P12_other_hm_gate,P13_perm_endpoint_gate,P14_cte_confirmation,P15_conditional_field_stability,P16_final_field_decision",
    )

    add_row(
        rows,
        question_id="Q22_time_dependency_healing",
        question_area="Time dependency",
        representative_question="When should self-healing or time-dependent permeability be introduced?",
        resolution_status="deferred_not_current_objective",
        current_answer=(
            "No current local evidence separates temporal healing from spatial heterogeneity, EDZ damage, "
            "bedding anisotropy, and unresolved observation gates."
        ),
        local_evidence=(
            f"objective_completion_state={objective.get('completion_state')}; "
            f"partial_requirements={objective.get('partial_requirement_ids', [])}; "
            "active runs remain deterministic candidate/sampler evidence, not a time-dependent inversion."
        ),
        remaining_action="Revisit only after a final residual policy, accepted boundary/stream gates, and a stable field objective exist.",
        model_consequence="Do not add time-dependent permeability parameters to the frozen-source first-stage workflow.",
        authoritative_artifacts="inversion_workflow/objective_readiness_audit.md; measurement_chapter.tex",
        related_ids="time_dependency,self_healing",
    )

    frame = pd.DataFrame(rows).sort_values("question_id").reset_index(drop=True)
    status_counts = frame["resolution_status"].value_counts().sort_index().to_dict()
    externally_blocked = int(
        frame["resolution_status"].isin(
            ["external_provider_response_required", "waiting_user_send_and_provider_response"]
        ).sum()
    )
    internal_decision = int(
        frame["resolution_status"].isin(
            [
                "internal_policy_decision_required",
                "internal_policy_after_calibration",
                "internal_policy_with_provider_confirmation",
                "not_ready_final_decision_required",
            ]
        ).sum()
    )
    resolved = int(frame["resolution_status"].str.startswith("resolved").sum())
    summary = {
        "status": "open_question_resolution_matrix_generated",
        "row_count": int(frame.shape[0]),
        "resolution_status_counts": status_counts,
        "resolved_or_current_scope_count": resolved,
        "external_or_send_response_required_count": externally_blocked,
        "internal_policy_or_final_decision_count": internal_decision,
        "open_questions_source_heading_count": heading_count(Path("../cda_knowledge_base/open_questions.md")),
        "open_questions_source_bullet_count": bullet_count(Path("../cda_knowledge_base/open_questions.md")),
        "report_active_unresolved_marker_count": as_int(report.get("active_report_unresolved_marker_count")),
        "citation_missing_or_weak_locator_count": as_int(citations.get("missing_or_weak_locator_count")),
        "citation_missing_bib_entry_count": as_int(citations.get("missing_bib_entry_count")),
        "traceability_all_observations_traceable": bool(traceability.get("all_observations_traceable", False)),
        "external_blocker_open_count": as_int(external.get("open_blocker_count")),
        "external_blocker_unsent_count": as_int(external.get("unsent_blocker_count")),
        "external_blocker_missing_response_count": as_int(external.get("missing_response_blocker_count")),
        "local_gate_possible_closure_evidence_count": as_int(local_recovery.get("possible_closure_evidence_count")),
        "download_gate_possible_closure_evidence_count": as_int(download_recovery.get("possible_closure_evidence_count")),
        "nmr_final_policy_selected": bool(nmr.get("final_nmr_policy_selected", False)),
        "permeability_current_report_policy": permeability.get("current_report_policy"),
        "permeability_same_support_batch_executable_now": bool(
            permeability.get("same_support_active_objective_batch_executable_now", False)
        ),
        "permeability_support_conflict_spatial_audit_status": permeability_support_conflict.get("status"),
        "permeability_support_conflict_spatial_active_support_cell_count": as_int(
            permeability_support_conflict.get("active_support_cell_count")
        ),
        "permeability_support_conflict_spatial_repeated_support_cell_count": as_int(
            permeability_support_conflict.get("repeated_support_cell_count")
        ),
        "permeability_support_conflict_spatial_range_ge_2_log10_cell_count": as_int(
            permeability_support_conflict.get("support_cells_observed_range_ge_2_log10")
        ),
        "permeability_support_conflict_spatial_configured_scalar_conflict_cell_count": as_int(
            permeability_support_conflict.get("configured_scalar_range_conflict_cell_count")
        ),
        "permeability_support_conflict_spatial_top_conflict_cell": permeability_support_conflict.get(
            "top_conflict_cell", {}
        ),
        "final_promotion_decision": final_promotion.get("promotion_decision"),
        "current_field_final_decision": final_promotion.get("current_field_final_decision"),
        "final_objective_pending_or_not_ready_decision_count": as_int(
            final_decision.get("pending_or_not_ready_decision_count")
        ),
        "final_objective_include_exclude_unblocks_promotion": bool(
            final_recommend.get("final_promotion_unblocked_by_this_packet", False)
        ),
        "final_objective_no_new_evidence_closeout_draft_status": final_no_new.get("status"),
        "final_objective_no_new_evidence_closeout_draft_count": as_int(
            final_no_new.get("draft_decision_count")
        ),
        "final_objective_no_new_evidence_closeout_draft_requires_approval": bool(
            final_no_new.get("requires_user_or_modelling_team_approval", False)
        ),
        "final_objective_no_new_evidence_closeout_draft_records_decisions": bool(
            final_no_new.get("records_actual_decisions", False)
        ),
        "final_objective_no_new_evidence_closeout_draft_promotes_field": bool(
            final_no_new.get("promotes_current_field", False)
        ),
        "final_objective_no_new_evidence_closeout_draft_unblocks_promotion": bool(
            final_no_new.get("final_promotion_unblocked_by_this_draft", False)
        ),
        "final_objective_no_new_evidence_closeout_draft_would_select_scenario": final_no_new.get(
            "would_select_scenario_if_all_rows_approved_and_audits_rerun"
        ),
        "final_objective_no_new_evidence_closeout_draft_would_select_winner": final_no_new.get(
            "would_select_winner_if_all_rows_approved_and_audits_rerun"
        ),
        "final_objective_no_new_evidence_acceptance_record_template_status": final_acceptance_template.get("status"),
        "final_objective_no_new_evidence_acceptance_record_template_rows": as_int(
            final_acceptance_template.get("template_row_count")
        ),
        "final_objective_no_new_evidence_acceptance_record_template_approval_rows_recorded": as_int(
            final_acceptance_template.get("approval_rows_recorded")
        ),
        "final_objective_no_new_evidence_acceptance_record_template_ready_to_apply": bool(
            final_acceptance_template.get("ready_to_apply_decisions", False)
        ),
        "permeability_likelihood_policy_acceptance_record_template_status": (
            permeability_acceptance_template.get("status")
        ),
        "permeability_likelihood_policy_acceptance_record_template_rows": as_int(
            permeability_acceptance_template.get("template_row_count")
        ),
        "permeability_likelihood_policy_acceptance_record_template_primary_policy_approvals_recorded": as_int(
            permeability_acceptance_template.get("primary_policy_approval_rows_recorded")
        ),
        "permeability_likelihood_policy_acceptance_record_template_primary_policy_approvals_required": as_int(
            permeability_acceptance_template.get("primary_policy_approval_rows_required")
        ),
        "permeability_likelihood_policy_acceptance_record_template_ready_to_apply": bool(
            permeability_acceptance_template.get("ready_to_apply_policy", False)
        ),
        "nmr_final_residual_policy_acceptance_record_template_status": nmr_acceptance_template.get("status"),
        "nmr_final_residual_policy_acceptance_record_template_rows": as_int(
            nmr_acceptance_template.get("template_row_count")
        ),
        "nmr_final_residual_policy_acceptance_record_template_primary_policy_approvals_recorded": as_int(
            nmr_acceptance_template.get("primary_policy_approval_rows_recorded")
        ),
        "nmr_final_residual_policy_acceptance_record_template_primary_policy_approvals_required": as_int(
            nmr_acceptance_template.get("primary_policy_approval_rows_required")
        ),
        "nmr_final_residual_policy_acceptance_record_template_ready_to_apply": bool(
            nmr_acceptance_template.get("ready_to_apply_policy", False)
        ),
        "next_action": (
            "Use this matrix as the orientation layer: resolved rows need only refreshes after new evidence; "
            "external rows need draft sending and provider-response filing; internal rows need explicit "
            "modelling-team choices before final promotion, including whether to accept or reject the "
            "conservative no-new-evidence closeout draft."
        ),
        "source_artifacts": [
            "cda_knowledge_base/open_questions.md",
            "inversion_workflow/report_open_comment_audit_summary.json",
            "Library/citation_locator_audit_summary.json",
            "inversion_workflow/measurement_report_traceability_audit_summary.json",
            "inversion_workflow/final_inversion_promotion_checklist_summary.json",
            "inversion_workflow/external_blocker_dashboard_summary.json",
            "inversion_workflow/final_objective_decision_register.csv",
            "inversion_workflow/measurement_gate_closure_request.csv",
            "inversion_workflow/final_objective_include_exclude_recommendations_summary.json",
            "inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json",
            "inversion_workflow/final_objective_no_new_evidence_acceptance_record_template_summary.json",
            "inversion_workflow/permeability_likelihood_support_recommendations_summary.json",
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json",
            "inversion_workflow/nmr_final_residual_policy_gate_summary.json",
            "inversion_workflow/nmr_final_residual_policy_acceptance_record_template_summary.json",
        ],
    }
    return frame, summary


def escape_table_cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Open Question Resolution Matrix",
        "",
        "This matrix consolidates the open-question notes, report-comment audit,",
        "measurement gates, citation/source checks, and final-promotion trackers.",
        "It distinguishes locally resolved questions from external provider gates and",
        "internal modelling decisions.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Rows: {summary['row_count']}",
        f"- Resolution status counts: {summary['resolution_status_counts']}",
        f"- Locally resolved/current-scope rows: {summary['resolved_or_current_scope_count']}",
        f"- External or send/response rows: {summary['external_or_send_response_required_count']}",
        f"- Internal policy/final-decision rows: {summary['internal_policy_or_final_decision_count']}",
        f"- Active report unresolved markers: {summary['report_active_unresolved_marker_count']}",
        f"- Citation missing/weak locators: {summary['citation_missing_or_weak_locator_count']}",
        f"- Citation missing BibTeX entries: {summary['citation_missing_bib_entry_count']}",
        f"- Final promotion decision: `{summary['final_promotion_decision']}`",
        f"- No-new-evidence closeout draft rows: {summary['final_objective_no_new_evidence_closeout_draft_count']}",
        f"- No-new-evidence draft records decisions: `{summary['final_objective_no_new_evidence_closeout_draft_records_decisions']}`",
        f"- No-new-evidence draft promotes field: `{summary['final_objective_no_new_evidence_closeout_draft_promotes_field']}`",
        f"- No-new-evidence acceptance-template rows approved: {summary['final_objective_no_new_evidence_acceptance_record_template_approval_rows_recorded']}/{summary['final_objective_no_new_evidence_acceptance_record_template_rows']}",
        f"- No-new-evidence acceptance-template ready to apply: `{summary['final_objective_no_new_evidence_acceptance_record_template_ready_to_apply']}`",
        f"- Permeability policy acceptance-template primary approvals: {summary['permeability_likelihood_policy_acceptance_record_template_primary_policy_approvals_recorded']}/{summary['permeability_likelihood_policy_acceptance_record_template_primary_policy_approvals_required']}",
        f"- Permeability policy acceptance-template ready to apply: `{summary['permeability_likelihood_policy_acceptance_record_template_ready_to_apply']}`",
        (
            "- Permeability support-conflict active/repeated/range>=2 cells: "
            f"{summary['permeability_support_conflict_spatial_active_support_cell_count']}/"
            f"{summary['permeability_support_conflict_spatial_repeated_support_cell_count']}/"
            f"{summary['permeability_support_conflict_spatial_range_ge_2_log10_cell_count']}"
        ),
        f"- NMR policy acceptance-template primary approvals: {summary['nmr_final_residual_policy_acceptance_record_template_primary_policy_approvals_recorded']}/{summary['nmr_final_residual_policy_acceptance_record_template_primary_policy_approvals_required']}",
        f"- NMR policy acceptance-template ready to apply: `{summary['nmr_final_residual_policy_acceptance_record_template_ready_to_apply']}`",
        "",
        "## Interpretation",
        "",
        "The open questions are no longer loose report comments.  They are now split into",
        "closed local documentation/source questions, external evidence gates, and explicit",
        "modelling-team decisions.  The current field remains an active-objective incumbent",
        "because the remaining external and internal rows have not been closed or explicitly",
        "excluded from the final objective.",
        "",
        "## Matrix",
        "",
        "| ID | Area | Status | Current answer | Remaining action | Model consequence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{escape_table_cell(row['question_id'])}`",
                    escape_table_cell(row["question_area"]),
                    f"`{escape_table_cell(row['resolution_status'])}`",
                    escape_table_cell(row["current_answer"]),
                    escape_table_cell(row["remaining_action"]),
                    escape_table_cell(row["model_consequence"]),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Evidence Pointers", ""])
    for _, row in frame.iterrows():
        lines.append(
            f"- `{row['question_id']}`: {row['representative_question']} "
            f"Artifacts: {row['authoritative_artifacts']}. Evidence: {row['local_evidence']}"
        )

    lines.extend(["", "## Next Action", "", summary["next_action"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for source in paths:
        if not source.exists():
            continue
        target = catalogue_dir / source.name
        shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    frame, summary = build_rows(args)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)

    frame.to_csv(args.output_csv, index=False)
    write_markdown(args.output_md, frame, summary)
    args.kb_output_md.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.output_md, args.kb_output_md)

    copies = copy_outputs(args.catalogue_dir, [args.output_csv, args.output_md])
    copies.append({"source": str(args.output_md), "catalogue_copy": str(args.kb_output_md)})
    summary["catalogue_copies"] = copies
    summary["generated_files"] = [
        str(args.output_csv),
        str(args.output_json),
        str(args.output_md),
        str(args.kb_output_md),
    ]
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    summary["catalogue_copies"] = copy_outputs(args.catalogue_dir, [args.output_csv, args.output_json, args.output_md])
    summary["catalogue_copies"].append({"source": str(args.output_md), "catalogue_copy": str(args.kb_output_md)})
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    copy_outputs(args.catalogue_dir, [args.output_json])


if __name__ == "__main__":
    main()
