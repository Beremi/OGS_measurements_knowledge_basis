#!/usr/bin/env python3
"""Build a decision request for direct-permeability likelihood semantics."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"),
    )
    parser.add_argument(
        "--policy-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_audit.csv"),
    )
    parser.add_argument(
        "--group-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_group_summary.csv"),
    )
    parser.add_argument(
        "--rerank-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json"),
        help="Optional no-OGS rerank summary for existing materialized candidate fields.",
    )
    parser.add_argument(
        "--winner-cross-stream-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json"),
        help="Optional audit joining likelihood-policy winners to executed cross-stream scorecard evidence.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit"),
    )
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is None or value is pd.NA:
        return None
    return value


def fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    if abs(number) < 1.0e-5 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.{digits}g}"


def policy_metric(policy: pd.DataFrame, policy_id: str, column: str) -> Any:
    if policy.empty or column not in policy.columns:
        return None
    row = policy[policy["policy_id"].astype(str).eq(policy_id)]
    if row.empty:
        return None
    return row.iloc[0].get(column)


def build_options(summary: dict[str, Any], policy: pd.DataFrame) -> list[dict[str, Any]]:
    current_objective = policy_metric(policy, "current_duplicate_weighted_gaussian", "objective_like_value")
    capped_objective = policy_metric(policy, "capped_gaussian_abs1_log10", "objective_like_value")
    huber_objective = policy_metric(policy, "huber_delta_2sigma", "objective_like_value")
    student_objective = policy_metric(policy, "student_t_nu4", "objective_like_value")
    support_mean = policy_metric(policy, "support_cell_weighted_mean_unit_gaussian", "objective_like_value")
    support_median = policy_metric(policy, "support_cell_weighted_median_unit_gaussian", "objective_like_value")
    inside_only = policy_metric(policy, "configured_scalar_inside_only_gaussian", "objective_like_value")
    top10 = summary.get("row_loss_top_10_share")
    conflict_groups = summary.get("support_groups_with_observed_range_ge_1_log10")
    outside = summary.get("active_rows_outside_configured_scalar_range")
    return [
        {
            "option_id": "keep_rowwise_gaussian_default",
            "decision_type": "retain_current_default",
            "recommended_default": True,
            "objective_policy": "duplicate-weighted Gaussian row residuals in log10 intrinsic permeability with sigma=0.5",
            "diagnostic_value": current_objective,
            "required_actions": (
                "Keep the active objective unchanged for reproducibility; report large row conflicts explicitly; "
                "do not claim that further smooth field sampling is the primary remedy."
            ),
            "risk_or_caveat": (
                f"Top-10 row-loss share is {fmt(top10, 3)} and {conflict_groups} support groups span at least "
                "one log10 unit, so the active objective over-emphasizes conflicting rows unless this is intentional."
            ),
            "acceptance_criteria": (
                "A modelling-team statement that the current rowwise Gaussian objective remains the default despite "
                "support-cell conflicts, plus wording that the field is not final for all measurement streams."
            ),
        },
        {
            "option_id": "use_robust_row_likelihood",
            "decision_type": "change_default_or_create_scenario",
            "recommended_default": False,
            "objective_policy": "Huber, capped-Gaussian, or Student-t row residuals in log10 permeability",
            "diagnostic_value": student_objective,
            "required_actions": (
                "Review the existing-field capped/Huber/Student-t rerank, then choose the robust kernel, scale, "
                "and whether it becomes the default or only a sensitivity scenario; refresh readiness/field-selection "
                "audits and rerank again if the accepted formula or scale differs."
            ),
            "risk_or_caveat": (
                f"Diagnostic objective-like values: capped={fmt(capped_objective)}, Huber={fmt(huber_objective)}, "
                f"Student-t={fmt(student_objective)}. These values are not identical likelihood normalizations."
            ),
            "acceptance_criteria": (
                "A written kernel formula, scale, outlier treatment, and rule for comparing historical row-Gaussian "
                "candidate objectives to the new policy."
            ),
        },
        {
            "option_id": "aggregate_by_model_support_cell",
            "decision_type": "change_default_or_create_scenario",
            "recommended_default": False,
            "objective_policy": "collapse rows sharing one active model support cell before scoring",
            "diagnostic_value": support_mean,
            "required_actions": (
                "Review the existing-field support-mean/support-median rerank, then choose mean, median, or another "
                "support aggregate; define whether observations at nearby depths but the same OGS support cell should "
                "be one datum; rerank again if the accepted grouping, statistic, or weights differ."
            ),
            "risk_or_caveat": (
                f"Support-cell weighted-mean objective is {fmt(support_mean)} while median objective is "
                f"{fmt(support_median)}; this difference shows that the aggregation rule itself is consequential."
            ),
            "acceptance_criteria": (
                "A written grouping key, aggregation statistic, group weight, and reporting rule for within-support "
                "observation ranges."
            ),
        },
        {
            "option_id": "gate_configured_scalar_outliers",
            "decision_type": "source_or_parameterization_decision",
            "recommended_default": False,
            "objective_policy": "treat rows outside configured scalar tensor range separately from ordinary Gaussian rows",
            "diagnostic_value": inside_only,
            "required_actions": (
                "Decide whether out-of-range rows are source-interpretation issues, require wider tensor eigenvalue bounds, "
                "or require tensor-shape release; do not force them into the existing scalar-bounded family silently."
            ),
            "risk_or_caveat": (
                f"{outside} active rows are outside the configured scalar range; inside-only Gaussian objective is "
                f"{fmt(inside_only)} and does not remove the broader support-cell conflicts."
            ),
            "acceptance_criteria": (
                "A written outlier disposition for each configured-scalar-range row and an explicit release decision "
                "if bounds or tensor shape change."
            ),
        },
        {
            "option_id": "new_parameterization_before_more_ogs",
            "decision_type": "future_search_gate",
            "recommended_default": False,
            "objective_policy": "do not spend more routine OGS on current smooth/local-basis family without a new field family",
            "diagnostic_value": current_objective,
            "required_actions": (
                "If the rowwise objective remains default, propose a genuinely new parameterization or support model before "
                "more OGS batches; otherwise use the existing-field rerank as the first screen and refresh it if the newly "
                "accepted likelihood policy differs from the diagnostic policies."
            ),
            "risk_or_caveat": (
                "Existing anisotropy, local-basis, production, cross-stream hybrid, and structural/EDZ screens did not "
                "find a material direct-improving follow-up family."
            ),
            "acceptance_criteria": (
                "A next-run gate that names the accepted likelihood policy, the field family to be tested, and the "
                "materiality threshold for spending additional OGS runs."
            ),
        },
    ]


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Permeability Likelihood Decision Request",
        "",
        "This request converts the direct-permeability likelihood-policy audit into modelling-team decisions.",
        "It does not change the active objective by itself.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Active direct rows: {summary['active_direct_rows']}",
        f"- Current row-Gaussian objective: {fmt(summary['current_gaussian_objective'])}",
        f"- Support-cell mean diagnostic objective: {fmt(summary['support_mean_unit_objective'])}",
        f"- Support-cell median diagnostic objective: {fmt(summary['support_median_unit_objective'])}",
        f"- Support groups with observed range >= 1 log10: {summary['support_groups_with_observed_range_ge_1_log10']}",
        f"- Active rows outside configured scalar range: {summary['active_rows_outside_configured_scalar_range']}",
        f"- Top-10 row-loss share: {fmt(summary['row_loss_top_10_share'], 3)}",
        "",
        "## Existing-Field Rerank Evidence",
        "",
        f"- Rerank status: `{summary.get('scenario_rerank_status')}`",
        f"- Candidate fields scored: {summary.get('scenario_rerank_candidate_fields_scored')}",
        f"- Current row-Gaussian best-tie count: {summary.get('scenario_rerank_current_gaussian_best_tie_count')}",
        f"- Current accepted field tied for row-Gaussian best: {summary.get('scenario_rerank_current_accepted_in_current_gaussian_best_tie_set')}",
        f"- Diagnostic policy winners outside the row-Gaussian best tie set: {summary.get('scenario_rerank_alternate_policy_winner_outside_current_gaussian_best_set_count')}",
        "",
        "## Winner Cross-Stream Evidence",
        "",
        f"- Cross-stream audit status: `{summary.get('winner_cross_stream_status')}`",
        f"- Policy winner rows with cross-stream scorecard evidence: {summary.get('winner_cross_stream_policy_winner_rows_with_cross_stream_scorecard')}",
        f"- Unique winner fields with cross-stream scorecard evidence: {summary.get('winner_cross_stream_unique_winners_with_cross_stream_scorecard')}",
        f"- Direct-only policy winner rows: {summary.get('winner_cross_stream_direct_only_policy_winner_rows')}",
        f"- Outside-tie direct-only policy winner rows: {summary.get('winner_cross_stream_outside_tie_direct_only_policy_winner_rows')}",
        f"- Row-Gaussian representative active rank: {summary.get('winner_cross_stream_row_gaussian_representative_active_rank')}",
        f"- Current accepted active rank: {summary.get('winner_cross_stream_current_accepted_active_rank')}",
        "",
        "## Decision Options",
        "",
        "| Option | Default? | Policy | Diagnostic value | Required action | Acceptance criteria |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['option_id']}`",
                    "`yes`" if row["recommended_default"] else "`no`",
                    str(row["objective_policy"]).replace("|", "\\|"),
                    fmt(row["diagnostic_value"]),
                    str(row["required_actions"]).replace("|", "\\|"),
                    str(row["acceptance_criteria"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommended Local Policy For Current Report State",
            "",
            "Keep `keep_rowwise_gaussian_default` as the recorded active objective for reproducibility.",
            "Report robust row likelihoods, support-cell aggregation, and scalar-range outlier handling as explicit",
            "decision/scenario options, not as silent replacements for the active objective.",
            "",
            "## Required Answer",
            "",
            "Before more active-objective OGS spending, record one of the following:",
            "",
            "- The rowwise Gaussian objective remains the default and the next run uses a genuinely new parameterization.",
            "- A robust row likelihood becomes the default or an explicit scenario, with formula and scale.",
            "- A support-cell aggregation policy becomes the default or an explicit scenario, with grouping and weights.",
            "- Configured-scalar-range outliers are excluded, reinterpreted, or used to release bounds/tensor shape.",
            "",
            "## Source Artifacts",
            "",
            f"- Policy audit: `{summary['policy_summary_json']}`",
            f"- Policy comparison: `{summary['policy_csv']}`",
            f"- Group summary: `{summary['group_csv']}`",
            f"- Existing-field rerank summary: `{summary.get('scenario_rerank_summary_json')}`",
            f"- Winner cross-stream audit summary: `{summary.get('winner_cross_stream_summary_json')}`",
            f"- Decision CSV: `{summary['output_csv']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_catalogue_artifacts(catalogue_dir: Path, artifacts: list[Path], repo: Path) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for source in artifacts:
        if not source.exists():
            continue
        target = derived / source.name
        shutil.copy2(source, target)
        copies.append(
            {
                "source": os.path.relpath(source.resolve(), repo),
                "catalogue_copy": os.path.relpath(target.resolve(), repo),
            }
        )
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    policy_summary_path = resolve(repo, args.policy_summary).resolve()
    policy_csv = resolve(repo, args.policy_csv).resolve()
    group_csv = resolve(repo, args.group_csv).resolve()
    rerank_summary_path = resolve(repo, args.rerank_summary).resolve()
    winner_cross_stream_summary_path = resolve(repo, args.winner_cross_stream_summary).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    policy_summary = read_json(policy_summary_path)
    rerank_summary = read_json(rerank_summary_path)
    winner_cross_stream_summary = read_json(winner_cross_stream_summary_path)
    policy = pd.read_csv(policy_csv) if policy_csv.exists() else pd.DataFrame()
    rows = build_options(policy_summary, policy)
    frame = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False)

    summary = {
        "status": "permeability_likelihood_decision_request_generated",
        "decision_option_count": int(frame.shape[0]),
        "recommended_current_report_policy": "keep_rowwise_gaussian_default",
        "default_policy_change_required": False,
        "active_direct_rows": policy_summary.get("active_direct_rows"),
        "current_gaussian_objective": policy_summary.get("current_gaussian_objective"),
        "support_mean_unit_objective": policy_summary.get("support_mean_unit_objective"),
        "support_median_unit_objective": policy_summary.get("support_median_unit_objective"),
        "support_groups_with_observed_range_ge_1_log10": policy_summary.get(
            "support_groups_with_observed_range_ge_1_log10"
        ),
        "active_rows_outside_configured_scalar_range": policy_summary.get(
            "active_rows_outside_configured_scalar_range"
        ),
        "row_loss_top_10_share": policy_summary.get("row_loss_top_10_share"),
        "scenario_rerank_status": rerank_summary.get("status"),
        "scenario_rerank_candidate_fields_scored": rerank_summary.get("candidate_fields_scored"),
        "scenario_rerank_current_gaussian_best_tie_count": rerank_summary.get("current_gaussian_best_tie_count"),
        "scenario_rerank_current_accepted_in_current_gaussian_best_tie_set": rerank_summary.get(
            "current_accepted_in_current_gaussian_best_tie_set"
        ),
        "scenario_rerank_alternate_policy_winner_outside_current_gaussian_best_set_count": rerank_summary.get(
            "alternate_policy_winner_outside_current_gaussian_best_set_count"
        ),
        "winner_cross_stream_status": winner_cross_stream_summary.get("status"),
        "winner_cross_stream_policy_winner_rows_with_cross_stream_scorecard": winner_cross_stream_summary.get(
            "policy_winner_rows_with_cross_stream_scorecard"
        ),
        "winner_cross_stream_unique_winners_with_cross_stream_scorecard": winner_cross_stream_summary.get(
            "unique_winners_with_cross_stream_scorecard"
        ),
        "winner_cross_stream_direct_only_policy_winner_rows": winner_cross_stream_summary.get(
            "direct_only_policy_winner_rows"
        ),
        "winner_cross_stream_outside_tie_direct_only_policy_winner_rows": winner_cross_stream_summary.get(
            "outside_tie_direct_only_policy_winner_rows"
        ),
        "winner_cross_stream_row_gaussian_representative_active_rank": winner_cross_stream_summary.get(
            "row_gaussian_representative_active_rank"
        ),
        "winner_cross_stream_current_accepted_active_rank": winner_cross_stream_summary.get(
            "current_accepted_active_rank"
        ),
        "policy_summary_json": str(policy_summary_path),
        "policy_csv": str(policy_csv),
        "group_csv": str(group_csv),
        "scenario_rerank_summary_json": str(rerank_summary_path),
        "winner_cross_stream_summary_json": str(winner_cross_stream_summary_path),
        "output_csv": str(output_csv),
        "summary_json": str(summary_output),
        "summary_markdown": str(markdown_output),
        "notes": [
            "This is a decision request, not a likelihood change.",
            "The active default remains duplicate-weighted rowwise Gaussian until the modelling team approves a change.",
            "The existing-field rerank and winner cross-stream audit are now available as evidence, but any accepted non-default policy should still trigger refreshed readiness audits and, if needed, targeted follow-up fields.",
        ],
    }
    write_markdown(markdown_output, rows, summary)
    summary["catalogue_copies"] = copy_catalogue_artifacts(
        catalogue_dir,
        [output_csv, markdown_output],
        repo,
    )
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, rows, summary)
    summary["catalogue_copies"].extend(copy_catalogue_artifacts(catalogue_dir, [summary_output], repo))
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, rows, summary)
    copy_catalogue_artifacts(catalogue_dir, [summary_output, markdown_output], repo)

    print(f"wrote {output_csv}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")
    print(f"recommended current report policy: {summary['recommended_current_report_policy']}")


if __name__ == "__main__":
    main()
