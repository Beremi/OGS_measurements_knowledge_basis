#!/usr/bin/env python3
"""Build the next-action gate for permeability field fitting."""

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
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive gate copies.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def join(values: list[Any], separator: str = "; ") -> str:
    return separator.join(str(value) for value in values if value not in {None, ""})


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    residual = read_json(Path("inversion_workflow/permeability_residual_conflict_audit_summary.json"))
    support_lb = read_json(Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"))
    support_spatial = read_json(Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"))
    decision = read_json(Path("inversion_workflow/permeability_likelihood_decision_request_summary.json"))
    outlier_disposition = read_json(
        Path("inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json")
    )
    rerank = read_json(Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json"))
    winner_cross = read_json(Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json"))
    final_matrix = read_json(Path("inversion_workflow/final_objective_scenario_matrix_summary.json"))
    promotion = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    current_field = read_json(Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"))
    production_decision = read_json(
        Path("inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.json")
    )

    support_gap = support_lb.get("same_support_reducible_objective_gap")
    support_fraction = support_lb.get("same_support_reducible_objective_fraction")
    spatial_top = support_spatial.get("top_conflict_cell", {})
    outside_tie_direct_only = winner_cross.get("outside_tie_direct_only_policy_winner_rows")
    final_options = final_matrix.get("option_count")
    current_winning_options = final_matrix.get("current_field_winning_option_count")
    open_criteria = promotion.get("open_criterion_ids", [])
    open_blockers = promotion.get("open_blocker_ids", [])
    current_run_id = current_field.get("run_id") or promotion.get("current_field_run_id")

    rows = [
        {
            "gate_id": "G01_same_support_active_objective_sampling",
            "gate_type": "stop_gate",
            "current_status": "do_not_run_more_same_support_sampling_now",
            "current_decision": "Pause routine same-support smooth/local-basis active-objective OGS batches.",
            "evidence": (
                f"support lower-bound gap={support_gap}; reducible fraction={support_fraction}; "
                f"current at lower bound={support_lb.get('current_at_single_support_lower_bound')}; "
                f"support-conflict spatial audit={support_spatial.get('status')}; "
                f"active/repeated/range>=2 support cells="
                f"{support_spatial.get('active_support_cell_count')}/"
                f"{support_spatial.get('repeated_support_cell_count')}/"
                f"{support_spatial.get('support_cells_observed_range_ge_2_log10')}; "
                f"production sampler recommendation={production_decision.get('recommendation')}"
            ),
            "prerequisite_to_reopen": (
                "Approve a changed support mapping, likelihood semantics, configured bound/tensor-shape release, "
                "or a new accepted measurement-stream objective."
            ),
            "allowed_next_action": (
                "Use existing audits as stop evidence; spend effort on likelihood/support decisions or external gates."
            ),
            "forbidden_until_prerequisite": (
                "Do not spend more OGS runs on the same support map and same active row-Gaussian objective."
            ),
            "source_artifacts": (
                "inversion_workflow/permeability_support_lower_bound_audit.md; "
                "inversion_workflow/permeability_support_conflict_spatial_audit.md; "
                "inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.md"
            ),
        },
        {
            "gate_id": "G02_likelihood_policy_decision",
            "gate_type": "internal_policy_gate",
            "current_status": "rowwise_gaussian_default_retained_for_current_report",
            "current_decision": decision.get("recommended_current_report_policy", "keep_rowwise_gaussian_default"),
            "evidence": (
                f"decision options={decision.get('decision_option_count')}; "
                f"top-10 row-loss share={decision.get('row_loss_top_10_share')}; "
                f"support mean objective={decision.get('support_mean_unit_objective')}; "
                f"support median objective={decision.get('support_median_unit_objective')}"
            ),
            "prerequisite_to_reopen": (
                "Record the exact robust kernel, support aggregation, outlier disposition, or new parameterization rule."
            ),
            "allowed_next_action": "Treat non-default policies as diagnostics and rerank evidence until approved.",
            "forbidden_until_prerequisite": "Do not silently replace the active likelihood with a diagnostic policy.",
            "source_artifacts": "inversion_workflow/permeability_likelihood_decision_request.md",
        },
        {
            "gate_id": "G03_nondefault_policy_winner_execution",
            "gate_type": "execution_gate",
            "current_status": "blocked_until_policy_approved_and_ogs_executed",
            "current_decision": "Do not replace the current accepted field with a direct-only non-default winner.",
            "evidence": (
                f"rerank scored fields={rerank.get('candidate_fields_scored')}; "
                f"outside-tie direct-only winners={outside_tie_direct_only}; "
                f"winner rows with cross-stream evidence="
                f"{winner_cross.get('policy_winner_rows_with_cross_stream_scorecard')}; "
                f"unique winners with cross-stream evidence="
                f"{winner_cross.get('unique_winners_with_cross_stream_scorecard')}"
            ),
            "prerequisite_to_reopen": (
                "Approve a non-default likelihood policy, execute targeted OGS/state sampling for its winner, "
                "and join the run to NMR/ERT/Taupe diagnostics before any promotion."
            ),
            "allowed_next_action": "Use policy winners as targeted candidates only after a written likelihood decision.",
            "forbidden_until_prerequisite": "Do not promote a direct-only policy winner to an all-measurement field.",
            "source_artifacts": (
                "inversion_workflow/permeability_likelihood_scenario_rerank.md; "
                "inversion_workflow/permeability_likelihood_winner_cross_stream_audit.md"
            ),
        },
        {
            "gate_id": "G04_configured_scalar_outliers",
            "gate_type": "bounds_or_tensor_shape_gate",
            "current_status": "local_outlier_disposition_recorded_policy_still_required",
            "current_decision": (
                "Do not widen eigenvalue bounds or release tensor shape from the scalar-envelope rows alone; "
                "keep them visible under the current default until the modelling team accepts or changes the policy."
            ),
            "evidence": (
                f"active rows outside configured scalar range="
                f"{residual.get('active_rows_outside_configured_scalar_range')}; "
                f"|residual|>=2 log10 rows={residual.get('very_large_residual_active_rows_ge_2_log10')}; "
                f"max abs residual={residual.get('direct_summary', {}).get('max_abs_log10_residual')}; "
                f"outlier disposition status={outlier_disposition.get('status')}; "
                f"unique outlier groups={outlier_disposition.get('unique_physical_outlier_group_count')}; "
                f"max envelope excess={outlier_disposition.get('max_range_excess_log10')} log10; "
                f"bounds release now={outlier_disposition.get('bounds_release_recommended_now')}; "
                f"tensor-shape release now={outlier_disposition.get('tensor_shape_release_recommended_now')}"
            ),
            "prerequisite_to_reopen": (
                "Modelling team accepts this local disposition or chooses a capped/robust row policy, "
                "support-cell aggregation, explicit outlier exclusion, wider eigenvalue bounds, "
                "or tensor-shape/anisotropy release."
            ),
            "allowed_next_action": "Use the disposition as local evidence for the bounds/tensor-shape policy discussion.",
            "forbidden_until_prerequisite": (
                "Do not treat scalar-range residuals as solved by more same-family sampling or by silent bounds release."
            ),
            "source_artifacts": (
                "inversion_workflow/permeability_residual_conflict_audit.md; "
                "inversion_workflow/permeability_configured_scalar_outlier_disposition.md"
            ),
        },
        {
            "gate_id": "G05_support_geometry_and_endpoint_update",
            "gate_type": "support_mapping_gate",
            "current_status": "blocked_by_support_conflicts_and_endpoint_geometry",
            "current_decision": "Keep endpoint-missing historical permeability rows inactive unless geometry is accepted.",
            "evidence": (
                f"support groups={support_lb.get('support_group_count')}; "
                f"groups with observed range >=2 log10="
                f"{support_lb.get('support_groups_with_observed_range_ge_2_log10')}; "
                f"spatial top conflict cell={spatial_top.get('primary_cell_id')} "
                f"({spatial_top.get('segments')} at {spatial_top.get('depth_min_m')}-"
                f"{spatial_top.get('depth_max_m')} m, observed range="
                f"{spatial_top.get('observed_log10_range')}); "
                f"open promotion criteria include P13={'P13_perm_endpoint_gate' in open_criteria}"
            ),
            "prerequisite_to_reopen": (
                "Accept missing endpoint traces/geometry or a new support aggregation policy, then rebuild targets."
            ),
            "allowed_next_action": "Wait for endpoint evidence or explicitly exclude endpoint-missing rows.",
            "forbidden_until_prerequisite": "Do not activate endpoint-missing rows as hard residuals.",
            "source_artifacts": (
                "inversion_workflow/permeability_support_lower_bound_audit.md; "
                "inversion_workflow/permeability_support_conflict_spatial_audit.md; "
                "inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md"
            ),
        },
        {
            "gate_id": "G06_measurement_stream_final_objective",
            "gate_type": "external_stream_gate",
            "current_status": "blocked_by_external_stream_gates",
            "current_decision": "Do not promote the active field as the final all-measurement result.",
            "evidence": (
                f"final-objective options={final_options}; current-field winning options={current_winning_options}; "
                f"unique winners={final_matrix.get('unique_winner_count')}; "
                f"open blockers={len(open_blockers)}"
            ),
            "prerequisite_to_reopen": (
                "Close or explicitly exclude ERT, Taupe/TDR, RH, other-HM, endpoint, CTE, and NMR-policy gates, "
                "then choose one final-objective scenario."
            ),
            "allowed_next_action": "Use the final objective scenario matrix to select or reject a final scenario.",
            "forbidden_until_prerequisite": "Do not call the current active field a final all-measurement inversion.",
            "source_artifacts": (
                "inversion_workflow/final_objective_scenario_matrix.md; "
                "inversion_workflow/final_inversion_promotion_checklist.md"
            ),
        },
        {
            "gate_id": "G07_current_field_package",
            "gate_type": "deliverable_gate",
            "current_status": "available_for_inspection_active_only",
            "current_decision": "Keep the packaged field as the active-objective incumbent, not a final field.",
            "evidence": (
                f"current run={current_run_id}; "
                f"triangle6 cells={current_field.get('field', {}).get('triangle6_cell_count')}; "
                f"positive-definite cells={current_field.get('field', {}).get('positive_definite_cell_count')}; "
                f"final decision={promotion.get('current_field_final_decision')}"
            ),
            "prerequisite_to_reopen": "Pass the final promotion checklist and final-objective scenario decision.",
            "allowed_next_action": "Use the package for inspection, reruns, and comparison against scenario winners.",
            "forbidden_until_prerequisite": "Do not present it as the completed all-measurement field.",
            "source_artifacts": (
                "inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD.md; "
                "inversion_workflow/current_field_selection_audit.md"
            ),
        },
        {
            "gate_id": "G08_posterior_or_optimizer_trace",
            "gate_type": "completion_gate",
            "current_status": "not_ready_until_objective_finalized",
            "current_decision": "Do not treat deterministic sampler batches as a converged posterior or optimizer trace.",
            "evidence": (
                "Current evidence is a deterministic candidate/sampler comparison; "
                f"promotion decision={promotion.get('promotion_decision')}; "
                f"open criteria={len(open_criteria)}"
            ),
            "prerequisite_to_reopen": (
                "Finalize the likelihood/objective gates, then run the chosen optimizer/posterior workflow "
                "against that objective."
            ),
            "allowed_next_action": "Keep deterministic batches as screening evidence.",
            "forbidden_until_prerequisite": "Do not claim a final Bayesian/optimizer fit.",
            "source_artifacts": (
                "inversion_workflow/objective_readiness_audit.md; "
                "inversion_workflow/final_inversion_promotion_checklist.md"
            ),
        },
    ]

    status_counts: dict[str, int] = {}
    gate_type_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["current_status"]] = status_counts.get(row["current_status"], 0) + 1
        gate_type_counts[row["gate_type"]] = gate_type_counts.get(row["gate_type"], 0) + 1

    summary = {
        "status": "permeability_next_field_fit_gate_generated",
        "gate_count": len(rows),
        "gate_type_counts": dict(sorted(gate_type_counts.items())),
        "gate_status_counts": dict(sorted(status_counts.items())),
        "overall_recommendation": (
            "pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes"
        ),
        "executable_same_support_active_objective_batch_now": False,
        "current_report_default_policy": decision.get("recommended_current_report_policy"),
        "current_field_run_id": current_run_id,
        "current_field_final_decision": promotion.get("current_field_final_decision"),
        "same_support_reducible_objective_gap": support_gap,
        "same_support_reducible_objective_fraction": support_fraction,
        "current_at_single_support_lower_bound": support_lb.get("current_at_single_support_lower_bound"),
        "outside_tie_direct_only_policy_winner_rows": outside_tie_direct_only,
        "active_rows_outside_configured_scalar_range": residual.get("active_rows_outside_configured_scalar_range"),
        "configured_scalar_outlier_disposition_status": outlier_disposition.get("status"),
        "configured_scalar_outlier_disposition_unique_group_count": outlier_disposition.get(
            "unique_physical_outlier_group_count"
        ),
        "configured_scalar_outlier_disposition_max_excess_log10": outlier_disposition.get("max_range_excess_log10"),
        "configured_scalar_outlier_disposition_bounds_release_now": outlier_disposition.get(
            "bounds_release_recommended_now"
        ),
        "configured_scalar_outlier_disposition_tensor_shape_release_now": outlier_disposition.get(
            "tensor_shape_release_recommended_now"
        ),
        "support_groups_with_observed_range_ge_2_log10": support_lb.get("support_groups_with_observed_range_ge_2_log10"),
        "support_conflict_spatial_audit_status": support_spatial.get("status"),
        "support_conflict_spatial_mesh_cell_count": support_spatial.get("mesh_cell_count"),
        "support_conflict_spatial_active_support_cell_count": support_spatial.get("active_support_cell_count"),
        "support_conflict_spatial_repeated_support_cell_count": support_spatial.get("repeated_support_cell_count"),
        "support_conflict_spatial_range_ge_1_log10_cell_count": (
            support_spatial.get("support_cells_observed_range_ge_1_log10")
        ),
        "support_conflict_spatial_range_ge_2_log10_cell_count": (
            support_spatial.get("support_cells_observed_range_ge_2_log10")
        ),
        "support_conflict_spatial_configured_scalar_conflict_cell_count": (
            support_spatial.get("configured_scalar_range_conflict_cell_count")
        ),
        "support_conflict_spatial_top_conflict_cell": spatial_top,
        "final_objective_option_count": final_options,
        "final_objective_current_field_winning_option_count": current_winning_options,
        "open_promotion_criterion_count": len(open_criteria),
        "open_promotion_criterion_ids": open_criteria,
        "open_blocker_count": len(open_blockers),
        "open_blocker_ids": open_blockers,
        "next_decision_sequence": [
            "Keep the current field active-only while final objective gates remain open.",
            "Do not run another same-support active-objective OGS batch under the current row-Gaussian policy.",
            "Use the spatial support-conflict audit to inspect where the repeated-row support conflicts sit on the mesh before changing support or likelihood semantics.",
            "Choose whether direct permeability needs robust rows, support-cell aggregation, scalar outlier handling, or a new parameterization.",
            "Use the configured-scalar outlier disposition: current local evidence does not justify bounds widening or tensor-shape release from the two duplicate envelope rows alone.",
            "If a non-default direct policy is approved and selects a direct-only winner, execute OGS/state/diagnostic evidence before any promotion.",
            "After external stream gates are closed or explicitly excluded, rebuild final-objective scenarios and the promotion checklist.",
        ],
        "source_artifacts": [
            "inversion_workflow/permeability_residual_conflict_audit_summary.json",
            "inversion_workflow/permeability_support_lower_bound_audit_summary.json",
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
            "inversion_workflow/permeability_likelihood_decision_request_summary.json",
            "inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json",
            "inversion_workflow/permeability_likelihood_scenario_rerank_summary.json",
            "inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json",
            "inversion_workflow/final_objective_scenario_matrix_summary.json",
            "inversion_workflow/final_inversion_promotion_checklist_summary.json",
            "inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json",
            "inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.json",
        ],
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "gate_id",
        "gate_type",
        "current_status",
        "current_decision",
        "evidence",
        "prerequisite_to_reopen",
        "allowed_next_action",
        "forbidden_until_prerequisite",
        "source_artifacts",
    ]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Permeability Next Field-Fit Gate",
        "",
        "This gate turns the current residual, likelihood-policy, rerank, and promotion",
        "audits into explicit next-action rules. It does not change the active",
        "objective, run OGS, or modify the frozen GESA model.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Gates: {summary['gate_count']}",
        f"- Overall recommendation: `{summary['overall_recommendation']}`",
        f"- Same-support active-objective batch executable now: {summary['executable_same_support_active_objective_batch_now']}",
        f"- Current report default policy: `{summary['current_report_default_policy']}`",
        f"- Current field final decision: `{summary['current_field_final_decision']}`",
        f"- Same-support reducible gap: {summary['same_support_reducible_objective_gap']}",
        f"- Spatial support cells active/repeated/range>=2 log10: "
        f"{summary['support_conflict_spatial_active_support_cell_count']}/"
        f"{summary['support_conflict_spatial_repeated_support_cell_count']}/"
        f"{summary['support_conflict_spatial_range_ge_2_log10_cell_count']}",
        f"- Outside-tie direct-only policy winners: {summary['outside_tie_direct_only_policy_winner_rows']}",
        "",
        "## Gate Table",
        "",
        "| Gate | Type | Status | Decision | Evidence | Reopen prerequisite |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate_id']}` | `{row['gate_type']}` | `{row['current_status']}` | "
            f"{md_cell(row['current_decision'])} | {md_cell(row['evidence'])} | "
            f"{md_cell(row['prerequisite_to_reopen'])} |"
        )

    lines.extend(["", "## Next Decision Sequence", ""])
    for item in summary["next_decision_sequence"]:
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
    rows, summary = build_rows()
    write_outputs(rows, summary, args)


if __name__ == "__main__":
    main()
