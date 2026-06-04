#!/usr/bin/env python3
"""Build a machine-readable checklist for final all-measurement field promotion."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


STATUS_ORDER = {
    "pass": 0,
    "pass_with_caveat": 1,
    "active_only_pass": 2,
    "blocked_external": 3,
    "blocked_internal_decision": 4,
    "fails_promotion": 5,
    "missing": 6,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_inversion_promotion_checklist.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_inversion_promotion_checklist.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive checklist copies.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


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
    match = re.search(
        r"Output written on main\.pdf \((\d+) pages",
        log_path.read_text(encoding="utf-8", errors="ignore"),
    )
    return int(match.group(1)) if match else None


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


def add_row(
    rows: list[dict[str, str]],
    *,
    criterion_id: str,
    criterion: str,
    status: str,
    evidence: str,
    required_for_promotion: str,
    source_artifacts: str,
) -> None:
    rows.append(
        {
            "criterion_id": criterion_id,
            "criterion": criterion,
            "status": status,
            "evidence": evidence,
            "required_for_promotion": required_for_promotion,
            "source_artifacts": source_artifacts,
        }
    )


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return dict(sorted(counts.items(), key=lambda item: STATUS_ORDER.get(item[0], 99)))


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], csv_path: Path, json_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Final Inversion Promotion Checklist",
        "",
        "This checklist is the current promotion gate for calling any permeability",
        "field a final all-measurement inversion result. It intentionally separates",
        "the accepted active-objective incumbent from unresolved final-promotion",
        "criteria.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Promotion decision: `{summary['promotion_decision']}`",
        f"- Criteria: {summary['criterion_count']}",
        f"- Status counts: {summary['status_counts']}",
        f"- Current field: `{summary.get('current_field_run_id')}`",
        f"- Active-objective decision: `{summary.get('active_objective_decision')}`",
        f"- Final all-measurement decision: `{summary.get('current_field_final_decision')}`",
        f"- Open blockers: {summary.get('open_blocker_count')} ({summary.get('open_blocker_ids')})",
        f"- Conditional scenario winners: {summary.get('conditional_unique_winner_count')} unique winners across {summary.get('conditional_scenario_count')} scenarios",
        "",
        "## Checklist",
        "",
        "| Criterion | Status | Evidence | Required for promotion |",
        "| --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['criterion']} | `{row['status']}` | "
            f"{row['evidence']} | {row['required_for_promotion']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The current field can be used as the active direct-permeability/raw-NMR incumbent.",
            "- It cannot be promoted to a final all-measurement field while external measurement gates remain unsent/unanswered.",
            "- It also cannot be promoted while conditional scenario winners are unstable across accepted or plausible gate outcomes.",
            "- A final promotion requires either closing the listed gates or recording an explicit modelling decision to exclude a gated stream from the final objective.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for source in summary["source_artifacts"]:
        lines.append(f"- `{source}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    report_open = read_json(Path("inversion_workflow/report_open_comment_audit_summary.json"))
    traceability = read_json(Path("inversion_workflow/measurement_report_traceability_audit_summary.json"))
    ogs_formulation = read_json(Path("inversion_workflow/ogs_formulation_consistency_audit_summary.json"))
    ogs_run_input = read_json(Path("inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.json"))
    current_field = read_json(Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"))
    current_selection = read_json(Path("inversion_workflow/current_field_selection_audit_summary.json"))
    conditional = read_json(Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"))
    conditional_package = read_json(
        Path("inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES_SUMMARY.json")
    )
    conditional_difference = read_json(
        Path("inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.json")
    )
    production_decision = read_json(
        Path("inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.json")
    )
    stream_gates = read_json(Path("inversion_workflow/measurement_stream_activation_gate_audit_summary.json"))
    external_blockers = read_json(Path("inversion_workflow/external_blocker_dashboard_summary.json"))
    cte_confirmation = read_json(Path("inversion_workflow/cte_confirmation_request_summary.json"))
    internal_decisions = read_json(Path("inversion_workflow/internal_gate_decision_register_summary.json"))
    nmr_final_policy_gate = read_json(Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"))
    support_conflict = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    lower_bound = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    policy_acceptance = read_json(
        Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json")
    )
    next_gate = read_json(Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"))
    permeability_policy_evidence = format_permeability_policy_evidence(
        support_conflict, lower_bound, policy_acceptance, next_gate
    )
    release_gate = read_json(Path("inversion_workflow/inversion_release_gate_audit.json"))
    citations = read_json(Path("Library/citation_locator_audit_summary.json"))

    field_summary = current_field.get("field", {})
    current_field_ready = (
        current_field.get("status") == "current_permeability_field_package_generated"
        and int(field_summary.get("triangle6_cell_count", 0) or 0) > 0
        and int(field_summary.get("positive_definite_cell_count", 0) or 0)
        == int(field_summary.get("triangle6_cell_count", -1) or -1)
        and Path(str(current_field.get("packaged_mesh", ""))).exists()
    )
    active_decision = current_selection.get("active_objective_decision")
    final_decision = current_selection.get("final_all_measurement_decision")
    open_blocker_ids = external_blockers.get("open_blocker_ids", [])
    open_blocker_id_set = set(open_blocker_ids)
    required_gate_fail_count = int(stream_gates.get("required_gate_fail_count", 0) or 0)
    conditional_unique_winner_count = int(conditional.get("unique_winner_count", 0) or 0)
    conditional_scenario_count = int(conditional.get("scenario_count", 0) or 0)
    current_wins = int(conditional.get("current_field_winning_scenario_count", 0) or 0)

    rows: list[dict[str, str]] = []

    add_row(
        rows,
        criterion_id="P01_report_build",
        criterion="Report build is clean and has no active review markers.",
        status=(
            "pass"
            if log_is_clean(Path("main.log"), Path("main.blg"))
            and pdf_pages_from_log(Path("main.log")) is not None
            and as_int(report_open.get("active_report_unresolved_marker_count"), 1) == 0
            else "missing"
        ),
        evidence=(
            f"main.pdf pages={pdf_pages_from_log(Path('main.log'))}; log clean="
            f"{log_is_clean(Path('main.log'), Path('main.blg'))}; active report markers="
            f"{report_open.get('active_report_unresolved_marker_count')}."
        ),
        required_for_promotion="Keep the report build clean after every checklist or chapter edit.",
        source_artifacts="main.pdf; main.log; main.blg; inversion_workflow/report_open_comment_audit.md",
    )
    add_row(
        rows,
        criterion_id="P02_model_freeze",
        criterion="Frozen GESA model semantics are recovered and run-local edits are bounded.",
        status=(
            "pass_with_caveat"
            if ogs_formulation.get("all_hard_checks_pass")
            and ogs_run_input.get("execution_returncode") == 0
            else "missing"
        ),
        evidence=(
            f"formulation checks={ogs_formulation.get('check_count')}; hard failures="
            f"{ogs_formulation.get('fail_count')}; process={ogs_formulation.get('process_type')}; "
            f"run-input status={ogs_run_input.get('status')}; OGS returncode="
            f"{ogs_run_input.get('execution_returncode')}."
        ),
        required_for_promotion=(
            "Keep CTE and fixed-porosity caveats explicit; regenerate appended-data submeshes only if "
            "downstream meshio decoding is required."
        ),
        source_artifacts=(
            "MODEL_AUDIT.md; inversion_workflow/ogs_formulation_consistency_audit.md; "
            "inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.md"
        ),
    )
    add_row(
        rows,
        criterion_id="P03_measurement_traceability",
        criterion="All collected measurement classes are catalogued, processed, and linked to report/model evidence.",
        status=(
            "pass"
            if traceability.get("all_observations_traceable")
            and as_int(traceability.get("manifest_validation_failures"), 1) == 0
            else "missing"
        ),
        evidence=(
            f"traceability status={traceability.get('status')}; observations="
            f"{traceability.get('observation_count')}; missing sections="
            f"{traceability.get('missing_chapter_section_count')}; manifest failures="
            f"{traceability.get('manifest_validation_failures')}."
        ),
        required_for_promotion="Refresh traceability after adding any new files or provider responses.",
        source_artifacts="inversion_workflow/measurement_report_traceability_audit.md",
    )
    add_row(
        rows,
        criterion_id="P04_current_field_package",
        criterion="The current permeability field is packaged for inspection and rerun provenance.",
        status="pass" if current_field_ready else "missing",
        evidence=(
            f"status={current_field.get('status')}; run={current_field.get('run_id')}; cells="
            f"{field_summary.get('triangle6_cell_count')}; positive-definite="
            f"{field_summary.get('positive_definite_cell_count')}; mesh={current_field.get('packaged_mesh')}."
        ),
        required_for_promotion="Keep the packaged field synchronized with the accepted active-objective incumbent.",
        source_artifacts="inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD.md",
    )
    add_row(
        rows,
        criterion_id="P05_active_objective_incumbent",
        criterion="The packaged field is the current active direct-permeability/raw-NMR incumbent.",
        status="active_only_pass" if active_decision == "accept_as_current_active_objective_incumbent" else "missing",
        evidence=(
            f"active decision={active_decision}; active objective="
            f"{current_selection.get('key_numbers', {}).get('active_objective_value')}; "
            f"active rank={current_selection.get('key_numbers', {}).get('active_objective_rank')}."
        ),
        required_for_promotion=(
            "This is necessary but not sufficient; final promotion also requires stable accepted "
            "measurement semantics and closed gates."
        ),
        source_artifacts="inversion_workflow/current_field_selection_audit.md",
    )
    add_row(
        rows,
        criterion_id="P06_active_sampler_pause",
        criterion="Further same-neighborhood active-objective OGS spending is not currently justified.",
        status=(
            "active_only_pass"
            if production_decision.get("recommendation") == "pause_active_production_sampling"
            else "missing"
        ),
        evidence=(
            f"recommendation={production_decision.get('recommendation')}; production rounds="
            f"{production_decision.get('production_round_count')}; P(improve)="
            f"{production_decision.get('top_probability_of_improvement')}; EI="
            f"{production_decision.get('top_expected_improvement')}; reason="
            f"{production_decision.get('reason')}."
        ),
        required_for_promotion=(
            "Treat this only as an active-objective stopping point; it does not close gated "
            "all-measurement criteria."
        ),
        source_artifacts="inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.md",
    )
    add_row(
        rows,
        criterion_id="P07_release_gate",
        criterion="Run-local parameter release gate remains clean for executed candidates.",
        status=(
            "pass"
            if release_gate.get("status") == "pass" and as_int(release_gate.get("failure_count")) == 0
            else "missing"
        ),
        evidence=(
            f"status={release_gate.get('status')}; audited runs={release_gate.get('run_count')}; "
            f"checks={release_gate.get('check_count')}; failures={release_gate.get('failure_count')}."
        ),
        required_for_promotion="Continue to reject silent release of porosity, retention, mechanical, boundary, or thermal fields.",
        source_artifacts="inversion_workflow/inversion_release_gate_audit.md",
    )
    add_row(
        rows,
        criterion_id="P08_nmr_residual_policy",
        criterion="Final NMR residual semantics are settled.",
        status=(
            "blocked_internal_decision"
            if internal_decisions.get("nmr_default_promotion_status") == "local_policy_recorded_not_promoted_default"
            else "pass_with_caveat"
        ),
        evidence=(
            f"NMR default promotion status={internal_decisions.get('nmr_default_promotion_status')}; "
            f"final NMR policy selected={nmr_final_policy_gate.get('final_nmr_policy_selected')}; "
            f"recommended candidate policy={nmr_final_policy_gate.get('recommended_candidate_policy')}; "
            f"recommended candidate run={nmr_final_policy_gate.get('recommended_candidate_policy_run')}; "
            f"current raw incumbent rank under trend/anomaly="
            f"{nmr_final_policy_gate.get('current_raw_incumbent_rank_under_trend_anomaly')}; "
            f"trend/anomaly winner raw rank={nmr_final_policy_gate.get('trend_anomaly_winner_raw_rank')}; "
            f"follow-up recommendation={nmr_final_policy_gate.get('followup_recommendation')}; "
            f"trend/anomaly winner={current_selection.get('key_numbers', {}).get('nmr_trend_anomaly_winner')}; "
            f"current trend/anomaly rank={current_selection.get('key_numbers', {}).get('nmr_trend_anomaly_rank')}."
        ),
        required_for_promotion=(
            "Record whether final NMR uses raw absolute theta, model-error/bias handling, "
            "trend/anomaly residuals, or an explicit free-water correction."
        ),
        source_artifacts="inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_final_residual_policy_gate.md; inversion_workflow/internal_gate_decision_register.md",
    )
    gate_rows = [
        (
            "P09_ert_gate",
            "ERT transform/support and uncertainty gates are closed.",
            ["ert_transform_support", "ert_uncertainty"],
            "Accept ERT transform/support mask and covariance/uncertainty before ERT can select a final field.",
            "inversion_workflow/processed_observations/ert_resistivity_diagnostic.md; inversion_workflow/external_blocker_dashboard.md",
        ),
        (
            "P10_taupe_gate",
            "Taupe/TDR unit/calibration and uncertainty gates are closed.",
            ["taupe_unit_calibration"],
            "Accept workbook units/calibration and grouped uncertainty before Taupe/TDR can select a final field.",
            "inversion_workflow/taupe_tdr_trend_diagnostic.md; inversion_workflow/external_blocker_dashboard.md",
        ),
        (
            "P11_rh_gate",
            "RH/suction boundary-curve provenance and uncertainty gates are closed.",
            ["rh_active_curve_provenance"],
            "Resolve active curve generation, time axis, sensor screening, and uncertainty before RH informs a hard residual or retention/boundary release.",
            "inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; inversion_workflow/external_blocker_dashboard.md",
        ),
        (
            "P12_other_hm_gate",
            "Other HM numeric exports and uncertainty gates are closed.",
            ["hm_numeric_exports", "hm_uncertainty"],
            "Obtain hard-residual-ready Geoscope, laser scan, and levelling numeric exports or explicitly exclude them from final likelihood.",
            "inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; inversion_workflow/external_blocker_dashboard.md",
        ),
        (
            "P13_perm_endpoint_gate",
            "Historical permeability endpoint geometry/provenance is closed.",
            ["perm_endpoint_geometry"],
            (
                "Obtain the missing endpoint traces/geometries, or record that the current "
                "projected rows are the only accepted direct-permeability support while keeping "
                "the likelihood/support policy explicit."
            ),
            (
                "inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md; "
                "inversion_workflow/external_blocker_dashboard.md; "
                "inversion_workflow/permeability_support_conflict_spatial_audit.md; "
                "inversion_workflow/permeability_support_lower_bound_audit.md; "
                "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md"
            ),
        ),
        (
            "P14_cte_confirmation",
            "Suspicious thermal-expansivity value is confirmed or scoped out of interpretation.",
            ["cte_value_confirmation"],
            "Send/close the CTE confirmation and record whether CTE=1254.74 is intended, inactive, copied heat capacity, or another convention.",
            "inversion_workflow/cte_confirmation_request.md; inversion_workflow/external_blocker_dashboard.md",
        ),
    ]
    for criterion_id, criterion, gate_ids, required, sources in gate_rows:
        open_ids = [gate for gate in gate_ids if gate in open_blocker_id_set]
        add_row(
            rows,
            criterion_id=criterion_id,
            criterion=criterion,
            status="blocked_external" if open_ids else "pass",
            evidence=(
                f"open blocker ids for this criterion={open_ids}; dashboard status="
                f"{external_blockers.get('status')}; unsent blockers="
                f"{external_blockers.get('unsent_blocker_count')}; missing responses="
                f"{external_blockers.get('missing_response_blocker_count')}."
                + (f" {permeability_policy_evidence}." if criterion_id == "P13_perm_endpoint_gate" else "")
            ),
            required_for_promotion=required,
            source_artifacts=sources,
        )
    add_row(
        rows,
        criterion_id="P15_conditional_field_stability",
        criterion="The same permeability field wins across accepted or plausible final measurement scenarios.",
        status=(
            "fails_promotion"
            if conditional_unique_winner_count > 1 or current_wins != conditional_scenario_count
            else "pass"
        ),
        evidence=(
            f"conditional decision={conditional.get('final_decision')}; scenarios={conditional_scenario_count}; "
            f"unique winners={conditional_unique_winner_count}; current field wins={current_wins}; "
            f"candidate package status={conditional_package.get('status')}; difference audit status="
            f"{conditional_difference.get('status')}. {permeability_policy_evidence}."
        ),
        required_for_promotion=(
            "Close/accept/exclude gated streams, settle the direct-permeability support/likelihood policy, "
            "and rerun the scenario audit until the final objective has a stable winner."
        ),
        source_artifacts=(
            "inversion_workflow/conditional_field_selection_scenarios.md; "
            "inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES.md; "
            "inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md; "
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; "
            "inversion_workflow/permeability_next_field_fit_gate.md"
        ),
    )
    add_row(
        rows,
        criterion_id="P16_final_field_decision",
        criterion="The selected field is approved as the final all-measurement permeability inversion result.",
        status="fails_promotion" if final_decision != "promote_to_final_all_measurement_field" else "pass",
        evidence=(
            f"current field final decision={final_decision}; current selection status="
            f"{current_selection.get('status')}; selection status counts={current_selection.get('status_counts')}; "
            f"required stream-gate failures={required_gate_fail_count}. {permeability_policy_evidence}."
        ),
        required_for_promotion=(
            "Only switch to promoted after every preceding final-promotion criterion is pass or explicitly waived "
            "with a documented modelling decision, including the direct-permeability likelihood/support decision."
        ),
        source_artifacts=(
            "inversion_workflow/current_field_selection_audit.md; "
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; "
            "inversion_workflow/permeability_next_field_fit_gate.md"
        ),
    )
    add_row(
        rows,
        criterion_id="P17_citation_package",
        criterion="Citations, source locators, and unavailable/fulltext tracking are complete for current report claims.",
        status=(
            "pass"
            if citations.get("status") == "citation_locator_audit_generated"
            and as_int(citations.get("missing_or_weak_locator_count"), 1) == 0
            and as_int(citations.get("missing_bib_entry_count"), 1) == 0
            else "missing"
        ),
        evidence=(
            f"status={citations.get('status')}; citation instances={citations.get('citation_key_instance_count')}; "
            f"unique keys={citations.get('unique_cited_key_count')}; missing/weak locators="
            f"{citations.get('missing_or_weak_locator_count')}; missing BibTeX="
            f"{citations.get('missing_bib_entry_count')}."
        ),
        required_for_promotion="Rerun citation audit after adding sources or changing measurement semantics.",
        source_artifacts="Library/citation_locator_audit.md; Library/source_coverage_audit.md",
    )

    frame = pd.DataFrame(rows).sort_values(
        by="status", key=lambda col: col.map(lambda status: STATUS_ORDER.get(status, 99))
    )
    counts = status_counts(rows)
    hard_open_statuses = {"blocked_external", "blocked_internal_decision", "fails_promotion", "missing"}
    hard_open = [row for row in rows if row["status"] in hard_open_statuses]
    promotion_decision = "promote_to_final_all_measurement_field" if not hard_open else "do_not_promote_current_field"
    summary = {
        "status": "final_inversion_promotion_checklist_generated",
        "promotion_decision": promotion_decision,
        "criterion_count": len(rows),
        "status_counts": counts,
        "open_criterion_ids": [row["criterion_id"] for row in hard_open],
        "current_field_run_id": current_field.get("run_id"),
        "active_objective_decision": active_decision,
        "current_field_final_decision": final_decision,
        "open_blocker_count": external_blockers.get("open_blocker_count"),
        "open_blocker_ids": open_blocker_ids,
        "unsent_blocker_count": external_blockers.get("unsent_blocker_count"),
        "missing_response_blocker_count": external_blockers.get("missing_response_blocker_count"),
        "conditional_scenario_count": conditional_scenario_count,
        "conditional_unique_winner_count": conditional_unique_winner_count,
        "conditional_current_field_wins": current_wins,
        "required_stream_gate_fail_count": required_gate_fail_count,
        "production_sampler_recommendation": production_decision.get("recommendation"),
        "source_artifacts": [
            "inversion_workflow/report_open_comment_audit.md",
            "inversion_workflow/measurement_report_traceability_audit.md",
            "inversion_workflow/ogs_formulation_consistency_audit.md",
            "inversion_workflow/runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.md",
            "inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD.md",
            "inversion_workflow/current_field_selection_audit.md",
            "inversion_workflow/conditional_field_selection_scenarios.md",
            "inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES.md",
            "inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md",
            "inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.md",
            "inversion_workflow/measurement_stream_activation_gate_audit.md",
            "inversion_workflow/nmr_final_residual_policy_gate.md",
            "inversion_workflow/external_blocker_dashboard.md",
            "inversion_workflow/internal_gate_decision_register.md",
            "inversion_workflow/permeability_support_conflict_spatial_audit.md",
            "inversion_workflow/permeability_support_lower_bound_audit.md",
            "inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md",
            "inversion_workflow/permeability_next_field_fit_gate.md",
            "Library/citation_locator_audit.md",
        ],
    }

    write_outputs(frame, summary, args.output_csv, args.output_json, args.output_md)
    generated_files = [args.output_csv, args.output_json, args.output_md]
    if args.catalogue_dir:
        args.catalogue_dir.mkdir(parents=True, exist_ok=True)
        copies = []
        for path in generated_files:
            target = args.catalogue_dir / path.name
            shutil.copy2(path, target)
            copies.append({"source": str(path), "catalogue_copy": str(target)})
        summary["catalogue_copies"] = copies
        args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


if __name__ == "__main__":
    main()
