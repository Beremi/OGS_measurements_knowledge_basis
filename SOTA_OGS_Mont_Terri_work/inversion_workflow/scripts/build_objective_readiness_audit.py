#!/usr/bin/env python3
"""Audit current artifacts against the full report/model/inversion objective."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


STATUS_RANK = {
    "achieved": 0,
    "achieved_with_tracked_caveats": 1,
    "ready_pending_external_execution": 2,
    "partial": 3,
    "blocked_external": 4,
    "incomplete": 5,
    "missing": 6,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/objective_readiness_audit.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/objective_readiness_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/objective_readiness_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional measurement-catalogue derived_files directory to receive audit copies.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def file_exists(path: str | Path) -> bool:
    return Path(path).exists()


def file_nonempty(path: str | Path) -> bool:
    candidate = Path(path)
    return candidate.is_file() and candidate.stat().st_size > 0


def count_regex(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return len(re.findall(pattern, path.read_text(encoding="utf-8", errors="ignore"), flags=re.MULTILINE))


def log_is_clean(log_path: Path, blg_path: Path) -> bool:
    patterns = [
        r"LaTeX Warning",
        r"Package .*Warning",
        r"undefined references",
        r"Citation .* undefined",
        r"Fatal",
        r"! LaTeX Error",
        r"Overfull",
        r"Underfull",
    ]
    text = ""
    for path in [log_path, blg_path]:
        if path.exists():
            text += "\n" + path.read_text(encoding="utf-8", errors="ignore")
    return not any(re.search(pattern, text) for pattern in patterns)


def pdf_pages_from_log(log_path: Path) -> int | None:
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"Output written on main\.pdf \((\d+) pages", text)
    if not match:
        return None
    return int(match.group(1))


def read_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return int(pd.read_csv(path, usecols=[0]).shape[0])


def read_best_result_row(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if frame.empty or "total_active_objective_value" not in frame.columns:
        return {}
    frame = frame.copy()
    frame["total_active_objective_value"] = pd.to_numeric(frame["total_active_objective_value"], errors="coerce")
    return frame.sort_values("total_active_objective_value", na_position="last").iloc[0].to_dict()


def read_search_summaries(pattern: str) -> list[dict[str, Any]]:
    summaries = []
    for path in sorted(Path().glob(pattern)):
        summary = read_json(path)
        if summary:
            summary["_summary_path"] = str(path)
            summaries.append(summary)
    return summaries


def combined_search_best(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    best_rows = [summary.get("best_candidate", {}) for summary in summaries if summary.get("best_candidate")]
    if not best_rows:
        return {}
    return min(
        best_rows,
        key=lambda row: float(row.get("total_active_objective_value", float("inf"))),
    )


def combined_search_count(summaries: list[dict[str, Any]]) -> int:
    return sum(int(summary.get("evaluated_candidate_count", 0) or 0) for summary in summaries)


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return dict(sorted(counts.items(), key=lambda item: STATUS_RANK.get(item[0], 99)))


def add_row(
    rows: list[dict[str, str]],
    *,
    requirement_id: str,
    requirement: str,
    status: str,
    evidence: str,
    remaining_work: str,
    authoritative_artifacts: str,
) -> None:
    rows.append(
        {
            "requirement_id": requirement_id,
            "requirement": requirement,
            "status": status,
            "evidence": evidence,
            "remaining_work": remaining_work,
            "authoritative_artifacts": authoritative_artifacts,
        }
    )


def summarize_source_audit(path: Path) -> dict[str, int | str]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    def number_after(label: str) -> int | None:
        match = re.search(re.escape(label) + r":\s*(\d+)", text)
        return int(match.group(1)) if match else None

    return {
        "cited_keys": number_after("Cited keys in the report") or 0,
        "missing_bib_entries": number_after("Cited keys missing from `opalinus_clay.bib`") or 0,
        "missing_unavailable_entries": number_after(
            "Cited blocked/fulltext-unavailable keys missing from `unavailable_fulltexts.md`"
        )
        or 0,
    }


def build_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    manifest = read_json(Path("inversion_workflow/observation_manifest_validation.json"))
    processed = read_json(Path("inversion_workflow/processed_observations/processed_observation_summary.json"))
    coverage = read_json(Path("inversion_workflow/measurement_operator_coverage_summary.json"))
    measurement_model_entry = read_json(Path("inversion_workflow/measurement_model_entry_matrix_summary.json"))
    traceability = read_json(Path("inversion_workflow/measurement_report_traceability_audit_summary.json"))
    measurement_content = read_json(Path("../cda_knowledge_base/measurements/measurement_content_deep_dive_summary.json"))
    likelihood = read_json(Path("inversion_workflow/measurement_likelihood_model_summary.json"))
    stream_gate_audit = read_json(Path("inversion_workflow/measurement_stream_activation_gate_audit_summary.json"))
    gate_closure_request = read_json(Path("inversion_workflow/measurement_gate_closure_request_summary.json"))
    internal_gate_decision = read_json(Path("inversion_workflow/internal_gate_decision_register_summary.json"))
    external_gate_request_pack = read_json(Path("inversion_workflow/external_gate_request_pack_summary.json"))
    external_gate_response_intake = read_json(Path("inversion_workflow/external_gate_response_intake_summary.json"))
    external_gate_dispatch = read_json(Path("inversion_workflow/external_gate_dispatch_audit_summary.json"))
    gmail_live_state = read_json(Path("inversion_workflow/gmail_gate_live_state_audit_summary.json"))
    external_blocker_dashboard = read_json(Path("inversion_workflow/external_blocker_dashboard_summary.json"))
    local_gate_recovery = read_json(Path("inversion_workflow/local_gate_recovery_audit_summary.json"))
    download_gate_recovery = read_json(Path("inversion_workflow/download_gate_recovery_audit_summary.json"))
    cte_confirmation = read_json(Path("inversion_workflow/cte_confirmation_request_summary.json"))
    report_open_comment = read_json(Path("inversion_workflow/report_open_comment_audit_summary.json"))
    ogs_formulation = read_json(Path("inversion_workflow/ogs_formulation_consistency_audit_summary.json"))
    ogs_env = read_json(Path("inversion_workflow/OGS_ENVIRONMENT_AUDIT.json"))
    ogs_execution = read_json(Path("inversion_workflow/runs/direct_fit_observation_run/OGS_EXECUTION_STATUS.json"))
    ogs_run_input = read_json(Path("inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.json"))
    ogs_sampling = read_json(Path("inversion_workflow/runs/direct_fit_observation_run/ogs_state_sampling_summary.json"))
    direct_state_summary = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation_summary.json")
    )
    taupe_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_summary.json")
    )
    taupe_discrimination = read_json(Path("inversion_workflow/taupe_candidate_discrimination_summary.json"))
    taupe_weight_sensitivity = read_json(Path("inversion_workflow/taupe_series_weight_sensitivity_summary.json"))
    ert_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json")
    )
    ert_discrimination = read_json(Path("inversion_workflow/ert_candidate_discrimination_summary.json"))
    ert_support_sensitivity = read_json(Path("inversion_workflow/ert_support_sensitivity_summary.json"))
    nmr_bias_sensitivity = read_json(Path("inversion_workflow/nmr_candidate_bias_sensitivity_summary.json"))
    nmr_objective_decision = read_json(Path("inversion_workflow/nmr_objective_decision_summary.json"))
    nmr_trend_activation = read_json(Path("inversion_workflow/nmr_trend_anomaly_active_objective_summary.json"))
    nmr_final_policy_gate = read_json(Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"))
    nmr_final_policy_acceptance_template = read_json(
        Path("inversion_workflow/nmr_final_residual_policy_acceptance_record_template_summary.json")
    )
    cross_stream_scorecard = read_json(Path("inversion_workflow/cross_stream_candidate_scorecard_summary.json"))
    rh_candidate_curves = read_json(
        Path("inversion_workflow/processed_observations/rh_boundary_candidate_curve_summary.json")
    )
    rh_uncertainty = read_json(
        Path("inversion_workflow/processed_observations/rh_boundary_uncertainty_summary.json")
    )
    other_hm_source_audit = read_json(
        Path("inversion_workflow/processed_observations/other_hm_numeric_source_audit_summary.json")
    )
    citation_locator = read_json(Path("Library/citation_locator_audit_summary.json"))
    release_plan = read_json(Path("inversion_workflow/inversion_parameter_release_plan_summary.json"))
    release_gate = read_json(Path("inversion_workflow/inversion_release_gate_audit.json"))
    frozen_model_measurement = read_json(
        Path("inversion_workflow/frozen_model_measurement_inclusion_audit_summary.json")
    )
    candidate_set = read_json(
        Path("inversion_workflow/runs/regularized_ogs_candidate_set/REGULARIZED_OGS_CANDIDATE_SET.json")
    )
    adaptive_search = read_json(
        Path("inversion_workflow/runs/adaptive_combined_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    local_refinement_search = read_json(
        Path("inversion_workflow/runs/local_refinement_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    local_bracketing_search = read_json(
        Path("inversion_workflow/runs/local_bracketing_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    optimizer_search = read_json(
        Path("inversion_workflow/runs/optimizer_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    continuous_search = read_json(
        Path("inversion_workflow/runs/continuous_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    broad_continuous_search = read_json(
        Path("inversion_workflow/runs/broad_continuous_001_search/INVERSION_SEARCH_SUMMARY.json")
    )
    broad_continuous_cumulative_best = read_best_result_row(
        Path("inversion_workflow/runs/continuous_inversion_loop/broad_continuous_cumulative_search_results.csv")
    )
    lower_support_continuous_search = read_json(
        Path("inversion_workflow/runs/lower_support_continuous_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    continuous_loop_summary = read_json(
        Path("inversion_workflow/runs/continuous_inversion_loop/latest_loop_summary.json")
    )
    adaptive_plan = read_json(
        Path("inversion_workflow/runs/adaptive_combined_candidate_plan/ADAPTIVE_COMBINED_CANDIDATE_PLAN.json")
    )
    optimizer_proposal = read_json(
        Path("inversion_workflow/runs/bayesian_candidate_proposal/OPTIMIZER_CANDIDATE_PROPOSAL.json")
    )
    continuous_plan = read_json(
        Path("inversion_workflow/runs/continuous_bayesian_candidate_plan/CONTINUOUS_CANDIDATE_PLAN.json")
    )
    anisotropy_plan = read_json(
        Path("inversion_workflow/runs/anisotropy_sensitivity_plan/ANISOTROPY_SENSITIVITY_PLAN.json")
    )
    local_basis_plan = read_json(
        Path("inversion_workflow/runs/local_basis_sampler_plan/LOCAL_BASIS_SAMPLER_PLAN.json")
    )
    local_anisotropy_plan = read_json(
        Path("inversion_workflow/runs/local_anisotropy_sampler_plan/LOCAL_ANISOTROPY_SAMPLER_PLAN.json")
    )
    local_basis_search = read_json(
        Path("inversion_workflow/runs/local_basis_sampler_candidate_search/INVERSION_SEARCH_SUMMARY.json")
    )
    production_search_summaries = read_search_summaries(
        "inversion_workflow/runs/production_sampler*_candidate_search/INVERSION_SEARCH_SUMMARY.json"
    )
    production_search = production_search_summaries[0] if production_search_summaries else {}
    production_sampler = read_json(
        Path("inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_CONVERGENCE.json")
    )
    production_decision = read_json(
        Path("inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.json")
    )
    cross_stream_hybrid = read_json(
        Path("inversion_workflow/runs/cross_stream_hybrid_field_plan/CROSS_STREAM_HYBRID_FIELD_PLAN.json")
    )
    structural_edz_plan = read_json(
        Path("inversion_workflow/runs/structural_edz_field_family_plan/STRUCTURAL_EDZ_FIELD_FAMILY_PLAN.json")
    )
    permeability_residual_audit = read_json(
        Path("inversion_workflow/permeability_residual_conflict_audit_summary.json")
    )
    permeability_policy_audit = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json")
    )
    permeability_support_lower_bound = read_json(
        Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json")
    )
    permeability_support_spatial = read_json(
        Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json")
    )
    permeability_policy_decision = read_json(
        Path("inversion_workflow/permeability_likelihood_decision_request_summary.json")
    )
    permeability_outlier_disposition = read_json(
        Path("inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json")
    )
    permeability_policy_rerank = read_json(
        Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json")
    )
    permeability_policy_winner_cross_stream = read_json(
        Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json")
    )
    permeability_next_field_fit_gate = read_json(
        Path("inversion_workflow/permeability_next_field_fit_gate_summary.json")
    )
    permeability_likelihood_support_recommendations = read_json(
        Path("inversion_workflow/permeability_likelihood_support_recommendations_summary.json")
    )
    permeability_likelihood_policy_acceptance_template = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    current_field_package = read_json(Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"))
    current_field_visual = read_json(
        Path("inversion_workflow/current_permeability_field/visual_inspection/current_field_visual_inspection_summary.json")
    )
    current_field_selection = read_json(Path("inversion_workflow/current_field_selection_audit_summary.json"))
    current_field_reproducibility = read_json(
        Path("inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.json")
    )
    conditional_field_scenarios = read_json(
        Path("inversion_workflow/conditional_field_selection_scenarios_summary.json")
    )
    conditional_field_package = read_json(
        Path("inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES_SUMMARY.json")
    )
    conditional_field_difference = read_json(
        Path("inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.json")
    )
    final_promotion_checklist = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    final_closeout_playbook = read_json(Path("inversion_workflow/final_inversion_closeout_playbook_summary.json"))
    gmail_draft_review = read_json(Path("inversion_workflow/gmail_draft_send_review_packet_summary.json"))
    final_objective_decisions = read_json(Path("inversion_workflow/final_objective_decision_register_summary.json"))
    final_objective_scenario_matrix = read_json(
        Path("inversion_workflow/final_objective_scenario_matrix_summary.json")
    )
    final_objective_recommendations = read_json(
        Path("inversion_workflow/final_objective_include_exclude_recommendations_summary.json")
    )
    final_objective_no_new_evidence_draft = read_json(
        Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json")
    )
    final_objective_no_new_acceptance_template = read_json(
        Path("inversion_workflow/final_objective_no_new_evidence_acceptance_record_template_summary.json")
    )
    open_question_resolution = read_json(
        Path("inversion_workflow/open_question_resolution_matrix_summary.json")
    )
    nmr_trend_followup = read_json(
        Path("inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json")
    )
    candidate_best = candidate_set.get("best_current_candidate", {})
    candidate_set_executed = (
        candidate_set.get("ogs_mode") == "execute"
        and int(candidate_best.get("state_active_objective_rows", 0) or 0) > 0
        and int(candidate_best.get("active_component_count", 0) or 0) >= 2
    )
    adaptive_top_proposals = adaptive_plan.get("top_proposals", [])
    adaptive_top_candidate = (
        adaptive_top_proposals[0].get("candidate_id")
        if adaptive_top_proposals and isinstance(adaptive_top_proposals[0], dict)
        else None
    )
    optimizer_top_proposals = optimizer_proposal.get("top_proposals", [])
    optimizer_top_candidate = (
        optimizer_top_proposals[0].get("candidate_id")
        if optimizer_top_proposals and isinstance(optimizer_top_proposals[0], dict)
        else None
    )
    continuous_top_proposals = continuous_plan.get("top_proposals", [])
    continuous_top_candidate = (
        continuous_top_proposals[0].get("candidate_id")
        if continuous_top_proposals and isinstance(continuous_top_proposals[0], dict)
        else None
    )
    anisotropy_best = anisotropy_plan.get("best_candidate", {})
    local_basis_best = local_basis_plan.get("best_candidate", {})
    local_anisotropy_best = local_anisotropy_plan.get("best_candidate", {})
    local_anisotropy_candidate_count = int(local_anisotropy_plan.get("candidate_count", 0) or 0)
    local_anisotropy_anchor_count = int(local_anisotropy_plan.get("unique_anchor_cells", 0) or 0)
    local_anisotropy_best_delta = local_anisotropy_plan.get("best_direct_delta_vs_baseline")
    local_basis_search_best = local_basis_search.get("best_candidate", {})
    local_basis_search_best_id = local_basis_search_best.get("source_candidate_id") or "not_executed"
    local_basis_search_best_objective = (
        local_basis_search_best.get("total_active_objective_value")
        if local_basis_search_best.get("total_active_objective_value") is not None
        else "not_executed"
    )
    production_search_best = combined_search_best(production_search_summaries)
    production_search_best_id = production_search_best.get("source_candidate_id") or "not_executed"
    production_search_best_objective = (
        production_search_best.get("total_active_objective_value")
        if production_search_best.get("total_active_objective_value") is not None
        else "not_executed"
    )
    production_top_proposals = production_sampler.get("top_proposals", [])
    production_top_candidate = (
        production_top_proposals[0].get("candidate_id")
        if production_top_proposals and isinstance(production_top_proposals[0], dict)
        else None
    )
    production_top_family = (
        production_top_proposals[0].get("candidate_family")
        if production_top_proposals and isinstance(production_top_proposals[0], dict)
        else None
    )
    cross_stream_hybrid_best = cross_stream_hybrid.get("best_direct_candidate", {})
    cross_stream_hybrid_candidate_count = int(cross_stream_hybrid.get("candidate_count", 0) or 0)
    cross_stream_hybrid_target_count = int(cross_stream_hybrid.get("target_run_count", 0) or 0)
    cross_stream_hybrid_best_delta = cross_stream_hybrid.get("best_direct_delta_vs_active")
    structural_edz_status = structural_edz_plan.get("status")
    structural_edz_best = structural_edz_plan.get("best_direct_candidate", {})
    structural_edz_candidate_count = int(structural_edz_plan.get("candidate_count", 0) or 0)
    structural_edz_improving_count = int(structural_edz_plan.get("improving_candidate_count", 0) or 0)
    structural_edz_best_delta = structural_edz_plan.get("best_direct_delta_vs_active")
    structural_edz_best_family = structural_edz_best.get("family")
    structural_edz_support_counts = structural_edz_plan.get("support_feature_counts", {})
    permeability_residual_status = permeability_residual_audit.get("status")
    permeability_residual_active_rows = int(permeability_residual_audit.get("active_direct_rows", 0) or 0)
    permeability_residual_large_ge1 = int(
        permeability_residual_audit.get("large_residual_active_rows_ge_1_log10", 0) or 0
    )
    permeability_residual_very_large_ge2 = int(
        permeability_residual_audit.get("very_large_residual_active_rows_ge_2_log10", 0) or 0
    )
    permeability_residual_outside_range = int(
        permeability_residual_audit.get("active_rows_outside_configured_scalar_range", 0) or 0
    )
    permeability_residual_repeated_cells = int(
        permeability_residual_audit.get("support_cells_with_repeated_active_rows", 0) or 0
    )
    permeability_residual_cell_conflicts = int(
        permeability_residual_audit.get("support_cells_with_observed_range_ge_1_log10", 0) or 0
    )
    permeability_policy_status = permeability_policy_audit.get("status")
    permeability_policy_current_objective = permeability_policy_audit.get("current_gaussian_objective")
    permeability_policy_support_mean_objective = permeability_policy_audit.get("support_mean_unit_objective")
    permeability_policy_support_median_objective = permeability_policy_audit.get("support_median_unit_objective")
    permeability_policy_top10_loss_share = permeability_policy_audit.get("row_loss_top_10_share")
    permeability_policy_conflict_groups = int(
        permeability_policy_audit.get("support_groups_with_observed_range_ge_1_log10", 0) or 0
    )
    permeability_policy_repeated_groups = int(
        permeability_policy_audit.get("support_groups_with_repeated_rows", 0) or 0
    )
    permeability_support_lb_status = permeability_support_lower_bound.get("status")
    permeability_support_lb_current_objective = permeability_support_lower_bound.get("current_row_gaussian_objective")
    permeability_support_lb_lower_objective = permeability_support_lower_bound.get("single_support_lower_bound_objective")
    permeability_support_lb_reducible_gap = permeability_support_lower_bound.get("same_support_reducible_objective_gap")
    permeability_support_lb_reducible_fraction = permeability_support_lower_bound.get(
        "same_support_reducible_objective_fraction"
    )
    permeability_support_lb_at_bound = permeability_support_lower_bound.get("current_at_single_support_lower_bound")
    permeability_support_lb_groups = int(permeability_support_lower_bound.get("support_group_count", 0) or 0)
    permeability_support_lb_repeated_groups = int(
        permeability_support_lower_bound.get("repeated_support_group_count", 0) or 0
    )
    permeability_support_lb_conflict_ge2 = int(
        permeability_support_lower_bound.get("support_groups_with_observed_range_ge_2_log10", 0) or 0
    )
    permeability_support_lb_top2_share = permeability_support_lower_bound.get("top_2_support_group_loss_share")
    permeability_support_lb_top5_share = permeability_support_lower_bound.get("top_5_support_group_loss_share")
    permeability_support_spatial_status = permeability_support_spatial.get("status")
    permeability_support_spatial_mesh_cells = int(permeability_support_spatial.get("mesh_cell_count", 0) or 0)
    permeability_support_spatial_active_cells = int(
        permeability_support_spatial.get("active_support_cell_count", 0) or 0
    )
    permeability_support_spatial_repeated_cells = int(
        permeability_support_spatial.get("repeated_support_cell_count", 0) or 0
    )
    permeability_support_spatial_ge1 = int(
        permeability_support_spatial.get("support_cells_observed_range_ge_1_log10", 0) or 0
    )
    permeability_support_spatial_ge2 = int(
        permeability_support_spatial.get("support_cells_observed_range_ge_2_log10", 0) or 0
    )
    permeability_support_spatial_configured_conflict = int(
        permeability_support_spatial.get("configured_scalar_range_conflict_cell_count", 0) or 0
    )
    permeability_support_spatial_top = permeability_support_spatial.get("top_conflict_cell", {})
    permeability_policy_decision_status = permeability_policy_decision.get("status")
    permeability_policy_decision_recommended = permeability_policy_decision.get("recommended_current_report_policy")
    permeability_outlier_disposition_status = permeability_outlier_disposition.get("status")
    permeability_outlier_disposition_rows = int(permeability_outlier_disposition.get("outlier_row_count", 0) or 0)
    permeability_outlier_disposition_groups = int(
        permeability_outlier_disposition.get("unique_physical_outlier_group_count", 0) or 0
    )
    permeability_outlier_disposition_max_excess = permeability_outlier_disposition.get("max_range_excess_log10")
    permeability_outlier_disposition_support_range = permeability_outlier_disposition.get(
        "max_same_support_observed_range_log10"
    )
    permeability_outlier_bounds_release_now = permeability_outlier_disposition.get("bounds_release_recommended_now")
    permeability_outlier_tensor_release_now = permeability_outlier_disposition.get(
        "tensor_shape_release_recommended_now"
    )
    permeability_policy_rerank_status = permeability_policy_rerank.get("status")
    permeability_policy_rerank_scored = int(permeability_policy_rerank.get("candidate_fields_scored", 0) or 0)
    permeability_policy_rerank_best_ties = int(permeability_policy_rerank.get("current_gaussian_best_tie_count", 0) or 0)
    permeability_policy_rerank_current_accepted_tied = permeability_policy_rerank.get(
        "current_accepted_in_current_gaussian_best_tie_set"
    )
    permeability_policy_rerank_alt_outside = int(
        permeability_policy_rerank.get("alternate_policy_winner_outside_current_gaussian_best_set_count", 0) or 0
    )
    permeability_policy_winner_cross_status = permeability_policy_winner_cross_stream.get("status")
    permeability_policy_winner_cross_scorecard_rows = int(
        permeability_policy_winner_cross_stream.get("policy_winner_rows_with_cross_stream_scorecard", 0) or 0
    )
    permeability_policy_winner_cross_direct_only_rows = int(
        permeability_policy_winner_cross_stream.get("direct_only_policy_winner_rows", 0) or 0
    )
    permeability_policy_winner_cross_outside_direct_only_rows = int(
        permeability_policy_winner_cross_stream.get("outside_tie_direct_only_policy_winner_rows", 0) or 0
    )
    permeability_policy_winner_cross_row_gaussian_rank = permeability_policy_winner_cross_stream.get(
        "row_gaussian_representative_active_rank"
    )
    permeability_policy_winner_cross_current_rank = permeability_policy_winner_cross_stream.get(
        "current_accepted_active_rank"
    )
    permeability_next_gate_status = permeability_next_field_fit_gate.get("status")
    permeability_next_gate_recommendation = permeability_next_field_fit_gate.get("overall_recommendation")
    permeability_next_gate_count = int(permeability_next_field_fit_gate.get("gate_count", 0) or 0)
    permeability_next_gate_executable_now = permeability_next_field_fit_gate.get(
        "executable_same_support_active_objective_batch_now"
    )
    permeability_next_gate_status_counts = permeability_next_field_fit_gate.get("gate_status_counts", {})
    permeability_next_gate_current_policy = permeability_next_field_fit_gate.get("current_report_default_policy")
    permeability_support_recommendations_status = permeability_likelihood_support_recommendations.get("status")
    permeability_support_recommendations_count = int(
        permeability_likelihood_support_recommendations.get("recommendation_count", 0) or 0
    )
    permeability_support_recommendations_current_policy = permeability_likelihood_support_recommendations.get(
        "current_report_policy"
    )
    permeability_support_recommendations_at_lower_bound = permeability_likelihood_support_recommendations.get(
        "current_at_single_support_lower_bound"
    )
    permeability_support_recommendations_same_support_gap = permeability_likelihood_support_recommendations.get(
        "same_support_reducible_objective_gap"
    )
    permeability_support_recommendations_batch_executable = permeability_likelihood_support_recommendations.get(
        "same_support_active_objective_batch_executable_now"
    )
    permeability_support_recommendations_bounds_release_now = permeability_likelihood_support_recommendations.get(
        "bounds_release_recommended_now"
    )
    permeability_support_recommendations_tensor_release_now = permeability_likelihood_support_recommendations.get(
        "tensor_shape_release_recommended_now"
    )
    permeability_support_recommendations_unblocks_promotion = permeability_likelihood_support_recommendations.get(
        "final_promotion_unblocked_by_this_packet"
    )
    permeability_policy_acceptance_status = permeability_likelihood_policy_acceptance_template.get("status")
    permeability_policy_acceptance_rows = int(
        permeability_likelihood_policy_acceptance_template.get("template_row_count", 0) or 0
    )
    permeability_policy_acceptance_recorded = int(
        permeability_likelihood_policy_acceptance_template.get("primary_policy_approval_rows_recorded", 0) or 0
    )
    permeability_policy_acceptance_required = int(
        permeability_likelihood_policy_acceptance_template.get("primary_policy_approval_rows_required", 0) or 0
    )
    permeability_policy_acceptance_ready = permeability_likelihood_policy_acceptance_template.get(
        "ready_to_apply_policy"
    )
    permeability_policy_acceptance_records_decision = permeability_likelihood_policy_acceptance_template.get(
        "records_actual_decision"
    )
    permeability_policy_acceptance_changes_objective = permeability_likelihood_policy_acceptance_template.get(
        "changes_active_objective"
    )
    permeability_policy_acceptance_promotes_field = permeability_likelihood_policy_acceptance_template.get(
        "promotes_current_field"
    )
    permeability_policy_acceptance_same_support_executable = permeability_likelihood_policy_acceptance_template.get(
        "same_support_batch_executable_now"
    )
    current_field_status = current_field_package.get("status")
    current_field_run_id = current_field_package.get("run_id")
    current_field_deliverable_status = current_field_package.get("interpretation", {}).get("deliverable_status")
    current_field_mesh = current_field_package.get("packaged_mesh")
    current_field_stats_csv = current_field_package.get("stats_csv")
    current_field_summary = current_field_package.get("field", {})
    current_field_metrics = current_field_summary.get("field_metrics", {})
    current_field_cell_count = int(current_field_summary.get("triangle6_cell_count", 0) or 0)
    current_field_positive_cells = int(current_field_summary.get("positive_definite_cell_count", 0) or 0)
    current_field_nonpositive_cells = int(current_field_summary.get("non_positive_definite_cell_count", 0) or 0)
    current_field_max_asymmetry = current_field_summary.get("max_tensor_asymmetry_abs")
    current_field_anisotropy_p50 = current_field_metrics.get("k_eigen_ratio", {}).get("p50")
    current_field_theta_p50 = current_field_metrics.get("k_theta_deg_rd", {}).get("p50")
    current_field_porosity_p50 = current_field_metrics.get("n_rd", {}).get("p50")
    current_field_log10_kmin_p50 = current_field_metrics.get("log10_k_eigen_min", {}).get("p50")
    current_field_log10_kmax_p50 = current_field_metrics.get("log10_k_eigen_max", {}).get("p50")
    current_field_repro_status = current_field_reproducibility.get("status")
    current_field_repro_required_failures = int(
        current_field_reproducibility.get("required_failure_count", 0) or 0
    )
    current_field_repro_check_count = int(current_field_reproducibility.get("check_count", 0) or 0)
    current_field_repro_manifest_rows = int(current_field_reproducibility.get("manifest_row_count", 0) or 0)
    current_field_repro_run_input_files = int(
        current_field_reproducibility.get("run_input_snapshot_file_count", 0) or 0
    )
    current_field_repro_project_refs = int(current_field_reproducibility.get("project_reference_count", 0) or 0)
    current_field_repro_direct_rows = int(current_field_reproducibility.get("direct_used_rows", 0) or 0)
    current_field_repro_state_rows = int(current_field_reproducibility.get("state_used_rows", 0) or 0)
    current_field_repro_ready = (
        current_field_repro_status == "current_field_reproducibility_verified"
        and current_field_repro_required_failures == 0
    )
    current_field_visual_status = current_field_visual.get("status")
    current_field_visual_image_count = int(current_field_visual.get("image_count", 0) or 0)
    current_field_visual_positive_cells = int(current_field_visual.get("positive_definite_cells", 0) or 0)
    current_field_visual_geom_p50 = (
        current_field_visual.get("key_metrics", {}).get("log10_k_geom_m2", {}).get("p50")
    )
    current_field_visual_anchor_p50 = (
        current_field_visual.get("key_metrics", {}).get("local_basis_nearest_anchor_distance_m", {}).get("p50")
    )
    current_field_selection_status = current_field_selection.get("status")
    current_field_active_decision = current_field_selection.get("active_objective_decision")
    current_field_final_decision = current_field_selection.get("final_all_measurement_decision")
    current_field_selection_status_counts = current_field_selection.get("status_counts", {})
    current_field_selection_keys = current_field_selection.get("key_numbers", {})
    conditional_scenario_status = conditional_field_scenarios.get("status")
    conditional_scenario_count = int(conditional_field_scenarios.get("scenario_count", 0) or 0)
    conditional_scenario_unique_winners = int(conditional_field_scenarios.get("unique_winner_count", 0) or 0)
    conditional_scenario_current_wins = int(
        conditional_field_scenarios.get("current_field_winning_scenario_count", 0) or 0
    )
    conditional_scenario_final_decision = conditional_field_scenarios.get("final_decision")
    conditional_scenario_winners = conditional_field_scenarios.get("unique_winners", [])
    conditional_package_status = conditional_field_package.get("status")
    conditional_package_candidate_count = int(conditional_field_package.get("candidate_count", 0) or 0)
    conditional_package_output_dir = conditional_field_package.get("output_dir")
    conditional_package_stability = conditional_field_package.get("selection_stability")
    conditional_package_metric_evidence_rows = int(
        conditional_field_package.get("metric_evidence_row_count", 0) or 0
    )
    conditional_package_metric_evidence_missing = int(
        conditional_field_package.get("metric_evidence_missing_row_count", 0) or 0
    )
    conditional_difference_status = conditional_field_difference.get("status")
    conditional_difference_compared_count = int(conditional_field_difference.get("compared_candidate_count", 0) or 0)
    conditional_difference_cell_count = int(conditional_field_difference.get("cell_count", 0) or 0)
    conditional_difference_max_mean_abs = conditional_field_difference.get("max_candidate_mean_abs_delta_log10_k_geom")
    conditional_difference_max_gt_005 = conditional_field_difference.get("max_cells_abs_delta_gt_0p05")
    conditional_difference_max_gt_010 = conditional_field_difference.get("max_cells_abs_delta_gt_0p10")
    conditional_difference_largest_candidate = (
        conditional_field_difference.get("candidate_summaries", [{}])[0].get("run_id")
        if conditional_field_difference.get("candidate_summaries")
        else None
    )
    conditional_difference_markdown = conditional_field_difference.get("markdown")
    final_promotion_status = final_promotion_checklist.get("status")
    final_promotion_decision = final_promotion_checklist.get("promotion_decision")
    final_promotion_criterion_count = int(final_promotion_checklist.get("criterion_count", 0) or 0)
    final_promotion_status_counts = final_promotion_checklist.get("status_counts", {})
    final_promotion_open_criteria = final_promotion_checklist.get("open_criterion_ids", [])
    final_promotion_open_count = len(final_promotion_open_criteria)
    final_closeout_status = final_closeout_playbook.get("status")
    final_closeout_open_count = int(final_closeout_playbook.get("open_criterion_count", 0) or 0)
    final_closeout_external_count = int(final_closeout_playbook.get("external_closeout_count", 0) or 0)
    final_closeout_internal_count = int(final_closeout_playbook.get("internal_policy_closeout_count", 0) or 0)
    final_closeout_scenario_count = int(final_closeout_playbook.get("scenario_or_final_decision_count", 0) or 0)
    final_closeout_draft_ids = final_closeout_playbook.get("gmail_draft_ids", [])
    final_closeout_next_actions = final_closeout_playbook.get("next_actions", [])
    gmail_draft_review_status = gmail_draft_review.get("status")
    gmail_draft_review_count = int(gmail_draft_review.get("draft_count", 0) or 0)
    gmail_draft_review_unsent_count = int(gmail_draft_review.get("unsent_draft_count", 0) or 0)
    gmail_draft_review_ready_count = int(gmail_draft_review.get("ready_for_user_review_count", 0) or 0)
    gmail_draft_review_request_count = int(gmail_draft_review.get("request_count", 0) or 0)
    gmail_draft_review_ids = gmail_draft_review.get("draft_ids", [])
    final_objective_decision_status = final_objective_decisions.get("status")
    final_objective_decision_count = int(final_objective_decisions.get("decision_count", 0) or 0)
    final_objective_external_count = int(final_objective_decisions.get("external_stream_decision_count", 0) or 0)
    final_objective_internal_count = int(final_objective_decisions.get("internal_policy_decision_count", 0) or 0)
    final_objective_scenario_count = int(final_objective_decisions.get("scenario_or_final_decision_count", 0) or 0)
    final_objective_pending_count = int(final_objective_decisions.get("pending_or_not_ready_decision_count", 0) or 0)
    final_objective_exclusion_count = int(final_objective_decisions.get("explicit_exclusion_possible_count", 0) or 0)
    final_objective_decision_status_counts = final_objective_decisions.get("decision_status_counts", {})
    final_objective_scenario_status = final_objective_scenario_matrix.get("status")
    final_objective_scenario_option_count = int(final_objective_scenario_matrix.get("option_count", 0) or 0)
    final_objective_scenario_current_winning_count = int(
        final_objective_scenario_matrix.get("current_field_winning_option_count", 0) or 0
    )
    final_objective_scenario_unique_winner_count = int(
        final_objective_scenario_matrix.get("unique_winner_count", 0) or 0
    )
    final_objective_scenario_unscored_count = int(
        final_objective_scenario_matrix.get("unscored_future_option_count", 0) or 0
    )
    final_objective_scenario_non_likelihood_count = int(
        final_objective_scenario_matrix.get("not_final_likelihood_or_needs_new_policy_count", 0) or 0
    )
    final_objective_scenario_interpretation = final_objective_scenario_matrix.get("interpretation", [])
    final_objective_recommendation_status = final_objective_recommendations.get("status")
    final_objective_recommendation_count = int(final_objective_recommendations.get("recommendation_count", 0) or 0)
    final_objective_recommendation_external_count = int(
        final_objective_recommendations.get("external_measurement_or_provenance_recommendation_count", 0) or 0
    )
    final_objective_recommendation_internal_count = int(
        final_objective_recommendations.get("internal_policy_recommendation_count", 0) or 0
    )
    final_objective_recommendation_scenario_count = int(
        final_objective_recommendations.get("scenario_or_final_recommendation_count", 0) or 0
    )
    final_objective_recommendation_diagnostic_or_exclude_count = int(
        final_objective_recommendations.get("diagnostic_or_exclude_without_new_evidence_count", 0) or 0
    )
    final_objective_recommendation_waiver_not_recommended_count = int(
        final_objective_recommendations.get("waiver_not_recommended_count", 0) or 0
    )
    final_objective_recommendation_unblocks_promotion = bool(
        final_objective_recommendations.get("final_promotion_unblocked_by_this_packet", False)
    )
    final_objective_recommendation_current_label = final_objective_recommendations.get(
        "recommended_current_field_label"
    )
    final_objective_no_new_status = final_objective_no_new_evidence_draft.get("status")
    final_objective_no_new_count = int(
        final_objective_no_new_evidence_draft.get("draft_decision_count", 0) or 0
    )
    final_objective_no_new_external_count = int(
        final_objective_no_new_evidence_draft.get("external_or_provenance_draft_count", 0) or 0
    )
    final_objective_no_new_internal_count = int(
        final_objective_no_new_evidence_draft.get("internal_policy_draft_count", 0) or 0
    )
    final_objective_no_new_scenario_count = int(
        final_objective_no_new_evidence_draft.get("scenario_or_final_draft_count", 0) or 0
    )
    final_objective_no_new_requires_approval = bool(
        final_objective_no_new_evidence_draft.get("requires_user_or_modelling_team_approval", False)
    )
    final_objective_no_new_records_decisions = bool(
        final_objective_no_new_evidence_draft.get("records_actual_decisions", False)
    )
    final_objective_no_new_promotes_field = bool(
        final_objective_no_new_evidence_draft.get("promotes_current_field", False)
    )
    final_objective_no_new_unblocks_promotion = bool(
        final_objective_no_new_evidence_draft.get("final_promotion_unblocked_by_this_draft", False)
    )
    final_objective_no_new_scenario = final_objective_no_new_evidence_draft.get(
        "would_select_scenario_if_all_rows_approved_and_audits_rerun"
    )
    final_objective_no_new_winner = final_objective_no_new_evidence_draft.get(
        "would_select_winner_if_all_rows_approved_and_audits_rerun"
    )
    final_objective_no_new_current_winner = final_objective_no_new_evidence_draft.get(
        "current_field_is_winner_in_draft_scenario"
    )
    final_objective_no_new_acceptance_status = final_objective_no_new_acceptance_template.get("status")
    final_objective_no_new_acceptance_rows = int(
        final_objective_no_new_acceptance_template.get("template_row_count", 0) or 0
    )
    final_objective_no_new_acceptance_recorded = int(
        final_objective_no_new_acceptance_template.get("approval_rows_recorded", 0) or 0
    )
    final_objective_no_new_acceptance_required = int(
        final_objective_no_new_acceptance_template.get("approval_rows_required", 0) or 0
    )
    final_objective_no_new_acceptance_ready = bool(
        final_objective_no_new_acceptance_template.get("ready_to_apply_decisions", False)
    )
    final_objective_no_new_acceptance_records_decisions = bool(
        final_objective_no_new_acceptance_template.get("records_actual_decisions", False)
    )
    final_objective_no_new_acceptance_promotes_field = bool(
        final_objective_no_new_acceptance_template.get("promotes_current_field", False)
    )
    current_field_package_ready = (
        current_field_status == "current_permeability_field_package_generated"
        and current_field_cell_count > 0
        and current_field_positive_cells == current_field_cell_count
        and Path(str(current_field_mesh)).exists()
        and current_field_repro_ready
    )
    frozen_audit_status = frozen_model_measurement.get("status")
    frozen_audit_check_count = int(frozen_model_measurement.get("check_count", 0) or 0)
    frozen_audit_failure_count = int(frozen_model_measurement.get("failure_count", 0) or 0)
    frozen_audit_warning_count = int(frozen_model_measurement.get("warning_count", 0) or 0)
    frozen_audit_manifest_count = int(frozen_model_measurement.get("source_model_run_manifest_count", 0) or 0)
    frozen_audit_wrong_manifest_count = int(
        frozen_model_measurement.get("source_model_wrong_manifest_count", 0) or 0
    )
    frozen_audit_release_gate_runs = frozen_model_measurement.get("release_gate_run_count")
    frozen_audit_release_gate_checks = frozen_model_measurement.get("release_gate_check_count")
    frozen_audit_measurement_info = frozen_model_measurement.get("measurement_info", {})
    frozen_audit_measurement_info_rows = int(frozen_audit_measurement_info.get("source_file_rows", 0) or 0)
    frozen_audit_archive_rows = int(frozen_audit_measurement_info.get("archive_member_rows", 0) or 0)
    frozen_audit_workbook_rows = int(frozen_audit_measurement_info.get("workbook_sheet_rows", 0) or 0)
    frozen_audit_final_decision = frozen_model_measurement.get("final_promotion_decision")
    frozen_audit_open_blockers = frozen_model_measurement.get("final_promotion_open_blocker_ids", [])
    nmr_trend_followup_best = nmr_trend_followup.get("best_unevaluated_candidate", {})
    adaptive_search_best = adaptive_search.get("best_candidate", {})
    local_refinement_best = local_refinement_search.get("best_candidate", {})
    local_bracketing_best = local_bracketing_search.get("best_candidate", {})
    optimizer_search_best = optimizer_search.get("best_candidate", {})
    continuous_search_best = continuous_search.get("best_candidate", {})
    broad_continuous_search_best = broad_continuous_search.get("best_candidate", {})
    lower_support_continuous_search_best = lower_support_continuous_search.get("best_candidate", {})
    continuous_loop_search_best = continuous_loop_summary.get("search_best_candidate", {})
    continuous_loop_post_best = continuous_loop_summary.get("post_loop_best_candidate", {})
    executed_evidence_path = Path("inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv")
    if executed_evidence_path.exists():
        executed_evidence = pd.read_csv(executed_evidence_path)
        executed_combined_candidate_count = int(executed_evidence.shape[0])
        best_executed_row = executed_evidence.sort_values("total_active_objective_value").iloc[0].to_dict()
    else:
        executed_evidence = pd.DataFrame()
        executed_combined_candidate_count = int(candidate_set.get("selected_candidate_count", 0) or 0)
        best_executed_row = candidate_best
    if local_basis_search_best:
        local_basis_candidate_count = int(local_basis_search.get("evaluated_candidate_count", 0) or 0)
        executed_combined_candidate_count += local_basis_candidate_count
        local_basis_best_row = dict(local_basis_search_best)
        local_basis_best_row.setdefault("candidate_id", local_basis_best_row.get("source_candidate_id"))
        local_basis_best_row.setdefault(
            "direct_permeability_weighted_rmse_log10",
            local_basis_best_row.get("source_weighted_rmse_log10"),
        )
        local_basis_objective = local_basis_best_row.get("total_active_objective_value")
        current_best_objective = best_executed_row.get("total_active_objective_value")
        if local_basis_objective is not None and (
            current_best_objective is None or float(local_basis_objective) < float(current_best_objective)
        ):
            best_executed_row = local_basis_best_row
    if production_search_best:
        production_candidate_count = combined_search_count(production_search_summaries)
        executed_combined_candidate_count += production_candidate_count
        production_best_row = dict(production_search_best)
        production_best_row.setdefault("candidate_id", production_best_row.get("source_candidate_id"))
        production_best_row.setdefault(
            "direct_permeability_weighted_rmse_log10",
            production_best_row.get("source_weighted_rmse_log10"),
        )
        production_objective = production_best_row.get("total_active_objective_value")
        current_best_objective = best_executed_row.get("total_active_objective_value")
        if production_objective is not None and (
            current_best_objective is None or float(production_objective) < float(current_best_objective)
        ):
            best_executed_row = production_best_row
    source_audit = summarize_source_audit(Path("Library/source_coverage_audit.md"))

    processed_tables = processed.get("generated", [])
    processed_table_count = len(processed_tables)
    processed_total_rows = sum(int(table.get("rows", 0)) for table in processed_tables)
    coverage_statuses = coverage.get("coverage_status_counts", {})
    traceability_status = traceability.get("status")
    traceability_observation_count = int(traceability.get("observation_count", 0) or 0)
    traceability_all = bool(traceability.get("all_observations_traceable", False))
    traceability_status_counts = traceability.get("traceability_status_counts", {})
    traceability_missing_sections = int(traceability.get("missing_chapter_section_count", 0) or 0)
    traceability_missing_table_refs = int(traceability.get("missing_inventory_table_reference_count", 0) or 0)
    traceability_missing_model_entry = int(traceability.get("missing_model_entry_statement_count", 0) or 0)
    traceability_missing_artifact_obs = int(traceability.get("missing_expected_artifact_observation_count", 0) or 0)
    traceability_manifest_checks = int(traceability.get("manifest_validation_check_count", 0) or 0)
    traceability_manifest_failures = int(traceability.get("manifest_validation_failures", 0) or 0)
    traceability_data_content_rows = int(traceability.get("data_content_fact_row_count", 0) or 0)
    traceability_missing_data_content = int(traceability.get("missing_data_content_summary_count", 0) or 0)
    measurement_content_total_rows = int(measurement_content.get("total_fact_rows", 0) or 0)
    measurement_content_counts = measurement_content.get("measurement_fact_counts", {})
    active_groups = int(coverage.get("active_objective_groups", 0) or 0)
    observation_groups = int(coverage.get("observation_groups", 0) or 0)
    model_entry_status = measurement_model_entry.get("status")
    model_entry_rows = int(measurement_model_entry.get("row_count", 0) or 0)
    model_entry_active_count = int(measurement_model_entry.get("active_measurement_count", 0) or 0)
    model_entry_active_rows = int(measurement_model_entry.get("active_objective_row_total", 0) or 0)
    model_entry_class_counts = measurement_model_entry.get("model_entry_class_counts", {})
    model_entry_final_decisions = measurement_model_entry.get("final_decision_status_counts", {})
    model_entry_missing_likelihood = int(measurement_model_entry.get("rows_without_likelihood_row", 0) or 0)
    state_target_rows = int(coverage.get("state_target_rows", 0) or 0)
    state_sample_rows = int(coverage.get("state_sample_rows", 0) or 0)
    active_streams = int(likelihood.get("active_streams_now", 0) or 0)
    stream_gate_required_failures = int(stream_gate_audit.get("required_gate_fail_count", 0) or 0)
    stream_gate_required_warnings = int(stream_gate_audit.get("required_gate_warn_count", 0) or 0)
    stream_gate_diagnostic_or_boundary = int(stream_gate_audit.get("diagnostic_or_boundary_only_count", 0) or 0)
    stream_gate_not_ready = int(stream_gate_audit.get("not_ready_for_hard_residual_count", 0) or 0)
    stream_gate_decisions = stream_gate_audit.get("promotion_decision_counts", {})
    gate_closure_request_count = int(gate_closure_request.get("request_count", 0) or 0)
    gate_closure_external_count = int(gate_closure_request.get("external_request_count", 0) or 0)
    gate_closure_internal_count = int(gate_closure_request.get("internal_decision_count", 0) or 0)
    gate_closure_high_priority = gate_closure_request.get("high_priority_request_ids", [])
    external_pack_request_count = int(external_gate_request_pack.get("external_request_count", 0) or 0)
    external_pack_recipient_count = int(external_gate_request_pack.get("recipient_count", 0) or 0)
    external_pack_high_priority_count = int(
        external_gate_request_pack.get("high_priority_external_request_count", 0) or 0
    )
    external_pack_medium_priority_count = int(
        external_gate_request_pack.get("medium_priority_external_request_count", 0) or 0
    )
    external_pack_status = external_gate_request_pack.get("status")
    external_pack_request_ids = external_gate_request_pack.get("request_ids", [])
    external_pack_recipient_with_to_count = int(
        external_gate_request_pack.get("recipient_with_suggested_to_count", 0) or 0
    )
    external_pack_recipient_with_cc_count = int(
        external_gate_request_pack.get("recipient_with_suggested_cc_count", 0) or 0
    )
    external_pack_contact_route_counts = external_gate_request_pack.get("contact_route_counts", {})
    external_intake_status = external_gate_response_intake.get("status")
    external_intake_tracked_count = int(external_gate_response_intake.get("tracked_request_count", 0) or 0)
    external_intake_missing_count = int(external_gate_response_intake.get("missing_response_count", 0) or 0)
    external_intake_dir_count = int(external_gate_response_intake.get("intake_directory_count", 0) or 0)
    external_intake_template_count = int(external_gate_response_intake.get("response_note_template_count", 0) or 0)
    external_intake_with_to_count = int(
        external_gate_response_intake.get("tracked_request_with_suggested_to_count", 0) or 0
    )
    external_dispatch_status = external_gate_dispatch.get("status")
    external_dispatch_request_count = int(external_gate_dispatch.get("request_count", 0) or 0)
    external_dispatch_ready_count = int(external_gate_dispatch.get("ready_request_count", 0) or 0)
    external_dispatch_failed_check_count = int(external_gate_dispatch.get("failed_check_count", 0) or 0)
    external_dispatch_draft_count = int(external_gate_dispatch.get("draft_count", 0) or 0)
    external_dispatch_not_sent_count = int(external_gate_dispatch.get("not_sent_request_count", 0) or 0)
    external_dispatch_missing_response_count = int(external_gate_dispatch.get("missing_response_count", 0) or 0)
    external_dispatch_suggested_to_count = int(external_gate_dispatch.get("suggested_to_present_count", 0) or 0)
    external_dispatch_suggested_cc_count = int(external_gate_dispatch.get("suggested_cc_present_count", 0) or 0)
    external_dispatch_contact_route_counts = external_gate_dispatch.get("contact_route_status_counts", {})
    external_dispatch_gmail_draft_request_count = int(
        external_gate_dispatch.get("gmail_draft_request_count", 0) or 0
    )
    external_dispatch_unique_gmail_draft_count = int(
        external_gate_dispatch.get("unique_gmail_draft_count", 0) or 0
    )
    external_dispatch_gmail_send_status_counts = external_gate_dispatch.get("gmail_send_status_counts", {})
    gmail_live_state_status = gmail_live_state.get("status")
    gmail_live_state_checked_at = gmail_live_state.get("checked_at")
    gmail_live_state_expected_draft_count = int(gmail_live_state.get("expected_draft_count_including_cte", 0) or 0)
    gmail_live_state_observed_draft_count = int(gmail_live_state.get("observed_draft_count", 0) or 0)
    gmail_live_state_sent_result_count = int(gmail_live_state.get("sent_subject_search_result_count", 0) or 0)
    gmail_live_state_provider_reply_count = int(gmail_live_state.get("provider_reply_search_result_count", 0) or 0)
    gmail_live_state_teambeam_non_draft_count = int(
        gmail_live_state.get("teambeam_context_non_draft_result_count", 0) or 0
    )
    external_blocker_dashboard_status = external_blocker_dashboard.get("status")
    external_blocker_dashboard_count = int(external_blocker_dashboard.get("blocker_count", 0) or 0)
    external_blocker_dashboard_open_count = int(external_blocker_dashboard.get("open_blocker_count", 0) or 0)
    external_blocker_dashboard_unsent_count = int(external_blocker_dashboard.get("unsent_blocker_count", 0) or 0)
    external_blocker_dashboard_missing_count = int(
        external_blocker_dashboard.get("missing_response_blocker_count", 0) or 0
    )
    external_blocker_dashboard_external_count = int(
        external_blocker_dashboard.get("external_measurement_blocker_count", 0) or 0
    )
    external_blocker_dashboard_cte_count = int(
        external_blocker_dashboard.get("cte_confirmation_blocker_count", 0) or 0
    )
    external_blocker_dashboard_open_ids = external_blocker_dashboard.get("open_blocker_ids", [])
    local_gate_recovery_status = local_gate_recovery.get("status")
    local_gate_recovery_document_count = int(local_gate_recovery.get("document_count", 0) or 0)
    local_gate_recovery_evidence_count = int(local_gate_recovery.get("evidence_row_count", 0) or 0)
    local_gate_recovery_possible_closure_gates = local_gate_recovery.get("gates_with_closure_candidates", [])
    local_gate_recovery_still_external_gates = local_gate_recovery.get("gates_still_external_after_local_rescan", [])
    local_gate_recovery_gate_summaries = local_gate_recovery.get("gate_summaries", {})
    local_gate_recovery_possible_closure_count = sum(
        int(summary.get("possible_closure_evidence_count", 0) or 0)
        for summary in local_gate_recovery_gate_summaries.values()
        if isinstance(summary, dict)
    )
    local_gate_recovery_keyword_candidate_count = sum(
        int(summary.get("keyword_candidate_not_closure_count", 0) or 0)
        for summary in local_gate_recovery_gate_summaries.values()
        if isinstance(summary, dict)
    )
    download_gate_recovery_status = download_gate_recovery.get("status")
    download_gate_recovery_document_count = int(download_gate_recovery.get("document_count", 0) or 0)
    download_gate_recovery_evidence_count = int(download_gate_recovery.get("evidence_row_count", 0) or 0)
    download_gate_recovery_possible_closure_gates = download_gate_recovery.get("gates_with_closure_candidates", [])
    download_gate_recovery_still_external_gates = download_gate_recovery.get(
        "gates_still_external_after_downloads_scan", []
    )
    download_gate_recovery_gate_summaries = download_gate_recovery.get("gate_summaries", {})
    download_gate_recovery_possible_closure_count = sum(
        int(summary.get("possible_closure_evidence_count", 0) or 0)
        for summary in download_gate_recovery_gate_summaries.values()
        if isinstance(summary, dict)
    )
    download_gate_recovery_keyword_candidate_count = sum(
        int(summary.get("keyword_candidate_not_closure_count", 0) or 0)
        for summary in download_gate_recovery_gate_summaries.values()
        if isinstance(summary, dict)
    )
    download_gate_recovery_inventory_count = int(download_gate_recovery.get("inventory_row_count", 0) or 0)
    download_gate_recovery_duplicate_count = int(
        download_gate_recovery.get("catalogued_duplicate_sha1_verified_count", 0) or 0
    )
    download_gate_recovery_run_dir_count = int(
        download_gate_recovery.get("uncatalogued_extracted_or_run_output_directory_count", 0) or 0
    )
    cte_confirmation_status = cte_confirmation.get("status")
    cte_confirmation_request_status = cte_confirmation.get("request_status")
    cte_confirmation_response_status = cte_confirmation.get("response_status")
    cte_confirmation_suggested_to = cte_confirmation.get("suggested_to")
    cte_confirmation_suggested_cc = cte_confirmation.get("suggested_cc")
    cte_confirmation_gmail_draft_id = cte_confirmation.get("gmail_draft_id")
    cte_confirmation_gmail_send_status = cte_confirmation.get("gmail_send_status")
    report_open_status = report_open_comment.get("status")
    report_open_marker_count = int(report_open_comment.get("active_report_unresolved_marker_count", 0) or 0)
    report_resolved_formulation_count = int(report_open_comment.get("resolved_formulation_comment_count", 0) or 0)
    report_tracked_external_count = int(report_open_comment.get("tracked_external_blocker_count", 0) or 0)
    report_tracked_internal_count = int(report_open_comment.get("tracked_internal_or_provenance_item_count", 0) or 0)
    report_false_positive_count = int(report_open_comment.get("false_positive_marker_count", 0) or 0)
    report_open_item_ids = report_open_comment.get("active_report_open_item_ids", [])
    open_question_resolution_status = open_question_resolution.get("status")
    open_question_resolution_row_count = int(open_question_resolution.get("row_count", 0) or 0)
    open_question_resolution_counts = open_question_resolution.get("resolution_status_counts", {})
    open_question_resolution_resolved_count = int(
        open_question_resolution.get("resolved_or_current_scope_count", 0) or 0
    )
    open_question_resolution_external_count = int(
        open_question_resolution.get("external_or_send_response_required_count", 0) or 0
    )
    open_question_resolution_internal_count = int(
        open_question_resolution.get("internal_policy_or_final_decision_count", 0) or 0
    )
    ogs_formulation_status = ogs_formulation.get("status")
    ogs_formulation_check_count = int(ogs_formulation.get("check_count", 0) or 0)
    ogs_formulation_fail_count = int(ogs_formulation.get("fail_count", 0) or 0)
    ogs_formulation_tracked_caveat_count = int(ogs_formulation.get("tracked_caveat_count", 0) or 0)
    ogs_formulation_hard_checks_pass = bool(ogs_formulation.get("all_hard_checks_pass", False))
    ogs_formulation_run_fields = ogs_formulation.get("run_local_field_parameters", {})
    ogs_formulation_process_type = ogs_formulation.get("process_type")
    ogs_formulation_primary_variables = ogs_formulation.get("primary_variables", [])
    ogs_run_input_status = ogs_run_input.get("status")
    ogs_run_input_checks = [check for check in ogs_run_input.get("checks", []) if isinstance(check, dict)]
    ogs_run_input_check_count = len(ogs_run_input_checks)
    ogs_run_input_warning_count = sum(1 for check in ogs_run_input_checks if check.get("severity") == "warning")
    ogs_run_input_error_count = sum(1 for check in ogs_run_input_checks if check.get("severity") == "error")
    ogs_run_input_execution_returncode = ogs_run_input.get("execution_returncode")
    ogs_run_input_execution_backend = ogs_run_input.get("execution_backend")
    ogs_run_input_unreadable_meshes = [
        Path(str(mesh.get("path", ""))).name
        for mesh in ogs_run_input.get("meshes", [])
        if isinstance(mesh, dict) and mesh.get("exists") and not mesh.get("meshio_readable")
    ]
    internal_gate_decision_count = int(internal_gate_decision.get("decision_count", 0) or 0)
    internal_gate_local_policy_count = int(internal_gate_decision.get("local_policy_recorded_count", 0) or 0)
    internal_gate_active_or_ready_count = int(
        internal_gate_decision.get("active_or_ready_internal_policy_count", 0) or 0
    )
    internal_gate_diagnostic_or_boundary_count = int(
        internal_gate_decision.get("diagnostic_or_boundary_policy_count", 0) or 0
    )
    internal_gate_still_gated_count = int(
        internal_gate_decision.get("still_external_or_activation_gated_count", 0) or 0
    )
    internal_gate_remaining_caveat_count = int(
        internal_gate_decision.get("remaining_confirmation_or_promotion_caveat_count", 0) or 0
    )
    internal_gate_not_promoted_default_count = int(internal_gate_decision.get("not_promoted_default_policy_count", 0) or 0)
    nmr_default_promotion_status = internal_gate_decision.get("nmr_default_promotion_status")
    permeability_likelihood_policy_status = internal_gate_decision.get("permeability_likelihood_policy_status")
    internal_gate_status_counts = internal_gate_decision.get("status_counts", {})
    state_eval_counts = direct_state_summary.get(
        "evaluation_status_counts",
        likelihood.get("state_evaluation_status_counts", {}),
    )
    no_ogs_state_samples = int(state_eval_counts.get("no_ogs_state_samples", 0) or 0)
    sampled_ogs_outputs = int(ogs_sampling.get("output_file_count", direct_state_summary.get("ogs_output_times", 0)) or 0)
    sampled_state_rows = int(ogs_sampling.get("sample_row_count", direct_state_summary.get("state_sample_rows", 0)) or 0)
    active_state_rows = int(direct_state_summary.get("used_in_objective_rows", 0) or 0)
    taupe_compared_rows = int(taupe_diagnostic.get("compared_rows", 0) or 0)
    taupe_compared_series = int(taupe_diagnostic.get("compared_series", 0) or 0)
    taupe_diagnostic_mae = taupe_diagnostic.get("standardized_residual", {}).get("mae")
    taupe_discrimination_runs = int(taupe_discrimination.get("run_count", 0) or 0)
    taupe_full_active_runs = int(taupe_discrimination.get("runs_with_full_active_combined_objective", 0) or 0)
    taupe_mae_range = taupe_discrimination.get("taupe_mae_range")
    taupe_best_active_mae = taupe_discrimination.get("best_combined_taupe_mae")
    taupe_weight_runs = int(taupe_weight_sensitivity.get("run_count", 0) or 0)
    taupe_weight_series = int(taupe_weight_sensitivity.get("compared_series_count", 0) or 0)
    taupe_weight_uncompared = int(taupe_weight_sensitivity.get("uncompared_series_count", 0) or 0)
    taupe_weight_distinct_winners = int(taupe_weight_sensitivity.get("series_best_run_distinct_count", 0) or 0)
    taupe_weight_best_mean = taupe_weight_sensitivity.get("best_mean_weighting_rank", {})
    ert_compared_rows = int(ert_diagnostic.get("compared_rows", 0) or 0)
    ert_compared_outputs = int(ert_diagnostic.get("compared_output_times", 0) or 0)
    ert_residual_log10 = ert_diagnostic.get("area_weighted_residual_log10", {})
    ert_diagnostic_mae = ert_residual_log10.get("mae")
    ert_diagnostic_rmse = ert_residual_log10.get("rmse")
    ert_discrimination_runs = int(ert_discrimination.get("run_count", 0) or 0)
    ert_full_active_runs = int(ert_discrimination.get("runs_with_full_active_combined_objective", 0) or 0)
    ert_mae_range = ert_discrimination.get("ert_mae_log10_range")
    ert_best_active_mae = ert_discrimination.get("best_combined_ert_mae_log10")
    ert_support_runs = int(ert_support_sensitivity.get("run_count", 0) or 0)
    ert_support_variants = int(ert_support_sensitivity.get("support_variant_count", 0) or 0)
    ert_support_best_mean = ert_support_sensitivity.get("best_mean_support_rank", {})
    nmr_bias_runs = int(nmr_bias_sensitivity.get("run_count", 0) or 0)
    nmr_bias_best_label = nmr_bias_sensitivity.get("best_label_bias_combined", {})
    nmr_bias_best_trend = nmr_bias_sensitivity.get("best_trend_anomaly_combined", {})
    nmr_bias_rank_corr = nmr_bias_sensitivity.get("current_vs_label_bias_rank_correlation")
    nmr_decision_recommended = nmr_objective_decision.get("recommended_option_id")
    nmr_decision_best_run = nmr_objective_decision.get("best_recommended_run")
    nmr_decision_current_incumbent_rank = nmr_objective_decision.get("current_incumbent_recommended_rank")
    nmr_decision_best_current_rank = nmr_objective_decision.get("best_recommended_current_rank")
    nmr_decision_changed = nmr_objective_decision.get("active_objective_changed")
    nmr_trend_activation_best = nmr_trend_activation.get("best_trend_anomaly_active_objective", {})
    nmr_trend_activation_runs = nmr_trend_activation.get("runs_with_full_active_trend_objective")
    nmr_trend_activation_validation_delta = nmr_trend_activation.get("diagnostic_validation_max_abs_delta")
    nmr_trend_activation_raw_incumbent_rank = nmr_trend_activation.get(
        "raw_incumbent_rank_under_trend_anomaly"
    )
    nmr_trend_activation_winner_raw_rank = nmr_trend_activation.get("trend_anomaly_winner_raw_rank")
    nmr_final_policy_status = nmr_final_policy_gate.get("status")
    nmr_final_policy_selected = nmr_final_policy_gate.get("final_nmr_policy_selected")
    nmr_final_policy_current_default = nmr_final_policy_gate.get("current_report_default_policy")
    nmr_final_policy_recommended = nmr_final_policy_gate.get("recommended_candidate_policy")
    nmr_final_policy_recommended_run = nmr_final_policy_gate.get("recommended_candidate_policy_run")
    nmr_final_policy_followup = nmr_final_policy_gate.get("followup_recommendation")
    nmr_final_policy_materiality = nmr_final_policy_gate.get("followup_materiality_threshold")
    nmr_final_policy_best_advantage = nmr_final_policy_gate.get("followup_best_unevaluated_direct_advantage")
    nmr_final_policy_median_beating = nmr_final_policy_gate.get("followup_median_state_beating_candidates")
    nmr_final_policy_acceptance_status = nmr_final_policy_acceptance_template.get("status")
    nmr_final_policy_acceptance_rows = int(
        nmr_final_policy_acceptance_template.get("template_row_count", 0) or 0
    )
    nmr_final_policy_acceptance_recorded = int(
        nmr_final_policy_acceptance_template.get("primary_policy_approval_rows_recorded", 0) or 0
    )
    nmr_final_policy_acceptance_required = int(
        nmr_final_policy_acceptance_template.get("primary_policy_approval_rows_required", 0) or 0
    )
    nmr_final_policy_acceptance_ready = nmr_final_policy_acceptance_template.get("ready_to_apply_policy")
    nmr_final_policy_acceptance_records_decision = nmr_final_policy_acceptance_template.get(
        "records_actual_decision"
    )
    nmr_final_policy_acceptance_changes_objective = nmr_final_policy_acceptance_template.get(
        "changes_active_objective"
    )
    nmr_final_policy_acceptance_promotes_field = nmr_final_policy_acceptance_template.get(
        "promotes_current_field"
    )
    nmr_final_policy_acceptance_new_ogs = nmr_final_policy_acceptance_template.get("new_ogs_batch_recommended_now")
    cross_stream_winners = cross_stream_scorecard.get("stream_winners", {})
    cross_stream_best_mean = cross_stream_winners.get("mean_rank_all_streams", {})
    cross_stream_active = cross_stream_scorecard.get("active_incumbent_cross_stream", {})
    cross_stream_runs = int(cross_stream_scorecard.get("joined_run_count", 0) or 0)
    cross_stream_pareto = int(cross_stream_scorecard.get("pareto_all_streams_count", 0) or 0)
    cross_stream_top10_all = int(cross_stream_scorecard.get("top10_all_stream_candidates", 0) or 0)
    rh_candidate_rows = {
        str(row.get("candidate_id")): row
        for row in rh_candidate_curves.get("summary_rows", [])
        if isinstance(row, dict)
    }
    rh_preferred_candidate = rh_candidate_curves.get("preferred_policy_candidate")
    rh_preferred_curve = rh_candidate_rows.get(str(rh_preferred_candidate), {})
    rh_candidate_count = int(rh_candidate_curves.get("candidate_count", 0) or 0)
    rh_candidate_after_active_rows = int(
        rh_candidate_curves.get("comparison_status_counts", {}).get(
            "after_active_curve_time_range_requires_curve_extension_or_new_forcing",
            0,
        )
        or 0
    )
    rh_preferred_mae = rh_preferred_curve.get("overlap_abs_residual_mpa_mae")
    rh_uncertainty_envelope_dates = int(rh_uncertainty.get("envelope_date_count", 0) or 0)
    rh_uncertainty_active_outside = int(rh_uncertainty.get("active_curve_outside_envelope_count", 0) or 0)
    rh_uncertainty_overlap_range_p50 = (
        rh_uncertainty.get("overlap", {}).get("pressure_range_mpa", {}).get("p50")
    )
    other_hm_source_audit_requests = int(other_hm_source_audit.get("request_rows", 0) or 0)
    other_hm_hard_ready_requests = int(other_hm_source_audit.get("hard_residual_ready_request_count", 0) or 0)
    other_hm_support_ready_requests = int(other_hm_source_audit.get("local_support_ready_request_count", 0) or 0)
    pdf_pages = pdf_pages_from_log(Path("main.log"))
    latex_clean = log_is_clean(Path("main.log"), Path("main.blg"))
    cited_keys = source_audit["cited_keys"]
    missing_bib = source_audit["missing_bib_entries"]
    missing_unavailable = source_audit["missing_unavailable_entries"]
    citation_locator_status = citation_locator.get("status")
    citation_key_instances = int(citation_locator.get("citation_key_instance_count", 0) or 0)
    citation_unique_keys = int(citation_locator.get("unique_cited_key_count", cited_keys) or 0)
    citation_missing_or_weak_locator = int(citation_locator.get("missing_or_weak_locator_count", 0) or 0)
    citation_missing_bib = int(citation_locator.get("missing_bib_entry_count", missing_bib) or 0)
    citation_unavailable_missing_log = int(
        citation_locator.get("unavailable_fulltext_missing_log_count", missing_unavailable) or 0
    )
    citation_fulltext_statuses = citation_locator.get("fulltext_status_counts", {})

    rows: list[dict[str, str]] = []

    report_artifacts = [
        "main.tex",
        "measurement_chapter.tex",
        "main.pdf",
        "opalinus_clay.bib",
        "Library/source_coverage_audit.md",
    ]
    report_ready = (
        all(file_nonempty(path) for path in report_artifacts)
        and latex_clean
        and pdf_pages is not None
        and report_open_status == "report_open_comment_audit_generated"
        and report_open_marker_count == 0
    )
    add_row(
        rows,
        requirement_id="R01_report_workspace",
        requirement="Extract/setup an editable report workspace and produce a clean PDF.",
        status="achieved" if report_ready else "partial",
        evidence=(
            f"Report artifacts present={all(file_nonempty(path) for path in report_artifacts)}; "
            f"main.pdf pages from log={pdf_pages}; LaTeX/log scan clean={latex_clean}; "
            f"report open-comment audit status={report_open_status}; active report unresolved markers="
            f"{report_open_marker_count}; resolved formulation comments={report_resolved_formulation_count}."
        ),
        remaining_work="None for current build hygiene; rebuild after every report change.",
        authoritative_artifacts="main.tex; measurement_chapter.tex; main.pdf; main.log; main.blg; inversion_workflow/report_open_comment_audit.md",
    )

    model_artifacts = [
        "GESA_model_original/2025-04-03_CDA_N4_2D_250403",
        "GESA_model_original/2025-05-09_CDA_N4_2D_250509",
        "GESA_model_original/projection_on_mesh_2025-09-05",
        "ogs_settings/03_parameters_TRM.xml",
        "MODEL_AUDIT.md",
        "inversion_workflow/ogs_formulation_consistency_audit.md",
    ]
    model_files_present = all(file_exists(path) for path in model_artifacts)
    model_formulation_ready = (
        ogs_formulation_status == "ogs_formulation_consistency_audit_generated"
        and ogs_formulation_check_count >= 18
        and ogs_formulation_hard_checks_pass
    )
    add_row(
        rows,
        requirement_id="R02_source_model",
        requirement="Recover and understand the exchanged GESA OGS model without modifying its governing semantics.",
        status="achieved_with_tracked_caveats" if model_files_present and model_formulation_ready else "partial",
        evidence=(
            "April/May model folders, projection workflow, copied OGS settings, and model audit are present; "
            f"OGS formulation audit status={ogs_formulation_status}; checks={ogs_formulation_check_count}; "
            f"hard failures={ogs_formulation_fail_count}; process={ogs_formulation_process_type}; "
            f"primary variables={ogs_formulation_primary_variables}; run-local mesh fields={ogs_formulation_run_fields}; "
            f"run-input audit status={ogs_run_input_status}; checks={ogs_run_input_check_count}; "
            f"warnings={ogs_run_input_warning_count}; errors={ogs_run_input_error_count}; "
            f"meshio-unreadable meshes={ogs_run_input_unreadable_meshes}; OGS execution returncode="
            f"{ogs_run_input_execution_returncode} via {ogs_run_input_execution_backend}; "
            f"frozen-model/measurement audit status={frozen_audit_status}, checks="
            f"{frozen_audit_check_count}, failures={frozen_audit_failure_count}, warnings="
            f"{frozen_audit_warning_count}, run manifests checked={frozen_audit_manifest_count}, "
            f"wrong projection-source manifests={frozen_audit_wrong_manifest_count}."
        ),
        remaining_work="Keep the CTE provenance caveat and fixed-porosity mesh-field caveat explicit; the run-input audit header-verifies the appended-data submeshes and records OGS acceptance, but regenerate them with identifySubdomains if downstream meshio decoding is required.",
        authoritative_artifacts="GESA_model_original/; ogs_settings/; MODEL_AUDIT.md; main.tex; inversion_workflow/ogs_formulation_consistency_audit.md; inversion_workflow/frozen_model_measurement_inclusion_audit.md; inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.md",
    )

    add_row(
        rows,
        requirement_id="R03_raw_measurement_inventory",
        requirement="Cross-check collected measurement files, including ZIP contents and model-projection inputs.",
        status=(
            "achieved"
            if manifest.get("failures") == 0
            and manifest.get("observation_count") == 9
            and traceability_status == "measurement_report_traceability_audit_generated"
            and traceability_all
            and traceability_missing_data_content == 0
            and traceability_data_content_rows == measurement_content_total_rows
            and measurement_content_total_rows > 0
            else "partial"
        ),
        evidence=(
            f"Observation manifest checks={manifest.get('check_count')}; failures={manifest.get('failures')}; "
            f"observation groups={manifest.get('observation_count')}; traceability audit status="
            f"{traceability_status}; traceable observations={traceability_observation_count}; "
            f"traceability status counts={traceability_status_counts}; missing chapter sections="
            f"{traceability_missing_sections}; missing inventory table refs={traceability_missing_table_refs}; "
            f"missing model-entry statements={traceability_missing_model_entry}; missing artifact observations="
            f"{traceability_missing_artifact_obs}; missing data-content summaries="
            f"{traceability_missing_data_content}; data-content fact rows={traceability_data_content_rows}; "
            f"content-deep-dive total rows={measurement_content_total_rows}."
        ),
        remaining_work="Refresh manifest after adding any newly found TeamBeam/Gmail/Thunderbird files.",
        authoritative_artifacts="inversion_workflow/observation_manifest.json; inversion_workflow/observation_manifest_validation.json; inversion_workflow/measurement_report_traceability_audit.md",
    )

    add_row(
        rows,
        requirement_id="R04_processed_measurement_tables",
        requirement="Mine the collected attachments/ZIPs/workbooks into model-facing measurement tables.",
        status="achieved" if processed_table_count >= 16 and processed_total_rows > 0 else "partial",
        evidence=(
            f"Processed tables={processed_table_count}; total rows across generated tables={processed_total_rows}; "
            f"content-deep-dive fact rows={measurement_content_total_rows}; per-measurement content rows="
            f"{measurement_content_counts}."
        ),
        remaining_work="Regenerate after catalogue updates; keep source_file/source_member provenance columns.",
        authoritative_artifacts="inversion_workflow/scripts/build_processed_observations.py; inversion_workflow/processed_observations/",
    )

    add_row(
        rows,
        requirement_id="R05_measurement_semantics_chapter",
        requirement="Add rigorous measurement chapter explaining what each measurement observes and how it maps to OGS quantities.",
        status="achieved_with_tracked_caveats" if file_nonempty("measurement_chapter.tex") else "missing",
        evidence=(
            "Measurement chapter is present and describes permeability, NMR, ERT, Taupe/TDR, RH/suction, "
            "coordinates/bedding, projection workflow, and other HM monitoring with caveats; "
            f"the report open-comment audit records {report_resolved_formulation_count} resolved formulation "
            f"comments and {report_open_marker_count} active report review markers; "
            f"the measurement-report traceability audit covers {traceability_observation_count} observations "
            f"with all_observations_traceable={traceability_all} and {traceability_data_content_rows} "
            "catalogue content facts from the source-file content pass."
        ),
        remaining_work="Collaborator review is still needed for open calibration/provenance caveats such as Taupe units and RH curve generation.",
        authoritative_artifacts="measurement_chapter.tex; inversion_workflow/measurement_likelihood_model.md; inversion_workflow/report_open_comment_audit.md; inversion_workflow/measurement_report_traceability_audit.md",
    )

    add_row(
        rows,
        requirement_id="R06_sources_and_fulltexts",
        requirement="Document new sources in BibTeX, cite with locators, and track available/unavailable fulltexts.",
        status=(
            "achieved_with_tracked_caveats"
            if missing_bib == 0
            and missing_unavailable == 0
            and citation_locator_status == "citation_locator_audit_generated"
            and citation_missing_bib == 0
            and citation_missing_or_weak_locator == 0
            and citation_unavailable_missing_log == 0
            else "partial"
        ),
        evidence=(
            f"Cited keys={cited_keys}; missing BibTeX entries={missing_bib}; "
            f"blocked cited fulltexts missing from unavailable list={missing_unavailable}; "
            f"citation locator audit status={citation_locator_status}; citation key instances="
            f"{citation_key_instances}; unique cited keys={citation_unique_keys}; "
            f"missing/weak locators={citation_missing_or_weak_locator}; "
            f"citation-audit missing BibTeX={citation_missing_bib}; unavailable fulltexts missing "
            f"from log={citation_unavailable_missing_log}; fulltext statuses={citation_fulltext_statuses}."
        ),
        remaining_work="Acquire clean PDFs for blocked sources if institutional access becomes available; rerun the citation locator audit after adding or editing citations.",
        authoritative_artifacts="opalinus_clay.bib; Library/fulltexts/; Library/unavailable_fulltexts.md; Library/source_coverage_audit.md; Library/citation_locator_audit.md",
    )

    add_row(
        rows,
        requirement_id="R07_observation_operators",
        requirement="Represent all collected measurement classes in the frozen OGS workflow in a defensible way.",
        status="achieved_with_tracked_caveats" if observation_groups == 9 and active_groups >= 2 else "partial",
        evidence=(
            f"Observation groups={observation_groups}; coverage statuses={coverage_statuses}; "
            f"model-entry matrix status={model_entry_status}, rows={model_entry_rows}, "
            f"active measurement classes={model_entry_active_count}, active rows={model_entry_active_rows}, "
            f"entry classes={model_entry_class_counts}, final decision statuses={model_entry_final_decisions}, "
            f"rows without likelihood row={model_entry_missing_likelihood}; "
            f"measurement-report traceability={traceability_all} with statuses={traceability_status_counts}; "
            f"state target rows={state_target_rows}; state sample rows={state_sample_rows}; "
            f"ERT compared log-resistivity rows={ert_compared_rows} across {ert_compared_outputs} output times; "
            f"ERT cross-run audits={ert_discrimination_runs}; ERT support-sensitivity runs={ert_support_runs}; "
            f"RH candidate boundary curves={rh_candidate_count} with {rh_candidate_after_active_rows} post-active-curve rows; "
            f"RH uncertainty envelope dates={rh_uncertainty_envelope_dates}; active curve outside envelope rows="
            f"{rh_uncertainty_active_outside}; "
            f"other-HM numeric source audit requests={other_hm_source_audit_requests}; hard-ready requests="
            f"{other_hm_hard_ready_requests}; "
            f"Taupe compared trend rows={taupe_compared_rows} across {taupe_compared_series} series; "
            f"Taupe cross-run audits={taupe_discrimination_runs}; "
            f"Taupe series-weight sensitivity runs={taupe_weight_runs}; "
            f"stream activation-gate audit required failures={stream_gate_required_failures}, "
            f"warnings={stream_gate_required_warnings}, decisions={stream_gate_decisions}; "
            f"gate-closure requests={gate_closure_request_count} "
            f"({gate_closure_external_count} external, {gate_closure_internal_count} internal/confirmation); "
            f"external recipient drafts={external_pack_recipient_count} covering "
            f"{external_pack_request_count} external requests, with suggested To routes for "
            f"{external_pack_recipient_with_to_count}/{external_pack_recipient_count} recipients; "
            f"response intake tracks "
            f"{external_intake_tracked_count} requests with {external_intake_missing_count} missing responses; "
            f"dispatch audit status={external_dispatch_status}, ready requests="
            f"{external_dispatch_ready_count}/{external_dispatch_request_count}, failed checks="
            f"{external_dispatch_failed_check_count}, suggested To rows="
            f"{external_dispatch_suggested_to_count}, Gmail drafts="
            f"{external_dispatch_unique_gmail_draft_count}; "
            f"Gmail live-state audit={gmail_live_state_status}, checked_at="
            f"{gmail_live_state_checked_at}, observed drafts="
            f"{gmail_live_state_observed_draft_count}/{gmail_live_state_expected_draft_count}, "
            f"sent-subject hits={gmail_live_state_sent_result_count}, provider-reply hits="
            f"{gmail_live_state_provider_reply_count}; "
            f"external blocker dashboard={external_blocker_dashboard_status}, blockers="
            f"{external_blocker_dashboard_count}, open={external_blocker_dashboard_open_count}, "
            f"unsent={external_blocker_dashboard_unsent_count}, missing responses="
            f"{external_blocker_dashboard_missing_count}; "
            f"local gate recovery audit={local_gate_recovery_status}, documents rescanned="
            f"{local_gate_recovery_document_count}, possible gate-closing evidence rows="
            f"{local_gate_recovery_possible_closure_count}, gates still external after rescan="
            f"{len(local_gate_recovery_still_external_gates)}; "
            f"Downloads recovery audit={download_gate_recovery_status}, documents scanned="
            f"{download_gate_recovery_document_count}, possible gate-closing evidence rows="
            f"{download_gate_recovery_possible_closure_count}, verified duplicate/catalogue rows="
            f"{download_gate_recovery_duplicate_count}, uncatalogued run-output dirs="
            f"{download_gate_recovery_run_dir_count}; "
            f"internal local policies recorded={internal_gate_local_policy_count}/"
            f"{internal_gate_decision_count}."
        ),
        remaining_work="Keep ERT, Taupe/TDR, RH/suction, and other HM streams gated until their stream-specific support, calibration, uncertainty, provenance, and numeric-export decisions are satisfied; use the stream activation-gate audit, local gate recovery audit, Downloads recovery audit, gate-closure request package, external request pack, dispatch audit, response intake tracker, and internal decision register as the machine-readable blocker, local-rescan, outbound request, send-readiness, response-filing, and policy lists.",
        authoritative_artifacts="inversion_workflow/measurement_operator_coverage.md; inversion_workflow/measurement_model_entry_matrix.md; inversion_workflow/measurement_report_traceability_audit.md; inversion_workflow/measurement_stream_activation_gate_audit.md; inversion_workflow/local_gate_recovery_audit.md; inversion_workflow/download_gate_recovery_audit.md; inversion_workflow/gmail_gate_live_state_audit.md; inversion_workflow/external_blocker_dashboard.md; inversion_workflow/measurement_gate_closure_request.md; inversion_workflow/external_gate_request_pack.md; inversion_workflow/external_gate_dispatch_audit.md; inversion_workflow/external_gate_response_intake.md; inversion_workflow/internal_gate_decision_register.md; inversion_workflow/processed_observations/",
    )

    add_row(
        rows,
        requirement_id="R08_likelihood_activation",
        requirement="Define residuals, weighting, transforms, caveats, and activation gates before fitting.",
        status="achieved_with_tracked_caveats" if active_streams >= 2 and state_target_rows > 0 else "partial",
        evidence=(
            f"Likelihood streams={likelihood.get('measurement_streams')}; active streams now={active_streams}; "
            f"current objective rows={likelihood.get('total_current_objective_rows')}; "
            f"direct permeability likelihood-policy audit status={permeability_policy_status}, "
            f"current row-Gaussian objective={permeability_policy_current_objective}, "
            f"support-cell mean diagnostic objective={permeability_policy_support_mean_objective}, "
            f"top-10 row-loss share={permeability_policy_top10_loss_share}; "
            f"support lower-bound audit={permeability_support_lb_status}, "
            f"same-support reducible fraction={permeability_support_lb_reducible_fraction}, "
            f"current at lower bound={permeability_support_lb_at_bound}; "
            f"permeability likelihood decision request={permeability_policy_decision_status}, "
            f"recommended current-report policy={permeability_policy_decision_recommended}; "
            f"existing-field likelihood rerank={permeability_policy_rerank_status}, "
            f"scored fields={permeability_policy_rerank_scored}, row-Gaussian best ties="
            f"{permeability_policy_rerank_best_ties}, current accepted tied="
            f"{permeability_policy_rerank_current_accepted_tied}, diagnostic winners outside tie set="
            f"{permeability_policy_rerank_alt_outside}; winner cross-stream audit="
            f"{permeability_policy_winner_cross_status}, policy winners with scorecard evidence="
            f"{permeability_policy_winner_cross_scorecard_rows}, direct-only policy winners="
            f"{permeability_policy_winner_cross_direct_only_rows}, outside-tie direct-only winners="
            f"{permeability_policy_winner_cross_outside_direct_only_rows}, row-Gaussian representative active rank="
            f"{permeability_policy_winner_cross_row_gaussian_rank}, current accepted active rank="
            f"{permeability_policy_winner_cross_current_rank}; "
            f"state rows without OGS samples={no_ogs_state_samples}; "
            f"NMR bias/anomaly audit runs={nmr_bias_runs}, best label-bias run={nmr_bias_best_label.get('run_id')}, "
            f"current-vs-label-bias rank correlation={nmr_bias_rank_corr}; "
            f"NMR objective decision recommends={nmr_decision_recommended}, "
            f"recommended-run={nmr_decision_best_run}, active-objective-changed={nmr_decision_changed}, "
            f"active incumbent rank under recommendation={nmr_decision_current_incumbent_rank}; "
            f"NMR trend/anomaly executable mode status={nmr_trend_activation.get('status')}, "
            f"full-active runs={nmr_trend_activation_runs}, best executable run="
            f"{nmr_trend_activation_best.get('run_id')}, validation max abs delta="
            f"{nmr_trend_activation_validation_delta}; "
            f"NMR final residual policy gate status={nmr_final_policy_status}, "
            f"final policy selected={nmr_final_policy_selected}, current default="
            f"{nmr_final_policy_current_default}, recommended candidate policy="
            f"{nmr_final_policy_recommended}, recommended run={nmr_final_policy_recommended_run}, "
            f"follow-up={nmr_final_policy_followup}; NMR final-policy acceptance template status="
            f"{nmr_final_policy_acceptance_status}, primary approvals recorded/required="
            f"{nmr_final_policy_acceptance_recorded}/{nmr_final_policy_acceptance_required}, "
            f"ready to apply={nmr_final_policy_acceptance_ready}; "
            f"ERT diagnostic log10 MAE={ert_diagnostic_mae}, RMSE={ert_diagnostic_rmse}; "
            f"ERT cross-run MAE range={ert_mae_range}; "
            f"ERT support-sensitivity variants={ert_support_variants}, best mean support-rank run="
            f"{ert_support_best_mean.get('run_id')}; "
            f"RH preferred candidate={rh_preferred_candidate} overlap MAE={rh_preferred_mae} MPa; "
            f"RH envelope dates={rh_uncertainty_envelope_dates}, active outside envelope rows="
            f"{rh_uncertainty_active_outside}, overlap pressure-range p50={rh_uncertainty_overlap_range_p50} MPa; "
            f"Taupe diagnostic trend MAE={taupe_diagnostic_mae}; "
            f"Taupe cross-run MAE range={taupe_mae_range}; "
            f"Taupe series-weight compared series={taupe_weight_series}, distinct per-series winners="
            f"{taupe_weight_distinct_winners}, best mean weighting-rank run={taupe_weight_best_mean.get('run_id')}; "
            f"cross-stream scorecard runs={cross_stream_runs}, best mean-rank run="
            f"{cross_stream_best_mean.get('run_id')}, active-incumbent ERT rank="
            f"{cross_stream_active.get('ert_mae_rank')}, Taupe rank={cross_stream_active.get('taupe_mae_rank')}, "
            f"top-10-all-stream candidates={cross_stream_top10_all}; "
            f"stream activation-gate required failures={stream_gate_required_failures}, "
            f"diagnostic/boundary-only streams={stream_gate_diagnostic_or_boundary}, "
            f"not-ready hard-residual streams={stream_gate_not_ready}; "
            f"gate-closure requests={gate_closure_request_count}, high-priority="
            f"{gate_closure_high_priority}; "
            f"external request pack status={external_pack_status}, recipients="
            f"{external_pack_recipient_count}, requests={external_pack_request_count}; "
            f"recipient contact routes with suggested To={external_pack_recipient_with_to_count}, "
            f"suggested Cc={external_pack_recipient_with_cc_count}, route counts="
            f"{external_pack_contact_route_counts}; "
            f"response intake status={external_intake_status}, missing responses="
            f"{external_intake_missing_count}, intake dirs={external_intake_dir_count}, "
            f"note templates={external_intake_template_count}, rows with suggested To="
            f"{external_intake_with_to_count}; "
            f"dispatch audit status={external_dispatch_status}, ready requests="
            f"{external_dispatch_ready_count}/{external_dispatch_request_count}, failed checks="
            f"{external_dispatch_failed_check_count}, suggested To rows="
            f"{external_dispatch_suggested_to_count}, suggested Cc rows="
            f"{external_dispatch_suggested_cc_count}, Gmail draft request rows="
            f"{external_dispatch_gmail_draft_request_count}, unique Gmail drafts="
            f"{external_dispatch_unique_gmail_draft_count}; "
            f"Gmail live-state audit={gmail_live_state_status}, observed drafts="
            f"{gmail_live_state_observed_draft_count}/{gmail_live_state_expected_draft_count}, "
            f"sent-subject hits={gmail_live_state_sent_result_count}, provider-reply hits="
            f"{gmail_live_state_provider_reply_count}, recent CD-A/HERMES/TeamBeam non-draft hits="
            f"{gmail_live_state_teambeam_non_draft_count}; "
            f"external blocker dashboard={external_blocker_dashboard_status}, open blockers="
            f"{external_blocker_dashboard_open_count}/{external_blocker_dashboard_count}, "
            f"measurement blockers={external_blocker_dashboard_external_count}, "
            f"CTE confirmation blockers={external_blocker_dashboard_cte_count}; "
            f"local gate recovery rescan status={local_gate_recovery_status}, possible gate-closing "
            f"evidence rows={local_gate_recovery_possible_closure_count}, keyword-only candidate rows="
            f"{local_gate_recovery_keyword_candidate_count}, still-external gates="
            f"{local_gate_recovery_still_external_gates}; "
            f"Downloads recovery rescan status={download_gate_recovery_status}, possible gate-closing "
            f"evidence rows={download_gate_recovery_possible_closure_count}, keyword-only candidate rows="
            f"{download_gate_recovery_keyword_candidate_count}, still-external gates="
            f"{download_gate_recovery_still_external_gates}; "
            f"internal decision register local policies={internal_gate_local_policy_count}, "
            f"active/ready={internal_gate_active_or_ready_count}, diagnostic/boundary="
            f"{internal_gate_diagnostic_or_boundary_count}, hard-activation gated="
            f"{internal_gate_still_gated_count}, confirmation caveats="
            f"{internal_gate_remaining_caveat_count}, not-promoted-default policies="
            f"{internal_gate_not_promoted_default_count}, NMR default-promotion status="
            f"{nmr_default_promotion_status}, permeability likelihood-policy status="
            f"{permeability_likelihood_policy_status}."
        ),
        remaining_work="Keep the NMR bound-water/model-error caveat explicit and keep the recorded not-default policy for trend/anomaly NMR unless the modelling team deliberately reopens the objective semantics. The NMR final residual policy gate now records the exact current default, preferred provisional trend/anomaly policy, and no-new-batch recommendation, but final promotion still needs an accepted NMR residual choice; the acceptance template currently records no primary NMR-policy approval. Keep the direct permeability row-Gaussian policy recorded for reproducibility, use the existing-field likelihood rerank, support lower-bound audit, and winner cross-stream audit as decision evidence, but do not switch to robust tails or support-cell aggregation without an explicit modelling-team likelihood decision. Do not promote direct-only non-default winners without OGS execution and stream diagnostics. Use the ERT resistivity and Taupe trend diagnostics only as screens until ERT support/transform/uncertainty and Taupe units/uncertainty are calibrated, resolve RH boundary provenance before activating those streams, and keep other-HM residuals inactive because the local source, catalogue-recovery, and Downloads-recovery audits found no hard-ready numeric exports or local gate-closing evidence. Use the cross-stream scorecard, stream gate audit, local gate recovery audit, Downloads recovery audit, gate-closure request package, external request pack, dispatch audit, response intake tracker, and internal decision register to prevent reporting a field that only wins the active objective.",
        authoritative_artifacts="inversion_workflow/measurement_likelihood_model.csv; inversion_workflow/measurement_likelihood_model.md; inversion_workflow/permeability_likelihood_policy_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_decision_request.md; inversion_workflow/permeability_likelihood_scenario_rerank.md; inversion_workflow/permeability_likelihood_winner_cross_stream_audit.md; inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/nmr_final_residual_policy_gate.md; inversion_workflow/nmr_final_residual_policy_acceptance_record_template.md; inversion_workflow/measurement_stream_activation_gate_audit.md; inversion_workflow/local_gate_recovery_audit.md; inversion_workflow/download_gate_recovery_audit.md; inversion_workflow/gmail_gate_live_state_audit.md; inversion_workflow/external_blocker_dashboard.md; inversion_workflow/measurement_gate_closure_request.md; inversion_workflow/external_gate_request_pack.md; inversion_workflow/external_gate_dispatch_audit.md; inversion_workflow/external_gate_response_intake.md; inversion_workflow/internal_gate_decision_register.md; inversion_workflow/cross_stream_candidate_scorecard.md",
    )

    add_row(
        rows,
        requirement_id="R09_parameter_release_control",
        requirement="Keep the GESA model frozen while allowing staged run-local parameter fields.",
        status="achieved" if release_gate.get("status") == "pass" and release_plan.get("parameter_release_rows") == 14 else "partial",
        evidence=(
            f"Release-plan rows={release_plan.get('parameter_release_rows')}; active fields={release_plan.get('active_field_parameters_now')}; "
            f"release-gate status={release_gate.get('status')}; audited runs={release_gate.get('run_count')}; "
            f"checks={release_gate.get('check_count')}; gate failures={release_gate.get('failure_count')}; "
            f"CTE confirmation request status={cte_confirmation_status}, request="
            f"{cte_confirmation_request_status}, response={cte_confirmation_response_status}, "
            f"Gmail draft={cte_confirmation_gmail_draft_id or 'none'}; frozen-model/measurement "
            f"audit status={frozen_audit_status}, release-gate runs/checks="
            f"{frozen_audit_release_gate_runs}/{frozen_audit_release_gate_checks}, failures="
            f"{frozen_audit_failure_count}, wrong projection-source manifests="
            f"{frozen_audit_wrong_manifest_count}."
        ),
        remaining_work="Do not release porosity, retention, mechanical, boundary, or thermal parameters until their gates are satisfied; review/send and close the CTE confirmation request before interpreting thermal expansivity physically.",
        authoritative_artifacts="inversion_workflow/inversion_parameter_release_plan.md; inversion_workflow/inversion_release_gate_audit.md; inversion_workflow/frozen_model_measurement_inclusion_audit.md; inversion_workflow/thermal_expansivity_parameter_audit.md; inversion_workflow/cte_confirmation_request.md",
    )

    best = candidate_best
    add_row(
        rows,
        requirement_id="R10_permeability_field_fit",
        requirement="Fit or rank heterogeneous anisotropic permeability fields against currently active data.",
        status="partial" if best else "missing",
        evidence=(
            f"Executed combined candidates={executed_combined_candidate_count}; "
            f"regularized OGS mode={candidate_set.get('ogs_mode')}; best executed candidate={best_executed_row.get('candidate_id')}; "
            f"best combined active objective={best_executed_row.get('total_active_objective_value')}; "
            f"first adaptive batch best={adaptive_search_best.get('source_candidate_id')} "
            f"({adaptive_search_best.get('total_active_objective_value')}); "
            f"local refinement best={local_refinement_best.get('source_candidate_id')} "
            f"({local_refinement_best.get('total_active_objective_value')}); "
            f"local bracketing best={local_bracketing_best.get('source_candidate_id')} "
            f"({local_bracketing_best.get('total_active_objective_value')}); "
            f"optimizer-proposed batch best={optimizer_search_best.get('source_candidate_id')} "
            f"({optimizer_search_best.get('total_active_objective_value')}); "
            f"continuous-proposal batch best={continuous_search_best.get('source_candidate_id')} "
            f"({continuous_search_best.get('total_active_objective_value')}); "
            f"broad continuous batch best={broad_continuous_search_best.get('source_candidate_id')} "
            f"({broad_continuous_search_best.get('total_active_objective_value')}); "
            f"broad continuous cumulative best={broad_continuous_cumulative_best.get('source_candidate_id')} "
            f"({broad_continuous_cumulative_best.get('total_active_objective_value')}); "
            f"lower-support continuous batch best={lower_support_continuous_search_best.get('source_candidate_id')} "
            f"({lower_support_continuous_search_best.get('total_active_objective_value')}); "
            f"latest continuous-loop batch best={continuous_loop_search_best.get('source_candidate_id')} "
            f"({continuous_loop_search_best.get('total_active_objective_value')}); "
            f"post-loop best={continuous_loop_post_best.get('candidate_id')} "
            f"({continuous_loop_post_best.get('total_active_objective_value')}); "
            f"active components={best_executed_row.get('active_component_count')}; "
            f"state active rows={best_executed_row.get('state_active_objective_rows')}; "
            f"direct RMSE={best_executed_row.get('direct_permeability_weighted_rmse_log10')}; "
            f"permeability residual conflict audit status={permeability_residual_status}, active rows="
            f"{permeability_residual_active_rows}, |residual|>=1 log10 rows="
            f"{permeability_residual_large_ge1}, |residual|>=2 log10 rows="
            f"{permeability_residual_very_large_ge2}, outside configured scalar range="
            f"{permeability_residual_outside_range}, repeated support cells="
            f"{permeability_residual_repeated_cells}, support cells with observed range >=1 log10="
            f"{permeability_residual_cell_conflicts}; "
            f"permeability likelihood policy status={permeability_policy_status}, "
            f"support-cell mean diagnostic objective={permeability_policy_support_mean_objective}, "
            f"support-cell median diagnostic objective={permeability_policy_support_median_objective}, "
            f"top-10 row-loss share={permeability_policy_top10_loss_share}, "
            f"decision request={permeability_policy_decision_status}; "
            f"configured-scalar outlier disposition status={permeability_outlier_disposition_status}, "
            f"outlier rows/groups={permeability_outlier_disposition_rows}/"
            f"{permeability_outlier_disposition_groups}, max envelope excess="
            f"{permeability_outlier_disposition_max_excess}, max same-support range="
            f"{permeability_outlier_disposition_support_range}, bounds release now="
            f"{permeability_outlier_bounds_release_now}, tensor-shape release now="
            f"{permeability_outlier_tensor_release_now}; "
            f"support lower-bound audit status={permeability_support_lb_status}, "
            f"single-support lower-bound objective={permeability_support_lb_lower_objective}, "
            f"same-support reducible gap={permeability_support_lb_reducible_gap}, "
            f"current at lower bound={permeability_support_lb_at_bound}, "
            f"support groups with observed range >=2 log10={permeability_support_lb_conflict_ge2}; "
            f"support-conflict spatial audit status={permeability_support_spatial_status}, "
            f"mesh cells={permeability_support_spatial_mesh_cells}, active support cells="
            f"{permeability_support_spatial_active_cells}, repeated support cells="
            f"{permeability_support_spatial_repeated_cells}, support cells with range >=1/>=2 log10="
            f"{permeability_support_spatial_ge1}/{permeability_support_spatial_ge2}, "
            f"configured-scalar conflict cells={permeability_support_spatial_configured_conflict}, "
            f"top conflict cell={permeability_support_spatial_top.get('primary_cell_id')} "
            f"({permeability_support_spatial_top.get('segments')} at "
            f"{permeability_support_spatial_top.get('depth_min_m')}-"
            f"{permeability_support_spatial_top.get('depth_max_m')} m, observed range="
            f"{permeability_support_spatial_top.get('observed_log10_range')}); "
            f"release gate={best_executed_row.get('release_gate_status')}; global release checks={release_gate.get('check_count')}; "
            f"next-batch proposals={adaptive_plan.get('proposed_candidate_count')}; top proposal={adaptive_top_candidate}; "
            f"proposal mode={adaptive_plan.get('proposal_mode')}; "
            f"finite-candidate optimizer top={optimizer_top_candidate}; "
            f"optimizer acquisition={optimizer_proposal.get('acquisition')}; "
            f"continuous proposals={continuous_plan.get('continuous_candidate_count')}; "
            f"continuous top={continuous_top_candidate}; "
            f"continuous top predicted objective="
            f"{continuous_top_proposals[0].get('gp_combined_objective_mean') if continuous_top_proposals else None}; "
            f"anisotropy sensitivity candidates={anisotropy_plan.get('candidate_count')}; "
            f"best anisotropy direct candidate={anisotropy_best.get('candidate_id')} "
            f"(delta={anisotropy_best.get('direct_objective_delta_vs_baseline')}); "
            f"local-basis sampler candidates={local_basis_plan.get('candidate_count')}; "
            f"local-basis anchors={local_basis_plan.get('basis_anchor_count')}; "
            f"best local-basis direct candidate={local_basis_best.get('candidate_id')} "
            f"(delta={local_basis_best.get('direct_objective_delta_vs_baseline')}); "
            f"local-anisotropy sampler candidates={local_anisotropy_candidate_count}; "
            f"local-anisotropy anchors={local_anisotropy_anchor_count}; "
            f"best local-anisotropy direct candidate={local_anisotropy_best.get('candidate_id')} "
            f"(delta={local_anisotropy_best_delta}); "
            f"local-basis OGS batch best={local_basis_search_best_id} "
            f"({local_basis_search_best_objective}); "
            f"production OGS rounds best={production_search_best_id} "
            f"({production_search_best_objective}); "
            f"production OGS rounds={len(production_search_summaries)}; "
            f"production sampler evidence rows={production_sampler.get('executed_candidate_count')}; "
            f"production candidate pool={production_sampler.get('candidate_pool_count')}; "
            f"production executable unexecuted candidates="
            f"{production_sampler.get('unexecuted_executable_candidate_count')}; "
            f"production top proposal={production_top_candidate} ({production_top_family}); "
            f"production CV state RMSE={production_sampler.get('cv_state_objective_rmse')}; "
            f"production stop/continue decision={production_decision.get('recommendation')}; "
            f"cross-stream best mean-rank run={cross_stream_best_mean.get('run_id')} "
            f"(mean rank={cross_stream_best_mean.get('mean_rank_all_streams')}, "
            f"worst rank={cross_stream_best_mean.get('worst_rank_all_streams')}); "
            f"active incumbent cross-stream ranks: NMR-bias={cross_stream_active.get('nmr_label_bias_rank')}, "
            f"ERT={cross_stream_active.get('ert_mae_rank')}, Taupe={cross_stream_active.get('taupe_mae_rank')}; "
            f"cross-stream hybrid field screen candidates={cross_stream_hybrid_candidate_count} from "
            f"{cross_stream_hybrid_target_count} target winner runs; best direct hybrid="
            f"{cross_stream_hybrid_best.get('candidate_id')} with delta={cross_stream_hybrid_best_delta}; "
            f"structural/EDZ field-family screen status={structural_edz_status}, candidates="
            f"{structural_edz_candidate_count}, improving direct candidates={structural_edz_improving_count}, "
            f"best={structural_edz_best.get('candidate_id')} ({structural_edz_best_family}) "
            f"with delta={structural_edz_best_delta}; "
            f"current field package status={current_field_status}, run={current_field_run_id}, "
            f"cells={current_field_cell_count}, positive-definite cells={current_field_positive_cells}, "
            f"median log10 eigen-permeability=({current_field_log10_kmin_p50}, {current_field_log10_kmax_p50}), "
            f"anisotropy p50={current_field_anisotropy_p50}, theta p50={current_field_theta_p50}; "
            f"current field reproducibility audit status={current_field_repro_status}, checks="
            f"{current_field_repro_check_count}, required failures={current_field_repro_required_failures}, "
            f"manifest rows={current_field_repro_manifest_rows}, run-input files="
            f"{current_field_repro_run_input_files}, project refs={current_field_repro_project_refs}, "
            f"residual rows direct/state={current_field_repro_direct_rows}/{current_field_repro_state_rows}; "
            f"current field visual inspection={current_field_visual_status}, images="
            f"{current_field_visual_image_count}, rendered positive-definite cells="
            f"{current_field_visual_positive_cells}, log10 geometric-mean permeability p50="
            f"{current_field_visual_geom_p50}, nearest-anchor distance p50="
            f"{current_field_visual_anchor_p50} m; "
            f"frozen-model/measurement inclusion audit={frozen_audit_status}, checks="
            f"{frozen_audit_check_count}, measurement-info rows="
            f"{frozen_audit_measurement_info_rows}, archive rows={frozen_audit_archive_rows}, "
            f"workbook sheet rows={frozen_audit_workbook_rows}, promotion guard="
            f"{frozen_audit_final_decision}; "
            f"current field selection audit status={current_field_selection_status}, "
            f"active decision={current_field_active_decision}, final all-measurement decision="
            f"{current_field_final_decision}, status counts={current_field_selection_status_counts}; "
            f"conditional field scenarios status={conditional_scenario_status}, scenarios="
            f"{conditional_scenario_count}, unique winners={conditional_scenario_unique_winners}, "
            f"current-field wins={conditional_scenario_current_wins}, final decision="
            f"{conditional_scenario_final_decision}; conditional field candidate package status="
            f"{conditional_package_status}, candidates={conditional_package_candidate_count}, "
            f"selection stability={conditional_package_stability}, diagnostic metric evidence rows="
            f"{conditional_package_metric_evidence_rows}, missing metric rows="
            f"{conditional_package_metric_evidence_missing}; "
            f"conditional field difference audit status={conditional_difference_status}, compared fields="
            f"{conditional_difference_compared_count}, cells={conditional_difference_cell_count}, "
            f"largest-difference candidate={conditional_difference_largest_candidate}, "
            f"max mean abs delta log10 k={conditional_difference_max_mean_abs}, "
            f"max cells over 0.05/0.10 log10={conditional_difference_max_gt_005}/"
            f"{conditional_difference_max_gt_010}; final promotion checklist status="
            f"{final_promotion_status}, decision={final_promotion_decision}, criteria="
            f"{final_promotion_criterion_count}, open criteria={final_promotion_open_count}, "
            f"status counts={final_promotion_status_counts}; "
            f"permeability next field-fit gate status={permeability_next_gate_status}, "
            f"recommendation={permeability_next_gate_recommendation}, gates={permeability_next_gate_count}, "
            f"same-support active-objective batch executable now={permeability_next_gate_executable_now}, "
            f"gate statuses={permeability_next_gate_status_counts}."
        ),
        remaining_work="The current best executed field is now packaged for inspection and rerun provenance. The smooth magnitude, global anisotropy-angle/ratio, first local-basis magnitude family, local tensor-anisotropy screen, cross-family production sampler rounds, cross-stream hybrid magnitude blends, and structural/EDZ cap/shell/bedding/corridor screen have now been checked. The residual conflict, spatial support-conflict, likelihood-policy, configured-scalar outlier-disposition, and support lower-bound audits show the remaining direct mismatch is concentrated in large pulse-test residuals and repeated support-cell conflicts; the two scalar-envelope rows are now classified as one duplicated minor upper-envelope exceedance that does not by itself justify bounds widening or tensor-shape release. The accepted field is already at the single-support lower bound for the current support map. The next field-fit gate now records that no same-support active-objective batch is executable under the current row-Gaussian policy, and the likelihood-policy acceptance template records that no primary policy approval exists yet. Reopen OGS spending only after a support/likelihood/bounds/tensor-shape decision or accepted measurement-stream objective is recorded; do not accept a final field until the broader stream gates are resolved or explicitly excluded.",
        authoritative_artifacts="inversion_workflow/scripts/run_continuous_inversion_loop.py; inversion_workflow/scripts/build_anisotropy_sensitivity_plan.py; inversion_workflow/scripts/build_local_basis_sampler_plan.py; inversion_workflow/scripts/build_local_anisotropy_sampler_plan.py; inversion_workflow/scripts/build_production_sampler_convergence_audit.py; inversion_workflow/scripts/build_cross_stream_candidate_scorecard.py; inversion_workflow/scripts/build_cross_stream_hybrid_field_plan.py; inversion_workflow/scripts/build_structural_edz_field_family_plan.py; inversion_workflow/scripts/build_permeability_residual_conflict_audit.py; inversion_workflow/scripts/build_permeability_support_conflict_spatial_audit.py; inversion_workflow/scripts/build_permeability_likelihood_policy_audit.py; inversion_workflow/scripts/build_permeability_support_lower_bound_audit.py; inversion_workflow/scripts/build_permeability_likelihood_decision_request.py; inversion_workflow/scripts/build_permeability_configured_scalar_outlier_disposition.py; inversion_workflow/scripts/build_permeability_next_field_fit_gate.py; inversion_workflow/scripts/build_permeability_likelihood_policy_acceptance_template.py; inversion_workflow/scripts/build_current_permeability_field_package.py; inversion_workflow/scripts/build_current_field_reproducibility_audit.py; inversion_workflow/scripts/build_current_field_visual_inspection.py; inversion_workflow/scripts/build_current_field_selection_audit.py; inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; inversion_workflow/scripts/build_conditional_field_candidate_package.py; inversion_workflow/scripts/build_conditional_field_difference_audit.py; inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; inversion_workflow/scripts/build_frozen_model_measurement_inclusion_audit.py; inversion_workflow/permeability_residual_conflict_audit.md; inversion_workflow/permeability_support_conflict_spatial_audit.md; inversion_workflow/permeability_likelihood_policy_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_decision_request.md; inversion_workflow/permeability_configured_scalar_outlier_disposition.md; inversion_workflow/permeability_next_field_fit_gate.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD.md; inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md; inversion_workflow/current_permeability_field/visual_inspection/CURRENT_FIELD_VISUAL_INSPECTION.md; inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu; inversion_workflow/current_field_selection_audit.md; inversion_workflow/frozen_model_measurement_inclusion_audit.md; inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES.md; inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md; inversion_workflow/final_inversion_promotion_checklist.md; inversion_workflow/runs/continuous_inversion_loop/; inversion_workflow/runs/anisotropy_sensitivity_plan/; inversion_workflow/runs/local_basis_sampler_plan/; inversion_workflow/runs/local_anisotropy_sampler_plan/; inversion_workflow/runs/production_sampler_convergence/; inversion_workflow/runs/cross_stream_hybrid_field_plan/; inversion_workflow/runs/structural_edz_field_family_plan/; inversion_workflow/runs/regularized_ogs_candidate_set/; inversion_workflow/runs/adaptive_combined_candidate_plan/; inversion_workflow/runs/bayesian_candidate_proposal/; inversion_workflow/runs/continuous_bayesian_candidate_plan/; inversion_workflow/runs/lower_support_continuous_candidate_plan/; inversion_workflow/runs/smooth_permeability_candidate_search/; inversion_workflow/cross_stream_candidate_scorecard.md",
    )

    ogs_status = ogs_env.get("status")
    ogs_ready = ogs_status in {"ogs_executable_found", "ogs_container_found_runtime_available"}
    selected_ogs = ogs_env.get("selected_executable") or ogs_env.get("selected_container")
    ogs_execution_backend = ogs_execution.get("execution_backend")
    ogs_returncode = ogs_execution.get("returncode")
    if ogs_returncode == 0 and sampled_state_rows > 0 and active_state_rows > 0:
        ogs_requirement_status = "achieved_with_tracked_caveats"
    elif sampled_state_rows > 0:
        ogs_requirement_status = "partial"
    elif ogs_ready:
        ogs_requirement_status = "ready_pending_external_execution"
    else:
        ogs_requirement_status = "blocked_external"
    add_row(
        rows,
        requirement_id="R11_ogs_execution",
        requirement="Execute the prepared OGS model and sample pressure/saturation/temperature/displacement/porosity outputs.",
        status=ogs_requirement_status,
        evidence=(
            f"OGS environment status={ogs_status}; selected executable/container={selected_ogs}; "
            f"recorded execution backend={ogs_execution_backend}; sampled OGS outputs={sampled_ogs_outputs}; "
            f"sampled state rows={sampled_state_rows}; active state rows={active_state_rows}; "
            f"state evaluation counts={state_eval_counts}."
        ),
        remaining_work=(
            "Keep the fixed-porosity support fallback explicit, keep Taupe as a diagnostic trend screen, and resolve remaining ERT/Taupe/RH gates."
        ),
        authoritative_artifacts="inversion_workflow/OGS_ENVIRONMENT_AUDIT.md; inversion_workflow/scripts/run_ogs_model.py; inversion_workflow/scripts/sample_ogs_state_outputs.py",
    )

    add_row(
        rows,
        requirement_id="R12_full_combined_inversion",
        requirement="Use all defensible measurements to fit permeability, and possibly later parameter fields, in a combined objective.",
        status="partial" if candidate_set_executed and active_groups >= 2 else "incomplete",
        evidence=(
            f"Active objective groups now={active_groups}; state targets prepared={state_target_rows}; "
            f"sampled state rows={sampled_state_rows}; active state objective rows={active_state_rows}; "
            f"best executed combined objective={best_executed_row.get('total_active_objective_value')}; "
            f"best executed state rows={best_executed_row.get('state_active_objective_rows')}; "
            f"permeability residual audit active rows={permeability_residual_active_rows}, "
            f"|residual|>=1 log10 rows={permeability_residual_large_ge1}, "
            f"outside configured scalar range={permeability_residual_outside_range}; "
            f"permeability likelihood policy support-mean objective={permeability_policy_support_mean_objective}, "
            f"conflict support groups={permeability_policy_conflict_groups}, "
            f"top-10 row-loss share={permeability_policy_top10_loss_share}, "
            f"decision request={permeability_policy_decision_status}; "
            f"configured-scalar outlier disposition={permeability_outlier_disposition_status}, "
            f"rows/groups={permeability_outlier_disposition_rows}/"
            f"{permeability_outlier_disposition_groups}, max envelope excess="
            f"{permeability_outlier_disposition_max_excess}, bounds release now="
            f"{permeability_outlier_bounds_release_now}, tensor-shape release now="
            f"{permeability_outlier_tensor_release_now}; "
            f"support lower-bound status={permeability_support_lb_status}, "
            f"single-support lower-bound objective={permeability_support_lb_lower_objective}, "
            f"same-support reducible fraction={permeability_support_lb_reducible_fraction}, "
            f"current at lower bound={permeability_support_lb_at_bound}; "
            f"support-conflict spatial audit={permeability_support_spatial_status}, active/repeated/range>=2 cells="
            f"{permeability_support_spatial_active_cells}/{permeability_support_spatial_repeated_cells}/"
            f"{permeability_support_spatial_ge2}; "
            f"first adaptive batch best objective={adaptive_search_best.get('total_active_objective_value')}; "
            f"local refinement best objective={local_refinement_best.get('total_active_objective_value')}; "
            f"local bracketing best objective={local_bracketing_best.get('total_active_objective_value')}; "
            f"optimizer-proposed batch best objective={optimizer_search_best.get('total_active_objective_value')}; "
            f"continuous-proposal batch best objective={continuous_search_best.get('total_active_objective_value')}; "
            f"broad continuous batch best objective={broad_continuous_search_best.get('total_active_objective_value')}; "
            f"broad continuous cumulative best objective={broad_continuous_cumulative_best.get('total_active_objective_value')}; "
            f"lower-support continuous batch best objective={lower_support_continuous_search_best.get('total_active_objective_value')}; "
            f"latest continuous-loop batch best objective={continuous_loop_search_best.get('total_active_objective_value')}; "
            f"post-loop best objective={continuous_loop_post_best.get('total_active_objective_value')}; "
            f"adaptive proposals={adaptive_plan.get('proposed_candidate_count')}; "
            f"state term flat over executed candidates={adaptive_plan.get('state_objective_flat_over_executed_candidates')}; "
            f"optimizer top proposal={optimizer_top_candidate}; "
            f"optimizer best executed objective={optimizer_proposal.get('best_executed_combined_objective')}; "
            f"continuous proposal count={continuous_plan.get('continuous_candidate_count')}; "
            f"continuous top proposal={continuous_top_candidate}; "
            f"continuous top P(improve)="
            f"{continuous_top_proposals[0].get('probability_of_improvement') if continuous_top_proposals else None}; "
            f"anisotropy direct best={anisotropy_best.get('candidate_id')} "
            f"with delta={anisotropy_best.get('direct_objective_delta_vs_baseline')}; "
            f"local-basis direct best={local_basis_best.get('candidate_id')} "
            f"with delta={local_basis_best.get('direct_objective_delta_vs_baseline')}; "
            f"local-anisotropy direct best={local_anisotropy_best.get('candidate_id')} "
            f"with delta={local_anisotropy_best_delta}; "
            f"local-basis OGS best={local_basis_search_best_id} "
            f"with objective={local_basis_search_best_objective}; "
            f"production OGS rounds best={production_search_best_id} "
            f"with objective={production_search_best_objective}; "
            f"production OGS rounds={len(production_search_summaries)}; "
            f"production sampler top={production_top_candidate} ({production_top_family}) "
            f"with P(improve)="
            f"{production_top_proposals[0].get('probability_of_improvement') if production_top_proposals else None}; "
            f"production executable proposals={production_sampler.get('unexecuted_executable_candidate_count')}; "
            f"production nonexecutable diagnostic rows={production_sampler.get('nonexecutable_diagnostic_candidate_count')}; "
            f"production stop/continue decision={production_decision.get('recommendation')}; "
            f"cross-stream joined runs={cross_stream_runs}; "
            f"cross-stream Pareto candidates={cross_stream_pareto}; "
            f"top-10-all-stream candidates={cross_stream_top10_all}; "
            f"best mean-rank cross-stream run={cross_stream_best_mean.get('run_id')}; "
            f"cross-stream hybrid screen candidates={cross_stream_hybrid_candidate_count}; "
            f"best hybrid direct delta={cross_stream_hybrid_best_delta}; "
            f"structural/EDZ screen status={structural_edz_status}; candidates="
            f"{structural_edz_candidate_count}; improving candidates={structural_edz_improving_count}; "
            f"best structural/EDZ direct delta={structural_edz_best_delta}; "
            f"current field package ready={current_field_package_ready}; "
            f"current field visual inspection={current_field_visual_status} with "
            f"{current_field_visual_image_count} maps; "
            f"frozen-model/measurement audit={frozen_audit_status} with "
            f"{frozen_audit_check_count} checks and {len(frozen_audit_open_blockers)} "
            f"open final-promotion blockers; "
            f"current field deliverable status={current_field_deliverable_status}; "
            f"current field selection final decision={current_field_final_decision}; "
            f"selection audit failing-final criteria={current_field_selection_status_counts.get('fails_final_promotion')}; "
            f"selection audit blocked/gated criteria={current_field_selection_status_counts.get('blocked_or_gated')}; "
            f"conditional field scenario final decision={conditional_scenario_final_decision}; "
            f"conditional scenarios={conditional_scenario_count}, unique scenario winners="
            f"{conditional_scenario_unique_winners}, current-field wins={conditional_scenario_current_wins}; "
            f"conditional field package candidates={conditional_package_candidate_count}, "
            f"stability={conditional_package_stability}, diagnostic metric evidence rows="
            f"{conditional_package_metric_evidence_rows}, missing metric rows="
            f"{conditional_package_metric_evidence_missing}; "
            f"conditional field difference compared fields={conditional_difference_compared_count}, "
            f"largest-difference candidate={conditional_difference_largest_candidate}, "
            f"max mean abs delta log10 k={conditional_difference_max_mean_abs}, "
            f"max cells over 0.10 log10={conditional_difference_max_gt_010}; "
            f"final promotion checklist decision={final_promotion_decision}, "
            f"open criteria={final_promotion_open_count}, status counts={final_promotion_status_counts}; "
            f"final objective decision register status={final_objective_decision_status}, "
            f"decisions={final_objective_decision_count}, pending/not-ready={final_objective_pending_count}, "
            f"status counts={final_objective_decision_status_counts}; "
            f"final objective scenario matrix status={final_objective_scenario_status}, "
            f"options={final_objective_scenario_option_count}, current-field winning options="
            f"{final_objective_scenario_current_winning_count}, unique winners="
            f"{final_objective_scenario_unique_winner_count}, unscored future options="
            f"{final_objective_scenario_unscored_count}; "
            f"final objective no-new-evidence closeout draft status={final_objective_no_new_status}, "
            f"draft decisions={final_objective_no_new_count}, external/provenance rows="
            f"{final_objective_no_new_external_count}, internal rows={final_objective_no_new_internal_count}, "
            f"scenario/final rows={final_objective_no_new_scenario_count}, would-select scenario="
            f"{final_objective_no_new_scenario}, would-select winner={final_objective_no_new_winner}, "
            f"current field is draft-scenario winner={final_objective_no_new_current_winner}, "
            f"records decisions={final_objective_no_new_records_decisions}, promotes field="
            f"{final_objective_no_new_promotes_field}, unblocks promotion="
            f"{final_objective_no_new_unblocks_promotion}; acceptance template status="
            f"{final_objective_no_new_acceptance_status}, approvals recorded/required="
            f"{final_objective_no_new_acceptance_recorded}/"
            f"{final_objective_no_new_acceptance_required}, ready to apply="
            f"{final_objective_no_new_acceptance_ready}, records decisions="
            f"{final_objective_no_new_acceptance_records_decisions}, promotes field="
            f"{final_objective_no_new_acceptance_promotes_field}; "
            f"permeability next field-fit gate status={permeability_next_gate_status}, "
            f"recommendation={permeability_next_gate_recommendation}, "
            f"same-support active-objective batch executable now={permeability_next_gate_executable_now}; "
            f"NMR trend/anomaly follow-up recommendation={nmr_trend_followup.get('recommendation')}, "
            f"best unevaluated candidate={nmr_trend_followup_best.get('candidate_id')}, "
            f"best unevaluated direct advantage="
            f"{nmr_trend_followup.get('best_unevaluated_direct_advantage_vs_incumbent')}, "
            f"unevaluated runnable candidates={nmr_trend_followup.get('unevaluated_runnable_candidate_count')}."
        ),
        remaining_work="The continuous proposal loop has made the batch workflow repeatable, the direct anisotropy check does not justify a global angle/ratio-only OGS batch, the first local-basis OGS batch finds only a tiny combined-objective improvement, the local tensor-anisotropy screen worsens the direct objective, the executed production sampler rounds did not improve that incumbent, the cross-stream hybrid screen found no direct-improving blend, the structural/EDZ cap/shell/bedding/corridor screen found no direct-improving candidate, and the residual conflict plus likelihood/support lower-bound audits show many remaining pulse-test residuals are irreducible under the current one-value-per-support-cell map. The configured-scalar outlier disposition narrows the bounds/tensor-shape question: the two scalar-envelope rows are one duplicated minor upper-envelope exceedance and do not by themselves justify releasing bounds or tensor shape. The next field-fit gate therefore blocks another same-support active-objective batch until support/measurement interpretation, robust/aggregation likelihood semantics, an accepted configured-bound/tensor-shape decision, or external ERT/Taupe/RH gates change; the likelihood-policy acceptance template currently records no primary approval for such a change. The no-new-evidence closeout draft gives exact conservative text for choosing the narrow F01 scenario, but it still requires approval, decision-record edits, and regenerated scenario/current-field/promotion audits before any field label changes; choose one explicit final-objective scenario from the scenario matrix before claiming a full combined inversion.",
        authoritative_artifacts="inversion_workflow/scripts/evaluate_inversion_candidate.py; inversion_workflow/scripts/run_inversion_candidate_search.py; inversion_workflow/scripts/run_continuous_inversion_loop.py; inversion_workflow/scripts/build_bayesian_candidate_proposal.py; inversion_workflow/scripts/build_continuous_bayesian_candidate_plan.py; inversion_workflow/scripts/build_anisotropy_sensitivity_plan.py; inversion_workflow/scripts/build_local_basis_sampler_plan.py; inversion_workflow/scripts/build_local_anisotropy_sampler_plan.py; inversion_workflow/scripts/build_production_sampler_convergence_audit.py; inversion_workflow/scripts/build_cross_stream_candidate_scorecard.py; inversion_workflow/scripts/build_cross_stream_hybrid_field_plan.py; inversion_workflow/scripts/build_structural_edz_field_family_plan.py; inversion_workflow/scripts/build_permeability_residual_conflict_audit.py; inversion_workflow/scripts/build_permeability_support_conflict_spatial_audit.py; inversion_workflow/scripts/build_permeability_likelihood_policy_audit.py; inversion_workflow/scripts/build_permeability_support_lower_bound_audit.py; inversion_workflow/scripts/build_permeability_likelihood_decision_request.py; inversion_workflow/scripts/build_permeability_configured_scalar_outlier_disposition.py; inversion_workflow/scripts/build_permeability_next_field_fit_gate.py; inversion_workflow/scripts/build_permeability_likelihood_policy_acceptance_template.py; inversion_workflow/scripts/build_current_field_selection_audit.py; inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; inversion_workflow/scripts/build_conditional_field_candidate_package.py; inversion_workflow/scripts/build_conditional_field_difference_audit.py; inversion_workflow/scripts/build_final_objective_decision_register.py; inversion_workflow/scripts/build_final_objective_scenario_matrix.py; inversion_workflow/scripts/build_final_objective_no_new_evidence_closeout_draft.py; inversion_workflow/scripts/build_final_objective_no_new_evidence_acceptance_template.py; inversion_workflow/scripts/build_nmr_trend_anomaly_followup_plan.py; inversion_workflow/scripts/build_frozen_model_measurement_inclusion_audit.py; inversion_workflow/permeability_residual_conflict_audit.md; inversion_workflow/permeability_support_conflict_spatial_audit.md; inversion_workflow/permeability_likelihood_policy_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_decision_request.md; inversion_workflow/permeability_configured_scalar_outlier_disposition.md; inversion_workflow/permeability_next_field_fit_gate.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/runs/continuous_inversion_loop/; inversion_workflow/runs/anisotropy_sensitivity_plan/; inversion_workflow/runs/local_basis_sampler_plan/; inversion_workflow/runs/local_anisotropy_sampler_plan/; inversion_workflow/runs/production_sampler_convergence/; inversion_workflow/runs/cross_stream_hybrid_field_plan/; inversion_workflow/runs/structural_edz_field_family_plan/; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/; inversion_workflow/runs/adaptive_combined_candidate_plan/; inversion_workflow/runs/bayesian_candidate_proposal/; inversion_workflow/runs/continuous_bayesian_candidate_plan/; inversion_workflow/runs/lower_support_continuous_candidate_plan/; inversion_workflow/measurement_likelihood_model.md; inversion_workflow/cross_stream_candidate_scorecard.md; inversion_workflow/current_field_selection_audit.md; inversion_workflow/frozen_model_measurement_inclusion_audit.md; inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES.md; inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md; inversion_workflow/final_objective_decision_register.md; inversion_workflow/final_objective_scenario_matrix.md; inversion_workflow/final_objective_no_new_evidence_closeout_draft.md; inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.md",
    )

    add_row(
        rows,
        requirement_id="R13_open_questions",
        requirement="Resolve collaborator comments and remaining provenance/calibration questions where possible.",
        status="partial",
        evidence=(
            "Report resolves homogeneity/heterogeneity and relative-permeability formulation comments; "
            "thermal-expansivity audit proves the active CTE value is implausible as written, and "
            f"the CTE confirmation request is {cte_confirmation_status} with request status "
            f"{cte_confirmation_request_status}, Gmail draft {cte_confirmation_gmail_draft_id or 'none'}, "
            f"and response status {cte_confirmation_response_status}; "
            "the historical permeability endpoint request package now specifies the five missing traces; "
            "the other-HM request package now specifies the missing numeric Geoscope/laser/levelling exports; "
            "the other-HM numeric source audit verifies that the current local bundle has support geometry "
            "and slide-summary rows but zero hard-residual-ready request classes; "
            "the RH provenance request package now specifies the active-curve generation, time-axis, "
            "sensor-screening, conversion, and open/closed curve-mapping questions; "
            "the consolidated measurement gate-closure package now turns the 7 failed gates "
            "and 4 warnings into concrete external requests and internal decisions; "
            "the external gate request pack splits the 7 external requests into recipient-specific "
            "drafts, contact-route fields, and a tracking table; "
            "the external response-intake tracker creates stream-specific intake directories and "
            "records acceptance tests/refresh commands for each expected answer; "
            f"the external dispatch audit records {external_dispatch_ready_count}/"
            f"{external_dispatch_request_count} requests ready to send with "
            f"{external_dispatch_failed_check_count} failed checks and suggested To routes for "
            f"{external_dispatch_suggested_to_count} request rows; it also records "
            f"{external_dispatch_unique_gmail_draft_count} Gmail drafts covering "
            f"{external_dispatch_gmail_draft_request_count} request rows, while "
            f"{external_dispatch_missing_response_count} responses remain missing; "
            f"the local gate recovery audit rescans {local_gate_recovery_document_count} local source/index "
            f"documents and records {local_gate_recovery_evidence_count} keyword evidence rows, "
            f"{local_gate_recovery_possible_closure_count} possible gate-closing rows, and "
            f"{len(local_gate_recovery_still_external_gates)} gates still external after the local rescan; "
            f"the Downloads recovery audit scans {download_gate_recovery_document_count} raw-download documents "
            f"and records {download_gate_recovery_evidence_count} keyword evidence rows, "
            f"{download_gate_recovery_possible_closure_count} possible gate-closing rows, "
            f"{download_gate_recovery_duplicate_count} SHA1-verified duplicate/catalogue rows, and "
            f"{download_gate_recovery_run_dir_count} uncatalogued extracted/run-output directory; "
            f"the Gmail live-state audit checked the mailbox at {gmail_live_state_checked_at}, observed "
            f"{gmail_live_state_observed_draft_count}/{gmail_live_state_expected_draft_count} expected "
            f"external/CTE drafts, found {gmail_live_state_sent_result_count} sent-subject hits, "
            f"{gmail_live_state_provider_reply_count} provider-reply hits, and "
            f"{gmail_live_state_teambeam_non_draft_count} recent CD-A/HERMES/TeamBeam non-draft hits; "
            f"the external blocker dashboard consolidates those trackers into "
            f"{external_blocker_dashboard_count} blocker rows "
            f"({external_blocker_dashboard_external_count} external measurement gates and "
            f"{external_blocker_dashboard_cte_count} CTE confirmation row), with "
            f"{external_blocker_dashboard_open_count} open, {external_blocker_dashboard_unsent_count} unsent, "
            f"and {external_blocker_dashboard_missing_count} missing responses; "
            f"the internal gate decision register records local policies for {internal_gate_decision_count} internal "
            "or internal-with-confirmation items without closing external provenance/calibration gates; "
            "the NMR objective decision package now recommends within-label trend/anomaly "
            "residuals and the objective assembler now has a provisional executable mode "
            "plus a separate ranking package while the internal policy keeps the default active "
            "objective unchanged for the current report state, and the NMR acceptance template records "
            f"{nmr_final_policy_acceptance_recorded}/{nmr_final_policy_acceptance_required} primary approvals "
            f"with ready-to-apply={nmr_final_policy_acceptance_ready}; "
            "the direct permeability likelihood-policy audit keeps the row-Gaussian objective "
            "recorded but flags robust/aggregation semantics as a modelling-team decision before "
            "more active-objective OGS spending, the decision request records the exact options, "
            f"and the acceptance template records {permeability_policy_acceptance_recorded}/"
            f"{permeability_policy_acceptance_required} primary approvals with ready-to-apply="
            f"{permeability_policy_acceptance_ready}; "
            f"the report open-comment audit records {report_open_marker_count} active LaTeX markers, "
            f"{report_resolved_formulation_count} resolved formulation comments, "
            f"{report_tracked_external_count} external request gates, and "
            f"{report_tracked_internal_count} internal/provenance/operational items; "
            f"the final inversion promotion checklist records decision={final_promotion_decision}, "
            f"{final_promotion_open_count} open promotion criteria, and status counts "
            f"{final_promotion_status_counts}; "
            f"the final inversion close-out playbook records {final_closeout_open_count} open criteria, "
            f"{final_closeout_external_count} draft/response actions, "
            f"{final_closeout_internal_count} internal policy action, and "
            f"{final_closeout_scenario_count} scenario/final decision actions; "
            f"the Gmail draft send-review packet records {gmail_draft_review_count} drafts "
            f"covering {gmail_draft_review_request_count} requests, with "
            f"{gmail_draft_review_ready_count} ready for user review and "
            f"{gmail_draft_review_unsent_count} still unsent; "
            f"the final objective decision register records {final_objective_decision_count} "
            f"include/exclude decisions, including {final_objective_external_count} external stream "
            f"decisions, {final_objective_internal_count} internal policy decision, "
            f"{final_objective_scenario_count} scenario/final decisions, and "
            f"{final_objective_pending_count} pending or not-ready rows; "
            f"the final objective scenario matrix records {final_objective_scenario_option_count} "
            f"scenario options, {final_objective_scenario_current_winning_count} current-field winning "
            f"options, {final_objective_scenario_unique_winner_count} unique winners, and "
            f"{final_objective_scenario_unscored_count} unscored future option; "
            f"the no-new-evidence closeout draft records {final_objective_no_new_count} "
            f"draft decision rows, including {final_objective_no_new_external_count} external/provenance "
            f"rows, {final_objective_no_new_internal_count} internal policy row, and "
            f"{final_objective_no_new_scenario_count} scenario/final rows; it would select "
            f"{final_objective_no_new_scenario} with winner {final_objective_no_new_winner} only "
            f"if approved and regenerated, and records decisions={final_objective_no_new_records_decisions}, "
            f"promotes field={final_objective_no_new_promotes_field}, unblocks promotion="
            f"{final_objective_no_new_unblocks_promotion}; the acceptance-record template has "
            f"{final_objective_no_new_acceptance_recorded}/"
            f"{final_objective_no_new_acceptance_required} approvals recorded and ready-to-apply="
            f"{final_objective_no_new_acceptance_ready}; "
            f"the open-question resolution matrix records {open_question_resolution_row_count} rows, "
            f"{open_question_resolution_resolved_count} locally resolved/current-scope rows, "
            f"{open_question_resolution_external_count} external send/response rows, and "
            f"{open_question_resolution_internal_count} internal policy/final-decision rows; "
            "WORK_STATUS still tracks CTE confirmation and external data delivery."
        ),
        remaining_work="Review/send and close the CTE confirmation Gmail draft, get answers/files for the RH provenance request, obtain the requested Geoscope/laser-scan exports, obtain or approve missing historical permeability endpoints, keep the recorded NMR trend/anomaly not-default policy unless the modelling team reopens it, record any change to the direct-permeability robust/support-cell likelihood policy before more active-objective OGS spending, review/send the dispatch-ready recipient-specific external gate Gmail drafts, file responses through the intake tracker, then record an include, diagnostic-only, exclusion, or waiver decision in the final objective decision register. If the no-new-evidence draft is accepted, record its exact decisions first, rerun the scenario/current-field/promotion audits, and only then pick or reject the F01 scenario before refreshing the external blocker dashboard, local gate recovery, Downloads recovery, report open-comment audit, scenario audit, and current-field selection audit.",
        authoritative_artifacts="main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/report_open_comment_audit.md; inversion_workflow/open_question_resolution_matrix.md; inversion_workflow/thermal_expansivity_parameter_audit.md; inversion_workflow/cte_confirmation_request.md; inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/permeability_likelihood_decision_request.md; inversion_workflow/measurement_gate_closure_request.md; inversion_workflow/local_gate_recovery_audit.md; inversion_workflow/download_gate_recovery_audit.md; inversion_workflow/gmail_gate_live_state_audit.md; inversion_workflow/gmail_draft_send_review_packet.md; inversion_workflow/external_blocker_dashboard.md; inversion_workflow/final_inversion_promotion_checklist.md; inversion_workflow/final_inversion_closeout_playbook.md; inversion_workflow/final_objective_decision_register.md; inversion_workflow/final_objective_scenario_matrix.md; inversion_workflow/final_objective_no_new_evidence_closeout_draft.md; inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.md; inversion_workflow/external_gate_request_pack.md; inversion_workflow/external_gate_dispatch_audit.md; inversion_workflow/external_gate_response_intake.md; inversion_workflow/internal_gate_decision_register.md; inversion_workflow/measurement_gate_closure_email_draft.md; inversion_workflow/processed_observations/rh_boundary_provenance_request.md; inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md; inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; inversion_workflow/processed_observations/other_hm_numeric_source_audit.md",
    )

    frame = pd.DataFrame(rows)
    counts = status_counts(rows)
    worst = max((STATUS_RANK.get(row["status"], 99) for row in rows), default=99)
    completion_state = "not_complete" if worst > STATUS_RANK["achieved_with_tracked_caveats"] else "complete"
    incomplete_statuses = {"ready_pending_external_execution", "partial", "blocked_external", "incomplete", "missing"}
    blocking_statuses = {"blocked_external", "incomplete", "missing"}
    partial_items = [row for row in rows if row["status"] == "partial"]
    incomplete_items = [row for row in rows if row["status"] in incomplete_statuses]
    blocking_items = [row for row in rows if row["status"] in blocking_statuses]
    summary = {
        "completion_state": completion_state,
        "requirement_count": int(frame.shape[0]),
        "status_counts": counts,
        "non_complete_requirement_ids": [row["requirement_id"] for row in incomplete_items],
        "partial_requirement_ids": [row["requirement_id"] for row in partial_items],
        "blocking_or_incomplete_requirement_ids": [row["requirement_id"] for row in blocking_items],
        "blocking_or_incomplete_or_partial_requirement_ids": [
            row["requirement_id"] for row in incomplete_items
        ],
        "highest_priority_next_steps": [
            (
            "Pause the active direct-permeability plus NMR production sampler; the cross-stream hybrid, local-anisotropy, and structural/EDZ screens found no direct-improving follow-up family, and the support lower-bound audit shows zero same-support reducible direct-permeability gap, so prioritize measurement-stream gates or a support/likelihood/parameterization decision before more OGS runs."
                if production_decision.get("recommendation") == "pause_active_production_sampling"
                else "Use the production sampler/convergence audit to decide whether the next release-gated executable batch is worth running; treat it as convergence evidence, not final inversion proof."
            ),
            f"Use the permeability next field-fit gate before any new OGS spending: status={permeability_next_gate_status}, recommendation={permeability_next_gate_recommendation}, same-support active-objective batch executable now={permeability_next_gate_executable_now}, gate counts={permeability_next_gate_status_counts}.",
            f"Use the permeability likelihood/support recommendation packet before changing the direct objective: status={permeability_support_recommendations_status}, recommendations={permeability_support_recommendations_count}, current policy={permeability_support_recommendations_current_policy}, at lower bound={permeability_support_recommendations_at_lower_bound}, same-support gap={permeability_support_recommendations_same_support_gap}, same-support batch executable now={permeability_support_recommendations_batch_executable}, bounds release now={permeability_support_recommendations_bounds_release_now}, tensor-shape release now={permeability_support_recommendations_tensor_release_now}, promotion unblocked={permeability_support_recommendations_unblocks_promotion}.",
            f"Use the permeability likelihood-policy acceptance template as the signoff guardrail before changing the direct objective: status={permeability_policy_acceptance_status}, primary approvals recorded/required={permeability_policy_acceptance_recorded}/{permeability_policy_acceptance_required}, ready to apply={permeability_policy_acceptance_ready}, records decision={permeability_policy_acceptance_records_decision}, changes objective={permeability_policy_acceptance_changes_objective}, same-support batch executable now={permeability_policy_acceptance_same_support_executable}.",
            f"Use the configured-scalar outlier disposition before releasing permeability bounds or tensor shape: status={permeability_outlier_disposition_status}, rows/groups={permeability_outlier_disposition_rows}/{permeability_outlier_disposition_groups}, max envelope excess={permeability_outlier_disposition_max_excess}, bounds release now={permeability_outlier_bounds_release_now}, tensor-shape release now={permeability_outlier_tensor_release_now}.",
            "Use the stream activation-gate audit to close the 7 required failed gates before promoting ERT/Taupe/RH/other-HM hard residuals.",
            "Keep the direct-permeability rowwise Gaussian policy as the recorded current-report default unless the permeability likelihood decision request is explicitly answered; use the existing-field rerank evidence, and refresh it if the accepted robust/support-cell policy formula changes.",
            f"Use the NMR final residual policy gate before changing the NMR default: status={nmr_final_policy_status}, final policy selected={nmr_final_policy_selected}, current default={nmr_final_policy_current_default}, recommended candidate={nmr_final_policy_recommended}, follow-up={nmr_final_policy_followup}.",
            f"Use the NMR final residual-policy acceptance template as the signoff guardrail before changing the NMR default: status={nmr_final_policy_acceptance_status}, primary approvals recorded/required={nmr_final_policy_acceptance_recorded}/{nmr_final_policy_acceptance_required}, ready to apply={nmr_final_policy_acceptance_ready}, records decision={nmr_final_policy_acceptance_records_decision}, changes objective={nmr_final_policy_acceptance_changes_objective}, new OGS batch recommended now={nmr_final_policy_acceptance_new_ogs}.",
            f"Review/send the {external_dispatch_unique_gmail_draft_count} Gmail drafts covering {external_pack_request_count} external requests; suggested To routes are resolved for {external_pack_recipient_with_to_count}/{external_pack_recipient_count} recipients, the dispatch audit marks {external_dispatch_ready_count}/{external_dispatch_request_count} requests ready with {external_dispatch_failed_check_count} failed checks, and replies still need filing through the response-intake tracker, which currently records {external_intake_missing_count} missing responses.",
            f"The Gmail live-state audit checked the mailbox at {gmail_live_state_checked_at}: {gmail_live_state_observed_draft_count}/{gmail_live_state_expected_draft_count} expected external/CTE drafts were still observed as drafts, with {gmail_live_state_sent_result_count} sent-subject hits and {gmail_live_state_provider_reply_count} provider-reply hits.",
            f"Use the external blocker dashboard as the single send/response worklist: {external_blocker_dashboard_open_count}/{external_blocker_dashboard_count} blockers are open, including {external_blocker_dashboard_external_count} measurement gates and {external_blocker_dashboard_cte_count} CTE confirmation row.",
            f"Use the final inversion promotion checklist as the single all-measurement promotion gate: decision={final_promotion_decision}, {final_promotion_open_count}/{final_promotion_criterion_count} criteria open, and status counts {final_promotion_status_counts}.",
            f"Use the final inversion close-out playbook for action routing: {final_closeout_open_count} open criteria, {final_closeout_external_count} draft/response actions, {final_closeout_internal_count} internal policy action, {final_closeout_scenario_count} scenario/final decision actions, and draft ids {final_closeout_draft_ids}.",
            f"Use the final objective decision register to record include/exclude outcomes before final promotion: {final_objective_decision_count} decisions, {final_objective_external_count} external stream decisions, {final_objective_internal_count} internal policy decision, {final_objective_scenario_count} scenario/final decisions, {final_objective_pending_count} pending or not-ready rows, and {final_objective_exclusion_count} rows with an explicit exclusion path.",
            f"Use the final objective scenario matrix to choose or reject one final objective explicitly: {final_objective_scenario_option_count} options, {final_objective_scenario_current_winning_count} current-field winning options, {final_objective_scenario_unique_winner_count} unique winners, {final_objective_scenario_unscored_count} unscored future option, and {final_objective_scenario_non_likelihood_count} options needing a new policy or not representing a final likelihood.",
            f"Use the final objective include/exclude recommendations as the conservative no-new-evidence packet: status={final_objective_recommendation_status}, {final_objective_recommendation_count} recommendations, {final_objective_recommendation_external_count} external/provenance rows, {final_objective_recommendation_diagnostic_or_exclude_count} diagnostic-or-exclude recommendations, {final_objective_recommendation_waiver_not_recommended_count} waivers not recommended, and promotion unblocked={final_objective_recommendation_unblocks_promotion}.",
            f"Use the final objective no-new-evidence closeout draft only as review text until accepted: status={final_objective_no_new_status}, {final_objective_no_new_count} draft rows, would-select scenario={final_objective_no_new_scenario}, winner={final_objective_no_new_winner}, requires approval={final_objective_no_new_requires_approval}, records decisions={final_objective_no_new_records_decisions}, promotes field={final_objective_no_new_promotes_field}, and unblocks promotion={final_objective_no_new_unblocks_promotion}.",
            f"Use the no-new-evidence acceptance-record template as the signoff guardrail if F01 is chosen: status={final_objective_no_new_acceptance_status}, approvals recorded/required={final_objective_no_new_acceptance_recorded}/{final_objective_no_new_acceptance_required}, ready to apply={final_objective_no_new_acceptance_ready}, records decisions={final_objective_no_new_acceptance_records_decisions}, promotes field={final_objective_no_new_acceptance_promotes_field}.",
            f"Use the open-question resolution matrix as the orientation layer: status={open_question_resolution_status}, rows={open_question_resolution_row_count}, resolved/current-scope rows={open_question_resolution_resolved_count}, external send/response rows={open_question_resolution_external_count}, internal policy/final-decision rows={open_question_resolution_internal_count}, status counts={open_question_resolution_counts}.",
            f"Use the Gmail draft send-review packet to review outbound drafts before any send: {gmail_draft_review_ready_count}/{gmail_draft_review_count} drafts ready, {gmail_draft_review_unsent_count} unsent, {gmail_draft_review_request_count} covered requests, draft ids {gmail_draft_review_ids}.",
            f"The local gate recovery audit rescanned {local_gate_recovery_document_count} source/index documents and found {local_gate_recovery_possible_closure_count} local gate-closing evidence rows, so the {len(local_gate_recovery_still_external_gates)} failed external gates still need provider answers/files unless new local files are added.",
            f"The Downloads recovery audit scanned {download_gate_recovery_document_count} raw-download documents and found {download_gate_recovery_possible_closure_count} gate-closing evidence rows; it records {download_gate_recovery_duplicate_count} SHA1-verified duplicate/catalogue rows and {download_gate_recovery_run_dir_count} uncatalogued extracted/run-output directory.",
            "Keep the recorded NMR trend/anomaly not-default policy for the current report state; use it only as explicit scenario/provisional likelihood evidence unless the modelling team reopens the objective semantics.",
            f"Use the RH provenance request package to resolve boundary-curve generation before releasing retention or boundary parameters; review/send the CTE Gmail draft to {cte_confirmation_suggested_to} with {cte_confirmation_suggested_cc} as CC and record the response.",
            "Obtain the requested Geoscope/laser-scan exports and historical permeability endpoint geometry if those streams should become hard residuals.",
        ],
        "key_numbers": {
            "observation_manifest_failures": manifest.get("failures"),
            "processed_table_count": processed_table_count,
            "processed_total_rows": processed_total_rows,
            "observation_groups": observation_groups,
            "active_objective_groups": active_groups,
            "measurement_model_entry_matrix_status": model_entry_status,
            "measurement_model_entry_matrix_row_count": model_entry_rows,
            "measurement_model_entry_matrix_active_measurement_count": model_entry_active_count,
            "measurement_model_entry_matrix_active_objective_rows": model_entry_active_rows,
            "measurement_model_entry_matrix_entry_class_counts": model_entry_class_counts,
            "measurement_model_entry_matrix_final_decision_status_counts": model_entry_final_decisions,
            "measurement_model_entry_matrix_rows_without_likelihood_row": model_entry_missing_likelihood,
            "measurement_report_traceability_status": traceability_status,
            "measurement_report_traceability_observation_count": traceability_observation_count,
            "measurement_report_traceability_all_observations_traceable": traceability_all,
            "measurement_report_traceability_status_counts": traceability_status_counts,
            "measurement_report_traceability_manifest_check_count": traceability_manifest_checks,
            "measurement_report_traceability_manifest_failures": traceability_manifest_failures,
            "measurement_report_traceability_missing_chapter_section_count": traceability_missing_sections,
            "measurement_report_traceability_missing_inventory_table_reference_count": traceability_missing_table_refs,
            "measurement_report_traceability_missing_model_entry_statement_count": traceability_missing_model_entry,
            "measurement_report_traceability_missing_artifact_observation_count": traceability_missing_artifact_obs,
            "measurement_report_traceability_data_content_fact_rows": traceability_data_content_rows,
            "measurement_report_traceability_missing_data_content_summary_count": traceability_missing_data_content,
            "measurement_content_deep_dive_total_rows": measurement_content_total_rows,
            "measurement_content_deep_dive_counts": measurement_content_counts,
            "state_target_rows": state_target_rows,
            "state_rows_without_ogs_samples": no_ogs_state_samples,
            "sampled_ogs_outputs": sampled_ogs_outputs,
            "sampled_state_rows": sampled_state_rows,
            "active_state_objective_rows": active_state_rows,
            "nmr_candidate_bias_sensitivity_runs": nmr_bias_runs,
            "nmr_candidate_bias_best_label_bias_run": nmr_bias_best_label.get("run_id"),
            "nmr_candidate_bias_best_label_bias_combined_objective": nmr_bias_best_label.get(
                "label_bias_combined_objective"
            ),
            "nmr_candidate_bias_best_trend_anomaly_run": nmr_bias_best_trend.get("run_id"),
            "nmr_candidate_bias_best_trend_anomaly_combined_objective": nmr_bias_best_trend.get(
                "trend_anomaly_combined_objective"
            ),
            "nmr_candidate_bias_current_vs_label_bias_rank_correlation": nmr_bias_rank_corr,
            "nmr_objective_decision_recommended_option": nmr_decision_recommended,
            "nmr_objective_decision_active_objective_changed": nmr_decision_changed,
            "nmr_objective_decision_best_recommended_run": nmr_decision_best_run,
            "nmr_objective_decision_best_recommended_current_rank": nmr_decision_best_current_rank,
            "nmr_objective_decision_current_incumbent_recommended_rank": nmr_decision_current_incumbent_rank,
            "nmr_trend_anomaly_activation_status": nmr_trend_activation.get("status"),
            "nmr_trend_anomaly_activation_full_active_runs": nmr_trend_activation_runs,
            "nmr_trend_anomaly_activation_best_run": nmr_trend_activation_best.get("run_id"),
            "nmr_trend_anomaly_activation_best_objective": nmr_trend_activation_best.get(
                "nmr_trend_anomaly_active_objective"
            ),
            "nmr_trend_anomaly_activation_raw_incumbent_rank": nmr_trend_activation_raw_incumbent_rank,
            "nmr_trend_anomaly_activation_winner_raw_rank": nmr_trend_activation_winner_raw_rank,
            "nmr_trend_anomaly_activation_validation_max_abs_delta": nmr_trend_activation_validation_delta,
            "nmr_final_residual_policy_gate_status": nmr_final_policy_status,
            "nmr_final_residual_policy_selected": nmr_final_policy_selected,
            "nmr_final_residual_policy_current_default": nmr_final_policy_current_default,
            "nmr_final_residual_policy_recommended_candidate": nmr_final_policy_recommended,
            "nmr_final_residual_policy_recommended_run": nmr_final_policy_recommended_run,
            "nmr_final_residual_policy_followup_recommendation": nmr_final_policy_followup,
            "nmr_final_residual_policy_materiality_threshold": nmr_final_policy_materiality,
            "nmr_final_residual_policy_best_unevaluated_direct_advantage": nmr_final_policy_best_advantage,
            "nmr_final_residual_policy_median_state_beating_candidates": nmr_final_policy_median_beating,
            "nmr_final_residual_policy_acceptance_record_template_status": nmr_final_policy_acceptance_status,
            "nmr_final_residual_policy_acceptance_record_template_row_count": nmr_final_policy_acceptance_rows,
            "nmr_final_residual_policy_acceptance_record_template_primary_approval_rows_recorded": nmr_final_policy_acceptance_recorded,
            "nmr_final_residual_policy_acceptance_record_template_primary_approval_rows_required": nmr_final_policy_acceptance_required,
            "nmr_final_residual_policy_acceptance_record_template_ready_to_apply": nmr_final_policy_acceptance_ready,
            "nmr_final_residual_policy_acceptance_record_template_records_decision": nmr_final_policy_acceptance_records_decision,
            "nmr_final_residual_policy_acceptance_record_template_changes_active_objective": nmr_final_policy_acceptance_changes_objective,
            "nmr_final_residual_policy_acceptance_record_template_promotes_current_field": nmr_final_policy_acceptance_promotes_field,
            "nmr_final_residual_policy_acceptance_record_template_new_ogs_batch_recommended_now": nmr_final_policy_acceptance_new_ogs,
            "measurement_stream_gate_required_failures": stream_gate_required_failures,
            "measurement_stream_gate_required_warnings": stream_gate_required_warnings,
            "measurement_stream_gate_diagnostic_or_boundary_only_count": stream_gate_diagnostic_or_boundary,
            "measurement_stream_gate_not_ready_hard_residual_count": stream_gate_not_ready,
            "measurement_stream_gate_promotion_decision_counts": stream_gate_decisions,
            "measurement_gate_closure_request_count": gate_closure_request_count,
            "measurement_gate_closure_external_request_count": gate_closure_external_count,
            "measurement_gate_closure_internal_decision_count": gate_closure_internal_count,
            "measurement_gate_closure_high_priority_request_ids": gate_closure_high_priority,
            "external_gate_request_pack_status": external_pack_status,
            "external_gate_request_pack_request_count": external_pack_request_count,
            "external_gate_request_pack_recipient_count": external_pack_recipient_count,
            "external_gate_request_pack_high_priority_count": external_pack_high_priority_count,
            "external_gate_request_pack_medium_priority_count": external_pack_medium_priority_count,
            "external_gate_request_pack_request_ids": external_pack_request_ids,
            "external_gate_request_pack_recipient_with_suggested_to_count": external_pack_recipient_with_to_count,
            "external_gate_request_pack_recipient_with_suggested_cc_count": external_pack_recipient_with_cc_count,
            "external_gate_request_pack_contact_route_counts": external_pack_contact_route_counts,
            "external_gate_response_intake_status": external_intake_status,
            "external_gate_response_intake_tracked_request_count": external_intake_tracked_count,
            "external_gate_response_intake_missing_response_count": external_intake_missing_count,
            "external_gate_response_intake_directory_count": external_intake_dir_count,
            "external_gate_response_intake_note_template_count": external_intake_template_count,
            "external_gate_response_intake_with_suggested_to_count": external_intake_with_to_count,
            "external_gate_dispatch_audit_status": external_dispatch_status,
            "external_gate_dispatch_request_count": external_dispatch_request_count,
            "external_gate_dispatch_ready_request_count": external_dispatch_ready_count,
            "external_gate_dispatch_failed_check_count": external_dispatch_failed_check_count,
            "external_gate_dispatch_draft_count": external_dispatch_draft_count,
            "external_gate_dispatch_gmail_draft_request_count": external_dispatch_gmail_draft_request_count,
            "external_gate_dispatch_unique_gmail_draft_count": external_dispatch_unique_gmail_draft_count,
            "external_gate_dispatch_gmail_send_status_counts": external_dispatch_gmail_send_status_counts,
            "external_gate_dispatch_not_sent_request_count": external_dispatch_not_sent_count,
            "external_gate_dispatch_missing_response_count": external_dispatch_missing_response_count,
            "external_gate_dispatch_suggested_to_present_count": external_dispatch_suggested_to_count,
            "external_gate_dispatch_suggested_cc_present_count": external_dispatch_suggested_cc_count,
            "external_gate_dispatch_contact_route_counts": external_dispatch_contact_route_counts,
            "gmail_gate_live_state_status": gmail_live_state_status,
            "gmail_gate_live_state_checked_at": gmail_live_state_checked_at,
            "gmail_gate_live_state_expected_draft_count_including_cte": gmail_live_state_expected_draft_count,
            "gmail_gate_live_state_observed_draft_count": gmail_live_state_observed_draft_count,
            "gmail_gate_live_state_sent_subject_search_result_count": gmail_live_state_sent_result_count,
            "gmail_gate_live_state_provider_reply_search_result_count": gmail_live_state_provider_reply_count,
            "gmail_gate_live_state_teambeam_context_non_draft_result_count": gmail_live_state_teambeam_non_draft_count,
            "external_blocker_dashboard_status": external_blocker_dashboard_status,
            "external_blocker_dashboard_blocker_count": external_blocker_dashboard_count,
            "external_blocker_dashboard_open_blocker_count": external_blocker_dashboard_open_count,
            "external_blocker_dashboard_unsent_blocker_count": external_blocker_dashboard_unsent_count,
            "external_blocker_dashboard_missing_response_blocker_count": external_blocker_dashboard_missing_count,
            "external_blocker_dashboard_external_measurement_blocker_count": external_blocker_dashboard_external_count,
            "external_blocker_dashboard_cte_confirmation_blocker_count": external_blocker_dashboard_cte_count,
            "external_blocker_dashboard_open_blocker_ids": external_blocker_dashboard_open_ids,
            "local_gate_recovery_status": local_gate_recovery_status,
            "local_gate_recovery_document_count": local_gate_recovery_document_count,
            "local_gate_recovery_evidence_row_count": local_gate_recovery_evidence_count,
            "local_gate_recovery_possible_closure_evidence_count": local_gate_recovery_possible_closure_count,
            "local_gate_recovery_keyword_candidate_not_closure_count": local_gate_recovery_keyword_candidate_count,
            "local_gate_recovery_gates_with_possible_closure": local_gate_recovery_possible_closure_gates,
            "local_gate_recovery_gates_still_external_after_rescan": local_gate_recovery_still_external_gates,
            "download_gate_recovery_status": download_gate_recovery_status,
            "download_gate_recovery_document_count": download_gate_recovery_document_count,
            "download_gate_recovery_evidence_row_count": download_gate_recovery_evidence_count,
            "download_gate_recovery_possible_closure_evidence_count": download_gate_recovery_possible_closure_count,
            "download_gate_recovery_keyword_candidate_not_closure_count": download_gate_recovery_keyword_candidate_count,
            "download_gate_recovery_gates_with_possible_closure": download_gate_recovery_possible_closure_gates,
            "download_gate_recovery_gates_still_external_after_scan": download_gate_recovery_still_external_gates,
            "download_gate_recovery_inventory_row_count": download_gate_recovery_inventory_count,
            "download_gate_recovery_catalogued_duplicate_sha1_verified_count": download_gate_recovery_duplicate_count,
            "download_gate_recovery_uncatalogued_extracted_or_run_output_directory_count": download_gate_recovery_run_dir_count,
            "cte_confirmation_request_status": cte_confirmation_status,
            "cte_confirmation_request_request_status": cte_confirmation_request_status,
            "cte_confirmation_request_response_status": cte_confirmation_response_status,
            "cte_confirmation_gmail_draft_id": cte_confirmation_gmail_draft_id,
            "cte_confirmation_gmail_send_status": cte_confirmation_gmail_send_status,
            "cte_confirmation_request_suggested_to": cte_confirmation_suggested_to,
            "cte_confirmation_request_suggested_cc": cte_confirmation_suggested_cc,
            "report_open_comment_audit_status": report_open_status,
            "report_active_unresolved_marker_count": report_open_marker_count,
            "report_resolved_formulation_comment_count": report_resolved_formulation_count,
            "report_tracked_external_gate_count": report_tracked_external_count,
            "report_tracked_internal_or_provenance_item_count": report_tracked_internal_count,
            "report_false_positive_marker_count": report_false_positive_count,
            "report_active_open_item_ids": report_open_item_ids,
            "open_question_resolution_matrix_status": open_question_resolution_status,
            "open_question_resolution_matrix_row_count": open_question_resolution_row_count,
            "open_question_resolution_matrix_status_counts": open_question_resolution_counts,
            "open_question_resolution_matrix_resolved_or_current_scope_count": open_question_resolution_resolved_count,
            "open_question_resolution_matrix_external_or_send_response_required_count": (
                open_question_resolution_external_count
            ),
            "open_question_resolution_matrix_internal_policy_or_final_decision_count": (
                open_question_resolution_internal_count
            ),
            "ogs_formulation_consistency_status": ogs_formulation_status,
            "ogs_formulation_consistency_check_count": ogs_formulation_check_count,
            "ogs_formulation_consistency_fail_count": ogs_formulation_fail_count,
            "ogs_formulation_consistency_hard_checks_pass": ogs_formulation_hard_checks_pass,
            "ogs_formulation_consistency_tracked_caveat_count": ogs_formulation_tracked_caveat_count,
            "ogs_formulation_consistency_process_type": ogs_formulation_process_type,
            "ogs_formulation_consistency_primary_variables": ogs_formulation_primary_variables,
            "ogs_formulation_consistency_run_local_field_parameters": ogs_formulation_run_fields,
            "ogs_run_input_audit_status": ogs_run_input_status,
            "ogs_run_input_check_count": ogs_run_input_check_count,
            "ogs_run_input_warning_count": ogs_run_input_warning_count,
            "ogs_run_input_error_count": ogs_run_input_error_count,
            "ogs_run_input_unreadable_meshio_meshes": ogs_run_input_unreadable_meshes,
            "ogs_run_input_execution_returncode": ogs_run_input_execution_returncode,
            "ogs_run_input_execution_backend": ogs_run_input_execution_backend,
            "citation_locator_audit_status": citation_locator_status,
            "citation_key_instance_count": citation_key_instances,
            "citation_unique_cited_key_count": citation_unique_keys,
            "citation_missing_or_weak_locator_count": citation_missing_or_weak_locator,
            "citation_missing_bib_entry_count": citation_missing_bib,
            "citation_unavailable_fulltext_missing_log_count": citation_unavailable_missing_log,
            "citation_fulltext_status_counts": citation_fulltext_statuses,
            "internal_gate_decision_count": internal_gate_decision_count,
            "internal_gate_local_policy_recorded_count": internal_gate_local_policy_count,
            "internal_gate_active_or_ready_policy_count": internal_gate_active_or_ready_count,
            "internal_gate_diagnostic_or_boundary_policy_count": internal_gate_diagnostic_or_boundary_count,
            "internal_gate_still_external_or_activation_gated_count": internal_gate_still_gated_count,
            "internal_gate_remaining_confirmation_or_promotion_caveat_count": internal_gate_remaining_caveat_count,
            "internal_gate_not_promoted_default_policy_count": internal_gate_not_promoted_default_count,
            "nmr_default_promotion_status": nmr_default_promotion_status,
            "permeability_likelihood_policy_status": permeability_likelihood_policy_status,
            "internal_gate_status_counts": internal_gate_status_counts,
            "cross_stream_scorecard_runs": cross_stream_runs,
            "cross_stream_scorecard_pareto_all_streams_count": cross_stream_pareto,
            "cross_stream_scorecard_top10_all_stream_candidates": cross_stream_top10_all,
            "cross_stream_best_mean_rank_candidate": cross_stream_best_mean.get("run_id"),
            "cross_stream_best_mean_rank": cross_stream_best_mean.get("mean_rank_all_streams"),
            "cross_stream_best_mean_worst_rank": cross_stream_best_mean.get("worst_rank_all_streams"),
            "cross_stream_active_incumbent_candidate": cross_stream_active.get("run_id"),
            "cross_stream_active_incumbent_nmr_label_bias_rank": cross_stream_active.get("nmr_label_bias_rank"),
            "cross_stream_active_incumbent_ert_rank": cross_stream_active.get("ert_mae_rank"),
            "cross_stream_active_incumbent_taupe_rank": cross_stream_active.get("taupe_mae_rank"),
            "cross_stream_hybrid_candidate_count": cross_stream_hybrid_candidate_count,
            "cross_stream_hybrid_target_run_count": cross_stream_hybrid_target_count,
            "cross_stream_hybrid_best_candidate": cross_stream_hybrid_best.get("candidate_id"),
            "cross_stream_hybrid_best_target_run": cross_stream_hybrid_best.get("target_run_id"),
            "cross_stream_hybrid_best_alpha": cross_stream_hybrid_best.get("alpha"),
            "cross_stream_hybrid_best_direct_objective": cross_stream_hybrid_best.get("objective_value"),
            "cross_stream_hybrid_best_delta_vs_active": cross_stream_hybrid_best_delta,
            "cross_stream_hybrid_best_weighted_rmse_log10": cross_stream_hybrid_best.get("weighted_rmse_log10"),
            "structural_edz_field_family_status": structural_edz_status,
            "structural_edz_field_family_candidate_count": structural_edz_candidate_count,
            "structural_edz_field_family_improving_candidate_count": structural_edz_improving_count,
            "structural_edz_field_family_best_candidate": structural_edz_best.get("candidate_id"),
            "structural_edz_field_family_best_family": structural_edz_best_family,
            "structural_edz_field_family_best_direct_objective": structural_edz_best.get("objective_value"),
            "structural_edz_field_family_best_delta_vs_active": structural_edz_best_delta,
            "structural_edz_field_family_best_weighted_rmse_log10": structural_edz_best.get("weighted_rmse_log10"),
            "structural_edz_field_family_active_support_cells": structural_edz_support_counts.get(
                "active_permeability_objective_support_cells"
            ),
            "structural_edz_field_family_ert_ready_support_cells": structural_edz_support_counts.get(
                "ert_ready_support_cells"
            ),
            "structural_edz_field_family_line_segments_available": structural_edz_support_counts.get(
                "line_segments_available"
            ),
            "current_permeability_field_package_status": current_field_status,
            "current_permeability_field_package_ready": current_field_package_ready,
            "current_permeability_field_deliverable_status": current_field_deliverable_status,
            "current_permeability_field_run_id": current_field_run_id,
            "current_permeability_field_mesh": current_field_mesh,
            "current_permeability_field_stats_csv": current_field_stats_csv,
            "current_permeability_field_triangle6_cell_count": current_field_cell_count,
            "current_permeability_field_positive_definite_cell_count": current_field_positive_cells,
            "current_permeability_field_non_positive_definite_cell_count": current_field_nonpositive_cells,
            "current_permeability_field_max_tensor_asymmetry_abs": current_field_max_asymmetry,
            "current_permeability_field_anisotropy_ratio_p50": current_field_anisotropy_p50,
            "current_permeability_field_theta_deg_p50": current_field_theta_p50,
            "current_permeability_field_porosity_p50": current_field_porosity_p50,
            "current_permeability_field_log10_k_eigen_min_p50": current_field_log10_kmin_p50,
            "current_permeability_field_log10_k_eigen_max_p50": current_field_log10_kmax_p50,
            "current_field_reproducibility_audit_status": current_field_repro_status,
            "current_field_reproducibility_audit_required_failures": current_field_repro_required_failures,
            "current_field_reproducibility_audit_check_count": current_field_repro_check_count,
            "current_field_reproducibility_manifest_row_count": current_field_repro_manifest_rows,
            "current_field_reproducibility_run_input_snapshot_file_count": current_field_repro_run_input_files,
            "current_field_reproducibility_project_reference_count": current_field_repro_project_refs,
            "current_field_reproducibility_direct_used_rows": current_field_repro_direct_rows,
            "current_field_reproducibility_state_used_rows": current_field_repro_state_rows,
            "current_field_visual_inspection_status": current_field_visual_status,
            "current_field_visual_inspection_image_count": current_field_visual_image_count,
            "current_field_visual_inspection_positive_definite_cells": current_field_visual_positive_cells,
            "current_field_visual_inspection_log10_k_geom_p50": current_field_visual_geom_p50,
            "current_field_visual_inspection_nearest_anchor_distance_p50_m": current_field_visual_anchor_p50,
            "current_field_selection_audit_status": current_field_selection_status,
            "current_field_selection_active_objective_decision": current_field_active_decision,
            "current_field_selection_final_all_measurement_decision": current_field_final_decision,
            "current_field_selection_status_counts": current_field_selection_status_counts,
            "current_field_selection_best_mean_rank_run": current_field_selection_keys.get("best_mean_rank_run"),
            "current_field_selection_nmr_trend_anomaly_winner": current_field_selection_keys.get("nmr_trend_anomaly_winner"),
            "current_field_selection_required_gate_fail_count": current_field_selection_keys.get("required_gate_fail_count"),
            "current_field_selection_missing_external_responses": current_field_selection_keys.get("missing_external_responses"),
            "conditional_field_selection_scenarios_status": conditional_scenario_status,
            "conditional_field_selection_scenario_count": conditional_scenario_count,
            "conditional_field_selection_unique_winner_count": conditional_scenario_unique_winners,
            "conditional_field_selection_current_field_winning_scenario_count": conditional_scenario_current_wins,
            "conditional_field_selection_final_decision": conditional_scenario_final_decision,
            "conditional_field_selection_unique_winners": conditional_scenario_winners,
            "conditional_field_candidate_package_status": conditional_package_status,
            "conditional_field_candidate_package_candidate_count": conditional_package_candidate_count,
            "conditional_field_candidate_package_output_dir": conditional_package_output_dir,
            "conditional_field_candidate_package_selection_stability": conditional_package_stability,
            "conditional_field_candidate_package_metric_evidence_row_count": (
                conditional_package_metric_evidence_rows
            ),
            "conditional_field_candidate_package_metric_evidence_missing_row_count": (
                conditional_package_metric_evidence_missing
            ),
            "conditional_field_difference_audit_status": conditional_difference_status,
            "conditional_field_difference_compared_candidate_count": conditional_difference_compared_count,
            "conditional_field_difference_cell_count": conditional_difference_cell_count,
            "conditional_field_difference_largest_candidate": conditional_difference_largest_candidate,
            "conditional_field_difference_max_mean_abs_delta_log10_k_geom": conditional_difference_max_mean_abs,
            "conditional_field_difference_max_cells_abs_delta_gt_0p05": conditional_difference_max_gt_005,
            "conditional_field_difference_max_cells_abs_delta_gt_0p10": conditional_difference_max_gt_010,
            "conditional_field_difference_markdown": conditional_difference_markdown,
            "final_inversion_promotion_checklist_status": final_promotion_status,
            "final_inversion_promotion_decision": final_promotion_decision,
            "final_inversion_promotion_criterion_count": final_promotion_criterion_count,
            "final_inversion_promotion_open_criterion_count": final_promotion_open_count,
            "final_inversion_promotion_open_criterion_ids": final_promotion_open_criteria,
            "final_inversion_promotion_status_counts": final_promotion_status_counts,
            "final_inversion_closeout_playbook_status": final_closeout_status,
            "final_inversion_closeout_open_criterion_count": final_closeout_open_count,
            "final_inversion_closeout_external_action_count": final_closeout_external_count,
            "final_inversion_closeout_internal_policy_action_count": final_closeout_internal_count,
            "final_inversion_closeout_scenario_or_final_decision_action_count": final_closeout_scenario_count,
            "final_inversion_closeout_gmail_draft_ids": final_closeout_draft_ids,
            "final_inversion_closeout_next_actions": final_closeout_next_actions,
            "final_objective_decision_register_status": final_objective_decision_status,
            "final_objective_decision_register_decision_count": final_objective_decision_count,
            "final_objective_decision_register_external_stream_decision_count": final_objective_external_count,
            "final_objective_decision_register_internal_policy_decision_count": final_objective_internal_count,
            "final_objective_decision_register_scenario_or_final_decision_count": final_objective_scenario_count,
            "final_objective_decision_register_pending_or_not_ready_count": final_objective_pending_count,
            "final_objective_decision_register_explicit_exclusion_possible_count": final_objective_exclusion_count,
            "final_objective_decision_register_status_counts": final_objective_decision_status_counts,
            "final_objective_scenario_matrix_status": final_objective_scenario_status,
            "final_objective_scenario_matrix_option_count": final_objective_scenario_option_count,
            "final_objective_scenario_matrix_current_field_winning_option_count": final_objective_scenario_current_winning_count,
            "final_objective_scenario_matrix_unique_winner_count": final_objective_scenario_unique_winner_count,
            "final_objective_scenario_matrix_unscored_future_option_count": final_objective_scenario_unscored_count,
            "final_objective_scenario_matrix_not_final_likelihood_or_needs_new_policy_count": final_objective_scenario_non_likelihood_count,
            "final_objective_scenario_matrix_interpretation": final_objective_scenario_interpretation,
            "final_objective_include_exclude_recommendations_status": final_objective_recommendation_status,
            "final_objective_include_exclude_recommendations_count": final_objective_recommendation_count,
            "final_objective_include_exclude_recommendations_external_or_provenance_count": final_objective_recommendation_external_count,
            "final_objective_include_exclude_recommendations_internal_policy_count": final_objective_recommendation_internal_count,
            "final_objective_include_exclude_recommendations_scenario_or_final_count": final_objective_recommendation_scenario_count,
            "final_objective_include_exclude_recommendations_diagnostic_or_exclude_without_new_evidence_count": final_objective_recommendation_diagnostic_or_exclude_count,
            "final_objective_include_exclude_recommendations_waiver_not_recommended_count": final_objective_recommendation_waiver_not_recommended_count,
            "final_objective_include_exclude_recommendations_unblocks_promotion": final_objective_recommendation_unblocks_promotion,
            "final_objective_include_exclude_recommendations_current_field_label": final_objective_recommendation_current_label,
            "final_objective_no_new_evidence_closeout_draft_status": final_objective_no_new_status,
            "final_objective_no_new_evidence_closeout_draft_count": final_objective_no_new_count,
            "final_objective_no_new_evidence_closeout_draft_external_or_provenance_count": final_objective_no_new_external_count,
            "final_objective_no_new_evidence_closeout_draft_internal_policy_count": final_objective_no_new_internal_count,
            "final_objective_no_new_evidence_closeout_draft_scenario_or_final_count": final_objective_no_new_scenario_count,
            "final_objective_no_new_evidence_closeout_draft_requires_approval": final_objective_no_new_requires_approval,
            "final_objective_no_new_evidence_closeout_draft_records_decisions": final_objective_no_new_records_decisions,
            "final_objective_no_new_evidence_closeout_draft_promotes_current_field": final_objective_no_new_promotes_field,
            "final_objective_no_new_evidence_closeout_draft_unblocks_promotion": final_objective_no_new_unblocks_promotion,
            "final_objective_no_new_evidence_closeout_draft_would_select_scenario": final_objective_no_new_scenario,
            "final_objective_no_new_evidence_closeout_draft_would_select_winner": final_objective_no_new_winner,
            "final_objective_no_new_evidence_closeout_draft_current_field_is_winner": final_objective_no_new_current_winner,
            "final_objective_no_new_evidence_acceptance_record_template_status": final_objective_no_new_acceptance_status,
            "final_objective_no_new_evidence_acceptance_record_template_row_count": final_objective_no_new_acceptance_rows,
            "final_objective_no_new_evidence_acceptance_record_template_approval_rows_recorded": final_objective_no_new_acceptance_recorded,
            "final_objective_no_new_evidence_acceptance_record_template_approval_rows_required": final_objective_no_new_acceptance_required,
            "final_objective_no_new_evidence_acceptance_record_template_ready_to_apply": final_objective_no_new_acceptance_ready,
            "final_objective_no_new_evidence_acceptance_record_template_records_decisions": final_objective_no_new_acceptance_records_decisions,
            "final_objective_no_new_evidence_acceptance_record_template_promotes_current_field": final_objective_no_new_acceptance_promotes_field,
            "gmail_draft_send_review_packet_status": gmail_draft_review_status,
            "gmail_draft_send_review_packet_draft_count": gmail_draft_review_count,
            "gmail_draft_send_review_packet_unsent_draft_count": gmail_draft_review_unsent_count,
            "gmail_draft_send_review_packet_ready_for_user_review_count": gmail_draft_review_ready_count,
            "gmail_draft_send_review_packet_request_count": gmail_draft_review_request_count,
            "gmail_draft_send_review_packet_draft_ids": gmail_draft_review_ids,
            "taupe_trend_compared_rows": taupe_compared_rows,
            "taupe_trend_compared_series": taupe_compared_series,
            "taupe_trend_diagnostic_mae": taupe_diagnostic_mae,
            "taupe_candidate_discrimination_runs": taupe_discrimination_runs,
            "taupe_candidate_discrimination_full_active_runs": taupe_full_active_runs,
            "taupe_candidate_discrimination_mae_range": taupe_mae_range,
            "taupe_best_active_objective_taupe_mae": taupe_best_active_mae,
            "taupe_series_weight_sensitivity_runs": taupe_weight_runs,
            "taupe_series_weight_sensitivity_compared_series": taupe_weight_series,
            "taupe_series_weight_sensitivity_uncompared_series": taupe_weight_uncompared,
            "taupe_series_weight_sensitivity_distinct_series_winners": taupe_weight_distinct_winners,
            "taupe_series_weight_sensitivity_best_mean_rank_run": taupe_weight_best_mean.get("run_id"),
            "taupe_series_weight_sensitivity_best_mean_rank": taupe_weight_best_mean.get(
                "mean_rank_across_weighting_modes"
            ),
            "ert_resistivity_compared_rows": ert_compared_rows,
            "ert_resistivity_compared_output_times": ert_compared_outputs,
            "ert_resistivity_diagnostic_mae_log10": ert_diagnostic_mae,
            "ert_resistivity_diagnostic_rmse_log10": ert_diagnostic_rmse,
            "ert_candidate_discrimination_runs": ert_discrimination_runs,
            "ert_candidate_discrimination_full_active_runs": ert_full_active_runs,
            "ert_candidate_discrimination_mae_log10_range": ert_mae_range,
            "ert_best_active_objective_ert_mae_log10": ert_best_active_mae,
            "ert_support_sensitivity_runs": ert_support_runs,
            "ert_support_sensitivity_variant_count": ert_support_variants,
            "ert_support_sensitivity_best_mean_rank_run": ert_support_best_mean.get("run_id"),
            "ert_support_sensitivity_best_mean_rank": ert_support_best_mean.get("mean_ert_support_rank"),
            "ert_support_sensitivity_best_worst_rank": ert_support_best_mean.get("worst_ert_support_rank"),
            "rh_boundary_candidate_count": rh_candidate_count,
            "rh_boundary_preferred_candidate": rh_preferred_candidate,
            "rh_boundary_preferred_candidate_overlap_mae_mpa": rh_preferred_mae,
            "rh_boundary_candidate_after_active_curve_rows": rh_candidate_after_active_rows,
            "rh_boundary_uncertainty_envelope_dates": rh_uncertainty_envelope_dates,
            "rh_boundary_uncertainty_active_outside_envelope_rows": rh_uncertainty_active_outside,
            "rh_boundary_uncertainty_overlap_pressure_range_p50_mpa": rh_uncertainty_overlap_range_p50,
            "other_hm_numeric_source_audit_requests": other_hm_source_audit_requests,
            "other_hm_numeric_source_audit_hard_ready_requests": other_hm_hard_ready_requests,
            "other_hm_numeric_source_audit_support_ready_requests": other_hm_support_ready_requests,
            "executed_combined_candidate_count": executed_combined_candidate_count,
            "best_combined_candidate": best_executed_row.get("candidate_id"),
            "best_combined_objective": best_executed_row.get("total_active_objective_value"),
            "best_combined_state_rows": best_executed_row.get("state_active_objective_rows"),
            "regularized_candidate_set_ogs_mode": candidate_set.get("ogs_mode"),
            "first_adaptive_batch_best_candidate": adaptive_search_best.get("source_candidate_id"),
            "first_adaptive_batch_best_objective": adaptive_search_best.get("total_active_objective_value"),
            "local_refinement_best_candidate": local_refinement_best.get("source_candidate_id"),
            "local_refinement_best_objective": local_refinement_best.get("total_active_objective_value"),
            "local_bracketing_best_candidate": local_bracketing_best.get("source_candidate_id"),
            "local_bracketing_best_objective": local_bracketing_best.get("total_active_objective_value"),
            "optimizer_search_best_candidate": optimizer_search_best.get("source_candidate_id"),
            "optimizer_search_best_objective": optimizer_search_best.get("total_active_objective_value"),
            "continuous_search_best_candidate": continuous_search_best.get("source_candidate_id"),
            "continuous_search_best_objective": continuous_search_best.get("total_active_objective_value"),
            "broad_continuous_search_best_candidate": broad_continuous_search_best.get("source_candidate_id"),
            "broad_continuous_search_best_objective": broad_continuous_search_best.get("total_active_objective_value"),
            "broad_continuous_cumulative_best_candidate": broad_continuous_cumulative_best.get("source_candidate_id"),
            "broad_continuous_cumulative_best_objective": broad_continuous_cumulative_best.get("total_active_objective_value"),
            "lower_support_continuous_search_best_candidate": lower_support_continuous_search_best.get("source_candidate_id"),
            "lower_support_continuous_search_best_objective": lower_support_continuous_search_best.get("total_active_objective_value"),
            "latest_continuous_loop_batch_best_candidate": continuous_loop_search_best.get("source_candidate_id"),
            "latest_continuous_loop_batch_best_objective": continuous_loop_search_best.get("total_active_objective_value"),
            "latest_continuous_loop_post_best_candidate": continuous_loop_post_best.get("candidate_id"),
            "latest_continuous_loop_post_best_objective": continuous_loop_post_best.get("total_active_objective_value"),
            "adaptive_next_candidate_count": adaptive_plan.get("proposed_candidate_count"),
            "adaptive_top_candidate": adaptive_top_candidate,
            "adaptive_state_flat_over_executed_candidates": adaptive_plan.get("state_objective_flat_over_executed_candidates"),
            "optimizer_candidate_count": optimizer_proposal.get("candidate_count"),
            "optimizer_training_candidate_count": optimizer_proposal.get("training_candidate_count"),
            "optimizer_top_candidate": optimizer_top_candidate,
            "optimizer_acquisition": optimizer_proposal.get("acquisition"),
            "continuous_candidate_count": continuous_plan.get("continuous_candidate_count"),
            "continuous_training_candidate_count": continuous_plan.get("training_candidate_count"),
            "continuous_top_candidate": continuous_top_candidate,
            "continuous_top_predicted_objective": (
                continuous_top_proposals[0].get("gp_combined_objective_mean")
                if continuous_top_proposals
                else None
            ),
            "continuous_top_probability_of_improvement": (
                continuous_top_proposals[0].get("probability_of_improvement")
                if continuous_top_proposals
                else None
            ),
            "anisotropy_sensitivity_candidate_count": anisotropy_plan.get("candidate_count"),
            "anisotropy_sensitivity_best_candidate": anisotropy_best.get("candidate_id"),
            "anisotropy_sensitivity_best_theta_deg": anisotropy_best.get("theta_deg"),
            "anisotropy_sensitivity_best_ratio": anisotropy_best.get("anisotropy_ratio"),
            "anisotropy_sensitivity_best_direct_objective": anisotropy_best.get("objective_value"),
            "anisotropy_sensitivity_best_delta_vs_baseline": anisotropy_best.get("direct_objective_delta_vs_baseline"),
            "local_basis_sampler_candidate_count": local_basis_plan.get("candidate_count"),
            "local_basis_sampler_anchor_count": local_basis_plan.get("basis_anchor_count"),
            "local_basis_sampler_execution_batch_size": local_basis_plan.get("execution_batch_size"),
            "local_basis_sampler_best_candidate": local_basis_best.get("candidate_id"),
            "local_basis_sampler_best_direct_objective": local_basis_best.get("objective_value"),
            "local_basis_sampler_best_delta_vs_baseline": local_basis_best.get("direct_objective_delta_vs_baseline"),
            "local_basis_sampler_best_weighted_rmse_log10": local_basis_best.get("weighted_rmse_log10"),
            "local_anisotropy_sampler_candidate_count": local_anisotropy_candidate_count,
            "local_anisotropy_sampler_anchor_count": local_anisotropy_anchor_count,
            "local_anisotropy_sampler_best_candidate": local_anisotropy_best.get("candidate_id"),
            "local_anisotropy_sampler_best_mode": local_anisotropy_best.get("mode"),
            "local_anisotropy_sampler_best_direct_objective": local_anisotropy_best.get("objective_value"),
            "local_anisotropy_sampler_best_delta_vs_baseline": local_anisotropy_best_delta,
            "local_anisotropy_sampler_best_weighted_rmse_log10": local_anisotropy_best.get("weighted_rmse_log10"),
            "permeability_residual_conflict_audit_status": permeability_residual_status,
            "permeability_residual_conflict_active_rows": permeability_residual_active_rows,
            "permeability_residual_conflict_large_rows_ge_1_log10": permeability_residual_large_ge1,
            "permeability_residual_conflict_large_rows_ge_2_log10": permeability_residual_very_large_ge2,
            "permeability_residual_conflict_outside_configured_scalar_range": permeability_residual_outside_range,
            "permeability_residual_conflict_repeated_support_cells": permeability_residual_repeated_cells,
            "permeability_residual_conflict_support_cells_observed_range_ge_1_log10": permeability_residual_cell_conflicts,
            "permeability_residual_conflict_interpretation": permeability_residual_audit.get("interpretation"),
            "permeability_likelihood_policy_audit_status": permeability_policy_status,
            "permeability_likelihood_policy_current_gaussian_objective": permeability_policy_current_objective,
            "permeability_likelihood_policy_support_mean_objective": permeability_policy_support_mean_objective,
            "permeability_likelihood_policy_support_median_objective": permeability_policy_support_median_objective,
            "permeability_likelihood_policy_top10_row_loss_share": permeability_policy_top10_loss_share,
            "permeability_likelihood_policy_repeated_support_groups": permeability_policy_repeated_groups,
            "permeability_likelihood_policy_conflict_support_groups": permeability_policy_conflict_groups,
            "permeability_likelihood_policy_recommendation": permeability_policy_audit.get("recommendation"),
            "permeability_support_lower_bound_status": permeability_support_lb_status,
            "permeability_support_lower_bound_current_objective": permeability_support_lb_current_objective,
            "permeability_support_lower_bound_single_support_objective": permeability_support_lb_lower_objective,
            "permeability_support_lower_bound_reducible_gap": permeability_support_lb_reducible_gap,
            "permeability_support_lower_bound_reducible_fraction": permeability_support_lb_reducible_fraction,
            "permeability_support_lower_bound_current_at_bound": permeability_support_lb_at_bound,
            "permeability_support_lower_bound_support_groups": permeability_support_lb_groups,
            "permeability_support_lower_bound_repeated_support_groups": permeability_support_lb_repeated_groups,
            "permeability_support_lower_bound_conflict_groups_ge_2_log10": permeability_support_lb_conflict_ge2,
            "permeability_support_lower_bound_top2_loss_share": permeability_support_lb_top2_share,
            "permeability_support_lower_bound_top5_loss_share": permeability_support_lb_top5_share,
            "permeability_support_lower_bound_interpretation": permeability_support_lower_bound.get("interpretation"),
            "permeability_support_conflict_spatial_audit_status": permeability_support_spatial_status,
            "permeability_support_conflict_spatial_mesh_cells": permeability_support_spatial_mesh_cells,
            "permeability_support_conflict_spatial_active_cells": permeability_support_spatial_active_cells,
            "permeability_support_conflict_spatial_repeated_cells": permeability_support_spatial_repeated_cells,
            "permeability_support_conflict_spatial_cells_ge_1_log10": permeability_support_spatial_ge1,
            "permeability_support_conflict_spatial_cells_ge_2_log10": permeability_support_spatial_ge2,
            "permeability_support_conflict_spatial_configured_conflict_cells": (
                permeability_support_spatial_configured_conflict
            ),
            "permeability_support_conflict_spatial_top_cell": permeability_support_spatial_top,
            "permeability_likelihood_decision_request_status": permeability_policy_decision_status,
            "permeability_likelihood_decision_recommended_current_policy": permeability_policy_decision_recommended,
            "permeability_likelihood_decision_option_count": permeability_policy_decision.get("decision_option_count"),
            "permeability_configured_scalar_outlier_disposition_status": permeability_outlier_disposition_status,
            "permeability_configured_scalar_outlier_disposition_rows": permeability_outlier_disposition_rows,
            "permeability_configured_scalar_outlier_disposition_unique_groups": permeability_outlier_disposition_groups,
            "permeability_configured_scalar_outlier_disposition_max_excess_log10": permeability_outlier_disposition_max_excess,
            "permeability_configured_scalar_outlier_disposition_max_support_range_log10": permeability_outlier_disposition_support_range,
            "permeability_configured_scalar_outlier_disposition_bounds_release_now": permeability_outlier_bounds_release_now,
            "permeability_configured_scalar_outlier_disposition_tensor_shape_release_now": permeability_outlier_tensor_release_now,
            "permeability_likelihood_scenario_rerank_status": permeability_policy_rerank_status,
            "permeability_likelihood_scenario_rerank_scored_fields": permeability_policy_rerank_scored,
            "permeability_likelihood_scenario_rerank_current_gaussian_best_ties": permeability_policy_rerank_best_ties,
            "permeability_likelihood_scenario_rerank_current_accepted_tied": permeability_policy_rerank_current_accepted_tied,
            "permeability_likelihood_scenario_rerank_alt_policy_winners_outside_tie_set": permeability_policy_rerank_alt_outside,
            "permeability_likelihood_winner_cross_stream_status": permeability_policy_winner_cross_status,
            "permeability_likelihood_winner_cross_stream_scorecard_rows": permeability_policy_winner_cross_scorecard_rows,
            "permeability_likelihood_winner_cross_stream_direct_only_rows": permeability_policy_winner_cross_direct_only_rows,
            "permeability_likelihood_winner_cross_stream_outside_tie_direct_only_rows": permeability_policy_winner_cross_outside_direct_only_rows,
            "permeability_likelihood_winner_cross_stream_row_gaussian_active_rank": permeability_policy_winner_cross_row_gaussian_rank,
            "permeability_likelihood_winner_cross_stream_current_accepted_active_rank": permeability_policy_winner_cross_current_rank,
            "permeability_next_field_fit_gate_status": permeability_next_gate_status,
            "permeability_next_field_fit_gate_recommendation": permeability_next_gate_recommendation,
            "permeability_next_field_fit_gate_count": permeability_next_gate_count,
            "permeability_next_field_fit_gate_executable_same_support_active_objective_batch_now": permeability_next_gate_executable_now,
            "permeability_next_field_fit_gate_status_counts": permeability_next_gate_status_counts,
            "permeability_next_field_fit_gate_current_report_default_policy": permeability_next_gate_current_policy,
            "permeability_likelihood_support_recommendations_status": permeability_support_recommendations_status,
            "permeability_likelihood_support_recommendations_count": permeability_support_recommendations_count,
            "permeability_likelihood_support_recommendations_current_policy": permeability_support_recommendations_current_policy,
            "permeability_likelihood_support_recommendations_at_lower_bound": permeability_support_recommendations_at_lower_bound,
            "permeability_likelihood_support_recommendations_same_support_gap": permeability_support_recommendations_same_support_gap,
            "permeability_likelihood_support_recommendations_same_support_batch_executable_now": permeability_support_recommendations_batch_executable,
            "permeability_likelihood_support_recommendations_bounds_release_now": permeability_support_recommendations_bounds_release_now,
            "permeability_likelihood_support_recommendations_tensor_shape_release_now": permeability_support_recommendations_tensor_release_now,
            "permeability_likelihood_support_recommendations_unblocks_promotion": permeability_support_recommendations_unblocks_promotion,
            "permeability_likelihood_policy_acceptance_record_template_status": permeability_policy_acceptance_status,
            "permeability_likelihood_policy_acceptance_record_template_row_count": permeability_policy_acceptance_rows,
            "permeability_likelihood_policy_acceptance_record_template_primary_approval_rows_recorded": permeability_policy_acceptance_recorded,
            "permeability_likelihood_policy_acceptance_record_template_primary_approval_rows_required": permeability_policy_acceptance_required,
            "permeability_likelihood_policy_acceptance_record_template_ready_to_apply": permeability_policy_acceptance_ready,
            "permeability_likelihood_policy_acceptance_record_template_records_decision": permeability_policy_acceptance_records_decision,
            "permeability_likelihood_policy_acceptance_record_template_changes_active_objective": permeability_policy_acceptance_changes_objective,
            "permeability_likelihood_policy_acceptance_record_template_promotes_current_field": permeability_policy_acceptance_promotes_field,
            "permeability_likelihood_policy_acceptance_record_template_same_support_batch_executable_now": permeability_policy_acceptance_same_support_executable,
            "local_basis_sampler_ogs_best_candidate": local_basis_search_best.get("source_candidate_id"),
            "local_basis_sampler_ogs_best_objective": local_basis_search_best.get("total_active_objective_value"),
            "production_search_round_count": len(production_search_summaries),
            "production_search_evaluated_candidate_count": combined_search_count(production_search_summaries),
            "production_search_best_candidate": production_search_best.get("source_candidate_id"),
            "production_search_best_objective": production_search_best.get("total_active_objective_value"),
            "production_search_best_state_rows": production_search_best.get("state_active_objective_rows"),
            "production_search_best_release_gate_status": production_search_best.get("release_gate_status"),
            "production_sampler_executed_candidate_count": production_sampler.get("executed_candidate_count"),
            "production_sampler_candidate_pool_count": production_sampler.get("candidate_pool_count"),
            "production_sampler_unexecuted_candidate_count": production_sampler.get("unexecuted_candidate_count"),
            "production_sampler_unexecuted_executable_candidate_count": production_sampler.get(
                "unexecuted_executable_candidate_count"
            ),
            "production_sampler_nonexecutable_diagnostic_candidate_count": production_sampler.get(
                "nonexecutable_diagnostic_candidate_count"
            ),
            "production_sampler_best_candidate": production_sampler.get("best_candidate"),
            "production_sampler_best_objective": production_sampler.get("best_combined_objective"),
            "production_sampler_best_smooth_candidate": production_sampler.get("best_smooth_candidate"),
            "production_sampler_best_smooth_objective": production_sampler.get("best_smooth_objective"),
            "production_sampler_local_basis_improvement_vs_previous_best": production_sampler.get(
                "local_basis_improvement_vs_previous_best"
            ),
            "production_sampler_top_candidate": production_top_candidate,
            "production_sampler_top_family": production_top_family,
            "production_sampler_top_probability_of_improvement": (
                production_top_proposals[0].get("probability_of_improvement")
                if production_top_proposals
                else None
            ),
            "production_sampler_cv_state_objective_rmse": production_sampler.get("cv_state_objective_rmse"),
            "production_sampler_decision": production_decision.get("recommendation"),
            "production_sampler_decision_reason": production_decision.get("reason"),
            "nmr_trend_followup_recommendation": nmr_trend_followup.get("recommendation"),
            "nmr_trend_followup_best_unevaluated_candidate": nmr_trend_followup_best.get("candidate_id"),
            "nmr_trend_followup_best_unevaluated_direct_advantage": nmr_trend_followup.get(
                "best_unevaluated_direct_advantage_vs_incumbent"
            ),
            "nmr_trend_followup_materiality_threshold": nmr_trend_followup.get("materiality_threshold"),
            "nmr_trend_followup_unevaluated_runnable_candidates": nmr_trend_followup.get(
                "unevaluated_runnable_candidate_count"
            ),
            "nmr_trend_followup_median_state_beating_candidates": nmr_trend_followup.get(
                "unevaluated_candidates_beating_incumbent_under_median_state"
            ),
            "ogs_environment_status": ogs_env.get("status"),
            "release_gate_status": release_gate.get("status"),
            "release_gate_run_count": release_gate.get("run_count"),
            "release_gate_check_count": release_gate.get("check_count"),
            "release_gate_failure_count": release_gate.get("failure_count"),
            "frozen_model_measurement_inclusion_audit_status": frozen_audit_status,
            "frozen_model_measurement_inclusion_audit_check_count": frozen_audit_check_count,
            "frozen_model_measurement_inclusion_audit_failure_count": frozen_audit_failure_count,
            "frozen_model_measurement_inclusion_audit_warning_count": frozen_audit_warning_count,
            "frozen_model_measurement_inclusion_audit_manifest_count": frozen_audit_manifest_count,
            "frozen_model_measurement_inclusion_audit_wrong_manifest_count": frozen_audit_wrong_manifest_count,
            "frozen_model_measurement_inclusion_audit_measurement_info_source_rows": (
                frozen_audit_measurement_info_rows
            ),
            "frozen_model_measurement_inclusion_audit_archive_member_rows": frozen_audit_archive_rows,
            "frozen_model_measurement_inclusion_audit_workbook_sheet_rows": frozen_audit_workbook_rows,
            "frozen_model_measurement_inclusion_audit_final_promotion_decision": frozen_audit_final_decision,
            "frozen_model_measurement_inclusion_audit_open_blocker_ids": frozen_audit_open_blockers,
            "pdf_pages": pdf_pages,
        },
        "notes": [
            "This audit is intentionally stricter than WORK_STATUS.md: it maps the original objective to evidence and non-completion gates.",
            "A status of partial or achieved_with_tracked_caveats can still leave collaborator/provenance decisions or broader optimization work open.",
            "Do not mark the overall goal complete while any requirement is blocked_external, incomplete, missing, or only partial.",
        ],
    }
    return frame, summary


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Objective Readiness Audit",
        "",
        "This audit maps the original report/model/inversion objective to current evidence.",
        "It is not a success declaration: it separates completed documentation and data",
        "work from the remaining OGS-backed inversion work.",
        "",
        f"- Completion state: `{summary['completion_state']}`",
        f"- Requirements audited: {summary['requirement_count']}",
        f"- Status counts: {', '.join(f'`{key}`={value}' for key, value in summary['status_counts'].items())}",
        f"- Non-complete requirement ids: {', '.join(summary['non_complete_requirement_ids']) or 'none'}",
        f"- Blocking/incomplete requirement ids: {', '.join(summary['blocking_or_incomplete_requirement_ids']) or 'none'}",
        f"- Partial requirement ids: {', '.join(summary['partial_requirement_ids']) or 'none'}",
        "",
        "## Requirement Table",
        "",
        "| Requirement | Status | Evidence | Remaining work |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['requirement_id']}` {row['requirement']}",
                    f"`{row['status']}`",
                    str(row["evidence"]).replace("|", "\\|"),
                    str(row["remaining_work"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Highest Priority Next Steps", ""])
    for item in summary["highest_priority_next_steps"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current package has a clean report build, validated measurement inventory,",
            "processed observation tables, measurement operators, likelihood activation",
            "rules, direct permeability candidate fields, and release-gate enforcement.",
            "It now has complete direct and regularized-candidate OGS runs with sampled NMR state residuals.",
            "It also has completed first adaptive, local refinement, and local bracketing OGS batches,",
            "plus finite-candidate, continuous, and lower-support continuous proposal layers over smooth permeability fields;",
            f"the current best combined candidate is {summary['key_numbers'].get('best_combined_candidate')} "
            f"with objective {summary['key_numbers'].get('best_combined_objective')}.",
            f"The measurement-report traceability audit has status "
            f"{summary['key_numbers'].get('measurement_report_traceability_status')}: "
            f"{summary['key_numbers'].get('measurement_report_traceability_observation_count')} observations, "
            f"all traceable={summary['key_numbers'].get('measurement_report_traceability_all_observations_traceable')}, "
            f"status counts {summary['key_numbers'].get('measurement_report_traceability_status_counts')}, "
            f"{summary['key_numbers'].get('measurement_report_traceability_manifest_failures')} manifest validation failures, "
            f"{summary['key_numbers'].get('measurement_report_traceability_data_content_fact_rows')} "
            "catalogue content facts, and "
            f"{summary['key_numbers'].get('measurement_report_traceability_missing_data_content_summary_count')} "
            "missing data-content summaries.",
            f"The measurement content-deep-dive contributes "
            f"{summary['key_numbers'].get('measurement_content_deep_dive_total_rows')} mined fact rows with "
            f"per-measurement counts {summary['key_numbers'].get('measurement_content_deep_dive_counts')}.",
            f"The measurement model-entry matrix has status "
            f"{summary['key_numbers'].get('measurement_model_entry_matrix_status')}: "
            f"{summary['key_numbers'].get('measurement_model_entry_matrix_row_count')} measurement classes, "
            f"{summary['key_numbers'].get('measurement_model_entry_matrix_active_measurement_count')} active classes, "
            f"{summary['key_numbers'].get('measurement_model_entry_matrix_active_objective_rows')} active rows, "
            f"entry classes {summary['key_numbers'].get('measurement_model_entry_matrix_entry_class_counts')}, "
            f"and final decision statuses "
            f"{summary['key_numbers'].get('measurement_model_entry_matrix_final_decision_status_counts')}.",
            f"The stream activation-gate audit records "
            f"{summary['key_numbers'].get('measurement_stream_gate_required_failures')} required failed gates "
            f"and {summary['key_numbers'].get('measurement_stream_gate_required_warnings')} warnings; "
            f"promotion decisions are "
            f"{summary['key_numbers'].get('measurement_stream_gate_promotion_decision_counts')}.",
            f"The measurement gate-closure package records "
            f"{summary['key_numbers'].get('measurement_gate_closure_request_count')} closure requests: "
            f"{summary['key_numbers'].get('measurement_gate_closure_external_request_count')} external "
            f"requests and "
            f"{summary['key_numbers'].get('measurement_gate_closure_internal_decision_count')} internal "
            f"or confirmation decisions.  High-priority ids are "
            f"{summary['key_numbers'].get('measurement_gate_closure_high_priority_request_ids')}.",
            f"The external request pack has status "
            f"{summary['key_numbers'].get('external_gate_request_pack_status')} and splits "
            f"{summary['key_numbers'].get('external_gate_request_pack_request_count')} external requests "
            f"into {summary['key_numbers'].get('external_gate_request_pack_recipient_count')} recipient drafts; "
            f"suggested To routes are present for "
            f"{summary['key_numbers'].get('external_gate_request_pack_recipient_with_suggested_to_count')} "
            f"recipients, with route counts "
            f"{summary['key_numbers'].get('external_gate_request_pack_contact_route_counts')}.",
            f"The response-intake tracker has status "
            f"{summary['key_numbers'].get('external_gate_response_intake_status')} and records "
            f"{summary['key_numbers'].get('external_gate_response_intake_missing_response_count')} missing responses "
            f"across {summary['key_numbers'].get('external_gate_response_intake_directory_count')} stream intake directories "
            f"with {summary['key_numbers'].get('external_gate_response_intake_note_template_count')} response-note templates "
            f"and {summary['key_numbers'].get('external_gate_response_intake_with_suggested_to_count')} "
            f"rows carrying suggested To routes.",
            f"The external dispatch audit has status "
            f"{summary['key_numbers'].get('external_gate_dispatch_audit_status')}: "
            f"{summary['key_numbers'].get('external_gate_dispatch_ready_request_count')}/"
            f"{summary['key_numbers'].get('external_gate_dispatch_request_count')} requests ready, "
            f"{summary['key_numbers'].get('external_gate_dispatch_failed_check_count')} failed checks, "
            f"{summary['key_numbers'].get('external_gate_dispatch_suggested_to_present_count')} suggested To rows, "
            f"{summary['key_numbers'].get('external_gate_dispatch_unique_gmail_draft_count')} Gmail drafts, "
            f"{summary['key_numbers'].get('external_gate_dispatch_not_sent_request_count')} not sent, and "
            f"{summary['key_numbers'].get('external_gate_dispatch_missing_response_count')} missing responses.",
            f"The external blocker dashboard has status "
            f"{summary['key_numbers'].get('external_blocker_dashboard_status')}: "
            f"{summary['key_numbers'].get('external_blocker_dashboard_open_blocker_count')}/"
            f"{summary['key_numbers'].get('external_blocker_dashboard_blocker_count')} blockers open, "
            f"{summary['key_numbers'].get('external_blocker_dashboard_unsent_blocker_count')} unsent, "
            f"{summary['key_numbers'].get('external_blocker_dashboard_missing_response_blocker_count')} missing responses, "
            f"with open ids {summary['key_numbers'].get('external_blocker_dashboard_open_blocker_ids')}.",
            f"The CTE confirmation request has status "
            f"{summary['key_numbers'].get('cte_confirmation_request_status')}: "
            f"{summary['key_numbers'].get('cte_confirmation_request_request_status')}, "
            f"{summary['key_numbers'].get('cte_confirmation_request_response_status')}, Gmail draft="
            f"{summary['key_numbers'].get('cte_confirmation_gmail_draft_id') or 'none'}, To="
            f"{summary['key_numbers'].get('cte_confirmation_request_suggested_to')}, Cc="
            f"{summary['key_numbers'].get('cte_confirmation_request_suggested_cc')}.",
            f"The report open-comment audit has status "
            f"{summary['key_numbers'].get('report_open_comment_audit_status')}: "
            f"{summary['key_numbers'].get('report_active_unresolved_marker_count')} active report markers, "
            f"{summary['key_numbers'].get('report_resolved_formulation_comment_count')} resolved formulation comments, "
            f"{summary['key_numbers'].get('report_tracked_external_gate_count')} external request gates, and "
            f"{summary['key_numbers'].get('report_tracked_internal_or_provenance_item_count')} "
            f"internal/provenance/operational items.",
            f"The open-question resolution matrix has status "
            f"{summary['key_numbers'].get('open_question_resolution_matrix_status')}: "
            f"{summary['key_numbers'].get('open_question_resolution_matrix_row_count')} rows, "
            f"{summary['key_numbers'].get('open_question_resolution_matrix_resolved_or_current_scope_count')} "
            f"locally resolved/current-scope rows, "
            f"{summary['key_numbers'].get('open_question_resolution_matrix_external_or_send_response_required_count')} "
            f"external send/response rows, and "
            f"{summary['key_numbers'].get('open_question_resolution_matrix_internal_policy_or_final_decision_count')} "
            f"internal policy/final-decision rows.",
            f"The OGS formulation consistency audit has status "
            f"{summary['key_numbers'].get('ogs_formulation_consistency_status')}: "
            f"{summary['key_numbers'].get('ogs_formulation_consistency_check_count')} checks, "
            f"{summary['key_numbers'].get('ogs_formulation_consistency_fail_count')} hard failures, "
            f"hard checks pass={summary['key_numbers'].get('ogs_formulation_consistency_hard_checks_pass')}, "
            f"tracked caveats={summary['key_numbers'].get('ogs_formulation_consistency_tracked_caveat_count')}, "
            f"process={summary['key_numbers'].get('ogs_formulation_consistency_process_type')}, "
            f"primary variables={summary['key_numbers'].get('ogs_formulation_consistency_primary_variables')}, "
            f"run-local fields={summary['key_numbers'].get('ogs_formulation_consistency_run_local_field_parameters')}.",
            f"The direct-run input audit has status {summary['key_numbers'].get('ogs_run_input_audit_status')}: "
            f"{summary['key_numbers'].get('ogs_run_input_check_count')} checks, "
            f"{summary['key_numbers'].get('ogs_run_input_warning_count')} warnings, "
            f"{summary['key_numbers'].get('ogs_run_input_error_count')} errors, "
            f"meshio-unreadable meshes={summary['key_numbers'].get('ogs_run_input_unreadable_meshio_meshes')}, "
            f"and recorded OGS returncode={summary['key_numbers'].get('ogs_run_input_execution_returncode')} "
            f"via {summary['key_numbers'].get('ogs_run_input_execution_backend')}.",
            f"The citation locator audit has status "
            f"{summary['key_numbers'].get('citation_locator_audit_status')}: "
            f"{summary['key_numbers'].get('citation_key_instance_count')} citation key instances, "
            f"{summary['key_numbers'].get('citation_unique_cited_key_count')} unique cited keys, "
            f"{summary['key_numbers'].get('citation_missing_or_weak_locator_count')} missing or weak locators, "
            f"{summary['key_numbers'].get('citation_missing_bib_entry_count')} missing BibTeX entries, and "
            f"{summary['key_numbers'].get('citation_unavailable_fulltext_missing_log_count')} unavailable fulltexts "
            f"missing from the tracking log.",
            f"The internal gate decision register records "
            f"{summary['key_numbers'].get('internal_gate_local_policy_recorded_count')} local policies: "
            f"{summary['key_numbers'].get('internal_gate_active_or_ready_policy_count')} active/ready policies "
            f"and {summary['key_numbers'].get('internal_gate_diagnostic_or_boundary_policy_count')} "
            f"diagnostic or boundary-only policies; "
            f"{summary['key_numbers'].get('internal_gate_still_external_or_activation_gated_count')} remain "
            f"gated before hard likelihood promotion, and "
            f"{summary['key_numbers'].get('internal_gate_remaining_confirmation_or_promotion_caveat_count')} carry "
            f"optional confirmation caveats. "
            f"{summary['key_numbers'].get('internal_gate_not_promoted_default_policy_count')} explicit not-default "
            f"policies are recorded; NMR default promotion status is "
            f"{summary['key_numbers'].get('nmr_default_promotion_status')} and permeability likelihood policy "
            f"status is {summary['key_numbers'].get('permeability_likelihood_policy_status')}.",
            f"The NMR objective decision recommends "
            f"{summary['key_numbers'].get('nmr_objective_decision_recommended_option')} with best run "
            f"{summary['key_numbers'].get('nmr_objective_decision_best_recommended_run')}; the executable "
            f"trend/anomaly package validates against the diagnostic audit with max absolute delta "
            f"{summary['key_numbers'].get('nmr_trend_anomaly_activation_validation_max_abs_delta')}. "
            f"The active incumbent is rank "
            f"{summary['key_numbers'].get('nmr_trend_anomaly_activation_raw_incumbent_rank')} "
            f"under that treatment, and the internal policy records that the default active objective is not "
            f"promoted for the current report state. The NMR final residual policy gate has status "
            f"{summary['key_numbers'].get('nmr_final_residual_policy_gate_status')}, selected="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_selected')}, current default="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_current_default')}, recommended candidate="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_recommended_candidate')}, and follow-up "
            f"{summary['key_numbers'].get('nmr_final_residual_policy_followup_recommendation')}. The NMR "
            f"final residual-policy acceptance-record template has status "
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_status')}: "
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_primary_approval_rows_recorded')}/"
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_primary_approval_rows_required')} "
            f"primary approvals recorded, ready-to-apply="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_ready_to_apply')}, "
            f"records decision="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_records_decision')}, "
            f"changes active objective="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_changes_active_objective')}, "
            f"and new OGS batch recommended now="
            f"{summary['key_numbers'].get('nmr_final_residual_policy_acceptance_record_template_new_ogs_batch_recommended_now')}.",
            "A direct anisotropy sensitivity pass now shows that changing only the global",
            "principal-direction angle or anisotropy ratio does not improve the pulse-test objective;",
            f"the best anisotropy candidate is {summary['key_numbers'].get('anisotropy_sensitivity_best_candidate')} "
            f"with delta {summary['key_numbers'].get('anisotropy_sensitivity_best_delta_vs_baseline')}.",
            "A first local-basis direct sampler now perturbs residual-derived support cells independently;",
            f"its best direct candidate is {summary['key_numbers'].get('local_basis_sampler_best_candidate')} "
            f"with delta {summary['key_numbers'].get('local_basis_sampler_best_delta_vs_baseline')}.",
            f"The executed local-basis OGS batch improves the combined incumbent to "
            f"{summary['key_numbers'].get('local_basis_sampler_ogs_best_candidate')} with objective "
            f"{summary['key_numbers'].get('local_basis_sampler_ogs_best_objective')}.",
            f"A local anisotropy sampler then screens "
            f"{summary['key_numbers'].get('local_anisotropy_sampler_candidate_count')} tensor-orientation/ratio "
            f"candidates over {summary['key_numbers'].get('local_anisotropy_sampler_anchor_count')} anchor cells; "
            f"its best direct candidate is "
            f"{summary['key_numbers'].get('local_anisotropy_sampler_best_candidate')} with delta "
            f"{summary['key_numbers'].get('local_anisotropy_sampler_best_delta_vs_baseline')}, so local "
            f"tensor-anisotropy release is not justified by the active direct target screen.",
            f"The production sampler/convergence audit now consolidates "
            f"{summary['key_numbers'].get('production_sampler_executed_candidate_count')} accepted OGS rows, "
            f"tracks {summary['key_numbers'].get('production_sampler_unexecuted_executable_candidate_count')} "
            f"unexecuted candidates with materialized meshes, and leads with "
            f"{summary['key_numbers'].get('production_sampler_top_candidate')} "
            f"({summary['key_numbers'].get('production_sampler_top_family')}).",
            f"The production stop/continue decision is "
            f"{summary['key_numbers'].get('production_sampler_decision')}: "
            f"{str(summary['key_numbers'].get('production_sampler_decision_reason')).rstrip('.')}.",
            f"The executed production sampler rounds are worse than the incumbent: their best row is "
            f"{summary['key_numbers'].get('production_search_best_candidate')} with objective "
            f"{summary['key_numbers'].get('production_search_best_objective')}.",
            f"The cross-stream scorecard joins {summary['key_numbers'].get('cross_stream_scorecard_runs')} "
            f"runs across active objective, NMR bias/anomaly, ERT, and Taupe diagnostics; "
            f"no candidate is top-10 in every stream, and the best mean-rank compromise is "
            f"{summary['key_numbers'].get('cross_stream_best_mean_rank_candidate')} "
            f"with mean rank {summary['key_numbers'].get('cross_stream_best_mean_rank')} "
            f"and worst rank {summary['key_numbers'].get('cross_stream_best_mean_worst_rank')}.",
            f"The cross-stream hybrid field screen then blends "
            f"{summary['key_numbers'].get('cross_stream_hybrid_candidate_count')} fields from "
            f"{summary['key_numbers'].get('cross_stream_hybrid_target_run_count')} diagnostic winner runs; "
            f"the best direct hybrid is "
            f"{summary['key_numbers'].get('cross_stream_hybrid_best_candidate')} "
            f"with delta {summary['key_numbers'].get('cross_stream_hybrid_best_delta_vs_active')} versus the "
            f"active incumbent, so it does not justify OGS spending on the active objective alone.",
            f"The structural/EDZ field-family screen checks "
            f"{summary['key_numbers'].get('structural_edz_field_family_candidate_count')} cap/shell/"
            f"bedding/corridor fields and finds "
            f"{summary['key_numbers'].get('structural_edz_field_family_improving_candidate_count')} "
            f"direct-improving candidates; the best family is "
            f"{summary['key_numbers'].get('structural_edz_field_family_best_family')} with delta "
            f"{summary['key_numbers'].get('structural_edz_field_family_best_delta_vs_active')}.",
            f"The permeability residual and likelihood-policy audits then show "
            f"{summary['key_numbers'].get('permeability_residual_conflict_large_rows_ge_1_log10')} "
            f"active direct rows above one log10 residual, "
            f"{summary['key_numbers'].get('permeability_likelihood_policy_conflict_support_groups')} "
            f"conflicting support groups, and top-10 row-loss share "
            f"{summary['key_numbers'].get('permeability_likelihood_policy_top10_row_loss_share')}; "
            f"the support-cell mean diagnostic objective is "
            f"{summary['key_numbers'].get('permeability_likelihood_policy_support_mean_objective')}, "
            f"and the support lower-bound audit records current objective "
            f"{summary['key_numbers'].get('permeability_support_lower_bound_current_objective')} versus "
            f"single-support lower bound "
            f"{summary['key_numbers'].get('permeability_support_lower_bound_single_support_objective')} "
            f"with reducible gap "
            f"{summary['key_numbers'].get('permeability_support_lower_bound_reducible_gap')}, "
            f"so the remaining direct mismatch is also a likelihood/support decision. The decision request "
            f"status is {summary['key_numbers'].get('permeability_likelihood_decision_request_status')} "
            f"with recommended current policy "
            f"{summary['key_numbers'].get('permeability_likelihood_decision_recommended_current_policy')}. "
            f"The support-conflict spatial audit maps "
            f"{summary['key_numbers'].get('permeability_support_conflict_spatial_active_cells')} "
            f"active support cells on "
            f"{summary['key_numbers'].get('permeability_support_conflict_spatial_mesh_cells')} mesh cells, "
            f"with {summary['key_numbers'].get('permeability_support_conflict_spatial_repeated_cells')} "
            f"repeated support cells and "
            f"{summary['key_numbers'].get('permeability_support_conflict_spatial_cells_ge_2_log10')} "
            f"cells spanning at least two log10 units. "
            f"The configured-scalar outlier disposition records "
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_rows')} "
            f"outlier rows in "
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_unique_groups')} "
            f"physical group, max envelope excess "
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_max_excess_log10')} "
            f"log10, max same-support range "
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_max_support_range_log10')} "
            f"log10, bounds release now="
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_bounds_release_now')}, "
            f"and tensor-shape release now="
            f"{summary['key_numbers'].get('permeability_configured_scalar_outlier_disposition_tensor_shape_release_now')}. "
            f"The existing-field rerank scored "
            f"{summary['key_numbers'].get('permeability_likelihood_scenario_rerank_scored_fields')} "
            f"fields, found "
            f"{summary['key_numbers'].get('permeability_likelihood_scenario_rerank_current_gaussian_best_ties')} "
            f"active row-Gaussian best ties with the current accepted field tied="
            f"{summary['key_numbers'].get('permeability_likelihood_scenario_rerank_current_accepted_tied')}, "
            f"and found "
            f"{summary['key_numbers'].get('permeability_likelihood_scenario_rerank_alt_policy_winners_outside_tie_set')} "
            f"diagnostic policy winners outside that tie set. The winner cross-stream audit records "
            f"{summary['key_numbers'].get('permeability_likelihood_winner_cross_stream_direct_only_rows')} "
            f"direct-only policy-winner rows, including "
            f"{summary['key_numbers'].get('permeability_likelihood_winner_cross_stream_outside_tie_direct_only_rows')} "
            f"outside-tie winners lacking OGS/cross-stream evidence; the row-Gaussian representative has active "
            f"rank {summary['key_numbers'].get('permeability_likelihood_winner_cross_stream_row_gaussian_active_rank')} "
            f"versus current accepted active rank "
            f"{summary['key_numbers'].get('permeability_likelihood_winner_cross_stream_current_accepted_active_rank')}.",
            f"The permeability next field-fit gate has status "
            f"{summary['key_numbers'].get('permeability_next_field_fit_gate_status')} and recommendation "
            f"{summary['key_numbers'].get('permeability_next_field_fit_gate_recommendation')}; "
            f"same-support active-objective batch executable now="
            f"{summary['key_numbers'].get('permeability_next_field_fit_gate_executable_same_support_active_objective_batch_now')}, "
            f"with gate statuses {summary['key_numbers'].get('permeability_next_field_fit_gate_status_counts')}.",
            f"The permeability likelihood/support recommendation packet has status "
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_status')}: "
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_count')} "
            f"recommendations, current policy="
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_current_policy')}, "
            f"at lower bound={summary['key_numbers'].get('permeability_likelihood_support_recommendations_at_lower_bound')}, "
            f"same-support gap={summary['key_numbers'].get('permeability_likelihood_support_recommendations_same_support_gap')}, "
            f"same-support batch executable now="
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_same_support_batch_executable_now')}, "
            f"bounds release now="
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_bounds_release_now')}, "
            f"tensor-shape release now="
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_tensor_shape_release_now')}, "
            f"and promotion unblocked="
            f"{summary['key_numbers'].get('permeability_likelihood_support_recommendations_unblocks_promotion')}.",
            f"The permeability likelihood-policy acceptance-record template has status "
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_status')}: "
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_primary_approval_rows_recorded')}/"
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_primary_approval_rows_required')} "
            f"primary policy approvals recorded, ready-to-apply="
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_ready_to_apply')}, "
            f"records decision="
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_records_decision')}, "
            f"changes active objective="
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_changes_active_objective')}, "
            f"and same-support batch executable now="
            f"{summary['key_numbers'].get('permeability_likelihood_policy_acceptance_record_template_same_support_batch_executable_now')}.",
            f"The NMR trend/anomaly follow-up screen recommends "
            f"{summary['key_numbers'].get('nmr_trend_followup_recommendation')}; its best unevaluated runnable "
            f"candidate is {summary['key_numbers'].get('nmr_trend_followup_best_unevaluated_candidate')} with "
            f"direct advantage {summary['key_numbers'].get('nmr_trend_followup_best_unevaluated_direct_advantage')} "
            f"against a materiality threshold of "
            f"{summary['key_numbers'].get('nmr_trend_followup_materiality_threshold')}, and "
            f"{summary['key_numbers'].get('nmr_trend_followup_median_state_beating_candidates')} candidates beat the "
            f"incumbent under the median observed trend/anomaly state term.",
            f"The ERT support-sensitivity audit checks "
            f"{summary['key_numbers'].get('ert_support_sensitivity_runs')} selected runs over "
            f"{summary['key_numbers'].get('ert_support_sensitivity_variant_count')} support variants; "
            f"its best mean support-rank run is "
            f"{summary['key_numbers'].get('ert_support_sensitivity_best_mean_rank_run')} "
            f"with mean rank {summary['key_numbers'].get('ert_support_sensitivity_best_mean_rank')}.",
            f"The Taupe/TDR series-weight audit checks "
            f"{summary['key_numbers'].get('taupe_series_weight_sensitivity_runs')} runs over "
            f"{summary['key_numbers'].get('taupe_series_weight_sensitivity_compared_series')} compared "
            f"A3/A4 series; there are "
            f"{summary['key_numbers'].get('taupe_series_weight_sensitivity_distinct_series_winners')} "
            f"distinct per-series winner runs, while the best mean weighting-rank run is "
            f"{summary['key_numbers'].get('taupe_series_weight_sensitivity_best_mean_rank_run')}.",
            f"The RH boundary uncertainty audit spans "
            f"{summary['key_numbers'].get('rh_boundary_uncertainty_envelope_dates')} daily envelope rows; "
            f"the active curve is outside the local RH-derived candidate envelope on "
            f"{summary['key_numbers'].get('rh_boundary_uncertainty_active_outside_envelope_rows')} rows, "
            f"with overlap pressure-range p50 "
            f"{summary['key_numbers'].get('rh_boundary_uncertainty_overlap_pressure_range_p50_mpa')} MPa.",
            f"The other-HM numeric source audit checks "
            f"{summary['key_numbers'].get('other_hm_numeric_source_audit_requests')} missing-export request classes; "
            f"{summary['key_numbers'].get('other_hm_numeric_source_audit_support_ready_requests')} have local support "
            f"geometry or extracted labels, but "
            f"{summary['key_numbers'].get('other_hm_numeric_source_audit_hard_ready_requests')} are hard-residual-ready.",
            f"The active incumbent "
            f"{summary['key_numbers'].get('cross_stream_active_incumbent_candidate')} has cross-stream "
            f"ranks NMR-bias={summary['key_numbers'].get('cross_stream_active_incumbent_nmr_label_bias_rank')}, "
            f"ERT={summary['key_numbers'].get('cross_stream_active_incumbent_ert_rank')}, and "
            f"Taupe={summary['key_numbers'].get('cross_stream_active_incumbent_taupe_rank')}, so it should "
            f"remain conditional on the unresolved diagnostic gates.",
            f"The frozen-model/measurement inclusion audit has status "
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_status')} with "
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_check_count')} checks, "
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_failure_count')} failures, "
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_manifest_count')} run "
            f"manifests checked, and measurement-info source/archive/workbook rows "
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_measurement_info_source_rows')}/"
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_archive_member_rows')}/"
            f"{summary['key_numbers'].get('frozen_model_measurement_inclusion_audit_workbook_sheet_rows')}.",
            f"The final inversion promotion checklist records "
            f"{summary['key_numbers'].get('final_inversion_promotion_decision')} with "
            f"{summary['key_numbers'].get('final_inversion_promotion_open_criterion_count')}/"
            f"{summary['key_numbers'].get('final_inversion_promotion_criterion_count')} open criteria "
            f"and status counts {summary['key_numbers'].get('final_inversion_promotion_status_counts')}.",
            f"The final inversion close-out playbook expands those into "
            f"{summary['key_numbers'].get('final_inversion_closeout_external_action_count')} "
            f"draft/response actions, "
            f"{summary['key_numbers'].get('final_inversion_closeout_internal_policy_action_count')} "
            f"internal policy action, and "
            f"{summary['key_numbers'].get('final_inversion_closeout_scenario_or_final_decision_action_count')} "
            f"scenario/final decision actions.",
            f"The final objective decision register records "
            f"{summary['key_numbers'].get('final_objective_decision_register_decision_count')} "
            f"include/exclude decisions, "
            f"{summary['key_numbers'].get('final_objective_decision_register_pending_or_not_ready_count')} "
            f"pending or not-ready rows, and "
            f"{summary['key_numbers'].get('final_objective_decision_register_explicit_exclusion_possible_count')} "
            f"rows with an explicit exclusion path.",
            f"The final objective scenario matrix records "
            f"{summary['key_numbers'].get('final_objective_scenario_matrix_option_count')} "
            f"explicit final-objective options, "
            f"{summary['key_numbers'].get('final_objective_scenario_matrix_current_field_winning_option_count')} "
            f"current-field winning options, "
            f"{summary['key_numbers'].get('final_objective_scenario_matrix_unique_winner_count')} unique winners, "
            f"{summary['key_numbers'].get('final_objective_scenario_matrix_unscored_future_option_count')} "
            f"unscored future option, and "
            f"{summary['key_numbers'].get('final_objective_scenario_matrix_not_final_likelihood_or_needs_new_policy_count')} "
            f"options that either need a new policy or are not a final likelihood.",
            f"The final objective include/exclude recommendation packet has status "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_status')}: "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_count')} "
            f"recommendations, "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_external_or_provenance_count')} "
            f"external/provenance rows, "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_diagnostic_or_exclude_without_new_evidence_count')} "
            f"diagnostic-or-exclude recommendations without new evidence, and "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_waiver_not_recommended_count')} "
            f"waivers not recommended. It does not unblock promotion="
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_unblocks_promotion')} "
            f"and keeps the field label at "
            f"{summary['key_numbers'].get('final_objective_include_exclude_recommendations_current_field_label')}.",
            f"The final objective no-new-evidence closeout draft has status "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_status')}: "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_count')} "
            f"draft rows, "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_external_or_provenance_count')} "
            f"external/provenance rows, "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_internal_policy_count')} "
            f"internal policy row, and "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_scenario_or_final_count')} "
            f"scenario/final rows. If approved and regenerated it would select "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_would_select_scenario')} "
            f"with winner "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_would_select_winner')}, "
            f"but records decisions="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_records_decisions')}, "
            f"promotes current field="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_promotes_current_field')}, "
            f"and unblocks promotion="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_closeout_draft_unblocks_promotion')}.",
            f"The no-new-evidence acceptance-record template has status "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_status')}: "
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_approval_rows_recorded')}/"
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_approval_rows_required')} "
            f"approval rows recorded, ready-to-apply="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_ready_to_apply')}, "
            f"records decisions="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_records_decisions')}, "
            f"and promotes current field="
            f"{summary['key_numbers'].get('final_objective_no_new_evidence_acceptance_record_template_promotes_current_field')}.",
            f"The Gmail draft send-review packet records "
            f"{summary['key_numbers'].get('gmail_draft_send_review_packet_ready_for_user_review_count')}/"
            f"{summary['key_numbers'].get('gmail_draft_send_review_packet_draft_count')} drafts ready for user review, "
            f"{summary['key_numbers'].get('gmail_draft_send_review_packet_unsent_draft_count')} unsent drafts, "
            f"and {summary['key_numbers'].get('gmail_draft_send_review_packet_request_count')} covered requests.",
            "It is still not the requested final inversion because the comparison remains deterministic",
            "proposal/sampler-batch selection rather than a converged posterior or optimizer trace and",
            "ERT/Taupe/RH gates remain open.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


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


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for source in paths:
        if not source.exists():
            continue
        target = catalogue_dir / source.name
        shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    frame, summary = build_rows()
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    catalogue_dir = args.catalogue_dir.resolve()
    summary["catalogue_copies"] = copy_outputs(
        catalogue_dir,
        [args.output_csv, args.output_md],
    )
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    write_markdown(args.output_md, frame, summary)
    summary["catalogue_copies"] = copy_outputs(
        catalogue_dir,
        [args.output_csv, args.output_json, args.output_md],
    )
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    copy_outputs(catalogue_dir, [args.output_json])


if __name__ == "__main__":
    main()
