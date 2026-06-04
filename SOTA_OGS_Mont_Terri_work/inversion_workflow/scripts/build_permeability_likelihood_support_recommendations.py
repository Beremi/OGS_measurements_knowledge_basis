#!/usr/bin/env python3
"""Build a consolidated direct-permeability likelihood/support recommendation packet."""

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
        "--policy-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"),
    )
    parser.add_argument(
        "--decision-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request_summary.json"),
    )
    parser.add_argument(
        "--support-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_support_lower_bound_audit_summary.json"),
    )
    parser.add_argument(
        "--support-spatial-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"),
    )
    parser.add_argument(
        "--outlier-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json"),
    )
    parser.add_argument(
        "--rerank-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json"),
    )
    parser.add_argument(
        "--winner-cross-stream-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json"),
    )
    parser.add_argument(
        "--next-gate-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_support_recommendations.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_support_recommendations_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_support_recommendations.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def fmt(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def policy_winner_lines(rerank: dict[str, Any]) -> list[str]:
    winners = rerank.get("policy_winners", {})
    if not isinstance(winners, dict):
        return []
    lines: list[str] = []
    for policy_id, winner in sorted(winners.items()):
        if not isinstance(winner, dict):
            continue
        lines.append(
            f"{policy_id}: winner={winner.get('winner_candidate_id')}, "
            f"value={winner.get('winner_objective_like_value')}, "
            f"winner_in_current_gaussian_best_tie_set={winner.get('winner_in_current_gaussian_best_tie_set')}, "
            f"current_rank={winner.get('current_accepted_rank')}"
        )
    return lines


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    policy = read_json(args.policy_summary)
    decision = read_json(args.decision_summary)
    support = read_json(args.support_summary)
    support_spatial = read_json(args.support_spatial_summary)
    outlier = read_json(args.outlier_summary)
    rerank = read_json(args.rerank_summary)
    winner_cross = read_json(args.winner_cross_stream_summary)
    next_gate = read_json(args.next_gate_summary)

    rows = [
        {
            "decision_id": "D01_current_report_policy",
            "topic": "Recorded direct-permeability policy",
            "current_evidence": (
                f"current Gaussian objective={policy.get('current_gaussian_objective')}; "
                f"active rows={policy.get('active_direct_rows')}; "
                f"effective objective weight={policy.get('effective_objective_weight')}; "
                f"recommended current-report policy={decision.get('recommended_current_report_policy')}"
            ),
            "recommendation": (
                "Keep the duplicate-weighted rowwise Gaussian direct-permeability policy "
                "as the current-report default for reproducibility."
            ),
            "what_not_to_do": (
                "Do not silently replace the recorded active objective with a robust, "
                "support-aggregated, capped, or outlier-filtered policy."
            ),
            "decision_required_before_change": (
                "The modelling team must explicitly approve any non-default likelihood formula "
                "and rerun the scenario/current-field/readiness audits."
            ),
            "effect_on_ogs_spending": "No new same-support OGS batch is justified by this row alone.",
        },
        {
            "decision_id": "D02_same_support_lower_bound",
            "topic": "Same-support field-search limit",
            "current_evidence": (
                f"current objective={support.get('current_row_gaussian_objective')}; "
                f"single-support lower bound={support.get('single_support_lower_bound_objective')}; "
                f"reducible gap={support.get('same_support_reducible_objective_gap')}; "
                f"support groups at lower bound={support.get('support_groups_current_at_lower_bound')}/"
                f"{support.get('support_group_count')}; "
                f"spatial active/repeated/range>=2 support cells="
                f"{support_spatial.get('active_support_cell_count')}/"
                f"{support_spatial.get('repeated_support_cell_count')}/"
                f"{support_spatial.get('support_cells_observed_range_ge_2_log10')}"
            ),
            "recommendation": (
                "Treat the remaining direct permeability loss as irreducible by another "
                "one-value-per-support-cell field in the current support map."
            ),
            "what_not_to_do": (
                "Do not spend more OGS runs on the same support and same row-Gaussian "
                "objective expecting the dominant direct loss to drop."
            ),
            "decision_required_before_change": (
                "Change support mapping, likelihood semantics, measurement interpretation, "
                "bounds, tensor shape, or accepted stream objective before reopening routine runs."
            ),
            "effect_on_ogs_spending": "Pause same-support active-objective OGS batches now.",
        },
        {
            "decision_id": "D03_support_aggregation",
            "topic": "Support-cell aggregation option",
            "current_evidence": (
                f"support groups={policy.get('support_group_count')}; repeated groups="
                f"{policy.get('support_groups_with_repeated_rows')}; groups range>=1 log10="
                f"{policy.get('support_groups_with_observed_range_ge_1_log10')}; "
                f"support mean objective={policy.get('support_mean_unit_objective')}; "
                f"support median objective={policy.get('support_median_unit_objective')}"
            ),
            "recommendation": (
                "Use support-cell aggregation only as an explicit alternative likelihood, "
                "not as an automatic correction."
            ),
            "what_not_to_do": (
                "Do not interpret the near-zero support-mean diagnostic as proof that the "
                "pulse-test dataset is physically resolved; it mostly proves the field matches "
                "duplicate-weighted support means."
            ),
            "decision_required_before_change": (
                "Choose mean, median, robust group, or another group statistic and state how "
                "repeated pulse-test rows should be weighted."
            ),
            "effect_on_ogs_spending": (
                "Existing-field rerank can be used first; new OGS is needed only after a "
                "non-default policy selects a candidate lacking state diagnostics."
            ),
        },
        {
            "decision_id": "D04_robust_row_policy",
            "topic": "Robust row likelihood option",
            "current_evidence": (
                f"row top-10 loss share={policy.get('row_loss_top_10_share')}; "
                f"Huber delta objective={policy.get('robust_huber_delta_2sigma_objective')}; "
                f"Student-t nu4 objective={policy.get('robust_student_t_nu4_objective')}; "
                f"row-Gaussian best ties={rerank.get('current_gaussian_best_tie_count')}"
            ),
            "recommendation": (
                "Keep robust row policies as candidate final-policy options, especially if "
                "the modelling team wants to reduce dominance by a few conflicting rows."
            ),
            "what_not_to_do": (
                "Do not call a robust result final until the residual scale, tail policy, and "
                "treatment of duplicate support rows are documented."
            ),
            "decision_required_before_change": (
                "Choose Huber, Student-t, capped Gaussian, or another robust form with explicit "
                "sigma, tail parameters, and normalization/weighting convention."
            ),
            "effect_on_ogs_spending": (
                "Huber and Student-t winners currently remain inside the row-Gaussian tie set; "
                "no immediate same-support OGS batch follows from these diagnostics alone."
            ),
        },
        {
            "decision_id": "D05_configured_scalar_outliers",
            "topic": "Configured scalar envelope rows",
            "current_evidence": (
                f"outlier rows={outlier.get('outlier_row_count')}; physical groups="
                f"{outlier.get('unique_physical_outlier_group_count')}; max envelope excess="
                f"{outlier.get('max_range_excess_log10')} log10; same-support range="
                f"{outlier.get('max_same_support_observed_range_log10')} log10; "
                f"bounds release={outlier.get('bounds_release_recommended_now')}; "
                f"tensor release={outlier.get('tensor_shape_release_recommended_now')}"
            ),
            "recommendation": (
                "Record the two active envelope rows as one duplicated BCD-A32 high-value "
                "case embedded in a larger same-support conflict; do not widen bounds or "
                "release tensor shape from these rows alone."
            ),
            "what_not_to_do": (
                "Do not treat the small envelope excess as sufficient evidence for a broader "
                "tensor-shape release."
            ),
            "decision_required_before_change": (
                "Accept this local disposition or choose an explicit outlier, capped, "
                "inside-only, bound-widening, or tensor-shape-release policy."
            ),
            "effect_on_ogs_spending": "This disposition does not reopen same-support active-objective OGS sampling.",
        },
        {
            "decision_id": "D06_existing_field_rerank",
            "topic": "No-OGS existing-field policy rerank",
            "current_evidence": (
                f"candidate fields scored={rerank.get('candidate_fields_scored')}; "
                f"current accepted in row-Gaussian best tie set="
                f"{rerank.get('current_accepted_in_current_gaussian_best_tie_set')}; "
                f"alternate policy winners outside tie set="
                f"{rerank.get('alternate_policy_winner_outside_current_gaussian_best_set_count')}"
            ),
            "recommendation": (
                "Use the existing-field rerank as decision evidence before proposing new "
                "field families."
            ),
            "what_not_to_do": (
                "Do not promote an alternate-policy winner solely from direct-permeability "
                "reranking."
            ),
            "decision_required_before_change": (
                "If the accepted formula differs from these audited policies, rerun the rerank "
                "under the exact accepted formula."
            ),
            "effect_on_ogs_spending": (
                "Only non-default winners that are not already executed/scored need targeted "
                "OGS execution after policy acceptance."
            ),
        },
        {
            "decision_id": "D07_cross_stream_requirement",
            "topic": "Non-default direct-policy winners",
            "current_evidence": (
                f"policy winner rows={winner_cross.get('policy_winner_rows')}; "
                f"with cross-stream scorecard={winner_cross.get('policy_winner_rows_with_cross_stream_scorecard')}; "
                f"outside-tie direct-only winners={winner_cross.get('outside_tie_direct_only_policy_winner_rows')}; "
                f"current accepted mean rank={winner_cross.get('current_accepted_mean_rank')}; "
                f"row-Gaussian representative mean rank={winner_cross.get('row_gaussian_representative_mean_rank')}"
            ),
            "recommendation": (
                "Require OGS state sampling and cross-stream diagnostics before any direct-only "
                "non-default winner can replace the current active field."
            ),
            "what_not_to_do": (
                "Do not treat direct-only materialized VTU candidates as final all-measurement "
                "candidates."
            ),
            "decision_required_before_change": (
                "After a non-default direct policy is approved, execute or audit the selected "
                "winner through OGS/state/NMR/ERT/Taupe diagnostics before promotion."
            ),
            "effect_on_ogs_spending": "Targeted OGS execution is conditional on policy acceptance and candidate selection.",
        },
        {
            "decision_id": "D08_next_field_fit_gate",
            "topic": "Next OGS field-fit action",
            "current_evidence": (
                f"gate status={next_gate.get('status')}; recommendation="
                f"{next_gate.get('overall_recommendation')}; executable same-support batch now="
                f"{next_gate.get('executable_same_support_active_objective_batch_now')}; "
                f"open blockers={next_gate.get('open_blocker_count')}"
            ),
            "recommendation": (
                "Pause same-support active-objective production sampling. Reopen only after "
                "a likelihood/support/bounds/tensor-shape decision or accepted measurement-stream "
                "objective changes the problem."
            ),
            "what_not_to_do": (
                "Do not present the current direct-permeability field as final or continue "
                "the same production sampler by inertia."
            ),
            "decision_required_before_change": (
                "Choose a direct-permeability policy and close or explicitly exclude external "
                "stream gates before final promotion."
            ),
            "effect_on_ogs_spending": "No same-support active-objective batch is executable now.",
        },
    ]
    frame = pd.DataFrame(rows)
    policy_lines = policy_winner_lines(rerank)
    summary = {
        "status": "permeability_likelihood_support_recommendations_generated",
        "recommendation_count": int(frame.shape[0]),
        "current_report_policy": decision.get("recommended_current_report_policy"),
        "current_gaussian_objective": policy.get("current_gaussian_objective"),
        "active_direct_rows": policy.get("active_direct_rows"),
        "support_group_count": policy.get("support_group_count"),
        "support_groups_with_observed_range_ge_1_log10": policy.get(
            "support_groups_with_observed_range_ge_1_log10"
        ),
        "support_conflict_spatial_status": support_spatial.get("status"),
        "support_conflict_spatial_active_support_cell_count": support_spatial.get("active_support_cell_count"),
        "support_conflict_spatial_repeated_support_cell_count": support_spatial.get("repeated_support_cell_count"),
        "support_conflict_spatial_range_ge_2_log10_cell_count": (
            support_spatial.get("support_cells_observed_range_ge_2_log10")
        ),
        "support_conflict_spatial_top_conflict_cell": support_spatial.get("top_conflict_cell", {}),
        "current_at_single_support_lower_bound": support.get("current_at_single_support_lower_bound"),
        "same_support_reducible_objective_gap": support.get("same_support_reducible_objective_gap"),
        "same_support_active_objective_batch_executable_now": next_gate.get(
            "executable_same_support_active_objective_batch_now"
        ),
        "bounds_release_recommended_now": outlier.get("bounds_release_recommended_now"),
        "tensor_shape_release_recommended_now": outlier.get("tensor_shape_release_recommended_now"),
        "alternate_policy_winner_outside_current_gaussian_best_set_count": rerank.get(
            "alternate_policy_winner_outside_current_gaussian_best_set_count"
        ),
        "outside_tie_direct_only_policy_winner_rows": winner_cross.get(
            "outside_tie_direct_only_policy_winner_rows"
        ),
        "final_promotion_unblocked_by_this_packet": False,
        "next_action": (
            "Keep the rowwise Gaussian direct-permeability policy as the current-report "
            "default, pause same-support active-objective OGS sampling, and require an "
            "explicit likelihood/support/outlier/bounds/tensor-shape decision before "
            "reopening field-fit execution."
        ),
        "policy_winner_summary_lines": policy_lines,
        "source_artifacts": [
            str(args.policy_summary),
            str(args.decision_summary),
            str(args.support_summary),
            str(args.support_spatial_summary),
            str(args.outlier_summary),
            str(args.rerank_summary),
            str(args.winner_cross_stream_summary),
            str(args.next_gate_summary),
        ],
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Permeability Likelihood And Support Recommendations",
        "",
        "This generated packet consolidates the direct-permeability likelihood, support,",
        "outlier, rerank, cross-stream, and next-field-fit audits into one decision-support",
        "record.  It does not change the active objective, alter OGS inputs, approve a",
        "non-default likelihood, or promote a field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Recommendations: {summary['recommendation_count']}",
        f"- Current-report policy: `{summary.get('current_report_policy')}`",
        f"- Current Gaussian objective: {summary.get('current_gaussian_objective')}",
        f"- Active direct rows: {summary.get('active_direct_rows')}",
        f"- Support groups: {summary.get('support_group_count')}",
        f"- Groups with observed range >= 1 log10: {summary.get('support_groups_with_observed_range_ge_1_log10')}",
        f"- Spatial support cells active/repeated/range>=2 log10: "
        f"{summary.get('support_conflict_spatial_active_support_cell_count')}/"
        f"{summary.get('support_conflict_spatial_repeated_support_cell_count')}/"
        f"{summary.get('support_conflict_spatial_range_ge_2_log10_cell_count')}",
        f"- Current at single-support lower bound: `{summary.get('current_at_single_support_lower_bound')}`",
        f"- Same-support reducible objective gap: {summary.get('same_support_reducible_objective_gap')}",
        f"- Same-support active-objective batch executable now: `{summary.get('same_support_active_objective_batch_executable_now')}`",
        f"- Bounds release recommended now: `{summary.get('bounds_release_recommended_now')}`",
        f"- Tensor-shape release recommended now: `{summary.get('tensor_shape_release_recommended_now')}`",
        f"- Alternate policy winners outside row-Gaussian best tie set: {summary.get('alternate_policy_winner_outside_current_gaussian_best_set_count')}",
        f"- Outside-tie direct-only policy winners: {summary.get('outside_tie_direct_only_policy_winner_rows')}",
        f"- Final promotion unblocked by this packet: `{summary.get('final_promotion_unblocked_by_this_packet')}`",
        "",
        "## Recommendation Table",
        "",
        "| Decision | Topic | Recommendation | Effect on OGS spending |",
        "| --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['decision_id']}` | {row['topic']} | {row['recommendation']} | "
            f"{row['effect_on_ogs_spending']} |"
        )

    lines.extend(["", "## Detailed Rows", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['decision_id']}` {row['topic']}",
                "",
                f"- Current evidence: {row['current_evidence']}",
                f"- Recommendation: {row['recommendation']}",
                f"- What not to do: {row['what_not_to_do']}",
                f"- Decision required before change: {row['decision_required_before_change']}",
                f"- Effect on OGS spending: {row['effect_on_ogs_spending']}",
                "",
            ]
        )

    lines.extend(["## Policy Winner Snapshot", ""])
    for line in summary.get("policy_winner_summary_lines", []):
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The active field is already at the single-support lower bound for the current one-value-per-support-cell mapping.",
            "- The support-conflict spatial audit maps those conflicts onto the current mesh, so support or likelihood changes can be reviewed against concrete cells rather than only aggregate counts.",
            "- The remaining direct pulse-test mismatch is therefore a likelihood/support/measurement-interpretation question before it is another same-family field-search question.",
            "- Robust tails, support-cell aggregation, capped row loss, configured-scalar inside-only scoring, and bounds/tensor-shape release are all policy choices, not automatic corrections.",
            "- The current report should keep the rowwise Gaussian policy for reproducibility unless the modelling team records a different policy and regenerates the downstream audits.",
            "- Use `permeability_likelihood_policy_acceptance_record_template.md` as the separate signoff guardrail before treating any policy option as approved.",
            "- This packet does not unblock final promotion.",
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
